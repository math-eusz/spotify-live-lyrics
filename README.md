# sylrics · 0.6.3

Live terminal lyrics, a configurable audio visualizer, and pages that follow phrase cadence. Native mode works without Spicetify or Spicy Lyrics.

The command is **`sylrics`**. The previous spelling, `slyrics`, remains a compatibility alias. [Português: instalação e comandos](QUICKSTART.pt-BR.md).

## Install

Requires Linux, Python **3.10+**, and `playerctl` for native playback. `cava` is optional for real audio visualization. `syncedlyrics` is optional: if present, its existing search is tried first; otherwise the built-in LRCLIB client fetches synchronized lyrics directly. An internet connection is needed for uncached lyrics.

Download `sylrics-0.6.3.tar.gz` from the [0.6.3 release](https://github.com/math-eusz/spotify-live-lyrics/releases/tag/v0.6.3), then run:

```sh
tar -xzf sylrics-0.6.3.tar.gz
cd sylrics-0.6.3
sh install.sh
```

The installer creates real executables in `~/.local/bin`, backs up previous runtime files, preserves your bridge credentials, migrates appearance settings and installs Fish completions. It does not run Spicetify. Open a new terminal and run `sylrics`. In the current terminal, `~/.local/bin/sylrics` always names the installed executable directly. Bash/Zsh users must have `~/.local/bin` on their PATH. Existing Fish aliases may shadow `slyrics`; the new `sylrics` command avoids that old alias.

On Arch/CachyOS, the native dependency is available through `sudo pacman -S playerctl`. Install CAVA separately if you want real audio bars.

## Choose a lyrics source

| Command | Behavior |
| --- | --- |
| `sylrics` | Open with saved settings; native is the default |
| `sylrics --source native` | Native playback and lyrics only for this session |
| `sylrics --source auto` | Prefer matching timed Spicy Lyrics data, otherwise native |
| `sylrics --source spicy` | Use the optional bridge clock; untimed lyrics still use native fallback |
| `sylrics source native` | Save native as the default; applies live |
| `sylrics bridge install` | Explicitly install/configure the optional Spicetify bridge |
| `sylrics bridge status` | Check whether the bridge has been configured |

For bridge mode, install Spicetify and Spicy Lyrics yourself first, run `sylrics bridge install`, then restart sylrics in `auto` or `spicy` mode. That explicit command backs up Spicetify configuration, installs the companion extension and applies Spicetify; Spotify may restart. Open lyrics in Spicy Lyrics to populate its cache. Native mode never starts the loopback server or reads the bridge cache.

A configured bridge listens only on `127.0.0.1:43829`, checks the origin and an installation-specific key, and reads only the current track's Spicy Lyrics cache. It does not request Spotify account tokens. The new key lives under `~/.config/spotify-live-lyrics/bridge-config.json`; an older installation key is also recognized.

## Dynamic pages

Dynamic mode groups lyrics by timestamp gaps and phrase cadence. Fast phrases can remain together up to the cap; slower phrases form shorter pages around the target duration. A pause of at least two seconds can end a page after just one phrase. The next page starts only at the next phrase's timestamp, independent of typing anticipation.

The default is **up to six vocal lines**, at least two before a duration-based break, and a target of 12 seconds. The hard cap is adjustable from 1 to 16. Blank separators and wrapped screen rows do not count as vocal lines. Small terminal windows show the active portion when all lines cannot fit.

```sh
sylrics config set pages.max_lines 8
sylrics config set pages.target_seconds 15
sylrics config set pages.pause_seconds 2.5
```

To recreate four-line pages:

```sh
sylrics config set pages.mode fixed
sylrics config set pages.max_lines 4
```

This uses lyric timing, **not mood, musical key, BPM analysis or voice separation**. LRC-only pause estimates depend on the lyric source. Spicy Lyrics can supply real phrase end times. The weighted continuous typewriter effect and 100 ms anticipation are preserved.

## Visualizer

| Mode | Meaning |
| --- | --- |
| `auto` | Real CAVA spectrum when available; clearly labeled animation otherwise |
| `spectrum` | Require real audio data; show an unavailable message if capture fails |
| `activity` | Decorative playback animation, not an audio measurement |
| `off` | Hide the visualizer and stop its CAVA process |

```sh
sylrics visualizer auto
sylrics config set visualizer.style wave
sylrics config set visualizer.width 40
sylrics config set visualizer.height 3
sylrics config set visualizer.only_gaps true
```

Styles are `bars`, `wave` and `dots`. CAVA monitors the system's default audio output; it does not isolate Spotify, classify a guitar, or detect a vocalist. The “intervalo vocal” label comes from lyric timestamps and can be estimated. Capture input can be `auto`, `pipewire` or `pulse`. Pausing freezes decorative motion and zeroes the bars. Real silent audio remains silent visually. Only-gap mode reserves visualizer space to keep the lyrics from jumping.

## Customize by file or command

```sh
sylrics config edit
sylrics config list
sylrics config get layout.alignment
sylrics config set layout.alignment left
sylrics config set layout.show_source false
sylrics theme purple
```

The lower-left source label is **off by default**, including migration from 0.5.0. Enable it with `sylrics config set layout.show_source true`. `layout.show_footer` controls the entire footer separately.

The file remains `~/.config/spotify-live-lyrics/ui.ini`, or `$XDG_CONFIG_HOME/spotify-live-lyrics/ui.ini`. Use `sylrics --config /path/ui.ini` for a separate profile. Saved changes reload within about half a second. Invalid values retain the last valid visual state. CLI edits are validated before an atomic replacement and keep up to 20 configuration backups. Session keyboard adjustments take precedence until the program exits.

| Section | Keys and values |
| --- | --- |
| `playback` | `source`: native/auto/spicy; `player`: MPRIS player name; `fps`: 15–240; `sync_offset`: -10–10 seconds; `type_ahead`: 0–0.5 seconds |
| `pages` | `mode`: dynamic/fixed; `min_lines`, `max_lines`: 1–16 with min ≤ max; `target_seconds`: 2–60; `pause_seconds`: 0.5–10 |
| `layout` | `alignment`: left/center/right; `vertical`: top/center/bottom; `padding`: 0–20; `line_spacing`: 0–4; `lyrics_width`: 10–240 |
| `layout` toggles | `border`, `icons`, `show_progress`, `show_source`, `show_footer`: true/false; `cursor`: short text or empty |
| `visualizer` | `mode`, `style`; `width`: 8–100; `height`: 1–6; `only_gaps`: true/false; `input`: auto/pipewire/pulse; `sensitivity`: 10–500 |
| `colors` | `text`, `muted`, `accent`, `border`, `background`: `#RRGGBB` or `default` |

Themes: `warm`, `purple`, `mono`, `ocean`. The default background inherits terminal transparency. Font size, blur and window decorations are controlled by your terminal. Unicode icons do not require a Nerd Font. The visual loop targets 180 FPS by default; display refresh depends on the terminal, font and hardware.

## Command library

| Command | Purpose |
| --- | --- |
| `sylrics play` | Start playback view |
| `sylrics demo` | Interactive preview without a music player |
| `sylrics source native` | Save the default source |
| `sylrics visualizer off` | Save the visualizer mode |
| `sylrics config path/list/get/set/edit` | Locate, inspect or edit configuration |
| `sylrics theme warm` | Apply a color preset with backup |
| `sylrics control play-pause` | Toggle playback through playerctl |
| `sylrics control next` / `previous` | Change tracks |
| `sylrics cache info` / `clear` | Inspect or remove cached LRC files |
| `sylrics doctor` | Report dependencies and configuration status |
| `sylrics bridge status` / `install` | Manage optional bridge integration |
| `sylrics --version` / `--help` | Version and command help |

During playback: `q` or Ctrl+C exits; Space toggles playback; `n`/`p` switch tracks; `v` cycles visualizers; `s` toggles source information; `a` cycles alignment; `+`/`-` adjust synchronization by 50 ms; `?` shows help. Shortcuts are session-only. Player-control shortcuts require playerctl, even when using the bridge.

## Reliability and limits

Player queries, lyric lookups and audio reading run outside the render loop. Successful lyrics are cached under `$XDG_CACHE_HOME/sylrics/lyrics` (normally `~/.cache/sylrics/lyrics`) for seven days, with a 64-file cap. Failed lookups retry after 60 seconds. Results are keyed by track; an old result cannot replace another song. Small playback-clock jitter is smoothed, while seeks and pause changes apply immediately.

These are synchronized lyric displays, not speech recognition. Incorrect source timestamps and alternate song versions can still produce incorrect timing. Live Spotify, PipeWire/PulseAudio and CAVA capture must be checked on your actual computer. Automated tests use fixture player/cache/audio processes and a real pseudo-terminal; they do not claim to hear your music.

## Backups and development

The previous state is preserved in release `v0.6.2`. The installer keeps overwritten runtime files under `~/.local/share/spotify-live-lyrics/backup/before-0.6.3-*`. Historical standalone Python installers remain downloadable from their original releases; they are no longer active installers in this source tree.

Run `python -m unittest discover -s tests -v`. The release workflow validates the project, builds source archives from exact commits, publishes checksums and never moves existing release tags. See [CHANGELOG.md](CHANGELOG.md).

Protocol references: [LRCLIB](https://lrclib.net/docs), [CAVA configuration](https://github.com/karlstav/cava/blob/master/example_files/config), [Spicy Lyrics cache](https://github.com/Spikerko/spicy-lyrics/blob/main/src/modules/Store.ts).

### Version 0.6.3: terminal theme and optional word reveal

` sylrics theme dynamic ` uses the terminal's default foreground/background and
indexed accent colors. Wallpaper-driven terminal palettes (including Noctalia
terminal templates) therefore carry through to sylrics. It does not extract colors
from wallpaper images; the terminal must receive palette updates. Static presets
remain available with `sylrics theme warm` (or `purple`, `mono`, `ocean`).

The visualizer label and persistent shortcut hints are hidden by default. Press
`?` for the controls panel. Use `sylrics visualizer off` to hide the visualizer,
`visualizer auto` to restore it, and `sylrics config set visualizer.show_label true`
to show its label. `layout.show_hints` enables the compact help hint.

`sylrics typing words-beta` animates characters within each word at weighted positions within
the existing line timeline, holding for up to 80 ms between words without accumulating delays.
This is an estimated beta animation, not voice detection or measured word timing.
`sylrics typing smooth` restores the default continuous typing. All options are
available in the live INI configuration, and command-line changes take precedence
over earlier session shortcuts after a successful configuration reload.

### Visualizador — 0.6.3

O visualizador ocupa 85% da largura útil e deixa uma linha de margem inferior.
A largura acompanha o redimensionamento da janela; os dados de áudio não mudam.
Para personalizar ao vivo:

```sh
sylrics config set visualizer.width_percent 85
sylrics config set visualizer.bottom_margin 1
```

`width_percent` aceita 0 a 100; 0 restaura a largura fixa de `visualizer.width`.
`bottom_margin` aceita 0 a 8 linhas. A borda e os avisos visíveis são respeitados.

## 0.6.3 — Suavização, fonte e destaque beta

O visualizador usa resposta suave baseada no tempo e oito níveis por célula.
A suavização padrão é 120 ms; valores maiores deixam a queda mais lenta.
Zero desativa o filtro. A pausa da reprodução zera as barras imediatamente.

```sh
sylrics config set visualizer.smoothing_ms 120
sylrics highlight bold-beta
sylrics highlight off
sylrics font 18
```

O destaque beta coloca em negrito a parte visível da palavra em digitação,
funciona com `smooth` e `words-beta`, e desaparece nos intervalos vocais.
É uma indicação estimada pela animação, não uma medição da voz.

`sylrics font 18` abre uma nova janela **Kitty**, com 18 pontos para toda a
interface, e salva o tamanho. Feche a janela antiga se não quiser duas instâncias.
`sylrics font` reutiliza o tamanho salvo (padrão: 14). Aceita de 6 a 48 pontos.
Não altera kitty.conf nem muda a fonte de um terminal já aberto. Em outros
terminais, use o zoom do terminal. A opção INI é `layout.font_size`.
Referência: [opções do Kitty](https://sw.kovidgoyal.net/kitty/invocation/).

As opções novas também estão no arquivo INI: `layout.word_highlight = off`
e `visualizer.smoothing_ms = 120`. O destaque começa desativado; as demais
preferências existentes são preservadas.
