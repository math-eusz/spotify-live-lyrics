import math
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from terminal_ui import Settings, TerminalUI, DEFAULTS
from visualizer import Visualizer
from preferences import set_value
from cli import main

ANSI = re.compile(r'\x1b\[[0-9;]*m')

class Revision063(unittest.TestCase):
    def test_smoothing_attack_release_and_pause(self):
        v = Visualizer()
        a = v.smooth([1.0], 0, 120)[0]
        b = v.smooth([1.0], .02, 120)[0]
        c = v.smooth([0.0], .04, 120)[0]
        self.assertTrue(0 < a < b < 1)
        self.assertTrue(0 < c < b)
        self.assertEqual(v.smooth([1], .05, 120, False), [0])
        self.assertEqual(v.smooth([.8], .06, 0), [.8])
        v.close()
        self.assertIsNone(v.last_frame)

    def test_smoothing_is_independent_of_frame_rate(self):
        results = []
        for fps in (60, 180):
            v = Visualizer()
            v.smoothed = [0.0]; v.last_frame = 0
            for frame in range(1, fps+1):
                value = v.smooth([1.0], frame/fps, 500)[0]
            results.append(value)
        self.assertAlmostEqual(*results, places=10)

    def test_fractional_bars_and_pause(self):
        v=Visualizer()
        cfg=dict(DEFAULTS['visualizer'], mode='spectrum', smoothing_ms='0', height='1', width='8')
        v.values=[.125,.25,.375,.5,.625,.75,.875,1];v.received=1
        self.assertEqual(v.frame(cfg,True,False,1),('▁▂▃▄▅▆▇█',))
        self.assertEqual(v.frame(cfg,False,False,1),(' '*8,))

    def test_word_highlight_does_not_shift_text_or_leak(self):
        settings=Settings('/missing')
        ui=TerminalUI(settings)
        args=dict(artist='Artist',title='Song',body='Previous\nHello wor█',
                  anchor='Previous\nHello world',size=(90,30))
        before=ui.compose(**args)
        settings.values['layout']['word_highlight']='bold-beta'
        after=ui.compose(**args)
        self.assertEqual([ANSI.sub('',r) for r in before],[ANSI.sub('',r) for r in after])
        text='\n'.join(after)
        selected=re.findall(r'\x1b\[1;4m(.*?)\x1b\[22;24m',text)
        self.assertEqual([ANSI.sub('',x) for x in selected],['wor'])
        self.assertNotIn('\x1b[1m','\n'.join(ui.compose(**args,gap=True)))
        self.assertNotIn('\x1b[1m','\n'.join(ui.compose(**args,help_open=True)))

    def test_font_command_uses_safe_arguments_and_persists(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'settings with spaces.ini'
            with patch('cli.shutil.which',return_value='/usr/bin/kitty'),patch('cli.subprocess.call',return_value=0) as run:
                self.assertEqual(main(['--config',str(path),'font','18']),0)
                argv=run.call_args.args[0]
                self.assertEqual(argv[:3],['/usr/bin/kitty','--override','font_size=18'])
                self.assertEqual(argv[-2:],['--config',str(path.resolve())])
                self.assertEqual(main(['--config',str(path),'font']),0)
                self.assertIn('font_size=18',run.call_args.args[0])
                old=path.read_bytes()
                self.assertEqual(main(['--config',str(path),'font','100']),1)
                self.assertEqual(path.read_bytes(),old)
            with patch('cli.shutil.which',return_value=None),patch('cli.subprocess.call') as run:
                self.assertEqual(main(['--config',str(path),'font','18']),1)
                run.assert_not_called()

    def test_new_configuration_validates_atomically(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ui.ini'
            set_value(path,'layout.word_highlight','bold-beta')
            set_value(path,'visualizer.smoothing_ms','200')
            old=path.read_bytes()
            for key,value in [('visualizer.smoothing_ms','-1'),('layout.word_highlight','bold'),('layout.font_size','0')]:
                with self.assertRaises(ValueError):set_value(path,key,value)
                self.assertEqual(path.read_bytes(),old)

