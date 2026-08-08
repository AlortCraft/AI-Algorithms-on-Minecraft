# Do simulador para o jogo

Todo o treino acontece fora do Minecraft. Este documento é o que impede isso
de virar autoengano.

## Por que treinar fora do jogo

O servidor roda a 20 ticks por segundo e não existe forma suportada de
acelerar isso. Com decisões a cada 4 ticks, dá **5 decisões por segundo**.

Medido nesta máquina (8 núcleos, Python puro, sem numpy):

| Configuração | Decisões por segundo |
|---|---|
| 1 bot no servidor real | ~5 |
| 8 bots num servidor (8 cópias do percurso) | ~40 |
| Simulador, 1 processo | ~2.500 |
| Simulador, 8 processos (`vetorizado.py`) | ~20.000 |

Mais servidores não ajudam: o teto de 20 TPS é por instância, e o limite vira
memória (~2 GB por servidor PaperMC). Paralelizar dentro do Minecraft rende
cerca de 8×; sair do Minecraft rende cerca de 4.000×.

O treino do Trecho A leva **17 segundos** no simulador. No servidor real, os
mesmos 4000 episódios levariam mais de duas horas.

## O risco, dito claramente

Uma política treinada num simulador errado aprende a explorar os erros do
simulador. O sintoma clássico é atingir 100% offline e falhar no jogo. Sem
medir a diferença, os resultados offline não valem nada.

## Procedimento de calibração

### 1. Gravar a trajetória real

Com o servidor no ar e o bot com `op`:

```
parkour calibrar
```

Roda uma sequência fixa de 38 ações — arrancada, cruzeiro, pulo parado, pulo
correndo, desvio para os dois lados e frenagem — e grava a posição a cada
tick em `resultados/metricas/trajetoria_real.json`.

A sequência está em `SEQUENCIA_PADRAO`, em `src/parkour/calibracao.py`. Não
mude sem regravar a trajetória: comparações entre sequências diferentes não
significam nada.

### 2. Comparar com o simulador

```bash
python -m src.parkour.calibracao --real resultados/metricas/trajetoria_real.json
```

### 3. Ler o resultado

**Critério de aceitação: pior erro da sequência abaixo de 0,2 bloco.**

> O critério anterior — "erro abaixo de 0,2 no tick 40" — estava errado e
> passou meses dando aprovação falsa. O tick 40 cai no meio da fase de
> caminhada, que é justamente a parte fácil: a calibração dava **APROVADO sem
> nunca ter comparado um salto**. O relatório agora quebra o erro por fase e
> julga pelo pior valor da sequência inteira. A coluna `cresceu` é a que
> importa: ela mostra em que fase o erro nasce.

O relatório separa o erro por eixo, e cada eixo aponta para uma causa:

| Sintoma | Causa provável | Onde mexer |
|---|---|---|
| Erro só em z, crescendo linear | velocidade errada | `aceleracao_chao`, `atrito_bloco` |
| Erro só em y durante o pulo | gravidade ou impulso | `velocidade_pulo`, `gravidade` |
| Erro em x com z certo | **eixos trocados** | a convenção de "frente" e "direita" |
| Erro que só aparece ao correr | multiplicador de corrida | `multiplicador_corrida`, `impulso_corrida_pulo` |
| Erro em degraus | altura do degrau | `degrau` |

As constantes ficam em `src/parkour/fisica.py`, na classe `Constantes`.

## Resultado da calibração em jogo (08/08/2026)

Rodada em servidor PaperMC 1.21.11 local, mineflayer 4.37.1, 5 sementes não se
aplicam aqui: a sequência é determinística.

| Fase | Ticks | Erro no fim | Cresceu |
|---|---|---|---|
| andar | 1–40 | 0,0749 | +0,0729 |
| correr | 41–80 | 0,0217 | −0,0581 |
| **correr_pulo** | 81–104 | **2,4460** | **+2,4185** |
| esquerda / direita | 105–136 | 2,31 | carrega o erro anterior |
| parar | 137–152 | 2,2830 | −0,0039 |

Erro final: 2,2830 bloco, sendo **dx −0,005, dy −0,0001, dz −2,2830**.

**O que bate, e bate muito bem:**

- caminhada e corrida em linha reta: erro de 0,07 e 0,02 bloco em 40 ticks;
- **o arco vertical do pulo é idêntico** — `y_real` e `y_sim` coincidem nas
  três casas decimais em todos os ticks dos dois saltos, incluindo o pico de
  1,252 e o ciclo de 12 ticks;
- velocidade de cruzeiro medida em jogo: **0,2159 bloco/tick** andando
  (documentado 0,21585) e 0,281 correndo (documentado 0,2806).

**O que não bate, e por quê:**

Todo o erro é horizontal e nasce no pulo com corrida. O mecanismo, medido tick
a tick:

| | tick do impulso | ticks seguintes, no ar |
|---|---|---|
| jogo | +0,481 | **0,286 constante**, sem decaimento |
| simulador | +0,356 | 0,350 → 0,345 → 0,340, decaindo |

**O simulador retém o impulso do pulo-com-corrida na velocidade; o jogo o
descarta depois de um tick** e volta à velocidade de cruzeiro do ar. O erro
entra a ~0,03 bloco/tick durante todo o voo.

