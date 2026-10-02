# 🚀 Instalação e primeiros passos

[← Página inicial](README.md) · [🎛️ Todos os comandos](COMMANDS.pt-BR.md)

## 🐧 Antes de começar

O sylrics funciona em Linux, com **Python 3.10+** e **playerctl**. Para acompanhar o Spotify ou spotify_player, ele precisa estar aberto e reproduzindo uma música. Para arquivos locais, o beta usa mpv e dispensa Spotify e playerctl. Spicetify e Spicy Lyrics são opcionais.

| Dependência | Para que serve | Obrigatória? |
|---|---|---|
| Python 3.10+ | Executar o programa. | Sim |
| playerctl | Consultar e controlar o player no modo nativo; necessário para os controles e cliques. | Sim, para o uso recomendado |
| curl e tar | Baixar e extrair o pacote pelos comandos abaixo. | Para este método de instalação |
| mpv | Reproduzir arquivos locais e editar a fila. | Somente para `local-beta` |
| CAVA | Fazer o visualizador acompanhar o áudio. | Não |
| syncedlyrics | Oferecer uma fonte adicional de letras. O LRCLIB já é usado diretamente. | Não |
| Kitty | Mostrar capas e abrir janelas com fonte definida por `sylrics font`. | Não, para letras |
| Pillow (`python-pillow` no Arch) | Decodificar as capas dos álbuns. | Não |

No Arch Linux / CachyOS:

```sh
sudo pacman -S --needed python playerctl curl tar
```

Para adicionar visualizador de áudio e capas (use Kitty):

```sh
sudo pacman -S --needed cava python-pillow
```

Em outras distribuições, use o gerenciador de pacotes correspondente. Estes comandos não instalam o Spotify.

## 📥 Instalar ou atualizar

Se o sylrics estiver aberto, encerre com `q` ou `Ctrl+C`. Depois:

```sh
curl -fLO https://github.com/math-eusz/spotify-live-lyrics/releases/download/v0.8.6/sylrics-0.8.6.tar.gz
tar -xzf sylrics-0.8.6.tar.gz
cd sylrics-0.8.6
sh install.sh
```

O instalador salva o programa em `~/.local/share/spotify-live-lyrics/` e cria os comandos em `~/.local/bin/`. O pacote e a configuração são verificados antes de substituir o código. Ele preserva as preferências existentes e faz backup dos arquivos substituídos na pasta `backup/` do programa. Não precisa ser executado com `sudo` e não altera o Spicetify.

Abra um **novo terminal**, coloque uma música no Spotify ou spotify_player e rode:

```sh
sylrics
```

O nome antigo `slyrics` continua funcionando.

## 🔊 Usar spotify_player

```sh
sylrics source native
sylrics player auto
sylrics
```

Para fixar o cliente de terminal, use `sylrics player spotify_player`. Caso não apareça em `playerctl -l`, confira `enable_media_control = true` em `~/.config/spotify-player/app.toml` e reinicie o spotify_player. Sua compilação precisa incluir o recurso `media-control`. A ponte Spicy não é necessária.

## 🖼️ Interface completa ou somente letras

```sh
sylrics view lyrics
```

Oculta cabeçalho, capa, progresso, moldura, rodapé e visualizador. Para voltar:

```sh
sylrics view full
```

A tecla **L** alterna os dois modos apenas na sessão. Para controlar somente a capa, use `sylrics cover on` ou `sylrics cover off`. As imagens requerem Kitty sem tmux, Pillow e uma capa informada pelo player. Em janelas pequenas o cabeçalho fica compacto.

## 🎨 Escolher um visual

Para letras centralizadas com visualizador amplo:

```sh
sylrics preset studio
```

Para uma interface discreta, sem visualizador:

```sh
sylrics preset minimal
```

Para usar a paleta do terminal, incluindo as cores do papel de parede quando o sistema fornece essa integração:

```sh
sylrics theme dynamic
```

Para letras maiores em uma nova janela Kitty:

```sh
sylrics font 18
```

## ⚡ Escolher o desempenho

Use `sylrics performance balanced` para equilibrar fluidez e consumo. `sylrics performance smooth` prioriza fluidez; `sylrics performance eco` reduz a frequência de atualização. Cores, layout e sincronização são preservados.

O programa reduz a atividade quando pausado ou sem player. Falhas temporárias de capa são tentadas novamente após 30 segundos; o cache de imagens continua limitado a oito entradas. Um cache de letras sem permissão não impede a busca pela internet.

## 🧪 Experimentar os recursos beta

Cada comando é opcional. Os ajustes ficam salvos.

| Recurso | Ativar | Desativar |
|---|---|---|
| Pausas entre palavras digitadas | `sylrics typing words-beta` | `sylrics typing smooth` |
| Destaque da palavra | `sylrics highlight bold-beta` | `sylrics highlight off` |
| Pontos animados nos intervalos | `sylrics gaps dots-beta` | `sylrics gaps off` |
| Clique para buscar uma palavra | `sylrics click-seek on` | `sylrics click-seek off` |

O clique atua em palavras visíveis e precisa de playerctl e de um terminal com suporte a mouse. Com tempos apenas por linha, a posição é estimada. Ele não altera o estado pausado/em reprodução.

## ↩️ Voltar ao padrão

Dentro do programa, pressione **0**. Pelo terminal, execute:

```sh
sylrics config reset
```

Isso salva um backup e restaura todas as preferências padrão, incluindo cores, fonte de letras e visualizador. Para recuperar a configuração anterior:

```sh
sylrics config restore
```

