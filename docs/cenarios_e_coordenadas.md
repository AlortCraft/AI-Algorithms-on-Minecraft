# Cenários e coordenadas de percurso

## O problema que esta camada resolve

O parkour oficial avança em `+Z`. O primeiro treino construído dentro de
`world_labirinto` começa em `(87, 125, 74)` e termina em `(35, 125, 74)`, ou
seja, avança em `-X`.

Antes desta mudança, o programa usava `z_depois - z_antes` como progresso em
todos os lugares. No treino do labirinto, Z permanece em 74. O bot podia andar
52 blocos em X e ainda seria registrado como parado. O estado também procurava
obstáculos em `z + 1`, na direção errada.

A solução não é duplicar os agentes. É converter o mundo para um sistema local
único antes de entregá-lo ao simulador e à IA:

```text
coordenadas do Minecraft       coordenadas que a IA recebe
x, y, z                 ->     lateral, altura, progresso
```

Para o primeiro treino:

```text
progresso = 87,5 - x_mundo + 0,5
lateral   = z_mundo
direção   = -X
yaw       = 90°
```

Na prática, o centro da célula inicial `(87,5, 125, 74,5)` vira progresso
`0,5`. Cada bloco percorrido em `-X` aumenta o progresso em um.

## Onde está cada parte

### `config/parkour.json`

Continua sendo a configuração comum: recompensa, estado, Q-Learning, DQN,
randomização e limites do episódio. Isso evita copiar parâmetros de IA para
cada mundo.

### `config/cenarios/*.json`

Escolhe o mundo e os trechos:

- `parkour_oficial.json`: usa `world_parkour` e herda os trechos antigos;
- `labirinto_parkours.json`: usa `world_labirinto` e cadastra os treinos simples.

Um trecho em direção arbitrária usa `inicio` e `fim`, em vez de `z_inicio` e
`z_meta`. Ele também pode indicar seu próprio arquivo `mapa`, o que permite que
cada um dos três parkours simples tenha uma exportação independente.

### `src/parkour/config.py`

Carrega `parkour.json` e sobrepõe o cenário escolhido. Também:

- lista cenários existentes;
- localiza o JSON de cada trecho;
- compara o `mundo` do cenário com `level-name` quando o servidor é local;
- inclui o cenário no nome do modelo salvo, evitando carregar uma tabela Q de
  outro mundo por engano.

### `src/parkour/coordenadas.py`

Contém `TransformacaoPercurso`. Ela descobre uma das quatro direções cardinais
`+X`, `-X`, `+Z` ou `-Z`, calcula o yaw e faz as conversões:

- posição do mundo -> posição local;
- posição local -> posição do mundo;
- velocidade do mundo -> velocidade local;
- célula de bloco do mundo <-> célula local.

Percursos diagonais são recusados de propósito. A física e as caixas de bloco
atuais trabalham sobre uma grade cardinal; aceitar diagonal sem modelá-la
corretamente esconderia um erro.

### `tools/mapear_percurso.py`

Lê os arquivos `.mca` entre dois pontos e gira os blocos para o sistema local.
Também guarda o nome dos blocos, usado depois para conferir o JSON contra o
Minecraft ao vivo.

No primeiro treino, a leitura encontrou uma pista de um bloco de largura em
`z_mundo=74`. Há apoio em 28 das 53 posições: depois das plataformas de início,
os blocos verdes aparecem alternados com vãos. Portanto, “só para frente” ainda
exige a ação de correr e pular; não é um piso contínuo.

### `src/parkour/percurso.py`

Continua oferecendo a geometria no formato antigo (`x` lateral e `z` adiante).
Ao encontrar `inicio`/`fim`, associa a transformação ao percurso e valida três
coisas antes de aceitar o JSON:

1. o mapa foi exportado em coordenadas locais;
2. início e fim do JSON são iguais aos do cenário;
3. o mundo gravado no JSON é o mundo esperado.

Essa validação impede usar silenciosamente um arquivo exportado antes de uma
mudança de coordenadas.

### `src/parkour/ambiente_mc.py`

`_CorpoDoBot` lê posição e velocidade reais e as apresenta em coordenadas
locais. O reset faz a conversão inversa para teleportar o bot e usa o yaw da
direção.

O método `verificar_geometria()` consulta uma amostra com `bot.blockAt()` e
compara nomes reais com o JSON. O treino não faz essa consulta em todo passo,
porque atravessar a ponte Python/JavaScript milhares de vezes deixaria o
treino lento.

### `src/parkour/main.py`

Aceita `--cenario` e `--trecho`, escolhe automaticamente o cenário que combina
com o `level-name` local quando o argumento é omitido e oferece o comando de
chat `parkour verificar`.

`parkour info` mostra as duas visões:

- coordenadas reais do mundo;
- lateral, altura e progresso vistos pela IA.

### `src/parkour/experimento.py` e `vetorizado.py`

Aceitam `--cenario`. Modelos e CSVs recebem o cenário no nome. Assim
`q_parkour_oficial_A_s0.json` e
`q_labirinto_parkours_frente_1_s0.json` nunca se confundem.

### `src/parkour/recompensa.py`

A fórmula não mudou; os nomes foram generalizados. Antes ela dizia “diferença
de Z”. Agora recebe “progresso antes/depois”. Como o ambiente já converteu a
posição, avançar em `-X` produz recompensa positiva normalmente.

### `testes/teste_ambiente.py`

Testa ida e volta, progresso e yaw nas quatro direções. Também carrega o
cenário real do labirinto e prova no simulador que repetir `correr_pulo`
conclui o primeiro percurso.

## Como usar

Treinar no primeiro percurso do labirinto:

```powershell
python -m src.parkour.experimento --cenario labirinto_parkours `
  --trecho frente_1 --agente q --episodios 4000
```

Conectar ao mesmo cenário:

```powershell
python -m src.parkour.main --cenario labirinto_parkours --trecho frente_1
```

No chat, antes de rodar uma política:

```text
parkour reset
parkour info
parkour verificar
```

Voltar ao mapa oficial:

```powershell
python -m src.parkour.main --cenario parkour_oficial
```

O PaperMC deve estar parado ao trocar `level-name`. Se o cenário e o
`server.properties` local discordarem, o programa encerra com uma explicação.

## Como cadastrar os outros dois treinos

Para cada percurso ainda faltam início e fim. Com o servidor encerrado por
`stop`, exporte:

```powershell
python -m tools.mapear_percurso `
  --mundo Servidor-BOT/world_labirinto `
  --inicio X_INICIO Y_INICIO Z_INICIO `
  --fim X_FIM Y_FIM Z_FIM `
  --saida config/mapas/world_labirinto_frente_2.json `
  --perfil
```

Depois acrescente `frente_2` a `config/cenarios/labirinto_parkours.json`. Não se
deve reutilizar o JSON de `frente_1`: cada exportação guarda e valida suas
próprias coordenadas.
