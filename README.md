# Spotify Live Lyrics

Letras do Spotify no terminal Linux, reveladas caractere por caractere conforme a reprodução avança.

Esta é a versão inicial do projeto, baseada no script já usado no CachyOS com Hyprland. O programa consulta o Spotify pelo `playerctl`, busca letras LRC pelo `syncedlyrics` e estima o progresso dos caracteres entre dois timestamps de linha.

## Requisitos

Python 3, `playerctl`, `syncedlyrics` disponíveis no PATH e Spotify expondo o player MPRIS `spotify`. Não são necessários pacotes Python importados além da biblioteca padrão. O executável `syncedlyrics` é uma dependência externa.

## Execução

Abra o Spotify e inicie uma música. Na pasta do projeto, execute:

```bash
python lyrics.py
```

Encerre com `Ctrl+C`. O programa verifica mudanças de artista e título automaticamente.

## Ajustes

As constantes ficam no início de `lyrics.py`. `FPS = 180` é a frequência alvo do loop, sem garantia de 180 atualizações reais do terminal. A posição é consultada a cada 0,10 segundo; status a cada 0,20 segundo; metadata a cada 0,50 segundo.

`SYNC_OFFSET = 0.20` adianta a letra em 200 ms; `SYNC_OFFSET = -0.20` atrasa em 200 ms. `TYPE_RATIO = 0.90` distribui a digitação por 90% do intervalo até a próxima linha.

## Limitações conhecidas

A sincronização dos caracteres é estimada: não há timestamps reais por palavra nesta versão. Intervalos instrumentais podem deixar a digitação lenta, e o último verso usa duração de referência de cinco segundos. Consultas e busca de letras são síncronas; podem interromper o loop visual. Não há cache, e as correções de pause, seek e troca de faixa dependem das consultas periódicas. O horário usado no frame é medido antes das consultas, o que também pode prejudicar a sincronização.

As próximas melhorias priorizam sincronização e fluidez. Esta versão inicial preserva o comportamento do script original para servir de referência.