A restauração também cria backup: executá-la repetidamente pode alternar entre os dois últimos estados. Mudanças no tamanho e na família da fonte são aplicadas à nova janela aberta por `sylrics font`.

## 🩺 Problemas comuns

| Situação | O que fazer |
|---|---|
| `sylrics: comando não encontrado` | Abra outro terminal ou rode `~/.local/bin/sylrics`. Em Bash/Zsh, confira se `~/.local/bin` está no PATH. |
| Spotify não aparece | Abra o aplicativo, coloque uma faixa e rode `sylrics doctor`. O player precisa ser compatível com playerctl. |
| A letra não foi encontrada | Tente outra faixa. Nem toda música tem letra sincronizada nas fontes disponíveis. |
| A letra aparece cedo ou tarde | Use `+` e `-` durante a reprodução; para salvar, use `sylrics config set playback.sync_offset 0.10`. Positivo adianta, negativo atrasa. |
| O visualizador não acompanha o som | Instale CAVA e teste `sylrics visualizer spectrum`. No modo `activity`, a animação é decorativa. |
| Quero ocultar o visualizador | Execute `sylrics visualizer off`. |
| Os “...” aparecem na hora errada | Execute `sylrics gaps off`. A detecção de pausas sem marcação ainda é beta e estimada. |
| O clique não vai exatamente à palavra | A precisão depende dos tempos recebidos. Letras com apenas tempos por linha usam estimativa. |
| Editei a configuração e deu erro | Use `sylrics config restore` para recuperar um backup ou `sylrics config reset` para voltar aos padrões. |
| Quero usar sem Spicy Lyrics | Execute `sylrics source native`. |

Teste uma prévia independente do Spotify com `sylrics demo`. Para relatar um problema, inclua a saída de `sylrics doctor`, a versão e o nome da música na [página de issues](https://github.com/math-eusz/spotify-live-lyrics/issues).

## 📁 Onde ficam os arquivos?

| Conteúdo | Local padrão |
|---|---|
| Configuração | `~/.config/spotify-live-lyrics/ui.ini` |
| Backups de configuração | `~/.config/spotify-live-lyrics/backup/` — até 20 backups |
| Programa | `~/.local/share/spotify-live-lyrics/` |
| Backup de instalação | Pasta `backup/` dentro do programa |
| Letras sincronizadas | Pasta `lrc/` dentro do programa — até 10 arquivos |
| Executáveis | `~/.local/bin/sylrics` e `~/.local/bin/slyrics` |

A configuração respeita `XDG_CONFIG_HOME`. O programa recolhe arquivos LRC sincronizados soltos na pasta pessoal e mantém apenas os dez mais recentes na pasta de letras. Consulte `sylrics cache info` para conferir o local usado.

## 🎧 Sem Spotify: arquivos locais (beta)

```sh
sudo pacman -S --needed mpv
sylrics local-beta ~/Músicas
```

Use `F` para ver a fila, `J`/`K` para selecionar, `U`/`D` para reorganizar e `Enter` para tocar. A pasta não é percorrida recursivamente. Para escolher a ordem inicial, passe vários arquivos ao comando. Ao encerrar o sylrics, a reprodução local também termina. A fila do Spotify não é alterada.

O mini player aparece automaticamente ao reduzir a janela. A capa encolhe junto e os botões ficam compactos. `sylrics controls off` oculta os botões; `sylrics controls on` restaura. As capas continuam dependendo de uma imagem disponível, Kitty sem tmux e Pillow.

Se o visualizador não recebe áudio, teste `cava` sozinho durante a reprodução. No modo `spectrum`, o sylrics agora mostra uma mensagem de indisponibilidade. Em sistemas com PulseAudio ou compatibilidade pipewire-pulse, experimente `sylrics config set visualizer.input pulse`; restaure a seleção automática com `sylrics config set visualizer.input auto`. Isso depende do suporte da sua compilação do CAVA.

Na v0.8.6, os controles usam apenas símbolos: **│◀** anterior, **▌▌** pausar, **▶** reproduzir e **▶│** próxima. A capa fica à esquerda, dentro de uma moldura arredondada que acompanha o tema. Em janelas extremamente pequenas, a moldura é omitida para preservar a imagem. Os comandos e atalhos continuam iguais.

A v0.8.6 segue a referência de player compacto: informações à esquerda, controles no centro e tempo integrado à barra inferior. A capa e sua borda continuam disponíveis; em janelas estreitas, os controles se reorganizam. O botão [M] abre as configurações.

## ⚙️ Configurações dentro do player

Pressione **M** ou clique em **[M]** no canto superior para abrir o menu. Ele funciona mesmo sem música tocando e no modo somente letras (pela tecla M).

Use **↑/↓** para selecionar e **←/→** para alterar. **Tab** ou **[ / ]** alternam entre Interface, Reprodução, Letras, Visualizador, Tema e Cores. Também é possível clicar nas setas da categoria e nas opções.

**E** edita um valor diretamente (como uma cor `#RRGGBB`, nome de player ou fonte); Enter confirma a edição. **S** ou o botão Salvar grava todas as alterações com backup. **Esc/M** descarta e fecha; durante edição, Esc cancela somente a entrada de texto. **R** carrega os padrões no menu, que só são gravados depois de Salvar.

As alterações válidas são pré-visualizadas durante a sessão. Valores inválidos não são aplicados nem gravados. No menu, as teclas e cliques não acionam a música por trás. A fonte e seu tamanho continuam exigindo uma nova janela com `sylrics font`; não alteram o zoom do terminal atual.
