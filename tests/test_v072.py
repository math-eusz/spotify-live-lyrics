import queue
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from interaction import InputParser, word_target
from lyrics import parse_lyrics
from paging import Pages
from spicy_bridge import timeline
from terminal_ui import Settings, TerminalUI, DEFAULTS
from sources import Player, Clock
from cli import main

class Version072(unittest.TestCase):
    def test_mouse_packets_split_at_every_boundary(self):
        packet='\033[<0;55;13M'
        for cut in range(len(packet)+1):
            parser=InputParser()
            events=parser.feed(packet[:cut])+parser.feed(packet[cut:])
            self.assertEqual(events,[('click',(54,12))])
        self.assertEqual(InputParser().feed('\033[A\033[<0;1;1m\033[<64;1;1Mq'),[('key','q')])

    def test_words_use_syllable_onset_and_native_estimates(self):
        lines,_=timeline({'Type':'Syllable','Content':[{'Type':'Vocal','Lead':{'Syllables':[
            {'Text':'wait','StartTime':3,'EndTime':4},
            {'Text':'now','StartTime':7,'EndTime':8}]}}]})
        self.assertEqual(word_target(lines[0],2),(3,False))
        self.assertEqual(word_target(lines[0],5),(7,False))
        self.assertIsNone(word_target(lines[0],4))
        native=parse_lyrics('[00:03]wait now\n[00:07]next')[0]
        target,estimate=word_target(native,6)
        self.assertTrue(estimate);self.assertTrue(3<target<7)

    def test_visible_cell_mapping_with_wrap_spacing_and_wide_characters(self):
        text='wait café 世界 now'
        for alignment in ('left','center','right'):
            cfg=Settings('/missing');cfg.values['layout'].update(alignment=alignment,lyrics_width='10')
            ui=TerminalUI(cfg)
            ui.compose('artist','title',text,anchor=text,size=(45,18))
            indexes={offset for row,offset in ui.hits.values()}
            self.assertEqual(indexes,{i for i,c in enumerate(text) if not c.isspace()})
            self.assertEqual(sum(offset==10 for row,offset in ui.hits.values()),2)
            ui.compose('artist','title','wait█',anchor=text,size=(45,18))
            self.assertEqual({offset for row,offset in ui.hits.values()},set(range(4)))
            ui.compose('artist','title',text,size=(45,18),help_open=True)
            self.assertFalse(ui.hits)
            cfg.values['layout']['click_seek']='false'
            ui.compose('artist','title',text,size=(45,18))
            self.assertFalse(ui.hits)

    def test_pause_beta_opt_out_and_short_marked_gap(self):
        lines=parse_lyrics('[00:02]wait\n[00:04]\n[00:04.2]now\n[00:06]\n[00:10]next')
        pages=Pages();cfg=dict(DEFAULTS['pages'],gap_animation='true')
        self.assertFalse(pages.render(lines,4.1,cfg)[2])
        self.assertIn('wait',pages.render(lines,4.1,cfg)[0])
        self.assertTrue(pages.render(lines,6,cfg)[2])
        self.assertEqual(pages.row_lines,[])
        cfg['gap_animation']='false'
        self.assertIn('now',pages.render(lines,6,cfg)[0])
        self.assertEqual(pages.render(lines,0,cfg)[0],'Introdução')
        self.assertEqual(pages.render(lines,1,cfg)[0],'Introdução')

    def test_beta_cli_and_existing_preferences(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini'
            for command,value in [('gaps','dots-beta'),('click-seek','off'),('gaps','off')]:
                self.assertEqual(main(['--config',str(path),command,value]),0)
            s=Settings(path);s.reload()
            self.assertEqual(s.values['pages']['gap_animation'],'false')
            self.assertEqual(s.values['layout']['click_seek'],'false')

    def test_background_seek_checks_track_and_resets_small_seek_clock(self):
        for actual in ('track:a','track:b'):
            player=Player.__new__(Player)
            player.name='spotify';player.lock=threading.Lock();player.data=None
            player.actions=queue.Queue(maxsize=8);player.seek_serial=0
            player.stop=threading.Event()
            self.assertTrue(player.seek(3.1,'track:a'))
            calls=[]
            def command(args):
                calls.append(args)
                if args[-1]=='{{mpris:trackid}}':return actual
                if 'metadata' in args:return 'Artist\tTitle\t9000000\t'+actual
                if 'status' in args:return 'Playing'
                if args[-1]=='position':player.stop.set();return '3.1'
                return ''
            with patch('sources.command',side_effect=command):player.work()
            sought=[args for args in calls if '3.100000' in args]
            self.assertEqual(bool(sought),actual=='track:a')
        clock=Clock()
        data=dict(uri='a',artist='Artist',title='Title',position=3,playing=True,measured_at=0)
        clock.position(data,0)
        data.update(position=2.8,measured_at=.1,seek_serial=1)
        self.assertEqual(clock.position(data,.1),2.8)

    def test_real_terminal_click_reaches_playerctl_and_restores_mouse(self):
        import os, pty, re, select, subprocess, sys, time
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);bins=home/'bin';bins.mkdir();log=home/'seek.txt'
            (bins/'playerctl').write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\na=sys.argv\nif "metadata" in a:\n print("track:a" if a[-1]=="{{mpris:trackid}}" else "Artist\\tFixture\\t60000000\\ttrack:a")\nelif "status" in a: print("Playing")\nelif a[-1]=="position": print("4")\nelif "position" in a: Path('+repr(str(log))+').write_text(a[-1])\n')
            (bins/'syncedlyrics').write_text('#!'+sys.executable+'\nprint("[00:01]Working native lyrics\\n[00:05]\\n[00:10]Next phrase")\n')
            for f in bins.iterdir():f.chmod(0o755)
            env=dict(os.environ,HOME=td,XDG_CONFIG_HOME=str(home/'cfg'),XDG_CACHE_HOME=str(home/'cache'),PATH=str(bins)+os.pathsep+os.environ['PATH'])
            cfg=home/'ui.ini';cfg.write_text('[visualizer]\nmode=off\n')
            master,slave=pty.openpty()
            proc=subprocess.Popen([sys.executable,str(root/'cli.py'),'--config',str(cfg)],env=env,stdin=slave,stdout=slave,stderr=slave)
            os.close(slave);output=b''
            try:
                until=time.monotonic()+5;point=None
                while time.monotonic()<until:
                    if select.select([master],[],[],.1)[0]:output+=os.read(master,65536)
                    screen=output.decode(errors='replace')
                    rows=re.split(r'\x1b\[(\d+);1H',screen)
                    for i in range(1,len(rows)-1,2):
                        plain=re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]','',rows[i+1])
                        if 'Working native' in plain:
                            point=(plain.index('native')+1,int(rows[i]));break
                    if point:break
                self.assertIsNotNone(point)
                os.write(master,f'\033[<0;{point[0]};{point[1]}M'.encode())
                until=time.monotonic()+3
                while time.monotonic()<until and not log.exists():
                    if select.select([master],[],[],.1)[0]:output+=os.read(master,65536)
                self.assertTrue(log.exists())
                self.assertTrue(1<float(log.read_text())<5)
                os.write(master,b'0')
                until=time.monotonic()+3
                while time.monotonic()<until and 'mode = auto' not in cfg.read_text():
                    if select.select([master],[],[],.1)[0]:output+=os.read(master,65536)
                reset_cfg=Settings(cfg);reset_cfg.reload()
                self.assertEqual(reset_cfg.values,DEFAULTS)
                self.assertTrue(list((home/'backup').glob('ui-*.ini')))
                os.write(master,b'q');proc.wait(timeout=3)
                while select.select([master],[],[],.1)[0]:
                    try:output+=os.read(master,65536)
                    except OSError:break
                self.assertIn(b'\033[?1000h\033[?1006h',output)
                self.assertIn(b'\033[?1000l\033[?1006l',output)
                self.assertEqual(proc.returncode,0)
            finally:
                if proc.poll() is None:proc.kill();proc.wait()
                os.close(master)

    def test_defaults_reset_backs_up_and_restore_recovers_preferences(self):
        from preferences import set_value, restore
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini'
            set_value(path,'colors.accent','#123456')
            set_value(path,'layout.click_seek','false')
            old=path.read_bytes()
            self.assertEqual(main(['--config',str(path),'config','reset']),0)
            cfg=Settings(path);cfg.reload()
            self.assertEqual(cfg.values,DEFAULTS)
            self.assertIn(old,[f.read_bytes() for f in (path.parent/'backup').glob('ui-*.ini')])
            restore(path)
            self.assertEqual(path.read_bytes(),old)
            path.write_text('broken INI')
            self.assertEqual(main(['--config',str(path),'config','reset']),0)
            cfg=Settings(path);cfg.reload()
            self.assertEqual(cfg.values,DEFAULTS)
