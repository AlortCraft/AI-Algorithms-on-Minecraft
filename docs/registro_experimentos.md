# Registro de experimentos

Este arquivo é a tabela da pág. 4 do PDF, viva.

**Regra do grupo: nenhum valor vira configuração oficial no
`config/parkour.json` sem uma linha aqui, com hipótese e evidência.** E vale a
outra regra da pág. 4: muda-se **uma decisão por experimento**, com o resto
constante.

Preencham as colunas em português comum antes de virar código. Se não dá para
escrever a hipótese numa frase, ela ainda não está clara o bastante.

---

## Decisões já tomadas, com a evidência que as sustenta

| Decisão | Alternativas consideradas | Hipótese | Evidência observada |
|---|---|---|---|
| Treinar fora do Minecraft | treinar no servidor; vários bots; vários servidores | O servidor a 20 TPS dá ~5 decisões/s; sair dele daria ordens de grandeza a mais | Medido: 5/s no servidor, ~2.500/s no simulador (1 núcleo), ~20.000/s com 8 processos. O Trecho A treina em **17 s** em vez de mais de 2 h |
| Caixa de colisão do bambu = 3/16, não bloco cheio | tratar bambu como bloco cheio; como atravessável | Se o bambu ocupasse a célula toda, o estágio Bamboo não teria solução | Com bloco cheio, 4 posições ficam intransponíveis. Com 3/16, sobra vão de 0,81 e o jogador (0,6) passa. **Falta confirmar em jogo** |
| Ações: 6 macro-ações de 4 ticks | 1 tick por decisão; ações mais longas | 4 ticks (200 ms) reduzem o problema 4× e ainda dão controle suficiente | O Q-Learning chega a 100% no Trecho A com esse conjunto |
| Estado: faixas de 0,5 bloco, não 3 pistas | 3 pistas inteiras; 12 faixas | A posição em x é contínua; um vão de bambu não coincide com pista nenhuma | Com 3 pistas, os vãos de 0,81 entre hastes sumiriam do estado |
| Faixa livre por sobreposição, não pelo centro | exigir o centro da faixa dentro do vão | A janela útil de uma passagem (0,4) é menor que a faixa (0,5) | Com o critério do centro, **até o ponto onde o bot nasce** aparecia como bloqueado |
| Obstáculo medido pela frente do corpo | medir pela célula onde o bot está | O obstáculo da célula atual já ficou para trás e não ajuda a decidir | Com a célula atual, o agente atravessava o slalom em linha reta até bater |
| Início sorteado dentro da faixa viável | início sempre no mesmo ponto | Ambiente e política determinísticos fazem 200 episódios de avaliação virarem 200 cópias | Sem variação, todas as taxas de generalização caíam em 0%, 33%, 67% ou 100% — o n real era 3, não 600 |
| Trechos derivados da ferramenta | escolher trechos no olho | Uma lista de trechos escrita à mão envelhece mal | `tools/mapear_mundo.py` deriva os trechos e detectou que **o estágio Copper não tem trecho andável nenhum** |

---

## Experimentos realizados

### 1. Aleatório × Guloso × Q-Learning no Trecho A

Constante: trecho A, mesmo estado, mesma recompensa, mesmo limite de passos,
5 sementes, avaliação com exploração zero. Só o agente muda.

```bash
python -m src.parkour.experimento --agente aleatorio --sementes 0 1 2 3 4
python -m src.parkour.experimento --agente guloso    --sementes 0 1 2 3 4
python -m src.parkour.experimento --agente q --episodios 4000 --sementes 0 1 2 3 4
python -m src.parkour.metricas --graficos
```

Resultado da rodada de referência (avaliação, exploração zero, ± é a variação
entre as 5 sementes), já com o `exploracao_decaimento` corrigido pelo
experimento 2:

| Agente | Conclusão | Recompensa | Quedas | Passos |
|---|---|---|---|---|
| aleatório | 23,7% ± 3,8% | 7,77 | 76,2% | 34,3 |
| **Q-Learning** | **100,0% ± 0,0%** | 36,57 | 0,0% | 19,7 |
| guloso (regra à mão) | 100,0% ± 0,0% | 36,37 | 0,0% | 20,4 |

Veredito automático: o Q-Learning **supera** o aleatório por margem muito maior
que a variação entre sementes (+76,3% contra ±3,8%). Empata com o guloso em
taxa de conclusão e o vence por pouco em recompensa e em número de passos
(19,7 contra 20,4) — ou seja, achou um caminho ligeiramente mais curto do que a
regra escrita à mão.

