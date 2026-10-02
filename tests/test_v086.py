import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tempfile
import unittest
from unittest.mock import patch
from copy import deepcopy
from terminal_ui import Settings, TerminalUI, DEFAULTS
from settings_menu import SettingsMenu
from interaction import InputParser

class SettingsEditor(unittest.TestCase):
    def test_preview_cancel_save_and_backup(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini';original='[layout]\ncover=true\n'
            path.write_text(original)
            menu=SettingsMenu();menu.begin(DEFAULTS)
            menu.index=list(DEFAULTS['layout']).index('cover')
            menu.handle(('key',' '),path)
            self.assertEqual(menu.preview()['layout']['cover'],'false')
            self.assertEqual(path.read_text(),original)
            self.assertEqual(menu.handle(('key','m'),path),'cancelled')
            self.assertEqual(menu.original['layout']['cover'],'true')
            menu.begin(DEFAULTS);menu.handle(('key',' '),path)
            self.assertEqual(menu.handle(('key','s'),path),'saved')
            cfg=Settings(path);cfg.reload();self.assertFalse(cfg.flag('cover'))
            self.assertIn(original,[p.read_text() for p in (path.parent/'backup').glob('*.ini')])

    def test_invalid_values_never_preview_or_replace_config(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini';path.write_text('[layout]\ncover=true\n')
            menu=SettingsMenu();menu.begin(DEFAULTS)
            menu.draft['playback']['fps']='-1';menu.revision+=1
            self.assertIsNone(menu.preview())
            self.assertIsNone(menu.handle(('key','s'),path))
            self.assertTrue(menu.open);self.assertTrue(menu.message)
            self.assertEqual(path.read_text(),'[layout]\ncover=true\n')
            menu.handle(('key','r'),path)
            self.assertIsNotNone(menu.preview())

    def test_arrows_and_escape_are_buffered(self):
        for arrow,name in [('A','up'),('B','down'),('C','right'),('D','left')]:
            parser=InputParser();self.assertEqual(parser.feed('\033'),[])
            self.assertEqual(parser.feed('['+arrow),[('nav',name)])
        parser=InputParser();parser.feed('\033')
        with patch('interaction.time.monotonic',return_value=parser.escape_at+.1):
            self.assertEqual(parser.flush(),[('key','\033')])

    def test_modal_owns_hits_and_cover_is_restored(self):
        settings=Settings('/missing');ui=TerminalUI(settings)
        for size in [(100,32),(45,16),(10,4)]:
            menu=SettingsMenu();menu.begin(DEFAULTS)
            ui.compose('Artist','Song','Lyric',size=size,menu=menu)
            self.assertFalse(ui.hits);self.assertFalse(ui.controls);self.assertIsNone(ui.cover_rect)
        ui.compose('Artist','Song','Lyric',size=(100,32))
        self.assertTrue(ui.hits);self.assertTrue(ui.controls);self.assertIsNotNone(ui.cover_rect)
        self.assertTrue(ui.menu_button)

    def test_text_editing_and_mouse_cancel_do_not_trigger_actions(self):
        menu=SettingsMenu();menu.begin(DEFAULTS)
        menu.index=list(DEFAULTS['layout']).index('font_family')
        menu.handle(('key','e'),Path('/unused'))
        menu.handle(('key','q'),Path('/unused'))
        self.assertTrue(menu.open);self.assertTrue(menu.editing)
        self.assertTrue(menu.buffer.endswith('q'))
        menu.hits[(1,1)]=('cancel',)
        self.assertEqual(menu.handle(('click',(1,1)),Path('/unused')),'cancelled')

    def test_terminal_menu_save_without_a_player(self):
        import os,pty,select,subprocess,time
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini';path.write_text('[visualizer]\nmode=off\n')
            master,slave=pty.openpty()
            proc=subprocess.Popen([sys.executable,str(root/'cli.py'),'--config',str(path),'demo'],stdin=slave,stdout=slave,stderr=slave,env=dict(os.environ,HOME=td))
            os.close(slave);output=b''
            def wait_for(text):
                nonlocal output
                deadline=time.monotonic()+4
                while time.monotonic()<deadline:
                    if select.select([master],[],[],.05)[0]:output+=os.read(master,65536)
                    if text.encode() in output:return
                self.fail('Missing: '+text+'\n'+output.decode(errors='replace')[-1000:])
            try:
                wait_for('Prévia interativa')
                os.write(master,b'm');wait_for('Configurações')
                # First option: full -> lyrics; save, then verify persisted setting.
                os.write(master,b'\033[Cs')
                deadline=time.monotonic()+3
                while time.monotonic()<deadline and 'view = lyrics' not in path.read_text():
                    if select.select([master],[],[],.05)[0]:output+=os.read(master,65536)
                self.assertIn('view = lyrics',path.read_text())
                os.write(master,b'm');time.sleep(.1);os.write(master,b'q')
                time.sleep(.1);self.assertIsNone(proc.poll())
                os.write(master,b'q');proc.wait(timeout=3);self.assertEqual(proc.returncode,0)
            finally:
                if proc.poll() is None:proc.kill();proc.wait()
                os.close(master)
