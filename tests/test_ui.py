import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from terminal_ui import TerminalUI, Settings, cells

ANSI = re.compile(r'\x1b\[[0-9;]*m')
def plain(rows):
    return [ANSI.sub('', row) for row in rows]


class Interface(unittest.TestCase):
    def test_center_stays_fixed_as_characters_appear(self):
        ui = TerminalUI(Settings('/nonexistent'))
        kwargs = dict(artist='Artist', title='Song', anchor='The full sentence', size=(100, 25))
        first = plain(ui.compose(body='T█', **kwargs))
        later = plain(ui.compose(body='The full█', **kwargs))
        a = next((y, row.index('T▎')) for y, row in enumerate(first) if 'T▎' in row)
        b = next((y, row.index('The full▎')) for y, row in enumerate(later) if 'The full▎' in row)
        self.assertEqual(a, b)

    def test_sizes_unicode_and_wrapping_stay_in_viewport(self):
        ui = TerminalUI(Settings('/nonexistent'))
        for width, height in ((135, 28), (70, 18), (30, 10), (15, 4), (2, 1)):
            rows = plain(ui.compose('日本語', 'A very long title ' * 10,
                         'coração é 世界 ' * 12, size=(width, height)))
            self.assertEqual(len(rows), height)
            self.assertTrue(all(cells(row) == width-1 for row in rows), (width, rows))

    def test_live_settings_and_invalid_edit_keep_last_valid_layout(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'ui.ini'
            settings = Settings(path)
            path.write_text('[layout]\nalignment = left\n[colors]\naccent = #123456\n')
            settings.reload()
            self.assertEqual(settings.values['layout']['alignment'], 'left')
            path.write_text('[layout]\nalignment = right\nline_spacing = 2\n')
            settings.next_check = 0
            settings.reload()
            self.assertEqual(settings.values['layout']['alignment'], 'right')
            path.write_text('[layout]\nalignment = broken\n')
            settings.next_check = 0
            settings.reload()
            self.assertEqual(settings.values['layout']['alignment'], 'right')
            self.assertTrue(settings.error)

    def test_progress_pause_and_missing_duration(self):
        ui = TerminalUI(Settings('/nonexistent'))
        text = '\n'.join(plain(ui.compose('Artist', 'Track', 'Body', position=65,
                            duration=240, playing=False, size=(100, 25))))
        for expected in ('1:05', '4:00', 'PAUSADO', '━'):
            self.assertIn(expected, text)
        text = '\n'.join(plain(ui.compose('', '', 'Waiting', duration=0, size=(100, 25))))
        self.assertIn('--:--', text)

    def test_very_long_phrase_keeps_current_typing_visible(self):
        ui = TerminalUI(Settings('/nonexistent'))
        rows = plain(ui.compose('Artist', 'Song', 'Hello█',
                     anchor='Hello ' * 100, size=(30, 10)))
        self.assertIn('Hello▎', '\n'.join(rows))

    def test_unchanged_frame_writes_nothing(self):
        ui = TerminalUI(Settings('/nonexistent'))
        with patch('terminal_ui.sys.stdout.write') as write, patch('terminal_ui.sys.stdout.flush'):
            ui.draw('Artist', 'Song', 'Line')
            write.reset_mock()
            ui.draw('Artist', 'Song', 'Line')
            write.assert_not_called()


if __name__ == '__main__':
    unittest.main()
