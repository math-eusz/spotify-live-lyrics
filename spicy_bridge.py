"""Display timing data already loaded by Spicy Lyrics, through a loopback bridge."""
import bisect
import hmac
import json
import math
import queue
import shutil
import lyrics as legacy
from terminal_ui import TerminalUI
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time

PORT = 43829
FPS = 180
LINES_PER_BLOCK = 4
TYPE_AHEAD = 0.10
PAUSE_SECONDS = 2.0
MAX_BODY = 2_000_000
ORIGINS = {"https://xpui.app.spotify.com", "https://open.spotify.com"}


def clean(value):
    return "".join(c for c in str(value) if c.isprintable())[:20000]


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Invalid timing")
    if not math.isfinite(value) or not 0 <= value <= 172800:
        raise ValueError("Invalid timing")
    return float(value)


def timeline(payload):
    """Normalize documented-by-source Spicy Lyrics Line/Syllable data; times are seconds."""
    if not isinstance(payload, dict):
        return [], "waiting"
    kind = payload.get("Type")
    if kind == "Static":
        return [], "static"
    if kind not in ("Syllable", "Line"):
        return [], "unsupported"
    result = []
    content = payload.get("Content", [])
    if not isinstance(content, list) or len(content) > 5000:
        raise ValueError("Invalid content")
    for item in content:
        if not isinstance(item, dict) or item.get("Type") != "Vocal":
            continue
        vocal = item.get("Lead", {}) if kind == "Syllable" else item
        if not isinstance(vocal, dict):
            raise ValueError("Invalid lead")
        chars, reveals = [], []
        if kind == "Syllable":
            parts = vocal.get("Syllables", [])
            if not isinstance(parts, list) or len(parts) > 10000:
                raise ValueError("Invalid syllables")
            ranges = []
            for index, part in enumerate(parts):
                if not isinstance(part, dict):
                    raise ValueError("Invalid syllable")
                start, end = number(part.get("StartTime")), number(part.get("EndTime"))
                if end < start:
                    raise ValueError("Reversed timing")
                text = clean(part.get("Text", ""))
                ranges.append((start, end))
                for k, char in enumerate(text):
                    chars.append(char)
                    reveals.append(start + (end - start) * (k + 1) / max(1, len(text)))
                if index + 1 < len(parts) and not part.get("IsPartOfWord", False):
                    if chars and not chars[-1].isspace():
                        chars.append(" "); reveals.append(end)
            if not ranges:
                continue
            start, end = min(a for a, _ in ranges), max(b for _, b in ranges)
        else:
            start, end = number(vocal.get("StartTime")), number(vocal.get("EndTime"))
            if end < start:
                raise ValueError("Reversed timing")
            chars = list(clean(vocal.get("Text", "")))
            reveals = [start + (end - start) * (i + 1) / max(1, len(chars))
                       for i in range(len(chars))]
        if not chars or not "".join(chars).strip():
            continue
        # A sequential terminal cannot reveal overlapping parts out of text order.
        for i in range(1, len(reveals)):
            reveals[i] = max(reveals[i - 1], reveals[i])
        weights, total = [], 0.0
        for char in chars:
            total += 0.25 if char.isspace() else 0.45 if char in ",.;:!?—-" else 1.0
            weights.append(total)
        result.append({"start": start, "end": end, "text": "".join(chars),
                       "reveals": reveals, "weights": weights, "blank": end,
                       "duration": max(0.1, (end - start) * legacy.TYPE_RATIO)})
    result.sort(key=lambda line: line["start"])
    return result, "syllable" if kind == "Syllable" else "line"


def render(lines, position, ahead=TYPE_AHEAD, complete=False):
    if not lines or position < lines[0]["start"]:
        return "♪ Instrumental..."
    return legacy.render_block(lines, position, ahead, LINES_PER_BLOCK, PAUSE_SECONDS, complete=complete)


class Fallback:
    """One background lookup at a time; results are keyed to their exact track."""
    def __init__(self):
        self.requests = queue.Queue(maxsize=1)
        self.results = queue.Queue()
        self.stop = threading.Event()
        self.cache = {}
        self.pending = set()
        self.available = bool(shutil.which("syncedlyrics"))
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.thread.start()

    def worker(self):
        while not self.stop.is_set():
            try:
                key = self.requests.get(timeout=0.2)
            except queue.Empty:
                continue
            raw = legacy.command(["syncedlyrics", "--synced-only",
                                  " - ".join(key[1:])], 30)
            self.results.put((key, legacy.parse_lyrics(raw)))

    def get(self, data):
        while True:
            try:
                key, lines = self.results.get_nowait()
            except queue.Empty:
                break
            self.pending.discard(key)
            if len(self.cache) >= 64:
                self.cache.pop(next(iter(self.cache)))
            self.cache[key] = (lines, time.monotonic())
        if not self.available:
            return [], "syncedlyrics não encontrado; necessário para a fonte antiga."
        key = (data["uri"], data["artist"], data["title"])
        if not key[1] or not key[2]:
            return [], "Aguardando artista e título para buscar na fonte antiga..."
        cached = self.cache.get(key)
        if cached and (cached[0] or time.monotonic() - cached[1] < 60):
            return cached[0], "Letra sincronizada não encontrada nas duas fontes."
        if key not in self.pending:
            try:
                self.requests.put_nowait(key)
            except queue.Full:
                pass
            else:
                self.pending.add(key)
        return [], "Buscando sincronização na fonte antiga..."


