# AI Algorithms on Minecraft

Projeto acadêmico de Introdução à Inteligência Artificial. Um bot joga
Minecraft Java Edition; a comunicação com o jogo usa Mineflayer via Python e o
servidor é PaperMC.

São dois trabalhos:

- **Labirinto** (`src/labirinto/`) — BFS, DFS e A\* no mapa `world_labirinto`.
  Experimento anterior, concluído.
- **Parkour** (`src/parkour/`) — agente de Aprendizado por Reforço no mapa
  `world_parkour`. É o trabalho atual, guiado pelo PDF
  `output/pdf/proposta_algoritmos_e_divisao_parkour.pdf`.

## A decisão que organiza o projeto de parkour

**O treino acontece fora do Minecraft. O jogo é o instrumento de validação.**

O servidor roda a 20 ticks por segundo e não há forma suportada de acelerar
isso: são cerca de 5 decisões por segundo. O simulador em Python puro faz
~2.500 por segundo num núcleo, e ~20.000 com 8 processos. O treino do primeiro
trecho leva **17 segundos** em vez de mais de duas horas.

Isso tem um preço, e ele é tratado de frente: uma política treinada num
simulador errado aprende a explorar os erros do simulador. Por isso a medição
sim-para-real é entrega, não detalhe — ver [docs/sim_para_real.md](docs/sim_para_real.md).

Duas consequências práticas:

- **Quase tudo roda sem instalar nada e sem o servidor ligado.** Só
  `src/parkour/main.py` precisa de Node.js e do PaperMC. Isso permite os cinco
  integrantes trabalharem em paralelo, num repositório onde só uma pessoa pode
  ligar o servidor por vez.
- Os 7 estágios do mapa viram 7 conjuntos de teste. Treinar num e avaliar nos
  outros é a pergunta da pág. 6 do PDF.

---

## Começando sem o servidor (o caminho normal)

Não precisa de Java, Node.js nem `pip install`.

```bash
# 1. Conferir que a física e o ambiente estão sãos (86 verificações, segundos)
python -m testes.teste_fisica
python -m testes.teste_ambiente

# 2. A referência: política aleatória
python -m src.parkour.experimento --agente aleatorio --sementes 0 1 2 3 4

# 3. O agente que aprende
python -m src.parkour.experimento --agente q --episodios 4000 --sementes 0 1 2 3 4

# 4. A comparação
python -m src.parkour.metricas
```

Para os gráficos, instale o matplotlib e rode `python -m src.parkour.metricas --graficos`.

### Outros comandos úteis

```bash
# Reler a geometria do mapa a partir dos arquivos do servidor
python -m tools.mapear_mundo --perfil

# Generalização: treinar num trecho, avaliar nos outros
python -m src.parkour.experimento --agente q --episodios 4000 \
    --avaliar-em B sand mud pale_garden nether end

# Treinar numa distribuição de corredores gerados
python -m src.parkour.experimento --agente q --gerados 40 --episodios 8000

# Varredura de hiperparâmetros, um processo por núcleo
python -m src.parkour.vetorizado --taxas 0.1 0.2 0.4 --decaimentos 0.999 0.9995

# DQN (precisa de torch)
python -m src.parkour.experimento --agente dqn --episodios 4000
```

### Escolher entre os dois mundos

Os parâmetros de IA continuam em `config/parkour.json`; mundo, geometria e
trechos podem ser escolhidos por cenário:

```bash
# Mapa grande original, que avança em +Z
python -m src.parkour.experimento --cenario parkour_oficial --agente q

# Treinos simples dentro de world_labirinto; o primeiro avança em -X
python -m src.parkour.experimento --cenario labirinto_parkours \
    --trecho frente_1 --agente q
```

O percurso `frente_1` começa em `(87, 125, 74)`, termina em
`(34, 125, 74)` e é transformado internamente para “lateral × progresso”.
Q-Learning e DQN não precisam conhecer o eixo real. A implementação e o modo
de usar o segundo treino, `frente_2`, estão em
[docs/cenarios_e_coordenadas.md](docs/cenarios_e_coordenadas.md).

## O mapa, como ele é de verdade

