import configparser
import io
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from terminal_ui import DEFAULTS, Settings
from preferences import ensure,set_value
from lyrics import parse_lyrics
from paging import Pages,page_starts
from sources import Clock,Lyrics,fetch_lrc
from app import choose_source,same_track
from visualizer import Visualizer


def data(name='A'):
    return dict(uri=name,artist='Artist',title=name,duration=60,position=0,playing=True,measured_at=0)


class Version06(unittest.TestCase):
    def test_dynamic_pages_fast_slow_and_hard_cap(self):
        fast=[dict(start=i,end=i+.9,blank=None) for i in range(20)]
        slow=[dict(start=i*8,end=i*8+7.9,blank=None) for i in range(8)]
        cfg=DEFAULTS['pages']
        self.assertEqual(page_starts(fast,cfg)[:3],[0,6,12])
        self.assertEqual(page_starts(slow,cfg),[0,2,4,6])
        self.assertEqual(page_starts(fast,dict(cfg,mode='fixed',max_lines='4')),[0,4,8,12,16])

    def test_gap_can_end_page_after_one_phrase(self):
        lines=[dict(start=0,end=1,blank=1),dict(start=10,end=11,blank=None)]
        self.assertEqual(page_starts(lines,DEFAULTS['pages']),[0,1])

    def test_page_transition_does_not_anticipate_and_seek_is_deterministic(self):
        lines=parse_lyrics('[00:10]First\n[00:12]Second\n[00:14]Third\n[00:16]Fourth')
        pages=Pages();cfg=dict(DEFAULTS['pages'],max_lines='2',mode='fixed')
        before=pages.render(lines,13.99,cfg)[0]
        self.assertIn('Second',before)
        self.assertNotIn('Third',before)
        self.assertNotIn('Second',pages.render(lines,14,cfg)[0])
        self.assertEqual(before,pages.render(lines,13.99,cfg)[0])
        self.assertTrue(pages.render(lines,0,cfg)[2])

    def test_native_ignores_spicy_and_auto_ignores_wrong_track(self):
        native=data();spicy=data('B');lines=[{'text':'wrong'}]
        self.assertEqual(choose_source('native',native,spicy,lines),(native,[],'Nativo'))
        self.assertEqual(choose_source('auto',native,spicy,lines),(native,[],'Nativo'))
        spicy=dict(native)
        self.assertEqual(choose_source('auto',native,spicy,lines)[1],lines)
        self.assertEqual(choose_source('auto',native,spicy,[])[1],[])
        self.assertIsNone(choose_source('spicy',native,None,[])[0])

    def test_pause_seek_and_stale_clock(self):
        clock=Clock();d=data()
        self.assertEqual(clock.position(d,0),0)
        self.assertAlmostEqual(clock.position(d,.2),.2)
        self.assertAlmostEqual(clock.position(d,5),.5)
        d.update(position=20,measured_at=6)
        self.assertEqual(clock.position(d,6),20)
        d.update(position=20.2,measured_at=6.2,playing=False)
        self.assertAlmostEqual(clock.position(d,6.2),20.2)
        self.assertAlmostEqual(clock.position(d,20),20.2)
        d.update(position=3,measured_at=21)
        self.assertEqual(clock.position(d,21),3)

    def test_config_migration_preserves_layout_and_invalid_value_is_atomic(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini'
            path.write_text('[layout]\nalignment = left\nshow_source = true\n')
            ensure(path)
            s=Settings(path);s.reload()
            self.assertEqual(s.values['layout']['alignment'],'left')
            self.assertEqual(s.values['playback']['source'],'native')
            self.assertFalse(s.flag('show_source'))
            before=path.read_bytes()
            with self.assertRaises(ValueError):set_value(path,'pages.max_lines','0')
            self.assertEqual(path.read_bytes(),before)
            set_value(path,'visualizer.mode','off')
            s.next_check=0;s.reload()
            self.assertEqual(s.values['visualizer']['mode'],'off')
            self.assertTrue(list((path.parent/'backup').glob('ui-*.ini')))

    def test_direct_lrclib_works_without_syncedlyrics(self):
        response=io.BytesIO(json.dumps({'syncedLyrics':'[00:01]Native lyrics'}).encode())
        with patch('sources.shutil.which',return_value=None),patch('sources.urllib.request.urlopen',return_value=response) as request:
            raw,label=fetch_lrc(data())
        self.assertEqual(label,'LRCLIB')
        self.assertEqual(parse_lyrics(raw)[0]['text'],'Native lyrics')
        self.assertIn('duration=60',request.call_args.args[0].full_url)

    def test_lyric_loader_cache_survives_relaunch(self):
        with tempfile.TemporaryDirectory() as td,patch('sources.fetch_lrc',return_value=('[00:01]Cached','fixture')) as fetch:
            first=Lyrics(td)
            try:
                first.get(data())
                result=first.results.get(timeout=2);first.results.put(result)
                self.assertEqual(first.get(data())[0][0]['text'],'Cached')
            finally:first.close();first.thread.join(1)
            second=Lyrics(td)
            try:
                second.get(data())
                result=second.results.get(timeout=2);second.results.put(result)
                self.assertEqual(second.get(data())[0][0]['text'],'Cached')
                self.assertEqual(fetch.call_count,1)
            finally:second.close();second.thread.join(1)

    def test_visualizer_decorative_label_pause_and_missing_cava(self):
        v=Visualizer();cfg=dict(DEFAULTS['visualizer'],mode='activity')
        a=v.frame(cfg,True,True,1);b=v.frame(cfg,True,True,2)
        self.assertNotEqual(a,b)
        self.assertIn('animação',a[0])
        self.assertEqual(v.frame(cfg,False,True,1),v.frame(cfg,False,True,2))
        self.assertEqual(v.frame(dict(cfg,mode='off'),True,True),())
        self.assertIn('indisponível',v.frame(dict(cfg,mode='spectrum'),True,True)[0])
        v.values=[.8]*32;v.received=1
        self.assertIn('áudio',v.frame(dict(cfg,mode='auto'),True,True,1)[0])

    def test_cava_process_reads_raw_frames_and_shuts_down(self):
        with tempfile.TemporaryDirectory() as td:
            exe=Path(td)/'cava'
            exe.write_text('#!/usr/bin/env python3\nimport time\nprint("500;1000;0;",flush=True)\ntime.sleep(10)\n');exe.chmod(0o755)
            with patch.dict(os.environ,PATH=td+os.pathsep+os.environ['PATH']):
                v=Visualizer()
                try:
                    v.configure(DEFAULTS['visualizer'])
                    until=time.monotonic()+2
                    while not v.values and time.monotonic()<until:time.sleep(.01)
                    self.assertEqual(v.values,[.5,1,0])
                    proc=v.proc
                finally:v.close()
                self.assertIsNotNone(proc.poll())

    def test_install_and_native_app_without_spicetify(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            old=home/'.local/share/spotify-live-lyrics'
            old.mkdir(parents=True);(old/'lyrics.py').write_text('old version')
            bins=home/'fake-bin';bins.mkdir()
            (bins/'playerctl').write_text('#!/usr/bin/env python3\nimport sys\nif "metadata" in sys.argv: print("Artist\\tNative Fixture\\t60000000\\ttrack:a")\nelif "status" in sys.argv: print("Playing")\nelif "position" in sys.argv: print("4.0")\n')
            (bins/'syncedlyrics').write_text('#!/usr/bin/env python3\nprint("[00:01]Working native lyrics\\n[00:10]Next phrase")\n')
            for file in bins.iterdir():file.chmod(0o755)
            env=dict(os.environ,HOME=td,XDG_CONFIG_HOME=str(home/'.config'),XDG_CACHE_HOME=str(home/'.cache'),PATH=str(bins)+os.pathsep+os.environ['PATH'])
            subprocess.run(['sh',str(ROOT/'install.sh')],env=env,check=True,capture_output=True,timeout=5)
            command=home/'.local/bin/sylrics'
            version=subprocess.check_output([str(command),'--version'],env=env,text=True)
            self.assertIn('0.6.0',version)
            subprocess.run([str(command),'visualizer','off'],env=env,check=True,capture_output=True)
            self.assertEqual(next((old/'backup').glob('*/lyrics.py')).read_text(),'old version')
            master,slave=pty.openpty()
            proc=subprocess.Popen([str(command)],env=env,stdin=slave,stdout=slave,stderr=slave)
            os.close(slave);output=b''
            try:
                until=time.monotonic()+4
                while time.monotonic()<until:
                    if select.select([master],[],[],.1)[0]:output+=os.read(master,65536)
                    if b'Working native' in output:break
                self.assertIn(b'Native Fixture',output)
                self.assertIn(b'Working native',output)
                os.write(master,b'q')
                self.assertEqual(proc.wait(timeout=3),0)
            finally:
                if proc.poll() is None:proc.kill();proc.wait()
                os.close(master)
