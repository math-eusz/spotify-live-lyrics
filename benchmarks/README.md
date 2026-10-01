# Benchmark de renderização

Execute `python benchmarks/render.py` a partir do projeto. Para comparar outra cópia do código, passe o caminho: `python benchmarks/render.py ../sylrics-0.8.0`.

O cenário usa 900 quadros, relógio de 180 Hz, terminal de 120×36 células, digitação words-beta e visualizador decorativo. Mede tempo de CPU do processo com `time.process_time()`, repete três vezes e informa a mediana. Não executa rede, CAVA, playerctl nem escrita em terminal real.

Na revisão local, a mediana passou de aproximadamente 1,11 s (0.8.0) para 0,57 s (0.8.1). O visualizador passou a respeitar seu limite independente de 60 FPS; a digitação continua com relógio de 180 Hz. Os resultados variam com a máquina, a carga e o tamanho do terminal. Não extrapole esse percentual para o consumo total do aplicativo.

A consulta agrupada do player é baseada nos campos `position` (microssegundos) e `status` documentados no [playerctl](https://github.com/altdesktop/playerctl#Printing-Properties-and-Metadata).