Tudo abaixo foi extraído dos arquivos `.mca` por `tools/mapear_mundo.py`, não
estimado no olho.

| | |
|---|---|
| Formato | ponte suspensa de 3 blocos de largura, x ∈ {999, 1000, 1001} |
| Piso | y=100; o bot anda em y=101 |
| Fora das 3 pistas | vazio — sair de lado é falha detectável |
| Percurso | linear em +Z, de z=996 a z=1391 |
| Estágios | 7: Bamboo, Sand, Mud, Copper, Pale Garden, Nether, End |

Os obstáculos formam um slalom: cada z bloqueia parte da largura, alternando
os lados. **A posição em x é contínua e isso importa** — a haste de bambu
ocupa só 3/16 do meio da célula, e o vão de 0,81 entre duas hastes deixa o
jogador (0,6 de largura) passar. Modelar bambu como bloco cheio tornaria o
estágio Bamboo intransponível.

Os trechos de treino em `config/parkour.json` foram derivados pela ferramenta,
que verifica não só se cada z tem passagem, mas se dá para ir de uma passagem
à seguinte. Por esse critério, **o estágio Copper não tem nenhum trecho
vencível andando**: em z=1217 a única passagem fica à esquerda e em z=1219 só
à direita, e o corpo do bot ocupa as duas células ao mesmo tempo na fronteira.
Aquele estágio exige pular, o que está fora do escopo atual.

## Estrutura

```text
config/
  parkour.json            # o que o grupo edita para fazer experimentos
  cenarios/               # escolha segura entre world_parkour e world_labirinto
  bot.json.exemplo        # modelo; o bot.json real fica fora do Git
  mapas/                  # geometria exportada do mundo
tools/
  nbt.py                  # leitor de .mca e NBT, só biblioteca padrão
  blocos.py               # caixas de colisão dos blocos
  mapear_mundo.py         # mundo -> JSON de geometria
  mapear_percurso.py      # corredor entre dois pontos, em X ou Z -> JSON local
  gerar_percurso.py       # corredores procedurais
src/parkour/
  fisica.py               # física do Minecraft em Python
  coordenadas.py          # mundo (X/Z) <-> lateral/progresso
  percurso.py             # geometria e análise de viabilidade
  geometria.py            # "o jogador cabe aqui?", definido uma vez só
  estado.py acoes.py recompensa.py
  ambiente_sim.py         # ambiente de treino (sem Minecraft)
  ambiente_mc.py          # ambiente de validação (no jogo)
  agentes/                # aleatorio, guloso, q_learning, dqn
  experimento.py metricas.py vetorizado.py calibracao.py
  main.py                 # o bot no jogo
testes/                   # rodam sem Minecraft, em segundos
docs/
  sim_para_real.md        # a calibração que sustenta o treino offline
  registro_experimentos.md# a tabela da pág. 4 do PDF
  dependencias.md         # por que estas bibliotecas e não as concorrentes
```

## Divisão entre os cinco integrantes (pág. 5 do PDF)

| # | Frente | Arquivos |
|---|---|---|
| 1 | Estado e percepção | `estado.py`, `percurso.py`, `tools/mapear_mundo.py` |
| 2 | Ações e recompensas | `acoes.py`, `recompensa.py`, `tools/gerar_percurso.py` |
| 3 | Fundamentos tabulares | `agentes/aleatorio.py`, `agentes/q_learning.py` |
| 4 | Fundamentos de redes | `agentes/dqn.py` |
| 5 | Método experimental | `experimento.py`, `metricas.py`, `docs/` |

`fisica.py` e a calibração são responsabilidade compartilhada de 1 e 5.

**Regra do grupo:** nenhum valor vira configuração oficial no
`config/parkour.json` sem uma linha em
[docs/registro_experimentos.md](docs/registro_experimentos.md), com hipótese e
evidência.

---

# Rodando dentro do Minecraft

Necessário só para validar: conferir a física contra o jogo e rodar a política
treinada. **Não é aqui que se treina.**

## Requisitos

- Minecraft Java Edition 1.21.11
- Java 21 para o PaperMC
- Node.js 22 ou mais recente para o Mineflayer
- Python 3.11 ou mais recente
- Pelo menos 2 GB de memória para o servidor

