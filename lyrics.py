import bisect
import math
import queue
import re
import shutil
import statistics
import subprocess
import threading
import time
from terminal_ui import TerminalUI

FPS = 180
PLAYER = "spotify"
LINES_PER_BLOCK = 4
PAUSE_SECONDS = 2.0
TYPE_AHEAD = 0.10       # Adianta a digitação em 100 ms, sem adiantar a troca de bloco.
SYNC_OFFSET = 0.00      # Corrige toda a letra; deixe zero inicialmente.
TYPE_RATIO = 0.95
POLL_INTERVAL = 0.10

STOP = threading.Event()
STATES = queue.Queue(maxsize=1)
REQUESTS = queue.Queue(maxsize=1)
RESULTS = queue.Queue()
DURATIONS = queue.Queue(maxsize=1)


def command(args, timeout=2):
    try:
        return subprocess.check_output(
            args, text=True, stderr=subprocess.DEVNULL, timeout=timeout
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def latest(channel, value):
    try:
        channel.get_nowait()
    except queue.Empty:
        pass
    channel.put_nowait(value)


def player_worker():
    song = None
    next_metadata = 0.0
    while not STOP.is_set():
        started = time.monotonic()
        if started >= next_metadata:
            raw = command(["playerctl", "-p", PLAYER, "metadata", "--format",
                           "{{artist}}\t{{title}}\t{{mpris:length}}"])
            fields = raw.split("\t")
            song = tuple(fields[:2]) if len(fields) >= 2 else None
            try:
                duration = float(fields[2]) / 1_000_000
                if not math.isfinite(duration):
                    duration = 0
            except (ValueError, IndexError):
                duration = 0
            latest(DURATIONS, max(0, duration))
            next_metadata = time.monotonic() + 0.5
        status = command(["playerctl", "-p", PLAYER, "status"])
        before = time.monotonic()
        raw_position = command(["playerctl", "-p", PLAYER, "position"])
        after = time.monotonic()
        try:
            position = float(raw_position)
            if not math.isfinite(position):
                raise ValueError
        except ValueError:
            latest(STATES, (None, "Stopped", 0.0, after))
        else:
            latest(STATES, (song, status, position, (before + after) / 2))
        STOP.wait(max(0, POLL_INTERVAL - (time.monotonic() - started)))


def parse_lyrics(raw):
    entries = []
    offset_match = re.search(r"\[offset:([+-]?\d+)\]", raw, re.I)
    offset = int(offset_match.group(1)) / 1000 if offset_match else 0.0
    pattern = r"\[(\d+):(\d+(?:\.\d+)?)\]"
    for row in raw.splitlines():
        if not re.match(pattern, row):
            continue
        tags = list(re.finditer(pattern, row))
        text = row[tags[-1].end():].strip()
        # Remove controles de terminal vindos da fonte da letra.
        text = "".join(c for c in text if c.isprintable())
        for tag in tags:
            stamp = int(tag[1]) * 60 + float(tag[2]) + offset
            entries.append((stamp, text))
    entries = sorted(set(entries))
    if not entries:
        return []

    # Estima o ritmo pelas linhas curtas; não é detecção de voz.
    rates = []
    for (start, text), (end, _) in zip(entries, entries[1:]):
        duration = end - start
        if text and 1 <= duration <= 6:
            rates.append(len(text) / duration)
    rate = max(7.0, min(22.0, statistics.median(rates) if rates else 13.0))

    lines = []
    for i, (start, text) in enumerate(entries):
        if not text:
            continue
        next_event = entries[i + 1][0] if i + 1 < len(entries) else None
        estimated = max(1.0, len(text) / rate)
        duration = max(0.1, next_event - start) if next_event is not None else estimated
        typing = duration * TYPE_RATIO
        if duration - estimated >= PAUSE_SECONDS:
            typing = estimated
        weights = []
        total = 0.0
        for char in text:
            total += 0.25 if char.isspace() else 0.45 if char in ",.;:!?—-" else 1.0
            weights.append(total)
        lines.append({"start": start, "text": text, "duration": max(0.1, typing),
                      "end": start + typing, "weights": weights,
                      "blank": entries[i + 1][0] if i + 1 < len(entries)
                      and not entries[i + 1][1] else None})
    return lines


def lyrics_worker():
    cache = {}
    while not STOP.is_set():
        try:
            song = REQUESTS.get(timeout=0.2)
        except queue.Empty:
            continue
        if song in cache:
            lines = cache[song]
        else:
            raw = command(["syncedlyrics", "--synced-only", " - ".join(song)], 30)
            lines = parse_lyrics(raw)
            if lines:
                if len(cache) >= 64:
                    cache.pop(next(iter(cache)))
                cache[song] = lines
        RESULTS.put((song, lines))


def render_block(lines, position, ahead=TYPE_AHEAD, block_size=LINES_PER_BLOCK,
                 pause_seconds=PAUSE_SECONDS, complete=False):
    current = bisect.bisect_right([line["start"] for line in lines], position) - 1
    if current < 0:
        return "..."
    first = (current // block_size) * block_size
    rows = []
    for i in range(first, current + 1):
        line = lines[i]
        if i > first:
            previous = lines[i - 1]
            silence_start = previous["blank"] if previous["blank"] is not None else previous["end"]
            if line["start"] - silence_start >= pause_seconds:
                rows.append("")
        if i < current:
            rows.append(line["text"])
            continue
        elapsed = max(0.0, position - line["start"] + ahead)
        progress = min(1.0, elapsed / line["duration"])
        count = bisect.bisect_right(line["weights"], progress * line["weights"][-1])
        count = min(len(line["text"]), max(1, count))
        cursor = "█" if progress < 1.0 else ""
        rows.append(line["text"] if complete else line["text"][:count] + cursor)
        silence_start = line["blank"] if line["blank"] is not None else line["end"]
        if position - silence_start >= pause_seconds:
            rows.append("")
    return "\n".join(rows)


def main():
    missing = [name for name in ("playerctl", "syncedlyrics") if not shutil.which(name)]
    if missing:
        print("Comando não encontrado: " + ", ".join(missing))
        return
    STOP.clear()
    threading.Thread(target=player_worker, daemon=True).start()
    threading.Thread(target=lyrics_worker, daemon=True).start()
    state = (None, "Stopped", 0.0, time.monotonic())
    song = None
    lines = []
    loading = False
    ui = TerminalUI()
    duration = 0
    print("\033[?1049h\033[?25l", end="", flush=True)
    try:
        while True:
            frame_start = time.monotonic()
            try:
                state = STATES.get_nowait()
            except queue.Empty:
                pass
            new_song, status, real_position, measured_at = state
            if new_song != song:
                song = new_song
                lines = []
                loading = bool(song)
                if song:
                    latest(REQUESTS, song)
            while True:
                try:
                    result_song, result_lines = RESULTS.get_nowait()
                except queue.Empty:
                    break
                if result_song == song:
                    lines = result_lines
                    loading = False
            now = time.monotonic()
            # Se as consultas falharem, não deixa o relógio correr indefinidamente.
            elapsed = min(0.5, max(0.0, now - measured_at)) if status == "Playing" else 0.0
            position = real_position + elapsed + SYNC_OFFSET
            try:
                duration = DURATIONS.get_nowait()
            except queue.Empty:
                pass
            if not song:
                body = "Abra o Spotify e toque uma música."
                anchor = body
            elif loading:
                body = anchor = "Buscando letra..."
            elif not lines:
                body = anchor = "Letra sincronizada não encontrada."
            else:
                body = render_block(lines, position)
                anchor = render_block(lines, position, complete=True)
            ui.draw(song[0] if song else '', song[1] if song else 'slyrics',
                    body, position, duration, status == 'Playing',
                    'Fonte antiga · digitação contínua', anchor)
            time.sleep(max(0.0, 1 / FPS - (time.monotonic() - frame_start)))
    except KeyboardInterrupt:
        pass
    finally:
        STOP.set()
        print("\033[0m\033[?25h\033[?1049l", end="", flush=True)


if __name__ == "__main__":
    import sys
    if "--legacy" in sys.argv:
        main()
    else:
        from spicy_bridge import main as bridge_main
        bridge_main()
