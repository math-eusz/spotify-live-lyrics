"""Deterministic lyric pages based on cadence and timestamp gaps, not audio mood."""
import bisect
from lyrics import render_block


def page_starts(lines, settings):
    maximum = int(settings['max_lines'])
    if settings['mode'] == 'fixed':
        return list(range(0, len(lines), maximum))
    minimum = int(settings['min_lines'])
    target = float(settings['target_seconds'])
    pause = float(settings['pause_seconds'])
    starts = [0] if lines else []
    for i in range(1, len(lines)):
        first = starts[-1]
        previous = lines[i-1]
        end = previous.get('blank')
        if end is None:
            end = previous['end']
        count = i - first
        if (count >= maximum or lines[i]['start'] - end >= pause or
                (count >= minimum and lines[i]['start'] - lines[first]['start'] >= target)):
            starts.append(i)
    return starts


class Pages:
    def __init__(self):
        self.key = None
        self.starts = []
        self.times = []

    def render(self, lines, position, settings, ahead=.1):
        key = (id(lines), tuple(settings.items()))
        if key != self.key:
            self.lines_ref = lines  # Keep identity alive while the cache is in use.
            self.starts = page_starts(lines, settings)
            self.times = [line['start'] for line in lines]
            self.key = key
        current = bisect.bisect_right(self.times, position) - 1
        if current < 0:
            return '♫ Introdução', '♫ Introdução', True
        page = bisect.bisect_right(self.starts, current) - 1
        first = self.starts[page]
        end = self.starts[page+1] if page+1 < len(self.starts) else len(lines)
        block = lines[first:end]
        kwargs = dict(ahead=ahead, block_size=max(1, len(block)),
                      pause_seconds=float(settings['pause_seconds']))
        body = render_block(block, position, **kwargs)
        anchor = render_block(block, position, complete=True, **kwargs)
        vocal_end = lines[current].get('blank')
        if vocal_end is None:
            vocal_end = lines[current]['end']
        gap = position - vocal_end >= float(settings['pause_seconds'])
        return body, anchor, gap
