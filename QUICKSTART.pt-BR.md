# sylrics 0.7.0 — instalação e primeiros passos

Feche a versão anterior com Ctrl+C. Baixe e instale:

```fish
cd ~/Downloads
curl -fLO https://github.com/math-eusz/spotify-live-lyrics/releases/download/v0.7.0/sylrics-0.7.0.tar.gz
tar -xzf sylrics-0.7.0.tar.gz
cd sylrics-0.7.0
sh install.sh
```

O instalador faz backup, preserva suas configurações e não altera o Spicetify.
Abra outro terminal e execute `sylrics` (ou `~/.local/bin/sylrics` no terminal atual).
No Arch/CachyOS, o modo nativo precisa de `playerctl`; CAVA é opcional para áudio real.

## Experimentar a 0.7.0

```fish
sylrics preset studio
sylrics config set visualizer.bar_spacing 1
sylrics config set visualizer.bar_width 1
sylrics reading rolling
```

O perfil studio combina letras centralizadas e um visualizador amplo. Minimal
oculta moldura e visualizador; cinema usa leitura contínua e visualização nos
intervalos. Nenhum perfil muda tema, fonte das letras, tamanho da fonte ou sincronização.

O modo rolling mantém as frases recentes e retira apenas a mais antiga quando
necessário. O máximo continua ajustável em `pages.max_lines`; pausas longas iniciam
um novo trecho. Use `sylrics reading dynamic` para retornar aos blocos adaptativos.

## Ajustes rápidos

```fish
sylrics config set visualizer.bar_spacing 2
sylrics config set visualizer.bar_width 2
sylrics config set layout.history_dim false
sylrics config restore
```

O espaçamento aceita 0–5 colunas; a espessura, 1–4. O último comando restaura o
backup mais recente da configuração, salvando antes o estado que ele vai substituir.
Ele recupera o último backup, não uma sessão inteira. Repetir o comando pode
alternar entre os dois últimos estados, pois a restauração também gera backup.

Pressione `?` para ajuda, `r` para alternar a leitura e `h` para o destaque beta.
Os atalhos são temporários; comandos de configuração ficam salvos e aplicam-se ao vivo.

## Funcionalidades preservadas

`sylrics theme dynamic` acompanha a paleta do terminal. `sylrics font 18` abre
uma nova janela Kitty com esse tamanho. `sylrics typing words-beta` anima as palavras
com pausas breves; `sylrics highlight bold-beta` destaca a palavra em digitação.
Esses efeitos estimam o ritmo da voz. `sylrics source native` funciona sem Spicy Lyrics.
`sylrics visualizer off` oculta o visualizador; `auto` usa CAVA ou animação decorativa.

As letras ficam em `~/.local/share/spotify-live-lyrics/lrc/`, com limite de 10,
limpeza ao iniciar/salvar e coleta dos LRC sincronizados soltos na pasta pessoal.
As configurações ficam em `~/.config/spotify-live-lyrics/ui.ini`.

Consulte [COMMANDS.pt-BR.md](COMMANDS.pt-BR.md) para os comandos e limites.
