"""Dependency-free terminal layout with live, validated INI settings."""
import configparser
import os
from pathlib import Path
import re
import shutil
import sys
import time
import unicodedata

DEFAULTS = {
    'layout': {'alignment': 'center', 'vertical': 'center', 'padding': '3',
               'line_spacing': '1', 'lyrics_width': '86', 'border': 'true',
               'show_progress': 'true', 'show_source': 'false',
               'show_footer': 'true', 'cursor': '▎', 'icons': 'true'},
    'playback': {'source': 'native', 'player': 'spotify', 'fps': '180',
                 'sync_offset': '0', 'type_ahead': '0.10'},
    'pages': {'mode': 'dynamic', 'min_lines': '2', 'max_lines': '6',
              'target_seconds': '12', 'pause_seconds': '2'},
    'visualizer': {'mode': 'auto', 'style': 'bars', 'width': '32', 'height': '3',
                   'only_gaps': 'false', 'input': 'auto', 'sensitivity': '100'},
    'colors': {'text': '#DEDAD0', 'muted': '#88867F', 'accent': '#C8BA91',
               'border': '#69675E', 'background': 'default'},
}
CONFIG_PATH = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'spotify-live-lyrics/ui.ini'


def safe(text):
    return ''.join(c for c in str(text) if c.isprintable())


def cells(text):
    return sum(0 if unicodedata.combining(c) else
               2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)


def crop(text, width):
    result, used = '', 0
    for c in safe(text):
        size = cells(c)
        if used + size > width:
            break
        result += c
        used += size
    return result


def truncate(text, width):
    text = safe(text)
    return text if cells(text) <= width else crop(text, max(0, width - 1)) + ('…' if width else '')


def chunks(text, width):
    """Hard wrap by display cells; unlike textwrap, preserves partial typing spaces."""
    result, part, used = [], '', 0
    for c in text:
        size = cells(c)
        if part and used + size > width:
            result.append(part)
            part, used = '', 0
        part += c
        used += size
    result.append(part)
    return result


def clock(seconds):
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    return f'{minutes}:{seconds:02d}'


class Settings:
    def __init__(self, path=CONFIG_PATH):
        self.path = Path(path)
        self.values = {k: dict(v) for k, v in DEFAULTS.items()}
        self.next_check = 0
        self.error = ''
        self.signature = None

    def reload(self):
        now = time.monotonic()
        if now < self.next_check:
            return
        self.next_check = now + .5
        try:
            stat = self.path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            if signature == self.signature:
                return
            parser = configparser.ConfigParser(interpolation=None)
            parser.read_dict(DEFAULTS)
            with self.path.open(encoding='utf-8') as file:
                parser.read_file(file)
            for name, allowed in [('alignment', ('left', 'center', 'right')),
                                  ('vertical', ('top', 'center', 'bottom'))]:
                if parser['layout'][name] not in allowed:
                    raise ValueError(name)
            for name, low, high in [('padding', 0, 20), ('line_spacing', 0, 4),
                                    ('lyrics_width', 10, 240)]:
                if not low <= parser.getint('layout', name) <= high:
                    raise ValueError(name)
            for name in ('border', 'show_progress', 'show_source', 'show_footer', 'icons'):
                parser.getboolean('layout', name)
            choices = {('playback', 'source'): ('native', 'auto', 'spicy'),
                       ('pages', 'mode'): ('dynamic', 'fixed'),
                       ('visualizer', 'mode'): ('auto', 'spectrum', 'activity', 'off'),
                       ('visualizer', 'style'): ('bars', 'wave', 'dots'),
                       ('visualizer', 'input'): ('auto', 'pipewire', 'pulse')}
            for (section, name), allowed in choices.items():
                if parser[section][name] not in allowed:
                    raise ValueError(name)
            for section, name, low, high in (
                ('playback', 'fps', 15, 240), ('pages', 'min_lines', 1, 16),
                ('pages', 'max_lines', 1, 16), ('visualizer', 'width', 8, 100),
                ('visualizer', 'height', 1, 6), ('visualizer', 'sensitivity', 10, 500)):
                if not low <= parser.getint(section, name) <= high:
                    raise ValueError(name)
            for section, name, low, high in (
                ('playback', 'sync_offset', -10, 10), ('playback', 'type_ahead', 0, .5),
                ('pages', 'target_seconds', 2, 60), ('pages', 'pause_seconds', .5, 10)):
                if not low <= parser.getfloat(section, name) <= high:
                    raise ValueError(name)
            if parser.getint('pages', 'min_lines') > parser.getint('pages', 'max_lines'):
                raise ValueError('min_lines > max_lines')
            if not re.fullmatch(r'[\w.,-]+', parser['playback']['player']):
                raise ValueError('player')
            parser.getboolean('visualizer', 'only_gaps')
            cursor = parser['layout']['cursor']
            if safe(cursor) != cursor or cells(cursor) > 2:
                raise ValueError('cursor')
            for color in parser['colors'].values():
                if color != 'default' and not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                    raise ValueError('color')
            self.values = {section: dict(parser[section]) for section in DEFAULTS}
            self.signature = signature
            self.error = ''
        except FileNotFoundError:
            self.error = ''
        except (OSError, ValueError, configparser.Error):
            self.error = 'ui.ini inválido · mantendo o último visual válido'

    def flag(self, name):
        return self.values['layout'][name].lower() in ('1', 'yes', 'true', 'on')


