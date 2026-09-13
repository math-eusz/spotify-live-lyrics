"""Display timing data already loaded by Spicy Lyrics, through a loopback bridge."""
import bisect
import hmac
import json
import math
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
        result.append({"start": start, "end": end, "text": "".join(chars), "reveals": reveals})
    result.sort(key=lambda line: line["start"])
    return result, "syllable" if kind == "Syllable" else "line"


def render(lines, position, ahead=TYPE_AHEAD):
    # Never use the anticipation offset for page changes or the instrumental intro.
    current = bisect.bisect_right([line["start"] for line in lines], position) - 1
    if current < 0:
        return "♪ Instrumental..."
    first = current // LINES_PER_BLOCK * LINES_PER_BLOCK
    rows = []
    for i in range(first, current + 1):
        line = lines[i]
        if i > first and line["start"] - lines[i - 1]["end"] >= PAUSE_SECONDS:
            rows.append("")
        if i != current:
            rows.append(line["text"])
        else:
            count = bisect.bisect_right(line["reveals"], position + ahead)
            cursor = "█" if count < len(line["text"]) and position < line["end"] else ""
            rows.append(line["text"][:count] + cursor)
    return "\n".join(rows)


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
                "playing": data["playing"]}
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
    previous = None
    print("\033[?1049h\033[?25l", end="", flush=True)
    try:
        while True:
            started = time.monotonic()
            data, lines, mode, received = state.snapshot()
            age = started - received
            if data is None or age > 3:
                screen = "Abra o Spotify com a ponte ativada e a letra no Spicy Lyrics.\nAguardando conexão..."
            else:
                elapsed = min(age, 0.35) if data["playing"] else 0.0
                position = data["position"] + max(0, elapsed)
                if lines:
                    body = render(lines, position)
                elif mode == "static":
                    body = "Esta letra não tem tempos de sincronização no Spicy Lyrics."
                elif mode == "unsupported":
                    body = "Formato de letra ainda não suportado pela ponte."
                else:
                    body = "Abra a letra desta música no Spicy Lyrics e aguarde carregar."
                label = "sílabas" if mode == "syllable" else "linha (digitação estimada)"
                paused = " · pausado" if not data["playing"] else ""
                screen = f"♪ {data['artist']} — {data['title']}\nSpicy Lyrics · {label}{paused}\n\n{body}"
            if screen != previous:
                print("\033[H\033[J" + screen, end="", flush=True)
                previous = screen
            time.sleep(max(0, 1 / FPS - (time.monotonic() - started)))
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown(); server.server_close()
        print("\033[?25h\033[?1049l", end="", flush=True)


if __name__ == "__main__":
    main()
