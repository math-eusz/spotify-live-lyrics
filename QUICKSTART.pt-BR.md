# sylrics 0.6.3 — instalação e comandos

O comando novo é **sylrics**. O antigo `slyrics` continua compatível.

## Instalar no seu PC

Baixe **sylrics-0.6.3.tar.gz** na release 0.6.3 e salve em Downloads. Feche a versão anterior com Ctrl+C. No terminal:

```fish
cd ~/Downloads
tar -xzf sylrics-0.6.3.tar.gz
cd sylrics-0.6.3
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

O programa funciona sem CAVA, usando uma animação decorativa (o rótulo pode ser ativado com `visualizer.show_label`). Instale CAVA para ter barras que reagem ao áudio do computador. Confira o estado com `sylrics doctor`.

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

A demonstração não depende do Spotify: `sylrics demo`. O diagnóstico é `sylrics doctor`.

## Revisão 0.6.3

O tema dinâmico acompanha a **paleta do terminal**. Na configuração com Noctalia,
que gera o tema do terminal a partir do papel de parede, isso permite acompanhar
as mudanças sem outro gerador de cores. O sylrics não lê a imagem do papel de
parede. Se o terminal não receber uma nova paleta, as cores permanecerão iguais.
A transparência e o fundo continuam sob controle do terminal.

```sh
sylrics theme dynamic
# Retornar às cores fixas:
sylrics theme warm
```

O rótulo do visualizador e a lista permanente de atalhos ficam ocultos por padrão.
Pressione `?` para abrir ou fechar a ajuda. O visualizador continua opcional:

```sh
sylrics visualizer off
sylrics visualizer auto
sylrics config set visualizer.show_label true
sylrics config set layout.show_hints true
```

**Digitação por palavra — beta:** anima cada palavra letra por letra e faz uma pausa breve antes da próxima,
sem interromper o relógio de reprodução. Usa o ritmo estimado da linha; não detecta
voz nem cria timestamps reais por palavra. Pausar ou buscar outro ponto da música
continua funcionando. A digitação contínua permanece como padrão.

```sh
sylrics typing words-beta
sylrics typing smooth
```

No arquivo `ui.ini`, as opções correspondentes são `[theme] mode = dynamic`,
`[visualizer] show_label = false`, `[layout] show_hints = false` e
`[playback] typing_mode = words-beta`. Comandos de configuração aplicam-se ao vivo,
inclusive depois de usar atalhos temporários. A instalação preserva suas escolhas.

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
