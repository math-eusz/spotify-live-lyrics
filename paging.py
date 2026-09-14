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

    def render(self, lines, position, settings, ahead=.1, typing_mode='smooth'):
        key = (id(lines), tuple(settings.items()))
        if key != self.key:
            self.lines_ref = lines  # Keep identity alive while the cache is in use.
            self.starts = page_starts(lines, settings)
            self.times = [line['start'] for line in lines]
            self.key = key
        current = bisect.bisect_right(self.times, position) - 1
        if current < 0:
            return self.rest(position, settings)
        page = bisect.bisect_right(self.starts, current) - 1
        first = self.starts[page]
        end = self.starts[page+1] if page+1 < len(self.starts) else len(lines)
        if settings['mode'] == 'rolling':
            first = max(0, current - int(settings['max_lines']) + 1)
            for i in range(first + 1, current + 1):
                previous = lines[i-1]
                vocal_end = previous.get('blank')
                if vocal_end is None:
                    vocal_end = previous['end']
                if lines[i]['start'] - vocal_end >= float(settings['pause_seconds']):
                    first = i
            end = current + 1
        block = lines[first:end]
        kwargs = dict(ahead=ahead, typing_mode=typing_mode, block_size=max(1, len(block)),
                      pause_seconds=float(settings['pause_seconds']))
        body = render_block(block, position, **kwargs)
        anchor = render_block(block, position, complete=True, **kwargs)
        vocal_end = lines[current].get('blank')
        if vocal_end is None:
            vocal_end = lines[current]['end']
        next_start = lines[current+1]['start'] if current+1 < len(lines) else float('inf')
        marked = lines[current].get('blank') is not None
        pause = float(settings['pause_seconds'])
        gap = position >= vocal_end and (marked or next_start - vocal_end >= pause)
        # Estimated ends need a short grace period; explicit silence is immediate.
        if gap and not marked:
            gap = position >= vocal_end + min(.5, pause)
        if gap and settings.get('gap_animation', 'true').lower() in ('true','1','yes','on'):
            return self.rest(position, settings)
        return body, anchor, gap

    @staticmethod
    def rest(position, settings):
        dots = '.' * (1 + int(max(0, position) / .45) % 3)
        return dots, '...', True

