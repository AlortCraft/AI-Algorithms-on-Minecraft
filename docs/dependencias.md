# Por que estas dependências, e não as concorrentes

A pág. 4 do PDF pede que decisões sejam justificadas, não escolhidas por
hábito. Isto vale também para as bibliotecas.

## O núcleo não depende de nada

Simulador, ambiente, Q-Learning tabular, testes e a tabela de métricas rodam
com Python puro. Isso não é purismo: é o que permite os cinco integrantes
trabalharem em paralelo, num projeto onde só uma pessoa pode ligar o servidor
por vez (os mundos são binários e não têm merge — ver README).

```bash
python -m testes.teste_fisica
python -m testes.teste_ambiente
python -m src.parkour.experimento --agente q --episodios 4000
python -m src.parkour.metricas
```

A tabela Q do Trecho A tem 3840 estados por 6 ações, uns 23 mil números. Uma
lista de listas dá conta. Numpy só passa a compensar no DQN.

## matplotlib

Serve para as curvas de aprendizado e comparações que a pág. 6 do PDF exige.

| Alternativa | Por que não |
|---|---|
| plotly | Gera HTML interativo, mais pesado, precisa de navegador, e exportar PNG para o relatório ainda exige o `kaleido`. |
| seaborn | É uma camada **sobre** o matplotlib. Dependência a mais por ganho só estético. |
| bokeh | Mesmo problema do plotly, com comunidade menor. |

matplotlib é o padrão em trabalho acadêmico, funciona offline e exporta PNG
direto. `src/parkour/metricas.py` funciona sem ele: só os gráficos ficam de
fora, a tabela sai igual.

## pandas

Agregação dos CSVs (média por semente, comparação entre agentes e trechos).
É genuinamente opcional — `metricas.py` usa só `csv` da biblioteca padrão.
Vale ter para análises próprias: um `groupby` de uma linha substitui vinte
linhas de laço propenso a erro.

## torch, e por que não TensorFlow/Keras, JAX ou stable-baselines3

Necessário só para `src/parkour/agentes/dqn.py`, a etapa 4.

**vs TensorFlow/Keras.** Keras é construído em volta de `model.fit()` sobre um
dataset fixo. RL não tem dataset fixo: o gradiente é aplicado a cada passo,
sobre um lote amostrado de uma memória que muda a cada transição. Em Keras
isso obriga a descer para `GradientTape`, que fica *mais* verboso que o
equivalente em torch — e perde justamente a abstração que seria a vantagem do
Keras. Instalação mais pesada, e o suporte a GPU no Windows foi descontinuado
nas versões recentes.

**vs JAX.** Desempenho excelente, mas o paradigma é funcional puro: estado
imutável, `jit`, `grad`, `vmap`. É um segundo assunto difícil empilhado sobre
RL, para um grupo de iniciantes. O suporte a Windows é o mais fraco dos três.

**vs stable-baselines3 como implementação principal.** Resolveria o DQN em dez
linhas — e é exatamente por isso que não serve aqui. A pág. 3 do PDF pergunta
*"o que o grupo espera aprender com cada algoritmo, além de apenas fazê-lo
rodar?"*. Usar uma implementação pronta como resposta principal esvazia o
trabalho.

**A favor do torch.** Grafo dinâmico: o laço de treino é Python comum, dá para
colocar `print` e depurar linha a linha. É o padrão de fato em RL, então todo
tutorial e resposta de fórum que o grupo encontrar já vem em torch. Instala
sem compilar.

**Instale a versão de CPU:**

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Uns 200 MB em vez de ~2,5 GB. GPU não traria ganho nenhum: a rede tem 11
entradas e duas camadas de 64, e o gargalo é o simulador, não a rede.

## gymnasium e stable-baselines3 — na etapa 5, como comparação

O ambiente segue a assinatura do Gymnasium (`reset`/`step` devolvendo
`obs, reward, terminated, truncated, info`) **sem depender do pacote**.

Com o servidor real, esses pacotes não teriam serventia: o ambiente não era
vetorizável nem resetável mais rápido que o tempo real. O simulador inverte
isso — o ambiente passa a ser resetável instantaneamente e roda milhares de
passos por segundo, que é o caso de uso deles.

Recomendação: escrever o ambiente e os agentes à mão (é o aprendizado), e
plugar SB3 no fim como **referência de comparação** — para checar se o nosso
DQN está no mesmo patamar de uma implementação madura, e para obter o PPO que
a pág. 3 cita sem gastar semanas. Comparar-se com uma referência é método, não
atalho.

## Node.js e Java

Necessários **só para a validação dentro do jogo** (`src/parkour/main.py`),
nunca para o treino. Um integrante sem Java instalado consegue fazer todo o
resto do trabalho.

- Java 21 para o PaperMC.
- Node.js 22 ou mais novo para o mineflayer, que o pacote `javascript` usa.
