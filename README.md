# IA no Minecraft: labirinto e Q-Learning de parkour

O repositório contém dois trabalhos independentes:

- `src/labirinto/`: BFS, DFS e A*; preservado sem alterações nesta simplificação;
- `src/parkour/`: somente Q-Learning tabular, treinado dentro do Minecraft.

Não existe mais simulador de parkour nem treinamento híbrido. Cada ação,
posição, queda e chegada usada pelo aprendizado vem do jogo aberto.

## Preparar

É necessário ter Python e Node.js instalados. Na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
npm install
```

Depois:

1. copie `config/bot.json.exemplo` para `config/bot.json`;
2. ajuste endereço, porta, nome e quantidade de bots;
3. selecione o mundo em `Servidor-BOT/server.properties`;
4. inicie o servidor e conceda OP ao bot, pois o reset usa `/tp`;
5. dê OP somente ao primeiro bot configurado;
6. conecte o programa (o exemplo inicia quatro bots):

```powershell
python -m src.parkour.main --cenario labirinto_parkours --trecho frente_1 --bots 4
```

## Treinar e testar no jogo

Use o chat do Minecraft:

```text
parkour info
parkour reset
parkour treinar 100
parkour rodar
parkour avaliar 30
parkour parar
```

`parkour treinar 100` cria uma tabela nova se ainda não existir ou continua a
tabela já salva. O número representa rodadas por bot: com quatro bots, são 400
episódios no total, executados em paralelo. Eles atualizam uma única tabela Q
protegida contra acessos simultâneos. A tabela e o histórico CSV são salvos após
cada episódio em `resultados/modelos/`.

O primeiro bot é o controlador. Ele cria a equipe `bots_parkour`, configura
`collisionRule never`, desliga dano por aglomeração e teleporta os demais. Por
isso somente sua conta precisa de OP. Essa regra remove empurrões por jogadores
e entidades, mas os bots continuam interagindo com blocos e mecanismos.

Para executar servidor e bots no mesmo PC, use `"host": "localhost"`. O número
do arquivo `config/bot.json` pode ser substituído temporariamente por `--bots`.
O perfil local do servidor reserva 6 GB ao Paper, reduz chunks e entidades
distantes, desliga a compressão de pacotes em localhost e elimina nascimento
natural de mobs. Comece com 40 bots e compare 30, 40 e 50 usando a quantidade
de episódios por minuto mostrada ao final do treino. Mais bots só valem a pena
enquanto aumentarem essa taxa e o MSPT permanecer abaixo de 50.

`parkour rodar` desliga temporariamente a exploração e executa uma tentativa
sem aprendizado. Essa é a forma mais simples de testar a política aprendida.

`parkour avaliar 30` distribui exatamente 30 tentativas entre os bots
conectados, também com exploração zero e sem aprendizado. Cada resultado é
salvo no mesmo histórico CSV com a fase `avaliacao`; ao final, o chat informa
a taxa de chegada, a média de passos e o ritmo de episódios por minuto.

O histórico CSV registra progresso horizontal, progresso validado por pouso,
altura final, ponto válido mais distante e quantas vezes cada ação foi usada.
A chegada só é aceita quando o bot cruza a meta e pousa; atravessar a linha em
queda não conta como sucesso. Nos trechos retos, entrar no volume entre
`(32, 124, 54)` e `(36, 127, 77)` encerra o episódio, mesmo que o bot ainda
esteja no ar. A posição é verificada a cada tick para que ele não atravesse a
plataforma antes de o episódio terminar.

Comece pelo cenário `labirinto_parkours`, trecho `frente_1`, com vãos de um
bloco. Depois use `frente_2`, com vãos de dois blocos, e `frente_3`, com
distâncias e alturas variadas, incluindo uma queda que causa dano. Os três
limitam o bot a quatro ações: andar, correr, correr pulando e andar pulando. O
mapa oficial possui também ações laterais e exige mais experiências reais. A
vida e a fome são restauradas no reset quando necessário, portanto a queda
obrigatória da `frente_3` não se acumula entre episódios.
A ordem atual é a versão 2 do catálogo, o estado de piso é versão 2 e a
recompensa é versão 2. Os modelos usam o sufixo
`_acoes_v2_estado_v2_recompensa_v2.json` e começam do zero. A recompensa das
três frentes só reconhece novo progresso depois de um pouso em apoio mapeado;
correr por baixo da pista não ensina uma política falsa. Os resultados antigos
permanecem no disco, mas não são carregados nem sobrescritos automaticamente.

## Parâmetros

Edite `config/parkour.json` com o servidor parado:

- `taxa_aprendizado`: quanto uma experiência nova altera a tabela;
- `desconto`: importância de recompensas futuras;
- `exploracao_inicial`, `exploracao_final` e `exploracao_decaimento` (o valor
  online padrão é `0.9995`, pensado para milhares de episódios);
- `exploracao_ao_expandir_acoes`: exploração restaurada ao liberar uma ação
  nova em um modelo compatível;
- pesos de progresso, queda, travamento e meta;
- ticks por ação e limite de passos do episódio;
- forma de transformar a situação em um estado discreto.

Altere um parâmetro por vez, treine tabelas separadas com `--modelo` e compare
várias execuções de `parkour rodar`, não apenas uma. Consulte
`docs/GUIA_Q_LEARNING.md` e `docs/PARTES_PARA_IMPLEMENTAR.md`.

## Estrutura mantida do parkour

```text
src/parkour/
  main.py           grupo de bots, conexão e comandos do Minecraft
  ambiente_mc.py    reset, ações e observações reais
  q_learning.py     algoritmo e tabela Q
  treinar.py        laço de episódios e histórico CSV
  estado.py         situação do jogo para índice da tabela
  acoes.py          controles disponíveis
  recompensa.py     sinal de aprendizado
  percurso.py       geometria estática exportada do percurso
  geometria.py      consulta dos blocos exportados
  coordenadas.py    direção local em relação à meta
  config.py         leitura das configurações
```

Os arquivos `tools/mapear_*.py` foram mantidos porque regeneram os mapas
estáticos quando o mundo ou o percurso muda.

## Labirinto

O projeto de labirinto, seus mapas e os mundos do servidor foram preservados.
Com `world_labirinto` carregado:

```powershell
python -m src.labirinto.main
```