**Um achado de método que vale mais que o número:** com o ponto de partida
fixo, uma versão anterior deste mesmo agente marcava 100% enganosamente.
Sortear o início dentro da faixa viável derrubou para 86,8% ± 22,3% e revelou
que metade das sementes divergia. Só depois de corrigir o hiperparâmetro
(experimento 2) o 100% voltou — desta vez de verdade, com variação zero. Sem
`variar_inicio`, o problema teria passado despercebido.

Note também que a conclusão no **treino** é 72,8%, bem abaixo dos 100% da
avaliação. Não é contradição: durante o treino o agente ainda explora e a
física tem ruído. É por isso que a pág. 6 do PDF manda avaliar em episódios
separados, com exploração zero.

### 2. Varredura de hiperparâmetros

```bash
python -m src.parkour.vetorizado --taxas 0.1 0.2 0.4 \
    --decaimentos 0.999 0.9995 --sementes 0 1 2 3 4
```

30 treinos, um processo por núcleo. A coluna `var` é a diferença entre a
melhor e a pior semente — é ela que separa "aprendeu" de "deu sorte".

| taxa | decaimento | conclusão | var entre sementes |
|---|---|---|---|
| 0,20 | **0,9995** | **100,0%** | **0,0%** |
| 0,40 | 0,9990 | 100,0% | 0,0% |
| 0,10 | 0,9990 | 92,6% | 37,0% |
| 0,20 | 0,9990 ← era o padrão | 86,8% | 51,5% |
| 0,40 | 0,9995 | 84,2% | 56,5% |
| 0,10 | 0,9995 | 81,6% | 92,0% |

**Achado que importa:** o padrão que estava no config (`taxa=0.20`,
`decaimento=0.999`) dava 86,8% com metade das sementes divergindo. Duas outras
combinações dão 100% com variação zero. A média sozinha esconderia isso — quem
denuncia é a coluna de variação.

**Lição de método:** uma varredura anterior com 3 sementes deu um ranking
diferente e chegou a mostrar essa mesma combinação com 66,7%. Três sementes
não bastaram para ordenar as combinações; cinco já separam.

**Decisão tomada:** `exploracao_decaimento` de `0.999` para `0.9995`, mantendo
`taxa_aprendizado` em `0.20`. Uma variável só muda, conforme a regra da pág. 4.
Hipótese: decair a exploração mais devagar dá tempo de visitar os estados
raros do fim do trecho antes de a política congelar. Evidência: 100% ± 0% em 5
sementes, contra 86,8% ± 51,5%.

### 3. Generalização: treinado no Trecho A, avaliado nos outros

```bash
python -m src.parkour.experimento --agente q --episodios 4000 \
    --avaliar-em B sand sand2 mud pale_garden pale_garden2 nether end end2
```

