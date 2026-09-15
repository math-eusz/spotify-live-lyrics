# 📦 Histórico de versões

[← Página inicial](README.md) · [⬇️ Downloads das versões](https://github.com/math-eusz/spotify-live-lyrics/releases)

Este histórico resume a evolução do sylrics em português. As primeiras versões foram numeradas retrospectivamente a partir das entregas completas do projeto. Cada versão publicada mantém seu código e seus arquivos originais.

## 🖱️ 0.7.2 — Interação e recuperação

Clique nas palavras para buscar um trecho, com tempos por sílaba quando disponíveis e estimativas quando há apenas tempos por linha. Novos comandos `click-seek on/off` e `gaps dots-beta/off`. A animação de intervalos passou a ser beta explícita, desativada em instalações novas; pausas curtas não apagam as letras.

A tecla **0** e `config reset` restauram os padrões com backup. A revisão incluiu eventos de mouse recebidos em partes, palavras com quebra de linha, caracteres largos, bloqueio de clique após troca de faixa e atualização imediata do relógio em pequenos saltos. **67 testes automatizados passaram.**

## 💬 0.7.1 — Intervalos e legibilidade

Correção das barras deformadas ao redimensionar, pontos animados nos intervalos vocais, negrito na frase atual e sublinhado no destaque beta de palavra. O comando de fonte passou a aceitar uma família instalada no sistema. **59 testes automatizados passaram.**

## 🎛️ 0.7.0 — Mais controle sobre o visual

Espaçamento e espessura das barras, leitura contínua com retirada individual de frases, perfis `minimal`, `studio` e `cinema`, histórico de frases em cor discreta e restauração da última configuração. Revisão da ajuda, completamentos de comandos e otimização da resolução de cores na renderização. **54 testes automatizados passaram.**

## 📁 0.6.4 — Letras organizadas

Pasta própria de arquivos LRC dentro do programa, limite de dez letras e remoção dos arquivos mais antigos ao iniciar ou salvar. Recolhimento de letras sincronizadas soltas na pasta pessoal e contenção dos arquivos criados por comandos externos de busca.

## 🌊 0.6.3 — Suavização e destaque

Suavização do visualizador baseada no tempo, barras com alturas fracionárias, destaque beta da palavra e abertura de uma janela Kitty com tamanho de fonte personalizável.

## ✍️ 0.6.2 — Digitação por palavra

Animação caractere por caractere dentro de cada palavra, seguida de pequenas pausas. Visualizador mais largo, com margem inferior e largura proporcional configuráveis.

## 🎨 0.6.1 — Tema dinâmico

Interface revisada, integração com a paleta de cores do terminal e modo beta de exibição por palavras. O tema pode acompanhar as cores do papel de parede quando o ambiente fornece essa paleta ao terminal.

## 🐧 0.6.0 — Uso independente

Modo nativo como padrão, integração opcional com Spicy Lyrics, busca pelo LRCLIB, páginas dinâmicas e visualizador configurável com CAVA. Introdução do comando `sylrics`, perfis de cores, configuração pelo terminal, atalhos, diagnóstico, demonstração e instalação por pacote de código-fonte.

## 🖼️ 0.5.0 — Interface personalizável

Letras centralizadas, borda, título, artista, progresso e estado de reprodução. Configuração por arquivo INI com aplicação ao vivo, quebra de linhas e adaptação ao tamanho do terminal.

## 🔧 0.4.2 — Reparo de instalações

Instalador de reparo para substituir versões antigas da ponte, com backup, verificação dos arquivos e preservação da configuração existente.

## 🔁 0.4.1 — Retorno automático à fonte nativa

Busca automática pelo syncedlyrics quando o Spicy Lyrics não fornece tempos utilizáveis, cache por música e proteção contra resultados atrasados de faixas anteriores. Restauração da digitação contínua.

## 🔌 0.4.0 — Ponte com Spicy Lyrics

Primeira integração local entre a extensão do Spotify e o terminal, com recebimento de letras e estado da reprodução. Esta versão histórica ainda exigia uso manual do modo antigo quando faltavam tempos; a correção chegou na 0.4.1.

## ⏱️ 0.3.0 — Sincronização e pausas

Consultas em segundo plano, adiantamento de 100 ms na digitação, separação de pausas e permanência da quarta frase até o início da quinta. Redução de redesenhos e proteção contra resultados de músicas já trocadas.

## 📖 0.2.0 — Blocos de quatro linhas

Frases anteriores permanecem visíveis enquanto a linha atual é digitada. A tela passa a ser organizada em blocos de até quatro linhas.

## 🌱 0.1.0 — Primeira versão

Letras do Spotify no terminal com playerctl e syncedlyrics, digitação progressiva, interpolação da posição e ajuste de sincronização.

---

**Sobre os testes:** as verificações automatizadas utilizam dados e processos simulados. A precisão na reprodução real depende dos tempos fornecidos pelas letras, do player e do terminal.

**Documentação atualizada:** página inicial, instalação e comandos reorganizados em português após a 0.7.2. Esta revisão de documentação não cria uma nova versão do programa.
