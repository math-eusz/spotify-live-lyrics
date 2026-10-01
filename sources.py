"""Native playback and lyrics; no Spicetify dependency or account token."""
import hashlib
import json
import math
import queue
import shutil
import threading
import time
import urllib.parse
import urllib.request
from lyrics import command, parse_lyrics
from lrc_store import LrcStore


def available_players():
    return list(dict.fromkeys(command(['playerctl', '-l']).splitlines()))


def resolve_player(preference='auto', current=None):
    names = available_players()
    # Old installations saved "spotify" as their default. Keep these working
    # with the terminal client too; an explicit spotify_player stays exclusive.
    if preference in ('auto', 'spotify'):
        candidates = [name for name in names if name.split('.')[0] in
                      ('spotify', 'spotify_player', 'spotify-player')]
    else:
        candidates = [name for name in names if name == preference or
                      name.startswith(preference + '.')]
    if len(candidates) < 2:
        return next(iter(candidates), None)
    playing = [name for name in candidates if
               command(['playerctl', '-p', name, 'status']) == 'Playing']
    choices = playing or candidates
    return current if current in choices else next(iter(choices), None)


def parse_player_snapshot(raw, player, measured_at, seek_serial=0):
    fields = raw.split('\t')
    try:
        if len(fields) != 8 or not fields[1] or fields[6] not in ('Playing', 'Paused', 'Stopped'):
            return None
        position = float(fields[7]) / 1_000_000
        duration = float(fields[2]) / 1_000_000 if fields[2] else 0
        if not math.isfinite(position) or not math.isfinite(duration):
            return None
        return dict(artist=fields[0], title=fields[1], duration=max(0, duration),
                    uri=fields[3] or fields[0]+' / '+fields[1], position=max(0, position),
                    album=fields[4], art_url=fields[5], player=player,
                    seek_serial=seek_serial, playing=fields[6]=='Playing', measured_at=measured_at)
    except (ValueError, OverflowError):
        return None


class Player:
    def __init__(self, name='auto'):
        self.name = name
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.data = None
        self.actions = queue.Queue(maxsize=8)
        self.seek_serial = 0
        self.selected = None
        self.next_discovery = 0
        self.thread = threading.Thread(target=self.work, daemon=True)
        self.thread.start()

    def work(self):
        while not self.stop.is_set():
            started = time.monotonic()
            if started >= getattr(self, 'next_discovery', 0):
                self.selected = resolve_player(self.name, getattr(self, 'selected', None))
                self.next_discovery = started + 1.0
            selected = self.selected
            if not selected:
                with self.lock:
                    self.data = None
                self.stop.wait(.2)
                continue
            try:
                action = self.actions.get_nowait()
            except queue.Empty:
                pass
            else:
                if isinstance(action, tuple):
                    stamp, expected, target, identity = action
                    live = command(['playerctl','-p',target,'metadata','--format','{{mpris:trackid}}'])
                    live_identity = command(['playerctl','-p',target,'metadata','--format','{{artist}}\t{{title}}']) if identity else None
                    if live == expected and target == selected and (identity is None or live_identity == identity):
                        command(['playerctl','-p',target,'position',f'{stamp:.6f}'])
                        self.seek_serial += 1
                elif action['player'] == selected:
                    command(['playerctl', '-p', selected, action['command']])
            # One process supplies a coherent metadata/status/position snapshot.
            # playerctl's template position is in microseconds, unlike `position`.
            before = time.monotonic()
            raw = command(['playerctl', '-p', selected, 'metadata', '--format',
                           '{{artist}}\t{{title}}\t{{mpris:length}}\t{{mpris:trackid}}\t{{album}}\t{{mpris:artUrl}}\t{{status}}\t{{position}}'])
            after = time.monotonic()
            data = parse_player_snapshot(raw, selected, (before+after)/2, self.seek_serial)
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
            snapshot = self.snapshot()
            if snapshot:
                self.actions.put_nowait({'command': action, 'player': snapshot.get('player')})
        except queue.Full:
            pass

    def seek(self, position, uri, player=None):
        if not math.isfinite(position) or position < 0 or not uri:
            return False
        try:
            data = self.snapshot()
            identity = data['artist']+'\t'+data['title'] if data else None
            self.actions.put_nowait((position, uri, player or getattr(self, 'selected', None) or self.name, identity))
            return True
        except queue.Full:
            return False

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
        key = (data.get('player'), data['uri'], data['artist'], data['title'], data.get('seek_serial', 0))
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
                    headers={'User-Agent': 'sylrics/0.8.1 (https://github.com/math-eusz/spotify-live-lyrics)'})
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
        self.store = LrcStore(cache_dir)
        self.cache_dir = self.store.directory
        try:
            self.store.maintain()
        except OSError:
            pass  # A read-only cache must not disable online lyrics.
        self.requests = queue.Queue(maxsize=1)
        self.results = queue.Queue()
        self.pending = set()
        self.cache = {}
        self.key_identity = self.key_value = None
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.work, daemon=True)
        self.thread.start()

    def key(self, data):
        identity = (data['uri'], data['artist'], data['title'], round(data.get('duration',0)))
        if identity != self.key_identity:
            self.key_identity = identity
            self.key_value = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()
        return self.key_value

    def work(self):
        while not self.stop.is_set():
            try:
                key, data = self.requests.get(timeout=.2)
            except queue.Empty:
                continue
            raw, label = '', 'Letra não encontrada · visualizador disponível'
            downloaded = False
            try:
                try:
                    raw = self.store.read(key)
                except OSError:
                    raw = ''
                lines = parse_lyrics(raw) if raw else []
                if lines:
                    label = 'Cache'
                else:
                    raw, label = fetch_lrc(data)
                    downloaded = True
                    lines = parse_lyrics(raw)
            except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
                lines = []
            if lines and downloaded:
                try:
                    self.store.save(key, raw)
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