class TerminalUI:
    def __init__(self, settings=None):
        self.settings = settings or Settings()
        self.previous = []
        self.last_size = None
        self.frame_key = None
        self.frame_rows = None

    def color(self, name):
        color = self.settings.values['colors'][name]
        if color == 'default':
            return '\033[49m' if name == 'background' else '\033[39m'
        r, g, b = (int(color[i:i+2], 16) for i in (1, 3, 5))
        return f'\033[{48 if name == "background" else 38};2;{r};{g};{b}m'

    def compose(self, artist, title, body, position=0, duration=0,
                playing=True, source='', anchor=None, size=None, visual=None, notice='', gap=False):
        self.settings.reload()
        width, height = size or shutil.get_terminal_size((100, 28))
        # Reserve the final column: writing it can cause terminal auto-wrap.
        width = max(1, width - 1)
        height = max(1, height)
        frame_key = (artist, title, body, int(position), int(duration),
                     int(width * min(1, max(0, position / duration))) if duration > 0 else 0,
                     playing, source, anchor, width, height, visual, notice, gap,
                     repr(self.settings.values), self.settings.error)
        if frame_key == self.frame_key:
            return self.frame_rows
        layout = self.settings.values['layout']
        border = self.settings.flag('border') and width >= 20 and height >= 7
        edge = int(border)
        padding = min(int(layout['padding']), max(0, (width - 12) // 2))
        left = edge + padding
        usable = max(1, width - 2 * left)
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        styles = [['text' for _ in range(width)] for _ in range(height)]

        def put(y, x, text, style='text'):
            if not 0 <= y < height:
                return
            for c in crop(text, max(0, width - x)):
                n = cells(c)
                if n == 0:
                    if x > 0:
                        grid[y][x-1] += c
                    continue
                if x < 0 or x + n > width:
                    break
                grid[y][x], styles[y][x] = c, style
                for k in range(1, n):
                    grid[y][x+k], styles[y][x+k] = '', style
                x += n

        if border:
            put(0, 0, '╭' + '─' * (width - 2) + '╮', 'border')
            put(height - 1, 0, '╰' + '─' * (width - 2) + '╯', 'border')
            for y in range(1, height - 1):
                put(y, 0, '│', 'border')
                put(y, width - 1, '│', 'border')
        header_y = edge + (1 if height >= 12 else 0)
        state = ('▶ TOCANDO' if playing else 'Ⅱ PAUSADO') if self.settings.flag('icons') else ('TOCANDO' if playing else 'PAUSADO')
        title_text = f'{title}  —  {artist}' if artist else title or 'slyrics'
        state_space = len(state) + 3 if usable >= 45 else 0
        put(header_y, left, truncate(title_text, usable - state_space))
        if state_space:
            put(header_y, left + usable - len(state), state, 'accent')
        content_top = header_y + 2
        if self.settings.flag('show_progress') and height >= 9:
            elapsed = clock(position)
            total = clock(duration) if duration > 0 else '--:--'
            track_width = max(1, usable - len(elapsed) - len(total) - 4)
            put(header_y + 1, left, elapsed, 'muted')
            bar_x = left + len(elapsed) + 2
            put(header_y + 1, bar_x, '─' * track_width, 'border')
            filled = int(track_width * min(1, max(0, position / duration))) if duration > 0 else 0
            if filled:
                put(header_y + 1, bar_x, '━' * filled, 'accent')
            put(header_y + 1, left + usable - len(total), total, 'muted')
            content_top = header_y + 3
        footer_y = height - edge - 2
        footer = self.settings.flag('show_footer') and height >= 12
        content_bottom = footer_y - 1 if footer else height - edge - 1
        visual = visual or ()
        visual_room = len(visual) + 2 if visual and height >= 16 else 0
        visual_y = content_bottom - len(visual) + 1
        if visual_room:
            content_bottom -= visual_room
        room = max(1, content_bottom - content_top + 1)
        wrap_width = min(usable, int(layout['lyrics_width']))
        visible_rows = body.split('\n')
        full_rows = (anchor if anchor is not None else body).split('\n')
        prepared = []
        for i, visible in enumerate(visible_rows):
            full = full_rows[i] if i < len(full_rows) else visible
            cursor = visible.endswith('█')
            visible = visible[:-1] if cursor else visible
            # Reserve full phrase geometry: centering must not move on each keystroke.
            segments = chunks(full, wrap_width)
            remaining = len(visible)
            for j, segment in enumerate(segments):
                count = min(len(segment), max(0, remaining))
                fragment = segment[:count]
                at_cursor = cursor and 0 <= remaining <= len(segment) and (remaining > 0 or j == 0)
                if at_cursor:
                    fragment += layout['cursor']
                prepared.append((fragment, min(wrap_width, cells(segment) + cells(layout['cursor'])), i == len(visible_rows)-1))
                remaining -= len(segment)
            if i + 1 < len(visible_rows):
                prepared.extend([('', 0, False)] * int(layout['line_spacing']))
        if len(prepared) > room:
            visible_end = max((i + 1 for i, row in enumerate(prepared) if row[0]), default=1)
            window_start = max(0, visible_end - room)
            prepared = prepared[window_start:window_start + room]
        offset = max(0, room - len(prepared))
        start_y = content_top + (offset // 2 if layout['vertical'] == 'center' else offset if layout['vertical'] == 'bottom' else 0)
        for y, (text, full_width, active) in enumerate(prepared, start_y):
            free = max(0, usable - full_width)
            x = left + (free // 2 if layout['alignment'] == 'center' else free if layout['alignment'] == 'right' else 0)
            put(y, x, crop(text, usable - (x-left)), 'accent' if active else 'text')
        if visual_room:
            for y, row in enumerate(visual, visual_y):
                row = crop(row, usable)
                put(y, left + max(0, (usable - cells(row)) // 2), row, 'accent')
        if footer:
            status = self.settings.error or notice or (source if self.settings.flag('show_source') else '')
            hint = 'q sair · espaço pausa · v visual · ? ajuda'
            if usable > len(hint) + 15:
                put(footer_y, left, truncate(status, usable - len(hint) - 3), 'muted')
                put(footer_y, left + usable - len(hint), hint, 'muted')
            else:
                put(footer_y, left, truncate(status or 'Ctrl+C sair', usable), 'muted')
        rows = []
        for row, style_row in zip(grid, styles):
            parts, previous = [self.color('background')], None
            for c, style in zip(row, style_row):
                if style != previous:
                    parts.append(self.color(style))
                    previous = style
                parts.append(c)
            rows.append(''.join(parts) + '\033[0m')
        self.frame_key, self.frame_rows = frame_key, rows
        return rows

    def draw(self, *args, **kwargs):
        size = shutil.get_terminal_size((100, 28))
        rows = self.compose(*args, **kwargs, size=size)
        output = []
        if size != self.last_size:
            output.append('\033[2J')
            self.previous = []
        for i, row in enumerate(rows):
            if i >= len(self.previous) or row != self.previous[i]:
                output.append(f'\033[{i+1};1H' + row)
        if output:
            sys.stdout.write(''.join(output))
            sys.stdout.flush()
        self.previous, self.last_size = rows, size
