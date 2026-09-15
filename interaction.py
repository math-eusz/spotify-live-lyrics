"""Buffered terminal events and timestamp targets for visible lyric words."""
# Mouse encoding: https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h3-Extended-coordinates
import re


class InputParser:
    def __init__(self):
        self.pending = ''

    def feed(self, text):
        self.pending += text
        events = []
        while self.pending:
            if not self.pending.startswith('\033'):
                events.append(('key', self.pending[0]))
                self.pending = self.pending[1:]
                continue
            if self.pending == '\033' or self.pending == '\033[':
                break
            if self.pending.startswith('\033['):
                match = re.match(r'\x1b\[[0-?]*[ -/]*[@-~]', self.pending)
                if not match:
                    if len(self.pending) > 128:
                        self.pending = ''
                    break
                sequence = match[0]
                mouse = re.fullmatch(r'\x1b\[<0;(\d+);(\d+)M', sequence)
                if mouse:
                    events.append(('click', (int(mouse[1])-1, int(mouse[2])-1)))
                self.pending = self.pending[len(sequence):]
            else:
                # Discard alt/escape combinations, never turn them into controls.
                self.pending = self.pending[2:]
        return events


def word_target(line, offset):
    for word in re.finditer(r'\S+', line['text']):
        if word.start() <= offset < word.end():
            starts = line.get('char_starts')
            if starts and len(starts) == len(line['text']):
                return starts[word.start()], False
            weight = line['weights'][word.start()-1] if word.start() else 0
            return line['start'] + line['duration'] * weight / line['weights'][-1], True
    return None
