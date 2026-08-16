# Cenários e coordenadas de percurso

O mapa oficial avança em `+Z`. Os treinos construídos em `world_labirinto`
avançam em `-X`. Para o Q-Learning, essas duas direções devem parecer iguais.

`TransformacaoPercurso`, em `src/parkour/coordenadas.py`, converte as
coordenadas reais:

```text
Minecraft: x, y, z  →  IA: lateral, altura, progresso
```

Assim, andar em direção à meta sempre aumenta `progresso`, independentemente
do eixo usado no mundo.

## Cenários existentes

`config/cenarios/parkour_oficial.json` usa `world_parkour` e os trechos de
`config/parkour.json`.

`config/cenarios/labirinto_parkours.json` usa `world_labirinto` e define:

- `frente_1`: de `(87, 125, 74)` até `(34, 125, 74)`;
- `frente_2`: de `(87, 125, 56)` até `(34, 125, 56)`.

Esses dois são percursos de parkour. Os algoritmos BFS, DFS e A* permanecem
separados em `src/labirinto`.

## Conectar e treinar

```powershell
python -m src.parkour.main --cenario labirinto_parkours --trecho frente_1
```

Depois use `parkour treinar N` no chat. Não existe uma etapa de treino fora do
jogo.

O nome do cenário e do trecho entra no nome da tabela Q, evitando usar por
engano uma tabela de outro mapa.

## Reexportar um percurso

Com o servidor desligado:

```powershell
python -m tools.mapear_percurso `
  --mundo Servidor-BOT/world_labirinto `
  --inicio 87 125 56 `
  --fim 34 125 56 `
  --saida config/mapas/world_labirinto_frente_2.json `
  --perfil
```

Cada JSON guarda suas coordenadas e o mundo de origem. `Percurso.carregar`
valida esses dados antes de iniciar o treinamento.