def choose_body(data, lines, mode, position, fallback, complete=False):
    if lines:
        label = "sílabas" if mode == "syllable" else "linhas"
        return render(lines, position, complete=complete), "Spicy Lyrics · " + label + " · digitação contínua"
    old_lines, message = fallback.get(data)
    body = legacy.render_block(old_lines, position, complete=complete) if old_lines else message
    return body, "Fonte antiga · digitação contínua"


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = None
        self.lines = []
        self.mode = "waiting"
        self.received = 0.0

    def update(self, data):
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Invalid message")
        uri = data.get("uri")
        if not isinstance(uri, str) or len(uri) > 300:
            raise ValueError("Invalid URI")
        position = number(data.get("position"))
        if not isinstance(data.get("playing"), bool):
            raise ValueError("Invalid playback state")
        parsed = None
        if "lyrics" in data:
            payload = data["lyrics"]
            if isinstance(payload, dict) and payload.get("uri") not in (None, uri):
                raise ValueError("Lyrics belong to another track")
            parsed = timeline(payload)
        safe = {"uri": uri, "title": clean(data.get("title", "")),
                "artist": clean(data.get("artist", "")), "position": position,
                "playing": data["playing"], "duration": number(data.get("duration", 0))}
        with self.lock:
            if not self.data or self.data["uri"] != uri:
                self.lines, self.mode = [], "waiting"
            if parsed is not None:
                self.lines, self.mode = parsed
            self.data = safe
            self.received = time.monotonic()

    def snapshot(self):
        with self.lock:
            return self.data, self.lines, self.mode, self.received


def handler_for(state, token):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, *args):
            pass

        def allowed(self):
            return (self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"
                    and self.headers.get("Origin") in ORIGINS)

        def reply(self, status):
            self.send_response(status)
            origin = self.headers.get("Origin")
            if origin in ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Slyrics-Key")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_OPTIONS(self):
            self.reply(204 if self.allowed() and self.path == "/state" else 403)

        def do_POST(self):
            if self.path != "/state" or not self.allowed():
                self.reply(403); return
            key = self.headers.get("X-Slyrics-Key", "")
            if not hmac.compare_digest(key, token):
                self.reply(403); return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= MAX_BODY:
                    self.reply(413); return
                data = json.loads(self.rfile.read(size))
                state.update(data)
            except (ValueError, TypeError, KeyError, AttributeError, OSError):
                self.reply(400); return
            self.reply(204)
    return Handler


def main():
    config = Path(__file__).resolve().parent / "bridge-config.json"
    try:
        token = json.loads(config.read_text())["token"]
        if not isinstance(token, str) or len(token) < 32:
            raise ValueError
    except (OSError, ValueError, KeyError):
        print("Execute install.py para configurar a ponte do Spicy Lyrics.")
        return
    state = State()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), handler_for(state, token))
    except OSError:
        print(f"Porta {PORT} ocupada. Feche outra execução do slyrics e tente novamente.")
        return
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    fallback = Fallback()
    ui = TerminalUI()
    print("\033[?1049h\033[?25l", end="", flush=True)
    try:
        while True:
            started = time.monotonic()
            data, lines, mode, received = state.snapshot()
            age = started - received
            if data is None or age > 3:
                ui.draw('', 'slyrics', 'Abra o Spotify com o Spicy Lyrics.\nAguardando conexão...',
                        playing=False, source='Ponte desconectada')
            else:
                elapsed = min(age, 0.5) if data["playing"] else 0.0
                position = data["position"] + max(0, elapsed) + legacy.SYNC_OFFSET
                body, label = choose_body(data, lines, mode, position, fallback)
                anchor, _ = choose_body(data, lines, mode, position, fallback, complete=True)
                ui.draw(data['artist'], data['title'], body, position,
                        data['duration'], data['playing'], label, anchor)
            time.sleep(max(0, 1 / FPS - (time.monotonic() - started)))
    except KeyboardInterrupt:
        pass
    finally:
        fallback.stop.set()
        server.shutdown(); server.server_close()
        print("\033[0m\033[?25h\033[?1049l", end="", flush=True)


if __name__ == "__main__":
    main()
