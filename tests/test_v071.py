import unittest
from paging import Pages
from lyrics import parse_lyrics
from terminal_ui import DEFAULTS, Settings, TerminalUI
from visualizer import fit_spectrum

class Version071(unittest.TestCase):
    def test_columns_remain_solid_after_resize(self):
        # Previously the upper row could be fractional while the lower wasn't full.
        for width in range(2,100):
            top=fit_spectrum(' █',width,1,0)
            bottom=fit_spectrum(' █',width,1,0)
            self.assertTrue(all(a==' ' or b=='█' for a,b in zip(top,bottom)))

    def test_marked_silence_hides_history_until_next_timestamp(self):
        lines=parse_lyrics('[00:02]First phrase\n[00:05]\n[00:10]Next phrase')
        pages=Pages();cfg=DEFAULTS['pages']
        self.assertIn('First',pages.render(lines,4.9,cfg)[0])
        for pos in (5,6,9.99):
            body,anchor,gap=pages.render(lines,pos,cfg)
            self.assertTrue(gap);self.assertEqual(anchor,'...')
            self.assertTrue(set(body)=={'.'})
        self.assertFalse(pages.render(lines,10,cfg)[2])
        self.assertIn('First',pages.render(lines,4.9,cfg)[0])

    def test_dots_animate_with_playback_and_estimated_short_gaps_stay_visible(self):
        pages=Pages();cfg=DEFAULTS['pages']
        lines=parse_lyrics('[00:02]First phrase\n[00:04]Next phrase')
        self.assertNotEqual(pages.render(lines,0,cfg)[0],pages.render(lines,.5,cfg)[0])
        self.assertFalse(pages.render(lines,3.99,cfg)[2])
        self.assertTrue(pages.render(lines,30,cfg)[2])
        self.assertEqual(pages.render(lines,30,cfg),pages.render(lines,30,cfg))

    def test_gap_animation_can_be_disabled(self):
        lines=parse_lyrics('[00:02]First phrase\n[00:05]\n[00:10]Next phrase')
        body,_,gap=Pages().render(lines,6,dict(DEFAULTS['pages'],gap_animation='false'))
        self.assertTrue(gap);self.assertIn('First',body)

    def test_current_phrase_bold_can_be_disabled(self):
        cfg=Settings('/missing');ui=TerminalUI(cfg)
        args=dict(artist='Artist',title='Song',body='Past\nCurrent',size=(80,24))
        self.assertIn('\033[1m',''.join(ui.compose(**args)))
        cfg.values['layout']['active_bold']='false'
        self.assertNotIn('\033[1m',''.join(ui.compose(**args)))