O pacote Python `javascript` instala a ponte para os módulos JavaScript
`mineflayer` e `vec3`. Na primeira execução isso demora e precisa de internet.
Se o Node.js não estiver instalado ou for anterior à versão 22, o bot falha
mesmo com a instalação do Python correta.

## 1. Preparar o Python

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 2. Escolher o mapa

Com o servidor **desligado**, edite apenas `level-name` em
`Servidor-BOT/server.properties`:

```properties
level-name=world_parkour     # ou world_labirinto
```

Não mova nem renomeie pastas: o PaperMC associa as dimensões auxiliares pelos
nomes `<level-name>_nether` e `<level-name>_the_end`. Nunca troque
`level-name` com o servidor rodando.

## 3. Iniciar o servidor

```bash
chmod +x Servidor-BOT/INICIAR_SERVIDOR.sh
./Servidor-BOT/INICIAR_SERVIDOR.sh
```

No Windows 11, `.\INICIAR_SERVIDOR.bat` no PowerShell, ou a tarefa do VS Code
`Iniciar servidor PaperMC` (`Ctrl+Shift+P` → `Tasks: Run Task`). Em qualquer
sistema com Java:

```bash
java -Xmx2G -Xms2G -jar paper-1.21.11-132.jar nogui
```

Espere a mensagem `Done`. Para encerrar, digite `stop` no console — fechar o
terminal à força pode corromper o mundo. Na primeira inicialização, mantenha
internet: o PaperMC baixa o arquivo original do Minecraft.

Já vêm habilitados: `allow-flight=true` (evita expulsões durante os saltos),
`enable-command-block=true` (checkpoints do mapa) e `level-name=world_parkour`.

### Conceder permissão de administrador

Na primeira vez que cada pessoa e o bot entram, rode no console do servidor,
**sem a barra**:

```text
op NOME_DO_JOGADOR
op NOME_DO_BOT
```

Sem isso o `/tp` do reset não funciona e nenhum episódio começa. O PaperMC
registra em `Servidor-BOT/ops.json`.

> O nome padrão do bot de parkour é `LucidioBot`. Confirme que
> `config/bot.json` usa esse nome e rode `op LucidioBot` no console do servidor.

## 4. Configurar o bot

```bash
cp config/bot.json.exemplo config/bot.json
```

Edite `host` (use `localhost` se o servidor está na mesma máquina, senão o IP
privado), `porta` (igual a `server-port`) e `usuario`. O `config/bot.json` está
no `.gitignore`, então cada integrante usa o próprio IP sem gerar conflito.

## 5. Rodar o bot

```bash
python -m src.parkour.main --cenario parkour_oficial

# ou, com world_labirinto selecionado no PaperMC
python -m src.parkour.main --cenario labirinto_parkours --trecho frente_1
```

Comandos no chat do Minecraft:

| Comando | O que faz |
|---|---|
| `parkour ajuda` | lista os comandos |
| `parkour info` | mostra o trecho carregado e a posição do bot |
| `parkour teste` | anda cinco blocos — confirma que a ponte funciona |
| `parkour reset` | teleporta para o início do trecho |
| `parkour marcar` | grava a posição do jogador, para ajustar o trecho sem o F3 |
| `parkour verificar` | compara uma amostra dos blocos reais com o JSON selecionado |
| `parkour calibrar` | grava a trajetória real para a calibração |
| `parkour guloso` | roda a política gulosa (não aprende, só confere) |
| `parkour rodar` | roda no jogo a política treinada offline |
| `parkour parar` | interrompe o que estiver rodando |

O primeiro teste presencial, e uma dúvida em aberto: **o bot atravessa o bloco
`bamboo`?** Um `parkour teste` perto de z=1011 ou z=1014 responde, e a
resposta muda a geometria exportada.

## Comandos do mapa de labirinto

Com `world_labirinto` selecionado e `python -m src.labirinto.main`:

