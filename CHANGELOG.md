# v0.7.2 — Clique nas palavras, intervalos beta e restauração de padrões

Os intervalos animados agora são uma opção beta explícita. `sylrics gaps dots-beta` ativa e `sylrics gaps off` desativa, inclusive na introdução. Instalações novas deixam o recurso desligado; atualizações preservam a escolha existente. Pausas curtas entre versos não apagam mais a letra. O limite é `pages.pause_seconds` (padrão: 2 segundos). Sem marcações vocais, a detecção continua estimada.

Clique com o botão esquerdo em uma palavra visível para buscar aquele trecho. `sylrics click-seek on` ativa e `sylrics click-seek off` desativa. O clique é beta e vem ativado por padrão. Com tempos por sílaba, usa o início da sílaba que contém o começo da palavra; com tempos apenas por linha, estima o início pelo ritmo da digitação. Não garante alinhamento exato com a voz. Requer playerctl e suporte a mouse do terminal. Não muda o estado reproduzindo/pausado. O controle recusa cliques após mudança de faixa ou redimensionamento ainda não desenhado. Ajuda, espaços e letras ainda invisíveis não são alvos.

Pressione **0** dentro do programa para restaurar as configurações padrão e limpar os ajustes da sessão. O comando equivalente é `sylrics config reset`. Ambos salvam backup antes da alteração. Use `sylrics config restore` para recuperar a configuração anterior. A restauração inclui tema, fonte de letras, visualizador e recursos beta; não remove o cache nem a ponte. O tamanho e a família da fonte do terminal são aplicados ao reabrir com `sylrics font`.

Revisão: processamento de eventos de mouse recebidos em partes, mapeamento de palavras conforme quebra de linha e alinhamento, suporte a caracteres largos, buscas fora do loop visual, aplicação imediata de pequenos saltos no relógio e restauração do modo de mouse ao sair. Comandos e completamentos Fish/Bash atualizados.

Testes automatizados incluem o fluxo completo em pseudoterminal com playerctl simulado. A reprodução dentro do Spotify do usuário ainda precisa de validação.

# v0.7.1 — Visualizador corrigido e intervalos animados

Corrige o redimensionamento do espectro: colunas inteiras são preservadas, evitando barras deformadas pela interpolação independente das linhas. Espaçamento, espessura e suavização continuam disponíveis.

Durante a introdução e os intervalos vocais, as frases são substituídas por pontos animados. A animação acompanha a posição de reprodução e congela ao pausar. Marcas explícitas de silêncio são respeitadas imediatamente; finais estimados recebem tolerância de 500 ms. Intervalos curtos não apagam as frases. Sem tempos detalhados, isso é uma estimativa, não detecção de voz.

A frase atual recebe cor de destaque e negrito, enquanto a palavra no modo beta recebe também sublinhado. O destaque não aparece em mensagens de intervalo ou na ajuda.

O comando de fonte aceita uma família monoespaçada instalada, sem alterar a configuração global do Kitty:

```sh
sylrics font 16 --family "monospace"
sylrics config set layout.active_bold false
sylrics config set pages.gap_animation false
```

O tamanho e a família se aplicam à janela aberta por `sylrics font`. A instalação mantém as preferências e cria backup da versão anterior. Spicy Lyrics continua opcional.

# 0.7.0

Configurable visualizer bar spacing (0–5 cells) and thickness (1–4 cells), with
fractional resampling that keeps gaps stable on resize. Rolling lyric windows
retain context until the next phrase and reset after vocal gaps. Minimal, studio
and cinema presets preserve colors, lyric source, synchronization and font size.
Previous lines can be dimmed; keyboard help adapts to smaller windows. New r/h
shortcuts control reading mode and beta highlight. Config restore recovers the
last backup, including after invalid manual edits. Resolve each ANSI color once
per composed frame instead of once per row/style run.

# 0.6.4

Store plain synchronized LRC files inside the application data directory, retaining
the ten newest by modification time. Import loose home-directory LRC files on
startup; isolate syncedlyrics side effects in a temporary directory. Share the
bounded store with native lyric loading and cache commands.

# 0.6.3

Time-based spectrum smoothing and fractional-height bars. Optional estimated
word highlight in bold, preserving wrapping and alignment. Kitty font-size
launcher with saved preferences; no global terminal configuration changes.

# 0.6.2

Animated characters within words-beta, with short holds that fit the line timeline.
Visualizer expands to 85% of available width, moves lower, and supports configurable
width percentage and bottom margin. Empty footer no longer reserves space.

# 0.6.1

Terminal-palette dynamic theme, on-demand keyboard help, optional visualizer labels,
and opt-in whole-word typing (beta). Fixed live configuration precedence after
session shortcuts. Existing native fallback and smooth typing remain available.

# Changelog

Retrospective release numbering for the complete versions delivered during development. Intermediate upload commits are not separate releases. Download names such as `v3` and `v4` were installer revisions, not prior semantic-version tags.

## v0.6.0 — Standalone lyrics, dynamic pages and visualizer

Native playback by default; optional Spicy Lyrics; cadence-based pages with configurable limits; CAVA spectrum or labeled activity animation; command-based live configuration; themes and keyboard controls; real `sylrics` executable and source archive installer with migration backups. The existing typewriter effect is preserved. No AUR/yay packaging is included.

[Release notes](releases/notes/v0.6.0.md) · [Source snapshot](https://github.com/math-eusz/spotify-live-lyrics/tree/v0.6.0)

## v0.5.0 — Customizable terminal interface

[Release notes](releases/notes/v0.5.0.md) · [Source snapshot](https://github.com/math-eusz/spotify-live-lyrics/tree/8e86603794090904a19604d8f7f1af0eea379731)

## v0.4.2 — Verified installation repair

[Release notes](releases/notes/v0.4.2.md) · [Source snapshot](https://github.com/math-eusz/spotify-live-lyrics/tree/194cc83a661bdc15a75c25eab6ed8c99ddfddd72)

## v0.4.1 — Automatic fallback and continuous typing

[Release notes](releases/notes/v0.4.1.md) · [Source snapshot](https://github.com/math-eusz/spotify-live-lyrics/tree/cd0b4a2dc220028905dbd95d4aabaa128f20291f)

## v0.4.0 — Spicy Lyrics local bridge

[Release notes](releases/notes/v0.4.0.md) · [Source snapshot](https://github.com/math-eusz/spotify-live-lyrics/tree/3c855f3881ea9feb396195e0e1dd2bb14334ebdd)

## v0.3.0 — Smoother timing and vocal pauses

[Release notes](releases/notes/v0.3.0.md) · [Source snapshot](https://github.com/math-eusz/spotify-live-lyrics/tree/644499646e6ba9c9a1d6689408ab1845f326b3d8)

## v0.2.0 — Four-line lyric blocks

[Release notes](releases/notes/v0.2.0.md) · [Source snapshot](https://github.com/math-eusz/spotify-live-lyrics/tree/b994f1e7518b088f9f286330018e2c5b69195c13)

## v0.1.0 — Original terminal lyrics

[Release notes](releases/notes/v0.1.0.md) · [Source snapshot](https://github.com/math-eusz/spotify-live-lyrics/tree/1dd12470d2efb92a1872a75e355ba1332bb6f86e)