Responde diretamente à pág. 6 do PDF ("desempenho no trecho treinado e em um
trecho diferente"). 5 sementes, exploração zero, sem retreinar.

| Trecho | Conclusão | Quedas |
|---|---|---|
| **A (treinado)** | **100,0% ± 0,0%** | 0,0% |
| pale_garden2 | 79,2% ± 7,3% | 20,3% |
| nether | 72,1% ± 6,5% | 27,9% |
| pale_garden | 58,7% ± 8,2% | 37,8% |
| end | 56,5% ± 12,5% | 43,5% |
| end2 | 16,9% ± 2,4% | 82,8% |
| sand | 8,8% ± 11,4% | 72,6% |
| mud | 7,8% ± 2,9% | 59,8% |
| sand2 | 6,2% ± 2,9% | 51,2% |
| B | 3,1% ± 1,4% | 76,0% |

**Conclusão: o agente decorou o Trecho A.** Cinco dos nove trechos ficam abaixo
do que a política *aleatória* faz no Trecho A (23,7%), e neles o bot cai da
ponte na maioria dos episódios. A queda de 100% para menos de 10% em `mud`,
`sand2` e `B` é a resposta direta à pergunta da pág. 6.

Onde o desempenho se sustenta (`pale_garden2`, `nether`), vale desconfiar: são
justamente os trechos mais curtos (9 e 8 blocos). Os trechos não têm a mesma
dificuldade, então comparar números **entre** trechos exige cuidado. O que a
tabela mostra com segurança é a queda em relação ao trecho treinado.

### 4. Treinar numa distribuição de corredores gerados

```bash
python -m src.parkour.experimento --agente q --gerados 40 --episodios 8000 \
    --avaliar-em A B sand sand2 mud pale_garden pale_garden2 nether end end2
```

Hipótese: treinar em muitos corredores diferentes produz uma política que
atravessa corredores, em vez de uma que decorou um. Custo esperado: pior no
Trecho A específico, melhor nos demais.

Este experimento **só é possível porque o treino é offline**. No servidor
real, cada corredor novo exigiria construir o mapa à mão.

A fase `avaliacao` roda em corredores da mesma família que o agente nunca viu
(sementes a partir de 10000). Avaliar nos mesmos corredores do treino mediria
memorização — exatamente o que o experimento quer evitar.

**Em corredores gerados nunca vistos: 75,7% ± 9,2%.** O agente aprendeu a
atravessar corredores da família, e não a decorar um.

Comparação com o agente treinado só no Trecho A (5 sementes cada):

| Trecho | Treinado no A | Treinado em 40 gerados | |
|---|---|---|---|
| **A** | 100,0% ± 0,0% | **16,9% ± 13,7%** | piora, maior que o ruído |
| B | 3,1% ± 1,4% | 4,7% ± 6,5% | igual |
| sand | 8,8% ± 11,4% | 20,0% ± 27,6% | dentro do ruído |
| sand2 | 6,2% ± 2,9% | 13,9% ± 12,7% | dentro do ruído |
| mud | 7,8% ± 2,9% | 59,1% ± 54,0% | dentro do ruído |
| pale_garden | 58,7% ± 8,2% | 70,9% ± 34,2% | dentro do ruído |
| pale_garden2 | 79,2% ± 7,3% | 80,6% ± 25,7% | igual |
| nether | 72,1% ± 6,5% | 57,0% ± 43,0% | dentro do ruído |
| **end** | 56,5% ± 12,5% | **100,0% ± 0,0%** | melhora maior que o ruído |
| **end2** | 16,9% ± 2,4% | **92,0% ± 17,9%** | melhora maior que o ruído |

**Conclusão: a hipótese se confirmou, com o custo previsto.** Treinar numa
distribuição troca desempenho no trecho específico (100% → 16,9% no A) por
desempenho em trechos que o agente nunca viu.

**Cuidado ao ler a tabela.** Só três linhas passam do critério de "diferença
maior que a variação entre sementes": as melhoras em `end` e `end2`, e a piora
no `A`. As outras seis são tendência, não conclusão. Os desvios do agente
treinado em gerados são enormes (±54% no `mud`, ±43% no `nether`) — sinal de
que 5 sementes ainda são poucas, ou de que 8000 episódios não bastam para 40
corredores.

**O resultado sólido do experimento é outro: 75,7% ± 9,2% em corredores
gerados nunca vistos.** Ali o desvio é pequeno e a amostra é grande, porque
avaliação e treino vêm da mesma distribuição. É a evidência mais limpa de que
o agente aprendeu a atravessar corredores em vez de decorar um.

*Observação:* este experimento usou os hiperparâmetros antigos. Vale repetir
com `exploracao_decaimento=0.9995`, que estabilizou o experimento 1 — parte
dos desvios enormes pode ser o mesmo problema.

Próximo passo natural: mais sementes e mais episódios, para tirar do ruído as
seis melhoras que hoje são só tendência.

---

### 5. Do simulador para o jogo: quanto se perde

**Pergunta:** a política treinada offline funciona dentro do Minecraft?

**Montagem:** servidor PaperMC 1.21.11 local, mineflayer 4.37.1, mundo
`world_parkour`, Trecho A, bot com `op`. Comandos `parkour guloso` e
`parkour rodar`.

| Agente | No simulador | No jogo |
|---|---|---|
| guloso (regra à mão) | 100,0% ± 0,0% | **travado, 28% de progresso, 13 passos** |
| Q-Learning treinado | 100,0% ± 0,0% | **travado, 28% de progresso, 15 passos** |

**Resposta: não transfere.** Os dois agentes que resolvem o trecho sempre no
simulador param no mesmo lugar no jogo — 28% de 17 blocos dá z≈1003,8, que é
exatamente o pilar de `moss_block` + `flowering_azalea` de z=1004.

**Por que.** No simulador, encostar num obstáculo custa um tick e o agente
desliza para o lado no passo seguinte. No jogo, prensar-se contra o pilar põe
o bot num estado em que o pulo deixa de funcionar e ele não sai mais dali —
medido e reproduzido, ver `docs/sim_para_real.md`. A política nunca aprendeu a
evitar esse estado porque ele não existe no simulador.

**Isto não é uma falha do Q-Learning.** O guloso, que é uma regra escrita à
mão e lê a geometria diretamente, falha do mesmo jeito e no mesmo ponto. O que
falhou foi o modelo do mundo, não o algoritmo — e é por isso que a pág. 6 do
PDF manda validar no jogo em vez de confiar no número do simulador.

**O que fazer com isso.** Duas frentes, nesta ordem:

1. modelar no simulador o custo de encostar num obstáculo (hoje é quase zero,
   no jogo é fatal), para a política aprender a manter distância;
2. corrigir a retenção do impulso de pulo-com-corrida na física, medida e
   documentada em `sim_para_real.md`.

A segunda muda a física e invalida todas as tabelas Q e todos os números
acima. Refazer custa uns 15 minutos de CPU. **Nada foi alterado ainda.**

---

### 6. Abrir o projeto para o mapa inteiro (em andamento)

**Motivo.** Ao inspecionar o mapa em jogo, descobrimos que os `trechos` do
config saíram do campo `andaveis` do `mapear_mundo.py`, definido como *"o
trecho que dá para vencer sem escalar"*. Batem um a um. **O projeto vinha
treinando exatamente nos pedaços do mapa que evitam a mecânica central dele.**

Todo estágio tem posições sem passagem na altura do piso — 8 dos 67 z do
Bamboo, 15 dos 58 do Pale Garden — e as sete placas de ouro que marcam o
início de cada estágio ficam todas em pórticos elevados.

**O que mudou.**

- `geometria.superficies()`: nova primitiva que responde "que alturas existem
  neste z". Antes tudo era relativo a um `y_pe` único;
- `Percurso._calcular_viaveis()`: busca sobre `(z, altura, faixa)` com andar,
  degrau e salto, mais fecho lateral dentro do mesmo z;
- catálogo de ações de 6 para 10: entram `esquerda_pulo`, `direita_pulo`
  (nenhuma ação pulava e ia para o lado — apoio na diagonal era inalcançável)
  e `lado_esquerdo`, `lado_direito` (toda esquiva empurrava para frente,
  contra a quina do obstáculo);
- agente guloso virou planejador: segue o mesmo grafo, salta vãos, sobe em
  apoio ao lado e entende o "bolso" lateral onde está.

**Onde chegou:** estágios inteiros com solução provada foram de **0 de 7 para
4 de 7** (Sand, Mud, Copper, Nether). O Copper não tinha nenhum trecho andável
e estava fora do config com uma nota dizendo que exigia pular por cima.

**A checagem de corredor, e o que ela revelou.** A análise passou a conferir
o que existe *entre* a decolagem e a aterrissagem de um salto longo
(`Percurso.corredor_do_salto`). A pergunta certa é **"existe algum x por onde
saltar?"** e não "a faixa inteira está limpa?": a primeira versão usava a faixa
toda, qualquer haste de bambu na célula do meio reprovava o salto, e nenhum
estágio sobrava.

Com ela, dois fatos apareceram:

1. **`pale_garden2` nunca teve solução.** A análise antiga mandava saltar de
   z=1262 para 1264 por cima de um muro em 1263. O trecho **saiu do config**, e
   os números dele no experimento 3 (78,2% e 80,6%) são de um trecho
   impossível, medidos com física que deixava atravessar. O agente guloso, que
   ficava pulando contra a parede até truncar, estava certo o tempo todo.
2. **Nenhum dos 7 estágios inteiros é comprovadamente vencível** com o modelo
   atual — a contagem "4 de 7" de antes vinha de saltos por cima de paredes.
   Todo estágio tem pelo menos uma subida de 2 blocos, e 2 blocos é mais que
   qualquer pulo do Minecraft: em Sand, z=1105 está em y=101 e z=1106 é parede
   sólida nas três pistas com topo em y=103.

**Isso não quer dizer que o mapa seja impossível** — ele é jogado por pessoas.
Quer dizer que falta mecânica no simulador. Os candidatos são justamente os que
o grupo apontou olhando o mapa em jogo: bloco de slime (9 no mapa, quicam e
preservam o momento do salto), escada (12, escaláveis) e os pórticos com
estrutura intermediária que servem de degrau. Nenhum está modelado.

**Estado atual: 41 testes, todos passando, com 9 trechos.**

**Os números dos experimentos 1 a 5 não valem mais.** Mudou o espaço de ações
(6 → 10), a análise de viabilidade e o sorteio de nascimento. As tabelas Q
salvas estão obsoletas. Eles passam a descrever *a versão plana do problema*,
que continua sendo um resultado válido desde que rotulado assim.

**Falta fazer:** altura no estado e na recompensa (hoje o estado é faixa
lateral × distância × máscara × no_chão, sem nenhuma informação vertical, e a
recompensa é só `z_depois - z_antes`); cactos, fogo e slime no simulador (55,
21 e 9 no mapa, todos ignorados hoje); e o retreino.

---

### 7. Ensinar a escalar: mudar a tarefa ou a recompensa?

**Pergunta.** Observando o bot em jogo, o grupo notou que ele vence os
obstáculos **desviando por baixo**, e nunca subindo neles. Medimos: na política
treinada no Trecho A, ele passa **88,1% do tempo no piso**. A proposta natural
foi punir estar na altura inicial.

**Por que não punimos.** Três razões: o piso é parte legítima da rota (no mapa
inteiro se sobe e se desce o tempo todo); premiar altura convida ao *reward
hacking*, já que com `por_passo = -0,02` subir num bloco e ficar parado pode
valer mais que avançar; e, principalmente, **se o trecho pode ser vencido
desviando, desviar é uma solução correta**. O agente não estava errado — a
tarefa é que não exigia escalada.

E a raiz é conhecida: os trechos vieram do campo `andaveis` do mapeador, ou
seja, exatamente os pedaços vencíveis sem escalar. Medimos que o Trecho A tem
passagem no piso em **18 dos 18 z**.

**O que fizemos.** Procuramos no mapa segmentos que tenham solução *e* exijam
escalada: existem **98**, um em cada estágio. Adicionamos dois ao config,
`bamboo_escalada` (z 1026-1036) e `end_escalada` (z 1380-1390), com 5 posições
cada onde não há passagem nenhuma na altura do piso. **A recompensa não mudou.**

**Resultado, 3 sementes, 8000 episódios:**

| | conclusão | tempo acima da partida | ações dominantes |
|---|---|---|---|
| Trecho A (plano) | 100,0% | 11,9% | correr 53%, esquerda 18%, correr_pulo 10% |
| **bamboo_escalada** | **98,7%** | **40,3%** | **correr_pulo 40%**, andar 27%, **direita_pulo 8%** |

O `correr_pulo` quadruplicou e o `direita_pulo` — subir num apoio ao lado —
saiu do zero. **A escalada foi aprendida como meio para avançar em z**, sem
nenhum prêmio por altura.

**Achado extra:** neste trecho o Q-Learning (98,7%) supera com folga o agente
guloso (28%), que é escrito à mão e lê a geometria. É o primeiro trecho em que
o aprendizado passa do "teto de referência" — a heurística é míope e a política
aprendida não é.

**Lição de método.** Quando o agente faz algo que parece errado, a primeira
pergunta é se a tarefa mede o que queremos, e não se a recompensa precisa de
mais um termo. Aqui a tarefa estava medindo "chegue ao fim", o desvio cumpria
isso, e nenhum ajuste de recompensa teria sido honesto.

---

## Experimentos previstos, ainda não feitos

| # | Experimento | O que responde | Comando |
|---|---|---|---|
| 5 | Estado `mascara` × `vao` | A informação mastigada acelera o aprendizado? Quanto da decisão já vem pronta? | mudar `estado.modo` no config |
| 6 | Q-Learning × DQN | A discretização perde informação que importa? | `--agente dqn` (precisa de torch) |
| 7 | Pesos de recompensa | O bot acumula recompensa sem progredir? | mudar um peso por vez em `recompensa` |
| 8 | Calibração sim-para-real | Qual o erro do simulador em relação ao jogo? | `parkour calibrar` + `python -m src.parkour.calibracao` |
| 9 | Política offline no jogo | Quanto se perde ao sair do simulador? | `parkour rodar` |
| 10 | Nosso DQN × stable-baselines3 | Nossa implementação está correta? | etapa 5 |

---

## Modelo de linha para novos experimentos

```
### N. <título>

Data:
Quem:
Pergunta:
O que mudou (uma coisa só):
O que ficou constante:
Comando:
Resultado (média ± variação entre sementes):
Conclusão:
O que isso muda no config (se muda):
```
