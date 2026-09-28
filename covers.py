"""Bounded, asynchronous artwork loading and optional Kitty image placement."""
import base64
import io
import os
from pathlib import Path
import queue
import secrets
import threading
import urllib.parse
import urllib.request

MAX_BYTES = 4 * 1024 * 1024


def supported():
    return not os.environ.get('TMUX') and (os.environ.get('TERM') == 'xterm-kitty' or bool(os.environ.get('KITTY_WINDOW_ID')))


def load_cover(url):
    # Pillow is optional. No image dependency is needed for lyrics or playback.
    from PIL import Image, ImageOps
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme == 'file' and parsed.netloc in ('', 'localhost'):
        with Path(urllib.parse.unquote(parsed.path)).open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
    elif parsed.scheme == 'https':
        request = urllib.request.Request(url, headers={'User-Agent': 'sylrics/0.8.0'})
        with urllib.request.urlopen(request, timeout=4) as stream:
            if urllib.parse.urlsplit(stream.geturl()).scheme != 'https':
                return None
            raw = stream.read(MAX_BYTES + 1)
    else:
        return None
    if len(raw) > MAX_BYTES:
        return None
    with Image.open(io.BytesIO(raw)) as original:
        if original.width * original.height > 16_000_000:
            return None
        image = ImageOps.exif_transpose(original).convert('RGB')
        image = ImageOps.fit(image, (256, 256))
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()


class Covers:
    def __init__(self):
        self.requests = queue.Queue(maxsize=1)
        self.results = queue.Queue()
        self.cache = {}
        self.requested = set()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.work, daemon=True)
        self.thread.start()

    def work(self):
        while not self.stop.is_set():
            try:
                url = self.requests.get(timeout=.2)
            except queue.Empty:
                continue
            try:
                png = load_cover(url)
            except Exception:
                # A corrupt/missing cover must never stop playback.
                png = None
            self.results.put((url, png))

    def get(self, url):
        while True:
            try:
                key, png = self.results.get_nowait()
            except queue.Empty:
                break
            self.requested.discard(key)
            self.cache[key] = png
            while len(self.cache) > 8:
                self.cache.pop(next(iter(self.cache)))
        if not url:
            return None
        if url in self.cache:
            return self.cache[url]
        if url not in self.requested:
            try:
                old = self.requests.get_nowait()
                self.requested.discard(old)
            except queue.Empty:
                pass
            self.requests.put_nowait(url)
            self.requested.add(url)
        return None

    def close(self):
        self.stop.set()


class KittyCover:
    def __init__(self):
        self.image_id = secrets.randbelow(2**31-1) + 1
        self.key = None

    def clear(self):
        if self.key is None:
            return ''
        self.key = None
        return f'\033_Ga=d,d=I,i={self.image_id},q=2\033\\'

    def update(self, png, rect, redraw=False):
        if not png or not rect or not supported():
            return self.clear()
        key = (png, rect)
        if key == self.key and not redraw:
            return ''
        output = self.clear()
        self.key = key
        x, y, width, height = rect
        output += f'\033[{y+1};{x+1}H'
        encoded = base64.b64encode(png).decode('ascii')
        pieces = [encoded[i:i+4096] for i in range(0, len(encoded), 4096)]
        for index, piece in enumerate(pieces):
            params = f'a=T,f=100,t=d,i={self.image_id},c={width},r={height},C=1,q=2,' if index == 0 else 'q=2,'
            output += '\033_G' + params + f'm={int(index+1 < len(pieces))};' + piece + '\033\\'
        return output
