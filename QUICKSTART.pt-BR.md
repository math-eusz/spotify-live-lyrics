# 🚀 Instalação e primeiros passos

[← Página inicial](README.md) · [🎛️ Todos os comandos](COMMANDS.pt-BR.md)

## 🐧 Antes de começar

O sylrics funciona em Linux, com **Python 3.10+** e **playerctl**. O Spotify precisa estar aberto e reproduzindo uma música. Spicetify e Spicy Lyrics são opcionais.

| Dependência | Para que serve | Obrigatória? |
|---|---|---|
| Python 3.10+ | Executar o programa. | Sim |
| playerctl | Consultar e controlar o player no modo nativo; necessário para os controles e cliques. | Sim, para o uso recomendado |
| curl e tar | Baixar e extrair o pacote pelos comandos abaixo. | Para este método de instalação |
| CAVA | Fazer o visualizador acompanhar o áudio. | Não |
| syncedlyrics | Oferecer uma fonte adicional de letras. O LRCLIB já é usado diretamente. | Não |
| Kitty | Abrir uma janela com tamanho e família de fonte definidos por `sylrics font`. | Apenas para esse comando |

No Arch Linux / CachyOS:

```sh
sudo pacman -S --needed python playerctl curl tar
```

Para adicionar o visualizador de áudio:

```sh
sudo pacman -S --needed cava
```

Em outras distribuições, use o gerenciador de pacotes correspondente. Estes comandos não instalam o Spotify.

## 📥 Instalar ou atualizar

Se o sylrics estiver aberto, encerre com `q` ou `Ctrl+C`. Depois:

```sh
curl -fLO https://github.com/math-eusz/spotify-live-lyrics/releases/download/v0.7.2/sylrics-0.7.2.tar.gz
tar -xzf sylrics-0.7.2.tar.gz
cd sylrics-0.7.2
sh install.sh
```

O instalador salva o programa em `~/.local/share/spotify-live-lyrics/` e cria os comandos em `~/.local/bin/`. Ele preserva as preferências existentes e faz backup dos arquivos substituídos na pasta `backup/` do programa. Não precisa ser executado com `sudo` e não altera o Spicetify.

Abra um **novo terminal**, coloque uma música no Spotify e rode:

```sh
sylrics
```

O nome antigo `slyrics` continua funcionando.

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
