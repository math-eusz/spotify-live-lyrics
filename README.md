# Spotify Live Lyrics

Real-time lyrics in the Linux terminal, using timing data already loaded by **Spicy Lyrics** in Spotify. Displays four vocal lines per page, keeps the fourth until the next phrase starts, and separates vocal gaps of at least two seconds.

## Install

Requires Python 3, Spicetify and the Spicy Lyrics extension installed and working in Spotify. Download `install_spicy_bridge.py` and run:

```sh
python ~/Downloads/install_spicy_bridge.py
```

Alternatively, download or clone this repository and run `python install.py` in its directory.

The installer backs up previous project files, the existing bridge extension and Spicetify configuration under `~/.local/share/spotify-live-lyrics/backup/`. It installs a small companion extension, appends it to your enabled extensions and runs `spicetify apply`, which can restart Spotify. It does not replace Spicy Lyrics.

Open a song's lyrics in Spicy Lyrics so that it loads and caches them. Then run:

```sh
python ~/.local/share/spotify-live-lyrics/lyrics.py
```

Your existing `slyrics` alias still works. Press Ctrl+C to exit. The terminal reports whether the data contains syllable timings or only line timings. Static lyrics are reported as unsynchronized rather than being given made-up timestamps.

## How it works

`slyrics-bridge.js` reads **only the current track** from Cache Storage entries whose names begin with `SpicyLyrics_LyricsStore`. It sends the lyrics and the Spicetify player's current position to a Python listener at `127.0.0.1:43829`. It does not request account tokens, intercept requests, query a lyrics API, or read unrelated caches. The per-install local bridge key is stored outside git.

`spicy_bridge.py` supports the `Syllable` and `Line` data structures. With syllable timings, characters are interpolated within each supplied syllable interval. These are not measured per-character timestamps. With line timings, character progression is estimated within the supplied line start/end. The bridge shows lead vocals; simultaneous backing vocals are not displayed.

The default `TYPE_AHEAD = 0.10` advances character progress by 100 ms. Page selection uses the unshifted playback position, so anticipation cannot clear page four before the next phrase starts. `LINES_PER_BLOCK = 4`, `PAUSE_SECONDS = 2.0` and `FPS = 180` can be adjusted at the top of `spicy_bridge.py`. The visual loop targets 180 iterations per second and writes only when the display changes; real display refresh depends on the terminal.

The bridge samples player state roughly every 100 ms. Python interpolates briefly between updates, freezes on pause and shows a disconnected message after three seconds without contact. Lyrics are resent periodically, allowing the terminal to restart independently. A track change clears the old track's lyrics.

## Compatibility and limits

This bridge is based on Spicy Lyrics' current cache envelope (`Content`, `ExpiresAt`) and `Syllable`/`Line` schemas. A future extension update may require adapting the bridge. Lyrics must have been loaded by Spicy Lyrics; the bridge does not start a lyrics search itself. Custom local-only TTML storage is not supported. Browser restrictions on localhost requests can also affect the live integration.

Tests cover real JavaScript-to-Python loopback transport with a mocked Spicetify player/cache, syllable timing, instrumental intros, four-line page boundaries, pauses, seek behavior, stale track data, request validation and installer backups. They do **not** establish that it works inside your particular Spotify/Spicetify installation; that needs a live test on your PC.

## Previous source

The previous playerctl/syncedlyrics implementation remains available explicitly:

```sh
python ~/.local/share/spotify-live-lyrics/lyrics.py --legacy
```

That mode still estimates character timing from LRC lines and inherits inaccurate source timestamps. It is not used as an automatic fallback for Spicy Lyrics.

## Remove the companion extension

```sh
spicetify config extensions slyrics-bridge.js-
spicetify apply
```

Use `--legacy` or restore `lyrics.py` from your timestamped backup if you want the previous terminal behavior.

## Development

Run `python -m unittest discover -s tests -v` with Node.js available for the transport test. The installable standalone script embeds `lyrics.py`, `spicy_bridge.py`, `slyrics-bridge.js` and `install.py`; regenerate it with `python build_installer.py` after changes.

## Protocol references

This project implements its own companion extension and renderer. The protocol was inspected in [Spicy Lyrics cache storage](https://github.com/Spikerko/spicy-lyrics/blob/main/src/modules/Store.ts), [lyrics fetch/cache](https://github.com/Spikerko/spicy-lyrics/blob/main/src/utils/Lyrics/fetchLyrics.ts) and [syllable rendering](https://github.com/Spikerko/spicy-lyrics/blob/main/src/utils/Lyrics/Applyer/Synced/Syllable.ts). Extension installation follows the [Spicetify documentation](https://spicetify.app/docs/customization/extensions).
