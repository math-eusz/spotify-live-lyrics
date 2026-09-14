import tempfile
import unittest
from pathlib import Path
from terminal_ui import Settings, TerminalUI, DEFAULTS
from preferences import set_theme, set_value
from lyrics import parse_lyrics, render_block
from visualizer import Visualizer


class Revision061(unittest.TestCase):
    def test_dynamic_palette_and_switch_back_preserve_background(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini'
            set_theme(path,'dynamic')
            settings=Settings(path); settings.reload()
            ui=TerminalUI(settings)
            self.assertEqual(ui.color('accent'),'\033[34m')
            self.assertEqual(ui.color('background'),'\033[49m')
            set_theme(path,'purple')
            settings.next_check=0;settings.reload()
            self.assertIn('38;2;',ui.color('accent'))
            self.assertEqual(settings.values['theme']['mode'],'static')
            old=path.read_bytes()
            with self.assertRaises(ValueError):set_value(path,'theme.mode','invalid')
            self.assertEqual(path.read_bytes(),old)

    def test_help_is_on_demand_and_labels_optional(self):
        ui=TerminalUI(Settings('/missing'))
        normal='\n'.join(ui.compose('Artist','Song','Phrase',size=(100,40)))
        self.assertNotIn('q sair',normal)
        self.assertNotIn('[?] Ajuda',normal)
        help_text='\n'.join(ui.compose('Artist','Song','Phrase',size=(100,40),help_open=True))
        self.assertIn('Controles de reprodução',help_text)
        self.assertIn('Encerrar',help_text)
        v=Visualizer();cfg=dict(DEFAULTS['visualizer'],mode='activity')
        self.assertEqual(len(v.frame(cfg,True,False,1)),int(cfg['height']))
        self.assertEqual(len(v.frame(dict(cfg,show_label='true'),True,False,1)),int(cfg['height'])+1)
        self.assertEqual(v.frame(dict(cfg,mode='off'),True,False),())

    def test_beta_animates_then_holds_without_drift(self):
        lines=parse_lyrics('[00:02]One longer word!\n[00:06]Next phrase')
        def visible(pos,**kw):
            return render_block(lines,pos,ahead=0,typing_mode='words-beta',**kw).rstrip('█')
        self.assertEqual(visible(1),'...')
        self.assertEqual(visible(2),'O')
        frames=[visible(2+i/1000) for i in range(4000)]
        self.assertIn('On',frames)
        self.assertIn('One l',frames)
        self.assertIn('One long',frames)
        self.assertGreaterEqual(frames.count('One'),70)
        self.assertEqual(frames[-1],'One longer word!')
        self.assertEqual([len(x) for x in frames],sorted(len(x) for x in frames))
        self.assertEqual(visible(2),'O')
        self.assertEqual(render_block(lines,2,ahead=0),'O█')
        self.assertEqual(visible(2,complete=True),'One longer word!')

    def test_visualizer_follows_window_and_stays_above_border(self):
        import re
        ui=TerminalUI(Settings('/missing'))
        for width,height in [(100,30),(180,45),(35,18)]:
            rows=ui.compose('Artist','Song','Phrase',size=(width,height),visual=('▮'*32,))
            rows=[re.sub(r'\x1b\[[0-9;]*m','',r) for r in rows]
            y=next(i for i,r in enumerate(rows) if '▮' in r)
            self.assertEqual(y,height-3)
            count=rows[y].count('▮')
            self.assertEqual(count,int((width-9)*.85))
            self.assertTrue(rows[y].startswith('│'))
        ui.settings.values['visualizer']['width_percent']='0'
        rows=ui.compose('A','B','C',size=(100,30),visual=('▮'*32,))
        self.assertEqual(sum(r.count('▮') for r in rows),32)