Baixar `impulso_corrida_pulo` de 0,20 para 0,07 derruba o erro final de 2,28
para 0,07 bloco — mas **isso mascara o sintoma, não corrige o mecanismo**: o
pior erro no meio do salto continua em ~2,1, porque a forma da curva de
velocidade continua errada. A correção certa é aplicar o impulso ao
deslocamento de um tick sem somá-lo à velocidade persistente, em
`src/parkour/fisica.py`.

**Consequência que precisa de decisão:** mexer nessa constante muda a física e
invalida as tabelas Q já treinadas e todos os números do
`registro_experimentos.md`. Refazer custa uns 15 minutos de CPU. A constante
**não foi alterada** — a decisão é do grupo.

### Detalhe que decidiu o projeto: a largura do bambu

Modelamos a haste de bambu como caixa fina (~3/16 de bloco) no meio da célula,
e não como cubo inteiro.

**Conferido em jogo em 08/08/2026, e a justificativa antiga estava errada.** O
texto anterior dizia que a haste fina "é o que torna o estágio transponível".
Não é: com 3/16 centrados numa pista de 1 bloco sobram 0,406 de cada lado, e o
jogador tem 0,6 de largura — ele **não** passa. O bot confirmou, parando em
z=1010,856 diante do bambu de z=1011.

O que torna o estágio transponível é **trocar de pista**, não espremer-se pelo
bambu. O modelo acerta o comportamento (bloqueia nos dois casos), mas pelo
motivo errado — e um modelo certo por engano quebra na primeira vez que a
geometria mudar.

Também conferido em jogo: `big_dripleaf_stem`, `short_grass`, `tall_grass` e
`light_weighted_pressure_plate` não têm colisão, como o modelo assume.

## Armadilhas do lado do jogo (todas medidas, nenhuma suposta)

**A calibração não roda no percurso.** O maior trecho reto sem obstáculos do
mundo inteiro tem **3 blocos**; a sequência precisa de uns 40. Na primeira
tentativa o bot bateu no pilar de z=1004 no tick 24 e os 128 ticks seguintes
mediram colisão, não física. A pista lisa fica descrita em `config/parkour.json`,
em `calibracao.pista`, e é construída e apagada com dois `/fill` (os comandos
estão no próprio config). Ela fica a 100 blocos do percurso.

**O bot trava e para de pular.** Prensado contra um obstáculo, o `jump` deixa
de ter efeito: `onGround` oscila e depois fica `False`, e o bot não sai do
lugar nem soltando todos os controles. Teleportado para fora, volta a pular
normalmente (+1,252); teleportado de volta, trava de novo. É posicional, não é
estado corrompido no cliente. `AmbienteMinecraft` detecta pelo `passos_parado`
e encerra o episódio com motivo `travado`, em vez de gastar os 120 passos
parado e registrar `tempo`, que pareceria indecisão do agente.

**`bot.time.age` não serve de relógio por tick.** O servidor manda a hora do
mundo uma vez por segundo, então ela anda de 20 em 20. Quem conta os ticks da
gravação é o laço, com `waitForTicks`, que medimos em 50,4 ms por tick. A
gravação agora avisa se demorar mais que o esperado, porque um tick a mais na
contagem vira "erro de física" no relatório.

**O `@On` do JSPyBridge passa `this` como primeiro argumento.** Sem ele, o
handler estoura no primeiro evento e o bot cai do servidor antes de responder
qualquer coisa.

## Blocos cuja colisão ainda é palpite

`tools/mapear_mundo.py` lista isto ao rodar. No `world_parkour`:

| Bloco | Quantidade | O que confirmar |
|---|---|---|
| `bamboo` | 710 | haste fina de 3/16 — sustenta o estágio Bamboo inteiro |
| `cactus` | 55 | causa dano; o simulador só trata a colisão |
| `big_dripleaf` | 8 + 22 caules | a folha inclina e derruba; não modelado |
| `ladder` | 12 | escalável; não modelado |
| `slime_block` | 9 | quica; tratado como bloco comum |
| `bamboo_trapdoor` | 8 | aberto ou fechado muda a colisão |

Os quatro últimos são justamente os mais difíceis de simular. É por isso que
os trechos de treino param antes deles.

## Randomização de domínio

Durante o treino, as constantes recebem um ruído de ±3% a cada episódio
(`randomizacao_de_dominio` no `config/parkour.json`). Isso produz uma política
que aguenta erro de modelo, em vez de uma que decorou o simulador.

As medidas do corpo do jogador (largura, altura, degrau) **não** recebem
ruído: elas são exatas.

A avaliação sempre roda com o ruído desligado. Medir uma política enquanto a
física treme mede outra coisa.

## Plano B, se a calibração reprovar

Usar `prismarine-physics` — o mesmo motor que o mineflayer já usa internamente
para prever movimento — como simulador, num processo Node conversando por
pipe. Mais lento que Python puro, e ainda assim ordens de grandeza mais rápido
que o servidor, com fidelidade garantida por construção.

Se o mineflayer conecta no servidor, `prismarine-physics` para aquela versão
existe: ele é dependência do mineflayer.

## O resultado que fecha o ciclo

```
parkour rodar
```

Roda no jogo a política treinada offline, sem retreinar. A **queda** na taxa
de conclusão em relação ao simulador é o custo de ter saído do simulador — e é
um resultado do trabalho, não um detalhe de implementação.
