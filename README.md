<div align="center">

# 🎵 sylrics

**Sua música, palavra por palavra, no terminal.**

Letras sincronizadas, visualizador de áudio e uma interface que você pode deixar do seu jeito.

**🐧 Linux · 🐍 Python 3.10+ · 📦 v0.8.3 · 📜 MIT**

[🚀 Instalar](#-instalação) · [🎛️ Comandos](COMMANDS.pt-BR.md) · [📖 Primeiros passos](QUICKSTART.pt-BR.md) · [📦 Versões](https://github.com/math-eusz/spotify-live-lyrics/releases)

</div>

---

## ✨ O que você pode fazer

| Recurso | Como funciona |
|---|---|
| 🖼️ Capa do álbum | Cartão com capa, artista, álbum, estado e progresso; imagem no Kitty. |
| ⏯️ Botões clicáveis | Anterior, reproduzir/pausar e próxima, inclusive no mini player. |
| 🎧 Player local · beta | Reproduza arquivos locais com mpv e edite a fila dentro do sylrics. |
| 📄 Somente letras | Oculte toda a interface com `sylrics view lyrics` ou alterne com `L`. |
| 🔊 Spotify e spotify_player | Seleção automática do player Spotify em reprodução via MPRIS. |
| 🎶 Letras em tempo real | Acompanhe a música com digitação caractere por caractere. |
| 🌊 Visualizador | Escolha barras, ondas ou pontos; ajuste largura, espaçamento e suavização. |
| 📖 Leitura adaptável | Use blocos fixos, blocos por duração e pausas ou frases que saem individualmente. |
| 🎨 Personalização | Mude cores, alinhamento, margens, fonte e destaque das letras. |
| 🖱️ Clique nas palavras · beta | Volte ao trecho correspondente clicando em uma palavra visível. |
| 💬 Intervalos animados · beta | Substitua as letras por “...” durante as pausas, se quiser. |
| 💾 Preferências e backup | Ajuste pelo terminal ou pelo arquivo de configuração e restaure quando precisar. |

**O Spicy Lyrics é opcional.** O modo nativo é o padrão e funciona sem Spicetify. Para acompanhar Spotify/spotify_player, mantenha o player aberto. O novo **modo local beta** reproduz arquivos do computador com mpv, sem Spotify, playerctl ou Spicetify.

## 🚀 Instalação

Você precisa de **Linux, Python 3.10+, playerctl, curl e tar**. Para o visualizador reagir ao áudio, instale também o **CAVA**.

No **Arch Linux / CachyOS**:

```sh
sudo pacman -S --needed python playerctl curl tar
```

Visualizador de áudio e capas opcionais (capas requerem Kitty):

```sh
sudo pacman -S --needed cava python-pillow
```

Baixe e instale a versão atual:

```sh
curl -fLO https://github.com/math-eusz/spotify-live-lyrics/releases/download/v0.8.3/sylrics-0.8.3.tar.gz
tar -xzf sylrics-0.8.3.tar.gz
cd sylrics-0.8.3
sh install.sh
```

Abra um novo terminal, coloque uma música no Spotify ou spotify_player e execute:

```sh
sylrics
```

> 💡 Já usa o programa? Feche com `q` ou `Ctrl+C` e execute a mesma instalação. Seus ajustes são preservados e os arquivos substituídos recebem backup. O instalador do sylrics não precisa de `sudo`.

Em outras distribuições Linux, instale as dependências pelo gerenciador de pacotes correspondente. Consulte o [guia de instalação](QUICKSTART.pt-BR.md) para detalhes e solução de problemas.

## 🖼️ Capa, interface e player

```sh
sylrics view full          # Interface completa
sylrics view lyrics        # Somente letras, sem cabeçalho, borda ou visualizador
sylrics cover on           # Mostrar capa (Kitty + Pillow)
sylrics cover off          # Ocultar capa
sylrics player auto        # Spotify ou spotify_player em reprodução
sylrics player spotify_player  # Usar apenas o cliente de terminal
```

Use **L** durante a reprodução para alternar a interface só nesta sessão. Os comandos acima ficam salvos e são aplicados ao vivo. O modo somente letras preserva as outras preferências e interrompe a captura do visualizador enquanto estiver ativo.

As capas vêm dos metadados do player, são carregadas em segundo plano e mantidas apenas em memória (até oito). Em terminais sem protocolo Kitty, dentro do tmux ou sem Pillow, aparece um ícone. Ao reduzir a janela, a capa diminui e o cabeçalho assume um formato de mini player. A capa permanece habilitada até você desativá-la ou selecionar o modo somente letras. Sem uma imagem disponível, aparece um ícone.

O spotify_player precisa publicar os controles MPRIS. Em `~/.config/spotify-player/app.toml`, confirme `enable_media_control = true` e reinicie o cliente se ele não aparecer em `playerctl -l`. A compilação precisa incluir `media-control`; a [documentação do spotify_player](https://github.com/aome510/spotify-player/blob/master/docs/config.md) explica essa opção.

A seleção automática considera apenas os players da família Spotify; outros aplicativos não assumem a reprodução. Se houver dois tocando, mantém o já selecionado. Configurações antigas com `player = spotify` também permitem a detecção do cliente de terminal. Para fixar outro nome MPRIS, use `sylrics player NOME`.

## 🎨 Deixe com a sua cara

Comece por um perfil:

| Perfil | Visual |
|---|---|
| `sylrics preset studio` | Letras centralizadas e visualizador amplo. |
| `sylrics preset minimal` | Leitura discreta, sem borda nem visualizador. |
| `sylrics preset cinema` | Mais espaço entre frases e visualizador nos intervalos. |

Os perfis preservam suas cores, fonte das letras, tamanho da fonte e ajustes de sincronização.

Alguns ajustes para experimentar — execute os que quiser:

```sh
# Usar as cores da paleta do terminal
sylrics theme dynamic

# Remover as frases antigas individualmente
sylrics reading rolling

# Aumentar o espaço entre as barras
sylrics config set visualizer.bar_spacing 2

# Abrir uma janela Kitty com fonte maior
sylrics font 18
```

O tema dinâmico acompanha o papel de parede **quando seu sistema atualiza a paleta do terminal**. Transparência e desfoque são configurados no terminal e no ambiente gráfico.

## ⚡ Desempenho sem perder personalização

```sh
sylrics performance balanced  # Letras até 120 FPS, visualizador até 60
sylrics performance smooth    # Letras até 180 FPS, visualizador até 90
sylrics performance eco       # Letras até 60 FPS, visualizador até 30
```

Os perfis alteram apenas limites de atualização. Ao pausar ou ficar sem player, o programa reduz a frequência automaticamente. Você também pode ajustar `playback.idle_fps` (5–60) e `visualizer.fps` (15–120). Uma atualização não aplica nenhum perfil automaticamente; preserva os seus ajustes.

A consulta normal de metadados, posição e estado passou de três processos playerctl para um por ciclo, mantendo a interpolação local. Quando existem tempos por sílaba, a exibição agora respeita esses tempos e as pausas internas; o modo beta não substitui os tempos reais por estimativas.

O benchmark sintético de 900 quadros (120×36 células, words-beta e visualizador decorativo) mediu aproximadamente metade do tempo de CPU da 0.8.0 no ambiente de teste. Isso não mede o consumo total no desktop. Para reproduzir: `python benchmarks/render.py`; detalhes em [benchmarks/README.md](benchmarks/README.md).

## 🧪 Recursos beta

| Ativar | Desativar | Efeito |
|---|---|---|
| `sylrics typing words-beta` | `sylrics typing smooth` | Digita cada palavra com uma pequena pausa entre elas. |
| `sylrics highlight bold-beta` | `sylrics highlight off` | Destaca a palavra em digitação com negrito e sublinhado. |
| `sylrics gaps dots-beta` | `sylrics gaps off` | Mostra pontos animados nos intervalos vocais. |
| `sylrics click-seek on` | `sylrics click-seek off` | Permite buscar um trecho clicando na palavra. |

Os pontos vêm desligados em instalações novas; o clique vem ligado. Atualizações preservam as escolhas existentes.

**Sobre a precisão:** o clique usa o início da sílaba quando esse dado está disponível. Com tempos apenas por linha, o momento da palavra é estimado. Pausas sem marcação também são estimadas; o programa não reconhece a voz ou os instrumentos pelo áudio.

## ⌨️ Atalhos durante a reprodução

| Tecla | Ação |
|---|---|
| `Espaço` | Reproduzir ou pausar. |
| `n` / `p` | Próxima faixa / faixa anterior. |
| `v` | Alternar o visualizador. |
| `l` | Alternar entre interface completa e somente letras. |
| `r` | Alternar o modo de leitura. |
| `h` | Ativar ou desativar o destaque beta da palavra. |
| `a` | Alternar o alinhamento. |
| `s` | Mostrar ou ocultar a origem das letras. |
| `+` / `-` | Adiantar ou atrasar a sincronização em 50 ms. |
| `0` | Restaurar os padrões e salvar backup. |
| `?` | Abrir ou fechar a ajuda. |
| `q` / `Ctrl+C` | Encerrar. |

Os ajustes feitos pelas teclas são temporários, **exceto `0`, que salva os padrões**. Os comandos de configuração ficam salvos.

## 🔌 Fontes de letras e áudio

| Modo | Quando usar |
|---|---|
| `sylrics source native` | Para usar sem Spicy Lyrics. Busca letras pelo syncedlyrics, se instalado, e pelo LRCLIB. |
| `sylrics source auto` | Para preferir os tempos da ponte e recorrer ao modo nativo quando necessário. |
| `sylrics source spicy` | Para usar o relógio da ponte; exige conexão com ela. Sem letra com tempos, tenta a busca nativa. |

A ponte pode ser instalada com `sylrics bridge install`. **Essa ação altera o Spicetify e pode reiniciar o Spotify.** Depois, abra a letra da faixa no Spicy Lyrics.

No visualizador, `auto` usa o CAVA quando há áudio disponível e, caso contrário, uma animação decorativa. `spectrum` usa somente áudio, `activity` é decorativo e `off` oculta o visualizador. O CAVA pode captar também o áudio de outros aplicativos.

## 🛠️ Precisa ajustar ou recuperar algo?

```sh
# Verificar dependências e configuração
sylrics doctor

# Abrir uma prévia sem Spotify
sylrics demo

# Ver todas as configurações
sylrics config list

# Restaurar padrões com backup
sylrics config reset

# Recuperar a última configuração salva em backup
sylrics config restore
```

📁 Configuração: `~/.config/spotify-live-lyrics/ui.ini` — respeita `XDG_CONFIG_HOME`.

📁 Programa: `~/.local/share/spotify-live-lyrics/`.

📁 Letras: `~/.local/share/spotify-live-lyrics/lrc/` — até **10 arquivos**, com limpeza dos mais antigos ao iniciar ou salvar. Letras LRC sincronizadas soltas na pasta pessoal são recolhidas para essa pasta.

[📚 Consultar todos os comandos](COMMANDS.pt-BR.md) · [🩺 Resolver problemas comuns](QUICKSTART.pt-BR.md#-problemas-comuns)

## 📦 Histórico e colaboração

A versão **0.8.3** substitui os rótulos de reprodução por símbolos │◀ / ▌▌ / ▶ / ▶│ e adiciona uma moldura arredondada à capa, sempre à esquerda. O mini player continua responsivo; a área de clique inclui o espaço ao redor de cada símbolo. O instalador faz backup dos arquivos substituídos e da configuração; suas preferências são preservadas.

Veja o [histórico de alterações em português](CHANGELOG.md) ou baixe uma [versão publicada](https://github.com/math-eusz/spotify-live-lyrics/releases).

Encontrou um problema? [Abra uma issue](https://github.com/math-eusz/spotify-live-lyrics/issues) informando a versão, seu terminal, a música e o que aconteceu. Se puder, inclua a saída de `sylrics doctor` e uma captura de tela.

Para verificar o código em uma cópia do repositório:

```sh
python -m unittest discover -s tests -v
```

Os testes automatizados cobrem instalação, redimensionamento, botões em terminal, busca por palavra e fila local. O CI Linux também verifica o protocolo IPC e a reprodução de áudio pelo mpv com saída nula (sem alto-falantes). Os tempos fornecidos pelas letras e o comportamento do Spotify precisam ser avaliados na reprodução real. Os 180 FPS são uma meta de atualização, não uma garantia de desempenho.

## 📜 Licença e créditos

Distribuído sob a [licença MIT](LICENSE).

O projeto utiliza playerctl para controlar a reprodução, LRCLIB e opcionalmente syncedlyrics para obter letras, CAVA para visualizar áudio e uma ponte opcional com Spicy Lyrics. O sylrics é um projeto independente, sem vínculo oficial com o Spotify.

## 🎧 Reprodução independente · beta

```sh
# Arch Linux / CachyOS — dependência opcional do modo local
sudo pacman -S --needed mpv
sylrics local-beta ~/Músicas
# Ou escolha arquivos, na ordem desejada
sylrics local-beta "/caminho/artista - faixa.mp3" "/caminho/outra.flac"
```

A pasta é lida em ordem alfabética, sem subpastas; limite de 1000 arquivos por sessão. São aceitos MP3, FLAC, OGG, Opus, WAV, M4A, AAC, WMA e AIFF, conforme os codecs do mpv. O comando abre o sylrics e um processo mpv próprio; ao sair, esse processo é encerrado. Nenhuma alteração é feita na configuração pessoal do mpv.

**Fila:** pressione `F` para abrir/fechar, `J`/`K` para selecionar, `U`/`D` para mover para cima/baixo e `Enter` para reproduzir a seleção. A ordem vale apenas para a sessão e não modifica os arquivos. Esta fila é do **modo local**; visualizar ou reorganizar a fila do Spotify ainda não está implementado.

Um arquivo `faixa.lrc` ao lado de `faixa.mp3` tem prioridade sobre a busca online. Os metadados do arquivo são usados na busca; sem artista/título corretos, o resultado pode ser impreciso. Para capa local, coloque `cover.jpg`, `cover.png`, `folder.jpg` ou `folder.png` na pasta. Extração da capa embutida no áudio ainda não está incluída. A reprodução local funciona offline; a busca online de letras exige conexão. Este beta não reproduz o catálogo do Spotify sem o cliente.

```sh
sylrics controls on       # Mostrar botões de reprodução
sylrics controls off      # Ocultar botões; atalhos continuam disponíveis
sylrics cover on          # Mostrar a capa, inclusive na janela compacta
sylrics view lyrics       # Mostrar somente letras
sylrics view full         # Restaurar a interface completa
```

Na v0.8.3, os controles usam apenas símbolos: **│◀** anterior, **▌▌** pausar, **▶** reproduzir e **▶│** próxima. A capa fica à esquerda, dentro de uma moldura arredondada que acompanha o tema. Em janelas extremamente pequenas, a moldura é omitida para preservar a imagem. Os comandos e atalhos continuam iguais.
