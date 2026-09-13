import subprocess
import re
import time

FPS = 180

# Quantas vezes por segundo consultamos de verdade o Spotify.
# O resto é interpolado localmente.
POSITION_INTERVAL = 0.10
STATUS_INTERVAL = 0.20
METADATA_INTERVAL = 0.50

# Ajuste fino.
# POSITIVO = letra fica mais adiantada
# NEGATIVO = letra fica mais atrasada
SYNC_OFFSET = 0.00

# Faz a digitação terminar um pouco antes da próxima linha.
# 0.90 = usa 90% do intervalo entre as linhas.
TYPE_RATIO = 0.90


def cmd(args):
    try:
        return subprocess.check_output(
            args,
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except:
        return ""


def get_song():
    result = cmd([
        "playerctl",
        "-p", "spotify",
        "metadata",
        "--format",
        "{{artist}}\t{{title}}"
    ])

    if "\t" not in result:
        return "", ""

    return result.split("\t", 1)


def get_real_position():
    try:
        return float(
            cmd([
                "playerctl",
                "-p", "spotify",
                "position"
            ])
        )
    except:
        return None


def get_status():
    return cmd([
        "playerctl",
        "-p", "spotify",
        "status"
    ])


def get_lyrics(artist, title):
    result = cmd([
        "syncedlyrics",
        "--synced-only",
        f"{artist} - {title}"
    ])

    lines = []

    for line in result.splitlines():
        match = re.match(
            r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)",
            line
        )

        if not match:
            continue

        minutes = int(match.group(1))
        seconds = float(match.group(2))
        text = match.group(3)

        timestamp = minutes * 60 + seconds

        lines.append((timestamp, text))

    return lines


def draw(artist, title, text):
    print("\033[H\033[J", end="")
    print(f"♪ {artist} — {title}\n")
    print(text, end="", flush=True)


artist = ""
title = ""

lyrics = []

last_metadata_check = 0
last_position_check = 0
last_status_check = 0

spotify_position = 0.0
position_sync_time = time.monotonic()

status = "Paused"

frame_time = 1 / FPS


while True:

    frame_start = time.monotonic()
    now = frame_start

    # -------------------------
    # MÚSICA / METADATA
    # -------------------------

    if now - last_metadata_check >= METADATA_INTERVAL:

        new_artist, new_title = get_song()

        last_metadata_check = now

        if not new_artist or not new_title:
            draw("", "", "Spotify não encontrado.")
            time.sleep(0.5)
            continue

        if (new_artist, new_title) != (artist, title):

            artist = new_artist
            title = new_title

            draw(
                artist,
                title,
                "Buscando letra..."
            )

            lyrics = get_lyrics(
                artist,
                title
            )

            real_pos = get_real_position()

            if real_pos is not None:
                spotify_position = real_pos
                position_sync_time = time.monotonic()

    # -------------------------
    # STATUS
    # -------------------------

    if now - last_status_check >= STATUS_INTERVAL:

        new_status = get_status()

        if new_status:
            status = new_status

        last_status_check = now

    # -------------------------
    # POSIÇÃO REAL DO SPOTIFY
    # -------------------------

    if now - last_position_check >= POSITION_INTERVAL:

        real_position = get_real_position()

        if real_position is not None:

            spotify_position = real_position
            position_sync_time = time.monotonic()

        last_position_check = now

    # -------------------------
    # INTERPOLAÇÃO
    # -------------------------

    if status == "Playing":

        elapsed = now - position_sync_time

        position = (
            spotify_position
            + elapsed
            + SYNC_OFFSET
        )

    else:

        position = (
            spotify_position
            + SYNC_OFFSET
        )

    # -------------------------
    # SEM LETRA
    # -------------------------

    if not lyrics:

        draw(
            artist,
            title,
            "Letra sincronizada não encontrada."
        )

        time.sleep(frame_time)
        continue

    # -------------------------
    # DESCOBRIR LINHA ATUAL
    # -------------------------

    current_index = None

    for i, (timestamp, _) in enumerate(lyrics):

        if timestamp <= position:
            current_index = i
        else:
            break

    if current_index is None:

        draw(
            artist,
            title,
            "..."
        )

        time.sleep(frame_time)
        continue

    start, text = lyrics[current_index]

    if current_index + 1 < len(lyrics):

        next_start = lyrics[current_index + 1][0]

    else:

        next_start = start + 5

    # -------------------------
    # DIGITAÇÃO
    # -------------------------

    line_duration = next_start - start

    typing_duration = max(
        line_duration * TYPE_RATIO,
        0.10
    )

    elapsed_line = position - start

    progress = elapsed_line / typing_duration

    progress = max(
        0.0,
        min(progress, 1.0)
    )

    char_count = int(
        len(text) * progress
    )

    if progress > 0:
        char_count = max(
            char_count,
            1
        )

    visible = text[:char_count]

    draw(
        artist,
        title,
        visible + "█"
    )

    # -------------------------
    # 180 FPS
    # -------------------------

    elapsed_frame = time.monotonic() - frame_start

    sleep_time = frame_time - elapsed_frame

    if sleep_time > 0:
        time.sleep(sleep_time)
