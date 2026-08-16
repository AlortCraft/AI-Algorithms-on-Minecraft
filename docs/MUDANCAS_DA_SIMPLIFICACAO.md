# O que foi removido e mantido

## Removido do parkour

- DQN, PyTorch e estado vetorial de rede neural;
- agentes aleatório e guloso separados;
- seleção entre vários algoritmos;
- simulador Python e sua física aproximada;
- treinamento híbrido e randomização de domínio;
- treinamento vetorizado e em vários processos;
- calibração automática, gravação de rotas e geração procedural;
- integração com pathfinder;
- gráficos e estrutura antiga de experimentos e métricas;
- testes e documentos exclusivos do simulador.

O sorteio epsilon-greedy não foi removido: ele é a estratégia de exploração do
próprio Q-Learning, e não um segundo agente.

## Mantido no parkour

- uma única classe `QLearning` e sua tabela;
- conexão Mineflayer com o Minecraft;
- ações, estado discreto e recompensa;
- reset por teleporte, detecção de queda, meta, travamento e tempo;
- salvamento da tabela e do CSV após cada episódio;
- treinamento paralelo com uma tabela compartilhada e nomes únicos;
- equipe automática sem colisão entre bots, jogadores e entidades comuns;
- mapas estáticos e ferramentas para exportá-los;
- cenários e trechos existentes.

## Preservado fora do parkour

O projeto de labirinto (`src/labirinto`), seus mapas e todos os mundos dentro de
`Servidor-BOT` não fazem parte da simplificação e foram preservados.
