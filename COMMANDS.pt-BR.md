# 🎛️ Comandos do sylrics · v0.7.2

[← Página inicial](README.md) · [🚀 Instalação](QUICKSTART.pt-BR.md)

As alterações de preferências ficam salvas. Os atalhos dentro do programa são temporários, exceto **0**, que salva os padrões com backup.

| Comando | Função |
|---|---|
| `sylrics` / `sylrics play` | Abrir o player; `slyrics` continua compatível. |
| `sylrics demo` | Prévia sem Spotify. |
| `sylrics --help` / `--version` | Ajuda ou versão instalada. |
| `sylrics doctor` | Verificar dependências e configuração. |
| `sylrics preset list` | Listar os perfis visuais. |
| `sylrics preset minimal` | Leitura discreta, sem moldura nem visualizador. |
| `sylrics preset studio` | Letras centralizadas e visualizador amplo. |
| `sylrics preset cinema` | Mais espaço entre frases, leitura contínua e visualizador nos intervalos. |
| `sylrics reading dynamic` | Blocos por duração e pausas. |
| `sylrics reading fixed` | Blocos de tamanho fixo. |
| `sylrics reading rolling` | Manter frases recentes e retirar as antigas individualmente. |
| `sylrics typing smooth` | Digitação contínua padrão. |
| `sylrics typing words-beta` | Digitação com pequenas pausas entre palavras. |
| `sylrics highlight bold-beta` / `off` | Ativar ou desativar negrito e sublinhado da palavra em digitação (estimado). |
| `sylrics font 18` / `sylrics font` | Abrir outra janela Kitty com tamanho escolhido ou salvo. |
| `sylrics theme dynamic` | Usar a paleta fornecida pelo terminal. |
| `sylrics theme warm` / `purple` / `ocean` / `mono` | Aplicar cores fixas. |
| `sylrics visualizer auto` / `spectrum` / `activity` / `off` | Áudio ou animação; somente áudio; animação decorativa; oculto. |
| `sylrics source native` / `auto` / `spicy` | Escolher a fonte de dados. Spicy exige ponte conectada. |
| `sylrics --source native` | Escolha válida só nesta execução. |
| `sylrics control play-pause` / `next` / `previous` | Controlar o player via playerctl. |
| `sylrics bridge status` / `install` | Consultar ou instalar a ponte opcional; install altera Spicetify. |
| `sylrics cache info` / `clear` | Conferir ou apagar as letras guardadas (máximo 10). |
| `sylrics config list` / `path` / `edit` | Listar valores, localizar ou editar o INI. |
| `sylrics config get CHAVE` | Consultar uma configuração. |
| `sylrics config set CHAVE VALOR` | Salvar uma configuração com validação e backup. |
| `sylrics gaps dots-beta` / `sylrics gaps off` | Ativar ou desativar os pontos animados nos intervalos (beta). |
| `sylrics click-seek on` / `sylrics click-seek off` | Ativar ou desativar a busca ao clicar em palavras visíveis (beta). |
| `sylrics font 18 --family "monospace"` | Escolher tamanho e família de fonte instalada, em uma nova janela Kitty. |
| `sylrics config reset` | Restaurar todos os padrões e salvar backup antes da mudança. |
| `sylrics config restore` | Restaurar o último backup, salvando antes o estado atual. |
| `sylrics --config ~/alternativo.ini` | Usar outro arquivo de configuração. |

Nas linhas com alternativas separadas por `/`, execute apenas uma alternativa.

## 🎨 Personalização pelo terminal

Exemplo: `sylrics config set visualizer.bar_spacing 2`.

