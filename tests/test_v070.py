import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from visualizer import fit_spectrum
from terminal_ui import Settings, TerminalUI, DEFAULTS, cells
from preferences import ensure, set_value, set_preset, restore, PRESETS
from paging import Pages
from lyrics import parse_lyrics
from cli import main

ANSI=re.compile(r'\x1b\[[0-9;]*m')

class Version070(unittest.TestCase):
    def test_bar_gap_and_thickness_survive_resize(self):
        for width in (1,2,7,31,87,153):
            for gap in range(6):
                for thickness in range(1,5):
                    row=fit_spectrum('█'*32,width,thickness,gap)
                    self.assertLessEqual(len(row),width)
                    self.assertFalse(row.startswith(' '))
                    self.assertFalse(row.endswith(' '))
                    if gap:
                        runs=re.findall(r' +',row)
                        self.assertTrue(all(len(run)==gap for run in runs))
                        self.assertTrue(all(len(run)==min(thickness,width) for run in re.findall(r'█+',row)))
        self.assertEqual(fit_spectrum('█',0),'')

    def test_fractional_resampling_is_gradual(self):
        self.assertEqual(fit_spectrum(' █',9,1,0),'     ████')

    def test_rolling_keeps_context_until_next_phrase_and_respects_seek(self):
        lines=parse_lyrics('[00:02]First\n[00:04]Second\n[00:06]Third\n[00:08]Fourth\n[00:10]Fifth')
        cfg=dict(DEFAULTS['pages'],mode='rolling',max_lines='3')
        pages=Pages()
        before=pages.render(lines,7.99,cfg)[0]
        self.assertIn('First',before)
        after=pages.render(lines,8,cfg)[0]
        self.assertNotIn('First',after)
        self.assertIn('Second',after)
        self.assertIn('Third',after)
        self.assertEqual(pages.render(lines,7.99,cfg)[0],before)
        self.assertTrue(pages.render(lines,0,cfg)[2])

    def test_rolling_starts_fresh_after_vocal_gap(self):
        lines=parse_lyrics('[00:02]First\n[00:04]\n[00:10]Next')
        body=Pages().render(lines,10,dict(DEFAULTS['pages'],mode='rolling'))[0]
        self.assertNotIn('First',body)

    def test_presets_preserve_sources_colors_and_can_be_undone(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini';ensure(path)
            set_value(path,'playback.source','spicy')
            set_value(path,'theme.mode','dynamic')
            set_value(path,'playback.sync_offset','0.3')
            for name in PRESETS:
                set_preset(path,name)
                s=Settings(path);s.reload()
                self.assertFalse(s.error)
                self.assertEqual(s.values['playback']['source'],'spicy')
                self.assertEqual(s.values['theme']['mode'],'dynamic')
                self.assertEqual(s.values['playback']['sync_offset'],'0.3')
            set_preset(path,'minimal')
            restore(path)
            s=Settings(path);s.reload()
            self.assertEqual(s.values['visualizer']['mode'],'auto')
            self.assertEqual(s.values['pages']['max_lines'],'5')

    def test_restore_can_recover_invalid_manual_edit(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini';ensure(path)
            set_value(path,'layout.padding','7')
            path.write_text('broken ini')
            self.assertEqual(main(['--config',str(path),'config','restore']),0)
            s=Settings(path);s.reload()
            self.assertFalse(s.error)

    def test_help_and_visualizer_stay_in_viewport(self):
        ui=TerminalUI(Settings('/missing'))
        for w,h in [(180,40),(70,18),(30,12),(15,5),(2,1)]:
            for help_open in (True,False):
                rows=ui.compose('Artista','Música','Uma frase█',anchor='Uma frase completa',
                    size=(w,h),help_open=help_open,visual=('█'*32,)*3)
                plain=[ANSI.sub('',r) for r in rows]
                self.assertEqual(len(plain),h)
                self.assertTrue(all(cells(r)==w-1 for r in plain))
                if w==70 and help_open:
                    self.assertIn('r: leitura','\n'.join(plain))

    def test_new_options_are_validated_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini';ensure(path)
            old=path.read_bytes()
            for key,value in [('visualizer.bar_spacing','6'),('visualizer.bar_width','0'),('layout.history_dim','bad')]:
                with self.assertRaises(ValueError):set_value(path,key,value)
                self.assertEqual(path.read_bytes(),old)