| Mensagem | Comportamento |
|---|---|
| `teste andar` | testa o deslocamento até uma coordenada fixa |
| `labirinto BFS` | busca em largura |
| `labirinto DFS` | busca em profundidade |
| `labirinto A*` | busca A\* |
| `labirinto DJ` | opção reservada para Dijkstra (ver limitações) |
| `teleporte` | teleporta o bot até o jogador configurado no código |

Os algoritmos pintam de vermelho os blocos explorados e de verde o caminho
final, então o bot precisa de permissão para `/setblock` e `/tp`.

---

## Estado atual e limitações conhecidas

Parkour:

- O estágio Copper não tem trecho vencível andando; exige pulo, fora do escopo.
- Dripleaf, slime block e escada não são simulados. Os trechos param antes deles.
- O catálogo de ações não tem marcha à ré, então um beco sem saída é definitivo.
- A calibração sim-para-real ainda não foi feita: os números do simulador batem
  com a *documentação* do jogo, não com o jogo medido.

Labirinto (experimento anterior):

- `labirinto DJ` ainda direciona para DFS em `main.py`, e `dijkstra()` em
  `buscas_informadas.py` monta a tupla errada e chama `heapq.heapush`, que não
  existe.
- O código assume altura fixa e movimento nos eixos X e Z; não controla saltos.
- Coordenadas e alguns nomes de jogador estão fixos no código.

## Fluxo do grupo

1. `git pull` antes de começar.
2. Crie uma branch para sua tarefa.
3. Não execute dois servidores na porta `25565` ao mesmo tempo.
4. Encerre o PaperMC com `stop` antes de trocar de mapa ou copiar mundos.
5. Não envie `.venv`, `__pycache__` nem `Servidor-BOT/backups`.
6. Registre cada experimento em `docs/registro_experimentos.md`.

## Compartilhando o estado do servidor pelo GitHub

O repositório versiona o estado persistente do servidor: blocos, construções,
command blocks, baús, entidades, inventários, posições, avanços e estatísticas.
O `.gitignore` mantém fora só o que é regenerado — logs, caches, bibliotecas do
PaperMC e `session.lock`, que nunca deve ser compartilhado.

Os arquivos `.mca`, `level.dat` e `playerdata/*.dat` são binários e o Git não
consegue combinar duas versões. **Apenas uma pessoa pode executar ou editar o
servidor compartilhado por vez.**

1. Confirme com o grupo que ninguém está usando o servidor.
2. Com o PaperMC fechado: `git pull`.
3. Inicie, faça as alterações e encerre com `stop`. Espere o Java terminar.
4. `git add .` e `git status`; revise a lista.
5. `git commit -m "..."` e `git push` imediatamente.
6. Avise o grupo. A próxima pessoa recomeça pelo `git pull`.

Nunca faça `git pull`, troque de branch ou resolva conflitos com o PaperMC
aberto.

## Solução de problemas

### O bot não conecta

- Confirme que o PaperMC chegou à mensagem `Done`.
- Verifique `host` e `porta` em `config/bot.json`.
- Confira firewall e rede privada na porta `25565`.
- Se o servidor está em outro computador, `localhost` não funciona.

### O mapa errado foi carregado

- Pare com `stop`, confira `level-name` em `Servidor-BOT/server.properties`.
- Confirme que não foi criada uma pasta como `world_parkour/world_parkour/level.dat`.

### Windows: `Failed to extract jar files` ou `AccessDeniedException`

Normalmente o Java ou o OneDrive travou um arquivo do PaperMC.

1. Confirme que não há outro servidor Java aberto e feche o terminal antigo.
2. Pause a sincronização do OneDrive.
3. Exclua apenas `Servidor-BOT/cache/mojang_1.21.11.jar`.
4. Rode de novo com internet; o PaperMC baixa esse cache outra vez.

Não exclua nenhuma pasta que comece com `world_`. Se o bloqueio persistir,
clone em uma pasta local fora do OneDrive, como `C:\Projetos\AI-Algorithms-on-Minecraft`.

### Aviso sobre `online-mode=false`

O servidor está em modo offline para o ambiente privado original. Não exponha
essa porta à internet: qualquer pessoa pode escolher qualquer nome sem
autenticação. Use rede privada controlada, ou ative `online-mode=true` quando
todos tiverem contas autenticadas.
