import base64
import io
import os
from pathlib import Path
import queue
import re
import tempfile
import threading
import unittest
from unittest.mock import patch
from sources import resolve_player, Player, Clock
from terminal_ui import Settings, TerminalUI, cells
from covers import load_cover, KittyCover, Covers, MAX_BYTES
from cli import main


def plain(rows):
    return [re.sub(r'\033\[[0-9;]*m', '', row) for row in rows]


class Version080(unittest.TestCase):
    def test_selects_playing_spotify_family_and_preserves_current(self):
        states={'spotify':'Paused','spotify_player':'Playing','firefox':'Playing'}
        def command(args):
            return '\n'.join(states) if '-l' in args else states.get(args[2], '')
        with patch('sources.command',side_effect=command):
            self.assertEqual(resolve_player(),'spotify_player')
            self.assertEqual(resolve_player('spotify'),'spotify_player')
            states['spotify']='Playing'
            self.assertEqual(resolve_player(current='spotify_player'),'spotify_player')
            self.assertEqual(resolve_player('firefox'),'firefox')
            self.assertIsNone(resolve_player('missing'))
            del states['spotify_player'];del states['spotify']
            self.assertIsNone(resolve_player())

    def test_metadata_and_old_player_cannot_receive_new_seek(self):
        player=Player.__new__(Player)
        player.name='auto';player.selected='spotify_player';player.next_discovery=float('inf')
        player.stop=threading.Event();player.lock=threading.Lock();player.data=None
        player.seek_serial=0;player.actions=queue.Queue()
        player.seek(2,'track:a','spotify')
        calls=[]
        def command(args):
            calls.append(args)
            if args[-1]=='{{mpris:trackid}}':return 'track:a'
            if 'metadata' in args:
                player.stop.set()
                return 'Artist\tSong\t60000000\ttrack:a\tAlbum\thttps://example.test/a.jpg\tPlaying\t4000000'
            if 'status' in args:return 'Playing'
            if args[-1]=='position':player.stop.set();return '4'
            return ''
        with patch('sources.command',side_effect=command):player.work()
        self.assertFalse(any(args[-1]=='2.000000' for args in calls))
        data=player.snapshot()
        self.assertEqual(data['player'],'spotify_player')
        self.assertEqual(data['album'],'Album')
        self.assertEqual(data['art_url'],'https://example.test/a.jpg')

    def test_lyrics_only_hides_chrome_but_retains_word_hit_testing(self):
        cfg=Settings('/missing');cfg.values['layout']['view']='lyrics'
        ui=TerminalUI(cfg)
        rows=plain(ui.compose('Artist','Song','A lyric',album='Album',size=(100,28),visual=('▮▮▮',),notice='Notice'))
        screen='\n'.join(rows)
        for hidden in ('Artist','Song','Album','Notice','Em reprodução','╭','▮'):
            self.assertNotIn(hidden,screen)
        self.assertIn('A lyric',screen)
        self.assertIsNone(ui.cover_rect)
        self.assertTrue(ui.hits)
        cfg.values['layout']['view']='full'
        screen='\n'.join(plain(ui.compose('Artist','Song','A lyric',album='Album',size=(100,28))))
        self.assertIn('Album',screen);self.assertIsNotNone(ui.cover_rect)

    def test_layout_fits_small_and_large_windows(self):
        cfg=Settings('/missing');ui=TerminalUI(cfg)
        for width,height in [(1,1),(10,4),(40,12),(70,24),(130,36)]:
            rows=plain(ui.compose('Artist','A long title','visible lyric',size=(width,height),album='Album'))
            self.assertEqual(len(rows),height)
            self.assertTrue(all(cells(row)==max(1,width-1) for row in rows))
        rows=plain(ui.compose('Artist','Song','lyric',size=(70,24),album='Album'))
        self.assertTrue(any('Album' in row for row in rows))

    def test_cover_decodes_local_jpeg_and_rejects_unsupported_or_large_input(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow opcional não instalado')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'cover.jpg';Image.new('RGB',(32,48),'purple').save(p)
            png=load_cover(p.as_uri())
            self.assertTrue(png.startswith(b'\x89PNG'))
            self.assertEqual(Image.open(io.BytesIO(png)).size,(256,256))
            p.write_bytes(b'x'*(MAX_BYTES+1))
            self.assertIsNone(load_cover(p.as_uri()))
            self.assertIsNone(load_cover('http://example.test/a.jpg'))

    def test_graphics_chunks_decode_and_remove_only_own_image(self):
        cover=KittyCover();png=b'PNG fixture'*1000
        with patch('covers.supported',return_value=True):
            out=cover.update(png,(3,2,12,6))
            payloads=re.findall(r'\033_G[^;]+;([^\033]*)\033\\',out)
            self.assertEqual(base64.b64decode(''.join(payloads)),png)
            self.assertIn('C=1,q=2',out)
            self.assertEqual(cover.update(png,(3,2,12,6)),'')
            self.assertIn('a=d,d=I,i='+str(cover.image_id),cover.update(None,None))
            self.assertEqual(cover.clear(),'')

    def test_cover_failures_do_not_stop_loader_or_repeatedly_download(self):
        with patch('covers.load_cover',side_effect=ValueError('bad image')) as load:
            worker=Covers()
            try:
                self.assertIsNone(worker.get('bad'))
                result=worker.results.get(timeout=1);worker.results.put(result)
                self.assertIsNone(worker.get('bad'))
                self.assertEqual(load.call_count,1)
            finally:worker.close();worker.thread.join(1)

    def test_new_commands_persist_and_preserve_customization(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini';path.write_text('[colors]\naccent=#123456\n')
            for args in [('view','lyrics'),('cover','off'),('player','spotify_player')]:
                self.assertEqual(main(['--config',str(path),*args]),0)
            cfg=Settings(path);cfg.reload()
            self.assertEqual(cfg.values['layout']['view'],'lyrics')
            self.assertFalse(cfg.flag('cover'))
            self.assertEqual(cfg.values['playback']['player'],'spotify_player')
            self.assertEqual(cfg.values['colors']['accent'],'#123456')
