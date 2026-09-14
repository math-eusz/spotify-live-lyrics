# sylrics 0.6.0 — instalação e comandos

O comando novo é **sylrics**. O antigo `slyrics` continua compatível.

## Instalar no seu PC

Baixe **sylrics-0.6.0.tar.gz** na release 0.6.0 e salve em Downloads. Feche a versão anterior com Ctrl+C. No terminal:

```fish
cd ~/Downloads
tar -xzf sylrics-0.6.0.tar.gz
cd sylrics-0.6.0
sh install.sh
```

O instalador faz backup dos arquivos substituídos, mantém a ponte antiga configurada e instala os comandos em `~/.local/bin`. Não precisa de sudo e não altera o Spicetify. Abra um terminal novo e execute:

```fish
sylrics
```

Para executar imediatamente no terminal atual:

```fish
~/.local/bin/sylrics
```

Se faltar playerctl no Arch/CachyOS:

```fish
sudo pacman -S playerctl
```

O programa funciona sem CAVA, usando animação identificada como tal. Instale CAVA para ter barras que reagem ao áudio do computador. Confira o estado com `sylrics doctor`.

## Escolher a fonte

O padrão é nativo, sem Spicy Lyrics. Para salvar outra opção:

```fish
sylrics source native
```

Troque `native` por `auto` para aproveitar a ponte quando ela tiver dados válidos, ou `spicy` para usar o relógio da ponte. Sem timestamps válidos, a busca nativa continua disponível. Para configurar a ponte opcional, use `sylrics bridge install`; só esse comando altera o Spicetify e pode reiniciar o Spotify. Depois reinicie o sylrics.

## Personalizar

```fish
sylrics theme purple
sylrics config set layout.alignment center
sylrics config set layout.show_source false
sylrics config set pages.max_lines 8
sylrics visualizer auto
sylrics config set visualizer.style wave
sylrics config set visualizer.only_gaps true
```

São exemplos independentes. As mudanças ficam salvas e aparecem ao vivo. Para escolher visualizador desligado, use `sylrics visualizer off`. `layout.show_source true` reativa o indicador inferior esquerdo. `sylrics config edit` abre o arquivo; `sylrics config list` mostra todas as opções.

As páginas são dinâmicas, limitadas inicialmente a 6 frases. Frases rápidas podem formar blocos maiores; frases lentas ou pausas podem formar blocos menores. O programa usa os tempos da letra: não analisa o sentimento da música nem identifica guitarra ou outros instrumentos.

## Atalhos durante a música

| Tecla | Ação |
| --- | --- |
| Espaço | Pausar/continuar |
| n / p | Próxima/anterior |
| v | Trocar visualizador |
| a | Trocar alinhamento |
| s | Mostrar/ocultar a fonte |
| + / - | Adiantar/atrasar 50 ms |
| ? | Ajuda |
| q ou Ctrl+C | Sair |

Os atalhos valem só para a execução atual. Para salvar escolhas, use os comandos `config`, `source`, `visualizer` ou `theme`.

## AUR / yay

A receita do pacote está pronta na release, mas **ainda não foi publicada no AUR**. `yay -S sylrics` ainda não funciona como rota de instalação do nosso projeto. O repositório está privado: falta disponibilizar o código publicamente e enviar a receita por uma conta de mantenedor do AUR.

Para testar o pacote local no Arch, baixe também `sylrics-0.6.0-aur.tar.gz`. Extraia a receita numa pasta, coloque o arquivo de código `sylrics-0.6.0.tar.gz` na mesma pasta do PKGBUILD e execute `makepkg -si` com seu usuário normal. O checksum da receita corresponde ao arquivo da release.

A demonstração não depende do Spotify: `sylrics demo`. O diagnóstico é `sylrics doctor`.
