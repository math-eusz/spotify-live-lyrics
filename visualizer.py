"""Optional CAVA spectrum. Activity mode is explicitly a decorative animation."""
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time


class Visualizer:
    def __init__(self):
        self.proc = None
        self.temp = None
        self.thread = None
        self.values = []
        self.received = 0
        self.key = None
        self.failed = False
        self.lock = threading.Lock()
        self.smoothed = []
        self.last_frame = None

    def configure(self, settings):
        key = (settings['mode'], settings['width'], settings['input'], settings['sensitivity'])
        if key == self.key:
            return
        self.close()
        self.key = key
        self.failed = False
        if settings['mode'] not in ('auto', 'spectrum'):
            return
        if not shutil.which('cava'):
            self.failed = True
            return
        self.temp = tempfile.TemporaryDirectory(prefix='sylrics-cava-')
        config = Path(self.temp.name) / 'config'
        method = '' if settings['input'] == 'auto' else 'method = ' + settings['input'] + '\n'
        config.write_text('[general]\nframerate = 60\nbars = ' + settings['width'] +
            '\nsensitivity = ' + settings['sensitivity'] + '\n[input]\n' + method +
            'source = auto\n[output]\nmethod = raw\nraw_target = /dev/stdout\n'
            'data_format = ascii\nascii_max_range = 1000\nbar_delimiter = 59\nframe_delimiter = 10\n')
        try:
            self.proc = subprocess.Popen(['cava', '-p', str(config)], stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
        except OSError:
            self.failed = True
            self.close()
            return
        self.thread = threading.Thread(target=self.read, args=(self.proc,), daemon=True)
        self.thread.start()

    def read(self, proc):
        try:
            for line in proc.stdout:
                try:
                    values = [min(1, max(0, int(v) / 1000)) for v in line.strip().split(';') if v]
                except ValueError:
                    continue
                if values and len(values) <= 512:
                    with self.lock:
                        self.values, self.received = values, time.monotonic()
        except (OSError, ValueError):
            pass

    def smooth(self, target, now, milliseconds, playing=True):
        if not playing:
            self.smoothed = [0.0] * len(target)
            self.last_frame = now
            return self.smoothed
        if len(self.smoothed) != len(target) or self.last_frame is None or now < self.last_frame:
            self.smoothed = [0.0] * len(target)
            self.last_frame = now - 1 / 60
        dt = min(.25, max(0.0, now - self.last_frame))
        self.last_frame = now
        for i, value in enumerate(target):
            # Faster attack, softer release; exponential response is FPS-independent.
            tau = milliseconds / 1000 * (.45 if value > self.smoothed[i] else 1.0)
            alpha = 1.0 if tau <= 0 else -math.expm1(-dt / tau)
            self.smoothed[i] += (value - self.smoothed[i]) * alpha
        return list(self.smoothed)

    def frame(self, settings, playing, gap, now=None):
        now = time.monotonic() if now is None else now
        mode = settings['mode']
        if mode == 'off':
            self.smoothed, self.last_frame = [], None
            return ()
        show_label = settings.get('show_label', 'false').lower() in ('true', '1', 'yes', 'on')
        if settings['only_gaps'].lower() in ('true', '1', 'yes', 'on') and not gap:
            return tuple('' for _ in range((1 if settings['style']=='wave' else int(settings['height']))+int(show_label)))
        width, height = int(settings['width']), int(settings['height'])
        with self.lock:
            values = list(self.values)
            age = now - self.received
        has_audio = mode in ('auto', 'spectrum') and bool(values) and age < 1
        if mode == 'spectrum' and not has_audio:
            return ('Áudio indisponível · verifique o CAVA',) if show_label else ()
        if has_audio:
            values = (values + [0] * width)[:width]
            label = '♫ Intervalo vocal · áudio' if gap else '♫ Áudio'
        else:
            values = [.1 + .55 * (math.sin(now*2.5 + i*.35) + 1)/2 for i in range(width)]
            label = '♫ Intervalo vocal · animação' if gap else '♫ Animação'
        if not playing:
            values = [0] * width
            label = 'Ⅱ Pausado'
        values = self.smooth(values, now, float(settings.get('smoothing_ms', '120')), playing)
        style = settings['style']
        if style == 'wave':
            glyphs = ' ▁▂▃▄▅▆▇█'
            rows = [''.join(glyphs[min(8, int(v*8))] for v in values)]
        else:
            rows = []
            for level in range(height, 0, -1):
                if style == 'dots':
                    rows.append(''.join('•' if v*height >= level-.6 else ' ' for v in values))
                else:
                    glyphs = ' ▁▂▃▄▅▆▇█'
                    rows.append(''.join(glyphs[min(8, max(0, int((v*height-level+1)*8)))]
                                        for v in values))
        return tuple(([label] if show_label else []) + rows)

    def close(self):
        if self.proc:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=1)
            if self.thread:
                self.thread.join(timeout=1)
            if self.proc.stdout:
                self.proc.stdout.close()
        self.proc = self.thread = None
        self.smoothed, self.last_frame = [], None
        if self.temp:
            self.temp.cleanup()
        self.temp = None
        with self.lock:
            self.values, self.received = [], 0


def fit_spectrum(row, width, bar_width=1, spacing=1):
    """Fit bands to available cells without stretching the gaps or restarting CAVA."""
    width = max(0, int(width))
    if not row or width == 0:
        return ''
    bar_width = max(1, min(int(bar_width), width))
    spacing = max(0, int(spacing))
    count = max(1, (width + spacing) // (bar_width + spacing))
    glyphs = ' ▁▂▃▄▅▆▇█'
    fractional = all(c in glyphs for c in row)
    bars = []
    for index in range(count):
        position = index * (len(row)-1) / (count-1) if count > 1 else (len(row)-1)/2
        low = int(position)
        high = min(low+1, len(row)-1)
        if fractional:
            level = glyphs.index(row[low]) * (1-position+low) + glyphs.index(row[high]) * (position-low)
            char = glyphs[min(8, max(0, round(level)))]
        else:
            char = row[min(len(row)-1, round(position))]
        bars.append(char * bar_width)
    return (' ' * spacing).join(bars)[:width]
