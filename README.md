# sylrics · 0.7.0

Synchronized lyrics in your Linux terminal, with smooth typing, an optional audio
visualizer, adaptive reading modes and live customization. Spicy Lyrics is optional.

## Install or update

Requires Python 3.10+ and `playerctl`. CAVA enables real audio visualization;
`syncedlyrics` is an optional lyric provider. The native fallback also uses LRCLIB.

```sh
curl -fLO https://github.com/math-eusz/spotify-live-lyrics/releases/download/v0.7.0/sylrics-0.7.0.tar.gz
tar -xzf sylrics-0.7.0.tar.gz
cd sylrics-0.7.0
sh install.sh
```

Run `sylrics` in a new terminal. `slyrics` remains an alias. The installer backs up
replaced program files and preserves preferences, lyrics and bridge configuration.
It does not require sudo or modify Spicetify. No AUR package is provided.

[Portuguese installation guide](QUICKSTART.pt-BR.md) · [Command reference](COMMANDS.pt-BR.md)

## New in 0.7.0

- Separate bar spacing and width, with proportional layout and gradual resampling.
- Rolling reading mode: retain recent phrases instead of clearing the entire block.
- Minimal, studio and cinema presets; source, colors, font and timing stay unchanged.
- Dimmed history, compact help for smaller windows, and keyboard reading/highlight toggles.
- Restore the last saved configuration backup, even after a malformed manual edit.
- Cached color resolution per composed frame; the unchanged-frame cache remains active.

```sh
sylrics preset studio
sylrics config set visualizer.bar_spacing 1
sylrics config set visualizer.bar_width 2
sylrics reading rolling
sylrics config set pages.max_lines 6
sylrics config restore
```

`bar_spacing` accepts 0–5 terminal cells; `bar_width` accepts 1–4. They apply to the
rendered bands in bars, dots and wave styles. Tiny windows may reduce visible width.
`visualizer.width` controls the input band count; proportional display width is
controlled by `visualizer.width_percent`. Resizing does not restart audio capture.

## Reading and appearance

`reading dynamic` groups phrases by timestamps, gaps and target duration. `reading
fixed` uses fixed blocks. `reading rolling` keeps up to `pages.max_lines` recent
phrases and starts fresh after a vocal gap. Changes use the actual phrase start,
without an early page switch from typing anticipation. No mode detects musical mood.

`typing smooth` is the continuous default. `typing words-beta` types each word and
holds briefly, fitting pauses inside the line timeline. `highlight bold-beta`
bolds the visible part of the current typed word; `highlight off` disables it.
Both beta effects estimate vocal timing rather than measure speech.

`theme dynamic` follows the terminal's indexed palette, including wallpaper-derived
palettes delivered by Noctalia. It does not read wallpaper images. Static presets:
`warm`, `purple`, `ocean`, `mono`. Transparency and blur belong to the terminal/desktop.

`font 18` opens a new Kitty window at 18 points and saves the size (6–48).
`font` reuses the saved size. It changes that window, not global kitty.conf or an
already-open terminal. Other terminals use their own zoom.

## Audio and lyric sources

`visualizer auto` uses CAVA when available, otherwise a decorative animation.
`spectrum` requires live CAVA samples, `activity` is decorative, `off` hides it.
The optional label identifies the mode. The visualizer does not identify instruments.
Smoothing is time-based (0–500 ms); pause zeroes the display. CAVA captures system audio.

`source native` requires no bridge. `source auto` prefers matching timed bridge data,
otherwise uses native lyrics. `source spicy` uses bridge metadata/clock but falls back
to native lyric search if bridge lyrics lack timings; it still needs a connected bridge.
`--source native` is a one-run override. Bridge setup is explicit: `bridge install`
modifies Spicetify and may restart Spotify. Open Spicy Lyrics in Spotify after installing.
The bridge listens on loopback with origin and installation-key checks.

## Settings, cache and controls

`config list`, `config get KEY`, `config set KEY VALUE`, `config edit`, `config path`
and `config restore` manage the live INI file. Defaults live in `ui.ini`.
The standard location is `~/.config/spotify-live-lyrics/ui.ini` (or XDG_CONFIG_HOME).
Changes through the CLI create up to 20 configuration backups. Presets are saved
changes; they are not automatically applied during an upgrade. Restoration uses
the latest backup and saves the configuration being replaced.

The LRC directory is `~/.local/share/spotify-live-lyrics/lrc/`. Startup imports loose
synchronized LRC files from the home directory, preserving modification dates.
Startup and writes keep only the ten newest regular LRC files. Reading does not
refresh dates; other files and symlinks are not removed. External lyric CLI writes
are contained in temporary directories. `cache info` and `cache clear` use this store.
Earlier JSON caches are left untouched and are no longer used.

In the player: `q` exits, space pauses, `n`/`p` change tracks, `v` changes visualizer,
`a` changes alignment, `s` toggles source information, `r` changes reading mode,
`h` toggles beta emphasis, `+`/`-` adjust offset by 50 ms, and `?` toggles help.
Keyboard preferences are temporary; CLI settings persist. Playback control uses playerctl.

## Verification and limits

```sh
python -m unittest discover -s tests -v
sylrics doctor
sylrics demo
```

Tests cover lyric timing, resizing, profiles, rollback, storage, installer and
fixture playback/audio processes. Local preview rendering is not a test against
Spotify on the user's desktop. Incorrect lyric timestamps can still be wrong.
The 180 FPS setting is a rendering target, not a performance guarantee.

Historical versions remain in releases. Current source is released under MIT.
