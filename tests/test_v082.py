import os
from pathlib import Path
import pty
import re
import select
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from terminal_ui import Settings, TerminalUI, cells, DEFAULTS
from local_player import LocalPlayer, collect_files
from visualizer import Visualizer
from cli import main

ROOT=Path(__file__).resolve().parents[1]


class Revision082(unittest.TestCase):
    def test_cover_survives_resize_and_controls_do_not_overlap_lyrics(self):
        settings=Settings('/missing');ui=TerminalUI(settings)
        for width,height in [(140,40),(70,24),(60,20),(44,14),(30,10),(15,5),(2,1)]:
            rows=ui.compose('Artist','Song','Current lyric',size=(width,height))
            self.assertIsNotNone(ui.cover_rect)
            x,y,w,h=ui.cover_rect
            self.assertTrue(0<=x<x+w<=max(1,width-1))
            self.assertTrue(0<=y<y+h<=height)
            self.assertEqual(len(rows),height)
            self.assertTrue(all(cells(re.sub(r'\033\[[0-9;]*m','',r))==max(1,width-1) for r in rows))
            self.assertFalse(set(ui.controls)&set(ui.hits))
            if width>=30 and height>=10:
                self.assertEqual(set(ui.controls.values()),{'previous','play-pause','next'})
        settings.values['layout']['cover']='false'
        ui.compose('Artist','Song','lyric',size=(60,20))
        self.assertIsNone(ui.cover_rect)
        settings.values['layout'].update(cover='true',view='lyrics')
        ui.compose('Artist','Song','lyric',size=(60,20))
        self.assertIsNone(ui.cover_rect);self.assertFalse(ui.controls)

    def test_controls_opt_out_and_queue_never_seeks_lyrics(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini'
            self.assertEqual(main(['--config',str(path),'controls','off']),0)
            settings=Settings(path);ui=TerminalUI(settings)
            ui.compose('Artist','Song','lyric',size=(60,20))
            self.assertFalse(ui.controls)
            self.assertTrue(ui.hits)
            ui.compose('Artist','Song','lyric',size=(60,20),queue_text='Fila local\n1. Example')
            self.assertFalse(ui.hits)

    def test_local_files_are_explicit_and_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'b.mp3').touch();(root/'a.flac').touch();(root/'notes.txt').touch()
            self.assertEqual([p.name for p in collect_files([td])],['a.flac','b.mp3'])
            with self.assertRaises(ValueError):collect_files(['https://example.com/song.mp3'])
            with self.assertRaises(ValueError):collect_files([root/'notes.txt'])
            with self.assertRaises(ValueError):collect_files([root/'b.mp3']*1001)

    def test_queue_move_uses_stable_ids_and_correct_mpv_destination(self):
        player=LocalPlayer.__new__(LocalPlayer)
        entries=[dict(id=i,filename=str(i)) for i in [9,4,7]]
        with patch.object(player,'request',side_effect=[entries,None]) as request:
            player.apply_action('queue',(4,'down'))
            self.assertEqual(request.call_args.args[0],['playlist-move',1,3])
        with patch.object(player,'request',side_effect=[entries,None]) as request:
            player.apply_action('queue',(4,'up'))
            self.assertEqual(request.call_args.args[0],['playlist-move',1,0])
        with patch.object(player,'request',return_value=entries) as request:
            player.apply_action('queue',(999,'play'))
            self.assertEqual(request.call_count,1)
        with patch.object(player,'request',return_value='/tmp/another.mp3') as request:
            player.apply_action('seek',('file:///tmp/song.mp3',10))
            self.assertEqual(request.call_count,1)

    def test_spectrum_failure_is_visible_without_optional_label(self):
        viz=Visualizer();cfg=dict(DEFAULTS['visualizer'],mode='spectrum',show_label='false')
        self.assertIn('CAVA',''.join(viz.frame(cfg,True,False)))

    def test_clickable_transport_works_with_word_clicks_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);bins=home/'bin';bins.mkdir();log=home/'actions.txt'
            (bins/'playerctl').write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\na=sys.argv\nif "-l" in a: print("spotify")\nelif "metadata" in a: print("Artist\\tFixture\\t60000000\\ttrack:a\\tAlbum\\t\\tPlaying\\t4000000")\nelif a[-1] in ("play-pause","next","previous"):\n with Path('+repr(str(log))+').open("a") as f: f.write(a[-1]+"\\n")\n')
            (bins/'syncedlyrics').write_text('#!'+sys.executable+'\nprint("[00:01]A fixture lyric\\n[00:10]Another lyric")\n')
            for f in bins.iterdir():f.chmod(0o755)
            cfg=home/'ui.ini';cfg.write_text('[layout]\nclick_seek=false\n[visualizer]\nmode=off\n')
            env=dict(os.environ,HOME=td,XDG_CONFIG_HOME=str(home/'cfg'),PATH=str(bins)+os.pathsep+os.environ['PATH'])
            master,slave=pty.openpty()
            proc=subprocess.Popen([sys.executable,str(ROOT/'cli.py'),'--config',str(cfg)],env=env,stdin=slave,stdout=slave,stderr=slave)
            os.close(slave);output=b''
            try:
                deadline=time.monotonic()+5;points={}
                while time.monotonic()<deadline and len(points)<3:
                    if select.select([master],[],[],.1)[0]:output+=os.read(master,65536)
                    rows=re.split(r'\x1b\[(\d+);1H',output.decode(errors='replace'))
                    for i in range(1,len(rows)-1,2):
                        plain=re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]','',rows[i+1])
                        for name in ('Anterior','Pausar','Próxima'):
                            if name in plain:points[name]=(plain.index(name)+1,int(rows[i]))
                self.assertEqual(len(points),3)
                for name,expected in [('Anterior','previous'),('Pausar','play-pause'),('Próxima','next')]:
                    x,y=points[name];os.write(master,f'\033[<0;{x};{y}M'.encode())
                    deadline=time.monotonic()+2
                    while time.monotonic()<deadline and (not log.exists() or expected not in log.read_text()):
                        if select.select([master],[],[],.05)[0]:os.read(master,65536)
                    self.assertIn(expected,log.read_text())
                os.write(master,b'q');proc.wait(timeout=3)
                self.assertEqual(proc.returncode,0)
            finally:
                if proc.poll() is None:proc.kill();proc.wait()
                os.close(master)

    def test_local_backend_json_ipc_pause_seek_queue_and_shutdown(self):
        import socket
        try:
            probe=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        except PermissionError:
            self.skipTest('Este ambiente bloqueia sockets Unix; executado no CI Linux.')
        probe.close()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fake=root/'mpv';audio=root/'song.wav';audio.touch()
            fake.write_text('#!'+sys.executable+'\n'+r'''
import json,socket,sys
from pathlib import Path
address=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--input-ipc-server='))
files=sys.argv[sys.argv.index('--')+1:]
entries=[dict(id=i+10,filename=name) for i,name in enumerate(files)]
index=0;paused=False;position=2
server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);server.bind(address);server.listen(1)
conn,_=server.accept();reader=conn.makefile('rb')
for raw in reader:
 msg=json.loads(raw);args=msg['command'];data=None
 if args[0]=='get_property':
  key=args[1]
  if key=='playlist':data=[dict(e,current=i==index) for i,e in enumerate(entries)]
  elif key=='path':data=entries[index]['filename']
  elif key=='metadata':data={'ARTIST':'Fixture','TITLE':'Local song'}
  elif key=='time-pos':data=position
  elif key=='duration':data=60
  elif key=='pause':data=paused
  elif key=='idle-active':data=False
 elif args[0]=='cycle':paused=not paused
 elif args[0]=='seek':position=args[1]
 elif args[0]=='set_property':
  if args[1]=='playlist-pos':index=args[2]
  elif args[1]=='pause':paused=args[2]
 elif args[0]=='playlist-move':
  current=entries[index]['id'];old,new=args[1:];item=entries.pop(old)
  entries.insert(new-1 if old<new else new,item)
  index=next(i for i,e in enumerate(entries) if e['id']==current)
 conn.sendall((json.dumps({'event':'tick'})+'\n').encode())
 conn.sendall((json.dumps({'request_id':msg['request_id'],'error':'success','data':data})+'\n').encode())
'''.replace("+'\\\\n'", "+'\\n'"))
            # Fixture is an IPC peer, not a real audio decoder.
            fake.chmod(0o755)
            with patch('local_player.shutil.which',return_value=str(fake)):
                player=LocalPlayer([audio,audio])
            def until(predicate):
                end=time.monotonic()+3
                while time.monotonic()<end:
                    if predicate():return
                    time.sleep(.01)
                self.fail('IPC did not reach expected state: '+player.error)
            try:
                until(lambda:player.snapshot() is not None)
                self.assertEqual(player.snapshot()['artist'],'Fixture')
                self.assertEqual(len(player.playlist()),2)
                player.control('play-pause')
                until(lambda:not player.snapshot()['playing'])
                player.seek(12,audio.as_uri())
                until(lambda:player.snapshot()['position']==12)
                player.queue_action(10,'down')
                until(lambda:player.playlist()[1]['id']==10)
                player.queue_action(11,'play')
                until(lambda:player.playlist()[0].get('current') and player.snapshot()['playing'])
            finally:
                player.close()
            self.assertIsNotNone(player.proc.poll())
            self.assertFalse(player.thread.is_alive())
            self.assertFalse(Path(player.socket_path).parent.exists())

    def test_real_mpv_decodes_audio_and_controls_queue(self):
        import shutil
        import wave
        if not shutil.which('mpv'):
            self.skipTest('mpv não instalado neste ambiente; teste executado no CI Linux.')
        with tempfile.TemporaryDirectory() as td:
            files=[Path(td)/name for name in ('one.wav','two.wav','three.wav')]
            for file in files:
                with wave.open(str(file),'wb') as audio:
                    audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(8000)
                    audio.writeframes(b'\0\0'*8000*10)
            real_popen=subprocess.Popen
            def silent(args,**kwargs):
                # Decode real audio through mpv, without a physical output device in CI.
                return real_popen([args[0],'--ao=null',*args[1:]],**kwargs)
            with patch('local_player.subprocess.Popen',side_effect=silent):
                player=LocalPlayer(files)
            def until(predicate):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    if predicate():return
                    time.sleep(.02)
                self.fail('mpv: '+player.error)
            try:
                until(lambda:player.snapshot() and player.snapshot()['duration']>9)
                player.control('play-pause')
                until(lambda:player.snapshot() and not player.snapshot()['playing'])
                player.seek(4,files[0].as_uri())
                until(lambda:abs(player.snapshot()['position']-4)<.2)
                identity=player.playlist()[0]['id']
                player.queue_action(identity,'down')
                until(lambda:player.playlist()[1]['id']==identity)
                player.queue_action(identity,'up')
                until(lambda:player.playlist()[0]['id']==identity)
                player.queue_action(player.playlist()[2]['id'],'play')
                until(lambda:player.snapshot() and player.snapshot()['uri']==files[2].as_uri() and player.snapshot()['playing'])
            finally:
                player.close()
            self.assertFalse(player.thread.is_alive())

    def test_local_lrc_is_used_offline_before_online_lookup(self):
        from sources import Lyrics
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'song.mp3';path.touch()
            path.with_suffix('.lrc').write_text('[00:01]Offline lyric\n[00:04]Next phrase\n')
            data=dict(uri=path.as_uri(),artist='Artist',title='Song',duration=30,local_path=str(path))
            with patch('sources.fetch_lrc',side_effect=AssertionError('Must not request online lyrics')):
                loader=Lyrics(Path(td)/'cache')
                try:
                    loader.get(data)
                    result=loader.results.get(timeout=2)
                    self.assertEqual(result[1][0]['text'],'Offline lyric')
                    self.assertIn('local',result[2])
                finally:
                    loader.close();loader.thread.join(timeout=1)

    def test_queue_selection_remains_visible_in_mini_player(self):
        ui=TerminalUI(Settings('/missing'))
        queue_text='Fila local · J/K selecionar · U/D mover · Enter tocar · F fechar\n'+'\n'.join(
            ('›' if i==8 else ' ')+f' {i}. File' for i in range(15))
        for size in [(44,14),(30,10),(90,28)]:
            rows=ui.compose('Artist','Title','Lyric',size=size,queue_text=queue_text)
            self.assertTrue(any('› 8. File' in re.sub(r'\033\[[0-9;]*m','',row) for row in rows))
            self.assertFalse(ui.hits)
