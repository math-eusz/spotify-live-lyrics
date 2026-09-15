<div align="center">

# 🎵 sylrics

**Sua música, palavra por palavra, no terminal.**

Letras sincronizadas, visualizador de áudio e uma interface que você pode deixar do seu jeito.

**🐧 Linux · 🐍 Python 3.10+ · 📦 v0.7.2 · 📜 MIT**

[🚀 Instalar](#-instalação) · [🎛️ Comandos](COMMANDS.pt-BR.md) · [📖 Primeiros passos](QUICKSTART.pt-BR.md) · [📦 Versões](https://github.com/math-eusz/spotify-live-lyrics/releases)

</div>

---

## ✨ O que você pode fazer

| Recurso | Como funciona |
|---|---|
| 🎶 Letras em tempo real | Acompanhe a música com digitação caractere por caractere. |
| 🌊 Visualizador | Escolha barras, ondas ou pontos; ajuste largura, espaçamento e suavização. |
| 📖 Leitura adaptável | Use blocos fixos, blocos por duração e pausas ou frases que saem individualmente. |
| 🎨 Personalização | Mude cores, alinhamento, margens, fonte e destaque das letras. |
| 🖱️ Clique nas palavras · beta | Volte ao trecho correspondente clicando em uma palavra visível. |
| 💬 Intervalos animados · beta | Substitua as letras por “...” durante as pausas, se quiser. |
| 💾 Preferências e backup | Ajuste pelo terminal ou pelo arquivo de configuração e restaure quando precisar. |

**O Spicy Lyrics é opcional.** O modo nativo é o padrão e funciona sem Spicetify. É necessário ter um player compatível em execução; o sylrics acompanha a reprodução, não toca as músicas sozinho.

## 🚀 Instalação

Você precisa de **Linux, Python 3.10+, playerctl, curl e tar**. Para o visualizador reagir ao áudio, instale também o **CAVA**.

No **Arch Linux / CachyOS**:

```sh
sudo pacman -S --needed python playerctl curl tar
```

Visualizador de áudio opcional:

```sh
sudo pacman -S --needed cava
```

Baixe e instale a versão atual:

```sh
curl -fLO https://github.com/math-eusz/spotify-live-lyrics/releases/download/v0.7.2/sylrics-0.7.2.tar.gz
tar -xzf sylrics-0.7.2.tar.gz
cd sylrics-0.7.2
sh install.sh
```

Abra um novo terminal, coloque uma música no Spotify e execute:

```sh
sylrics
```

> 💡 Já usa o programa? Feche com `q` ou `Ctrl+C` e execute a mesma instalação. Seus ajustes são preservados e os arquivos substituídos recebem backup. O instalador do sylrics não precisa de `sudo`.

Em outras distribuições Linux, instale as dependências pelo gerenciador de pacotes correspondente. Consulte o [guia de instalação](QUICKSTART.pt-BR.md) para detalhes e solução de problemas.

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

A versão **0.7.2** trouxe clique nas palavras, controle explícito dos intervalos beta e restauração dos padrões pela tecla `0`.

Veja o [histórico de alterações em português](CHANGELOG.md) ou baixe uma [versão publicada](https://github.com/math-eusz/spotify-live-lyrics/releases).

Encontrou um problema? [Abra uma issue](https://github.com/math-eusz/spotify-live-lyrics/issues) informando a versão, seu terminal, a música e o que aconteceu. Se puder, inclua a saída de `sylrics doctor` e uma captura de tela.

Para verificar o código em uma cópia do repositório:

```sh
python -m unittest discover -s tests -v
```

A v0.7.2 passou por **67 testes automatizados**, incluindo instalação e interação em terminal com player simulado. Os tempos fornecidos pelas letras e o comportamento do Spotify precisam ser avaliados na reprodução real. Os 180 FPS são uma meta de atualização, não uma garantia de desempenho.

## 📜 Licença e créditos

Distribuído sob a [licença MIT](LICENSE).

O projeto utiliza playerctl para controlar a reprodução, LRCLIB e opcionalmente syncedlyrics para obter letras, CAVA para visualizar áudio e uma ponte opcional com Spicy Lyrics. O sylrics é um projeto independente, sem vínculo oficial com o Spotify.
