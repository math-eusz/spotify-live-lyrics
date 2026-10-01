import io
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from sources import Player, parse_player_snapshot, Lyrics
from lyrics import command, parse_lyrics, render_block
from spicy_bridge import timeline
from terminal_ui import Settings, DEFAULTS
from paging import Pages
from visualizer import Visualizer
from covers import Covers
from cli import main

ROOT=Path(__file__).resolve().parents[1]


class Revision081(unittest.TestCase):
    def test_player_snapshot_microseconds_and_missing_artist(self):
        raw='\tTitle\t60000000\ttrack:a\tAlbum\t\tPlaying\t12345678'
        result=parse_player_snapshot(raw,'spotify',1)
        self.assertEqual(result['artist'],'')
        self.assertAlmostEqual(result['position'],12.345678)
        self.assertEqual(result['duration'],60)
        for invalid in (raw.replace('12345678','nan'),raw.replace('Playing','broken'),raw+'\textra'):
            self.assertIsNone(parse_player_snapshot(invalid,'spotify',1))
        with patch('lyrics.subprocess.check_output',return_value=raw+'\n'):
            self.assertEqual(command(['playerctl','metadata']),raw)

    def test_one_query_per_player_refresh(self):
        player=Player.__new__(Player)
        player.name='auto';player.selected='spotify';player.next_discovery=float('inf')
        player.stop=threading.Event();player.lock=threading.Lock();player.data=None
        player.actions=queue.Queue();player.seek_serial=0
        def sample(args):
            player.stop.set()
            return 'Artist\tTitle\t60000000\ttrack:a\tAlbum\t\tPlaying\t1000000'
        with patch('sources.command',side_effect=sample) as call:
            player.work()
        self.assertEqual(call.call_count,1)
        self.assertEqual(player.snapshot()['position'],1)

    def test_source_timing_preserves_word_gap_in_both_typing_modes(self):
        lines,_=timeline({'Type':'Syllable','Content':[{'Type':'Vocal','Lead':{'Syllables':[
            {'Text':'hello','StartTime':1,'EndTime':1.5},
            {'Text':'world','StartTime':4,'EndTime':4.5}]}}]})
        for mode in ('smooth','words-beta'):
            pages=Pages()
            for pos in (1.8,2,3.8):
                body,_,_=pages.render(lines,pos,DEFAULTS['pages'],ahead=0,typing_mode=mode)
                self.assertEqual(body.rstrip('█ '),'hello')
            self.assertIn('hello wo',pages.render(lines,4.21,DEFAULTS['pages'],ahead=0,typing_mode=mode)[0])
            self.assertEqual(pages.render(lines,4.5,DEFAULTS['pages'],ahead=0,typing_mode=mode)[0],'hello world')

    def test_native_word_schedule_cached_without_losing_animation(self):
        lines=parse_lyrics('[00:01]longer words\n[00:05]next')
        render_block(lines,1,typing_mode='words-beta')
        slots=lines[0]['_word_slots']
        frames=[render_block(lines,1+i/100,typing_mode='words-beta') for i in range(400)]
        self.assertIs(lines[0]['_word_slots'],slots)
        self.assertTrue(any('lon█' in frame for frame in frames))
        self.assertTrue(any('longer words' in frame for frame in frames))

    def test_bad_timestamps_do_not_kill_lyrics_worker(self):
        huge='9'*5000
        self.assertEqual(parse_lyrics('['+huge+':00]bad'),[])
        self.assertEqual(parse_lyrics('[offset:'+huge+']\n[00:01]bad'),[])
        self.assertEqual(parse_lyrics('[00:'+('9'*500)+']bad'),[])
        self.assertEqual(parse_lyrics('[00:01]Keep [01:02] inside the text')[0]['text'],'Keep [01:02] inside the text')
        self.assertEqual([x['start'] for x in parse_lyrics('[00:01][00:03]Repeat')],[1,3])

    def test_read_only_cache_still_fetches_online(self):
        data=dict(uri='track:a',artist='A',title='B',duration=4)
        with tempfile.TemporaryDirectory() as td, patch('sources.LrcStore.maintain',side_effect=PermissionError), patch('sources.LrcStore.read',side_effect=PermissionError), patch('sources.LrcStore.save',side_effect=PermissionError), patch('sources.fetch_lrc',return_value=('[00:01]Online','fixture')):
            loader=Lyrics(td)
            try:
                loader.get(data)
                result=loader.results.get(timeout=1);loader.results.put(result)
                self.assertEqual(loader.get(data)[0][0]['text'],'Online')
            finally:loader.close();loader.thread.join(1)

    def test_visualizer_rate_limited_independently_from_typing(self):
        v=Visualizer();cfg=dict(DEFAULTS['visualizer'],mode='activity',fps='30')
        with patch.object(v,'_frame',wraps=v._frame) as render:
            for i in range(180):v.frame(cfg,True,False,i/180)
            self.assertLessEqual(render.call_count,31)
            self.assertGreaterEqual(render.call_count,25)
            v.frame(cfg,False,False,1)
            self.assertTrue(all(not row.strip() for row in v.render_rows))

    def test_cover_retry_is_delayed_and_worker_is_lazy(self):
        worker=Covers()
        self.assertIsNone(worker.thread)
        with patch('covers.load_cover',side_effect=[None,b'PNG']) as load:
            try:
                worker.get('https://example.test/a')
                value=worker.results.get(timeout=1);worker.results.put(value)
                self.assertIsNone(worker.get(value[0]))
                self.assertEqual(load.call_count,1)
                worker.cache_times[value[0]]-=31
                worker.get(value[0])
                result=worker.results.get(timeout=1);worker.results.put(result)
                self.assertEqual(worker.get(value[0]),b'PNG')
                self.assertEqual(load.call_count,2)
            finally:worker.close();worker.thread.join(1)

    def test_performance_profile_is_atomic_and_preserves_visual(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini'
            path.write_text('[layout]\nalignment=left\n[colors]\naccent=#ABCDEF\n[playback]\nsource=native\n')
            self.assertEqual(main(['--config',str(path),'performance','eco']),0)
            cfg=Settings(path);cfg.reload()
            self.assertEqual(cfg.values['playback']['fps'],'60')
            self.assertEqual(cfg.values['visualizer']['fps'],'30')
            self.assertEqual(cfg.values['layout']['alignment'],'left')
            self.assertEqual(cfg.values['colors']['accent'],'#ABCDEF')
            self.assertEqual(len(list((path.parent/'backup').glob('*.ini'))),1)

    def test_install_preflight_leaves_existing_code_untouched(self):
        for fault in ('config','completion'):
            with tempfile.TemporaryDirectory() as td:
                home=Path(td);root=home/'package';root.mkdir()
                import shutil
                for name in ('install_user.py','terminal_ui.py','visualizer.py','covers.py'):
                    shutil.copy2(ROOT/name,root/name)
                # All runtime files must exist for preflight; source isn't executed.
                from install_user import RUNTIME
                for name in RUNTIME:
                    if not (root/name).exists():shutil.copy2(ROOT/name,root/name)
                config=home/'config/spotify-live-lyrics';config.mkdir(parents=True)
                if fault=='config':
                    (config/'ui.ini').write_text('invalid INI')
                    (root/'completions').mkdir()
                    shutil.copy2(ROOT/'completions/sylrics.fish',root/'completions/sylrics.fish')
                target=home/'.local/share/spotify-live-lyrics';target.mkdir(parents=True)
                old=target/'cli.py';old.write_text('original version')
                env=dict(os.environ,HOME=td,XDG_CONFIG_HOME=str(home/'config'))
                result=subprocess.run([sys.executable,str(root/'install_user.py')],env=env,capture_output=True,text=True,timeout=4)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(old.read_text(),'original version')
                self.assertFalse((target/'backup').exists())
