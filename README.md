# Spotify Live Lyrics

Letras do Spotify no terminal Linux, reveladas caractere por caractere em blocos de quatro frases.

## Requisitos e execução

Python 3, `playerctl` e `syncedlyrics` disponíveis no PATH. Abra o Spotify (player MPRIS `spotify`), toque uma música e execute `python lyrics.py` na pasta do projeto. Encerre com Ctrl+C.

## Comportamento

As frases completas permanecem no bloco. A quinta frase inicia uma nova página somente ao alcançar seu timestamp: o adiantamento da digitação não antecipa essa troca. Linhas vazias do LRC não contam entre as quatro frases. Pausas de pelo menos dois segundos ganham uma linha em branco, usando marcações vazias do LRC quando disponíveis ou uma estimativa baseada no tamanho das frases e no ritmo das demais linhas.

As consultas do Spotify e a busca de letras rodam em threads separadas do loop visual. Há cache em memória de até 64 músicas durante a execução. A tela só é redesenhada quando o conteúdo muda.

## Ajustes no início de lyrics.py

`LINES_PER_BLOCK = 4` controla frases por bloco. `PAUSE_SECONDS = 2.0` controla a pausa mínima para separar trechos. `TYPE_AHEAD = 0.10` adianta o progresso da digitação em 100 ms dentro da frase, sem revelar uma nova frase antes de seu timestamp. `SYNC_OFFSET = 0.00` corrige toda a linha do tempo: valores positivos adiantam tudo, inclusive trocas de bloco; negativos atrasam. `TYPE_RATIO = 0.95` usa 95% do intervalo disponível, com limite estimado para intervalos longos.

`FPS = 180` é o alvo do loop, sem garantia de 180 atualizações reais do terminal. Posição e status têm intervalo alvo de 100 ms; metadata, aproximadamente 500 ms. A duração das consultas pode aumentar esses intervalos.

## Limitações e validação

Não há análise do áudio nem timestamps reais por palavra. Pausas sem marcação e velocidade dos caracteres são estimadas e podem divergir do canto, especialmente em frases sustentadas. A busca ainda pode levar até 30 segundos; a interface continua respondendo durante a espera. A correção de pause e seek depende da próxima consulta.

Verificados localmente: sintaxe, permanência da quarta frase, transição para a quinta, pausas marcadas e estimadas, retorno para frases anteriores e parsing de timestamps repetidos. A sincronização com áudio real precisa ser avaliada no computador com o Spotify.