| Chave | Valores / finalidade |
|---|---|
| `visualizer.bar_spacing` | 0–5 colunas entre bandas; padrão 1. |
| `visualizer.bar_width` | 1–4 colunas por banda; padrão 1. |
| `visualizer.width_percent` | 0–100% da área útil; padrão 85; 0 usa largura fixa. |
| `visualizer.width` | 8–100 bandas de origem; padrão 32. |
| `visualizer.height` | 1–6 linhas; wave usa uma linha. |
| `visualizer.bottom_margin` | 0–8 linhas de margem inferior. |
| `visualizer.smoothing_ms` | 0–500 ms; 0 desativa o filtro. |
| `visualizer.sensitivity` | 10–500; sensibilidade do CAVA. |
| `visualizer.style` | bars, wave ou dots. |
| `visualizer.only_gaps` | true/false: visualizar só nos intervalos vocais estimados. |
| `visualizer.show_label` | true/false: identificar áudio/animação/pausa. |
| `visualizer.input` | auto, pipewire ou pulse, conforme suporte do CAVA. |
| `layout.active_bold` | true/false: negrito da frase atual. |
| `layout.click_seek` | true/false: clique nas palavras (beta). |
| `layout.font_family` | Família instalada; aplicada ao abrir com `sylrics font`. |
| `pages.gap_animation` | true/false: pontos nos intervalos (beta); false em instalações novas. |
| `layout.history_dim` | true/false: frases anteriores em cor discreta. |
| `layout.alignment` | left, center ou right. |
| `layout.vertical` | top, center ou bottom. |
| `layout.line_spacing` | 0–4 linhas de espaço entre frases. |
| `layout.padding` | 0–20 colunas laterais. |
| `layout.lyrics_width` | 10–240 colunas antes da quebra visual. |
| `layout.border` | true/false: moldura. |
| `layout.show_progress` | true/false: tempo e progresso. |
| `layout.show_source` | true/false: informação da fonte no rodapé. |
| `layout.show_footer` | true/false: habilitar avisos e informações inferiores. |
| `layout.show_hints` | true/false: indicação de ajuda no rodapé. |
| `layout.icons` | true/false: símbolos do estado de reprodução. |
| `layout.cursor` | Símbolo da digitação, por exemplo '▎'; '' oculta. |
| `pages.max_lines` | 1–16 frases; precisa ser maior ou igual a min_lines. |
| `pages.min_lines` | 1–16; mínimo para trocas por duração no modo dynamic. |
| `pages.target_seconds` | 2–60 s; alvo de duração dos blocos dinâmicos. |
| `pages.pause_seconds` | 0.5–10 s; pausa para separar trechos. |
| `playback.fps` | 15–240; alvo de atualização, padrão 180. |
| `playback.sync_offset` | −10 a 10 s; positivo adianta, negativo atrasa. |
| `playback.type_ahead` | 0–0.5 s; adianta digitação sem antecipar troca de frase. |
| `playback.player` | Nome MPRIS consultado pelo playerctl; padrão spotify. |
| `colors.text`, `colors.accent`, `colors.muted`, `colors.border`, `colors.background` | '#RRGGBB' ou default, usadas no tema estático. |

Também existem as chaves correspondentes aos comandos próprios: `pages.mode`,
`visualizer.mode`, `playback.source`, `playback.typing_mode`, `layout.word_highlight`,
`layout.font_size` (6–48; só ao abrir com font) e `theme.mode` (static/dynamic).

## ⌨️ Atalhos durante a reprodução

| Tecla | Ação |
|---|---|
| q / Ctrl+C | Encerrar. |
| Espaço | Pausar/retomar. |
| n / p | Próxima/anterior. |
| v | Alternar visualizador. |
| r | Alternar leitura dynamic/fixed/rolling. |
| h | Alternar destaque beta. |
| a | Alternar alinhamento. |
| s | Exibir/ocultar informação da fonte. |
| + / - | Ajustar sincronização em 50 ms. |
| ? | Abrir/fechar ajuda. |
| 0 | Restaurar e salvar os padrões, com backup automático. |
| Clique esquerdo | Buscar o trecho da palavra visível, quando habilitado. |

Os perfis alteram apresentação e leitura, mas preservam fonte das letras, cores,
tamanho da fonte, efeitos beta e sincronização. A restauração usa o último backup;
como ela salva o estado atual, restaurar novamente pode alternar entre dois estados.


## 🧪 Entenda os recursos beta

`words-beta` mantém a animação caractere por caractere e acrescenta pequenas pausas entre palavras. `bold-beta` destaca a palavra em digitação, não uma palavra reconhecida por análise da voz.

`dots-beta` esconde as frases durante intervalos e mostra pontos animados. A duração mínima para considerar uma pausa vem de `pages.pause_seconds`. Ao desativar, as frases permanecem durante os intervalos e a introdução usa uma mensagem estática.

O clique usa tempos de início de sílaba quando disponíveis; com tempos apenas por linha, estima a posição da palavra. Requer playerctl e suporte a mouse no terminal. Para voltar a selecionar texto sem captura de clique pelo programa, use `sylrics click-seek off`.

## 💡 Exemplos prontos

```sh
# Espaço entre barras: 0 junta; 2 deixa mais afastado
sylrics config set visualizer.bar_spacing 2

# Suavização do visualizador em milissegundos
sylrics config set visualizer.smoothing_ms 180

# Máximo de seis frases no modo de leitura contínua
sylrics reading rolling
sylrics config set pages.max_lines 6

# Abrir a configuração no VS Code, se instalado
EDITOR=code sylrics config edit
```

Os nomes dos comandos e valores (`true`, `false`, `rolling` etc.) permanecem como usados pelo programa. `true` ativa e `false` desativa. Execute `sylrics config list` para ver os valores atuais.
