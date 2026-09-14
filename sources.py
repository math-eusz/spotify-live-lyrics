"""Native playback and lyrics; no Spicetify dependency or account token."""
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from lyrics import command, parse_lyrics


class Player:
    def __init__(self, name='spotify'):
        self.name = name
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.data = None
        self.actions = queue.Queue(maxsize=8)
        self.thread = threading.Thread(target=self.work, daemon=True)
        self.thread.start()

    def work(self):
        while not self.stop.is_set():
            started = time.monotonic()
            try:
                action = self.actions.get_nowait()
            except queue.Empty:
                pass
            else:
                command(['playerctl', '-p', self.name, action])
            raw = command(['playerctl', '-p', self.name, 'metadata', '--format',
                           '{{artist}}\t{{title}}\t{{mpris:length}}\t{{mpris:trackid}}'])
            fields = raw.split('\t')
            status = command(['playerctl', '-p', self.name, 'status'])
            before = time.monotonic()
            position = command(['playerctl', '-p', self.name, 'position'])
            after = time.monotonic()
            data = None
            try:
                position = float(position)
                duration = float(fields[2]) / 1_000_000 if len(fields) > 2 and fields[2] else 0
                if len(fields) < 2 or not fields[1] or not math.isfinite(position) or not math.isfinite(duration):
                    raise ValueError
                data = dict(artist=fields[0], title=fields[1], duration=max(0, duration),
                            uri=fields[3] if len(fields)>3 else raw, position=max(0, position),
                            playing=status == 'Playing', measured_at=(before+after)/2)
            except (ValueError, IndexError):
                pass
            with self.lock:
                self.data = data
            self.stop.wait(max(0, .1 - (time.monotonic() - started)))

    def snapshot(self):
        with self.lock:
            return self.data

    def control(self, action):
        if action not in ('play-pause', 'next', 'previous'):
            return
        try:
            self.actions.put_nowait(action)
        except queue.Full:
            pass

    def close(self):
        self.stop.set()


class Clock:
    """Smooth small polling jitter; apply real seeks and pause changes immediately."""
    def __init__(self):
        self.key = None
        self.anchor = 0
        self.at = time.monotonic()
        self.playing = False
        self.measured = None
        self.last_received = self.at

    def position(self, data, now=None):
        now = time.monotonic() if now is None else now
        key = (data['uri'], data['artist'], data['title'])
        measured = data['measured_at']
        projected = data['position'] + (min(.5, max(0, now-measured)) if data['playing'] else 0)
        current = self.anchor + (max(0, now-self.at) if self.playing else 0)
        if key != self.key or data['playing'] != self.playing or abs(projected-current) > .75:
            self.anchor, self.at = projected, now
        elif measured != self.measured:
            # Converge without making already-visible characters disappear on tiny jitter.
            correction = max(-.015, min(.015, projected-current)) if data['playing'] else projected-current
            self.anchor, self.at = current + correction, now
        if measured != self.measured:
            self.last_received = now
        self.key, self.measured, self.playing = key, measured, data['playing']
        elapsed = min(max(0, now-self.at), max(0, self.last_received+.5-self.at)) if self.playing else 0
        return max(0, self.anchor+elapsed)


def fetch_lrc(data):
    if shutil.which('syncedlyrics'):
        raw = command(['syncedlyrics', '--synced-only', data['artist']+' - '+data['title']], timeout=12)
        if parse_lyrics(raw):
            return raw, 'syncedlyrics'
    params = dict(artist_name=data['artist'], track_name=data['title'])
    if data.get('duration', 0) > 0:
        params['duration'] = round(data['duration'])
    request = urllib.request.Request('https://lrclib.net/api/get?' + urllib.parse.urlencode(params),
                    headers={'User-Agent': 'sylrics/0.6.1 (https://github.com/math-eusz/spotify-live-lyrics)'})
    with urllib.request.urlopen(request, timeout=8) as response:
        payload = json.loads(response.read(1_000_001))
    if not isinstance(payload, dict):
        return '', 'Letra não encontrada'
    raw = payload.get('syncedLyrics') or ''
    if not isinstance(raw, str):
        return '', 'Letra não encontrada'
    return raw, 'LRCLIB' if raw else 'Faixa instrumental' if payload.get('instrumental') else 'Sem letra sincronizada'


class Lyrics:
    def __init__(self, cache_dir=None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(os.environ.get('XDG_CACHE_HOME', str(Path.home()/'.cache'))) / 'sylrics/lyrics'
        self.requests = queue.Queue(maxsize=1)
        self.results = queue.Queue()
        self.pending = set()
        self.cache = {}
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.work, daemon=True)
        self.thread.start()

    def key(self, data):
        return hashlib.sha256(json.dumps([data['uri'], data['artist'], data['title'], round(data.get('duration',0))], ensure_ascii=False).encode()).hexdigest()

    def work(self):
        while not self.stop.is_set():
            try:
                key, data = self.requests.get(timeout=.2)
            except queue.Empty:
                continue
            raw, label = '', 'Letra não encontrada · visualizador disponível'
            path = self.cache_dir / (key+'.json')
            try:
                if path.is_file() and time.time()-path.stat().st_mtime < 7*86400 and path.stat().st_size <= 1_000_000:
                    cached = json.loads(path.read_text())
                    if (cached.get('version') == 1 and isinstance(cached.get('lrc'),str)
                            and parse_lyrics(cached['lrc'])):
                        raw, label = cached['lrc'], str(cached.get('source','Cache'))
            except (OSError,ValueError,TypeError,AttributeError):
                raw=''
            try:
                if not raw:
                    raw, label = fetch_lrc(data)
                lines = parse_lyrics(raw)
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                lines = []
            if lines:
                try:
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    temp = path.with_suffix('.tmp')
                    temp.write_text(json.dumps(dict(version=1,lrc=raw,source=label)))
                    temp.chmod(0o600)
                    os.replace(temp,path)
                    old = sorted(self.cache_dir.glob('*.json'),key=lambda f:f.stat().st_mtime)
                    for file in old[:-64]:
                        file.unlink(missing_ok=True)
                except OSError:
                    pass
            self.results.put((key, lines, label))

    def get(self, data):
        while True:
            try:
                key, lines, label = self.results.get_nowait()
            except queue.Empty:
                break
            self.pending.discard(key)
            self.cache[key] = (lines, label, time.monotonic())
            if len(self.cache)>64:
                self.cache.pop(next(iter(self.cache)))
        key = self.key(data)
        cached = self.cache.get(key)
        if cached and (cached[0] or time.monotonic()-cached[2]<60):
            return cached[0], cached[1]
        if key not in self.pending:
            # Replace queued obsolete tracks; an in-flight lookup finishes separately.
            try:
                obsolete,_ = self.requests.get_nowait()
                self.pending.discard(obsolete)
            except queue.Empty:
                pass
            self.requests.put_nowait((key,dict(data)))
            self.pending.add(key)
        return [], 'Buscando letra…'

    def close(self):
        self.stop.set()
