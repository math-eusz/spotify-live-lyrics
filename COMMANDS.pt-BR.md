# sylrics 0.7.2 — referência de comandos

As alterações de preferências ficam salvas. Os atalhos dentro do player são temporários.

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
| `sylrics highlight bold-beta` / `off` | Ativar ou desativar negrito estimado da palavra atual. |
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
| `sylrics config restore` | Restaurar o último backup, salvando antes o estado atual. |
| `sylrics --config ~/alternativo.ini` | Usar outro arquivo de configuração. |

Nas linhas com alternativas separadas por `/`, execute apenas uma alternativa.

## Personalização com config set

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

## Teclas dentro do player

| Tecla minúscula | Ação |
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

Os perfis alteram apresentação e leitura, mas preservam fonte das letras, cores,
tamanho da fonte, efeitos beta e sincronização. A restauração usa o último backup;
como ela salva o estado atual, restaurar novamente pode alternar entre dois estados.


# v0.7.2 — Clique nas palavras, intervalos beta e restauração de padrões

Os intervalos animados agora são uma opção beta explícita. `sylrics gaps dots-beta` ativa e `sylrics gaps off` desativa, inclusive na introdução. Instalações novas deixam o recurso desligado; atualizações preservam a escolha existente. Pausas curtas entre versos não apagam mais a letra. O limite é `pages.pause_seconds` (padrão: 2 segundos). Sem marcações vocais, a detecção continua estimada.

Clique com o botão esquerdo em uma palavra visível para buscar aquele trecho. `sylrics click-seek on` ativa e `sylrics click-seek off` desativa. O clique é beta e vem ativado por padrão. Com tempos por sílaba, usa o início da sílaba que contém o começo da palavra; com tempos apenas por linha, estima o início pelo ritmo da digitação. Não garante alinhamento exato com a voz. Requer playerctl e suporte a mouse do terminal. Não muda o estado reproduzindo/pausado. O controle recusa cliques após mudança de faixa ou redimensionamento ainda não desenhado. Ajuda, espaços e letras ainda invisíveis não são alvos.

Pressione **0** dentro do programa para restaurar as configurações padrão e limpar os ajustes da sessão. O comando equivalente é `sylrics config reset`. Ambos salvam backup antes da alteração. Use `sylrics config restore` para recuperar a configuração anterior. A restauração inclui tema, fonte de letras, visualizador e recursos beta; não remove o cache nem a ponte. O tamanho e a família da fonte do terminal são aplicados ao reabrir com `sylrics font`.

Revisão: processamento de eventos de mouse recebidos em partes, mapeamento de palavras conforme quebra de linha e alinhamento, suporte a caracteres largos, buscas fora do loop visual, aplicação imediata de pequenos saltos no relógio e restauração do modo de mouse ao sair. Comandos e completamentos Fish/Bash atualizados.

Testes automatizados incluem o fluxo completo em pseudoterminal com playerctl simulado. A reprodução dentro do Spotify do usuário ainda precisa de validação.
