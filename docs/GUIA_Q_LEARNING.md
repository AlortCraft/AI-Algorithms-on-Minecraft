# Guia didático de Q-Learning

## 1. O problema

O bot precisa descobrir quando andar, correr e combinar essas velocidades com
o pulo. Não escrevemos uma regra
como “se houver um buraco, pule”. Em vez disso, deixamos o agente experimentar,
receber recompensas e guardar o resultado das experiências.

Cada interação possui cinco elementos:

1. `estado`: resumo da situação atual;
2. `ação`: escolha feita pelo agente;
3. `recompensa`: número que indica se a escolha ajudou;
4. `próximo estado`: situação observada depois da ação;
5. `terminou`: informa se houve chegada ou queda.

Uma experiência pode ser representada assim:

```text
estado 12 → correr e pular → recompensa +0,8 → estado 19
```

## 2. A tabela Q

A tabela Q possui uma linha por estado e uma coluna por ação.

| Estado | Andar | Correr | Correr e pular |
|---|---:|---:|---:|
| chão contínuo | 2,8 | 4,2 | 1,1 |
| buraco próximo | -2,0 | -3,0 | 6,5 |
| durante o salto | 0,2 | 0,7 | 2,1 |

Um valor alto significa que aquela ação costuma produzir bons resultados a
partir daquele estado. No código, a tabela é apenas uma lista de listas:

```python
self.tabela = [
    [0.0] * quantidade_acoes
    for _ in range(quantidade_estados)
]
```

Ela começa zerada porque o agente ainda não sabe nada.

## 3. Exploração e aproveitamento

Se o agente sempre escolher o maior valor desde o começo, todas as opções estão
empatadas em zero e ele pode deixar de conhecer ações úteis. Por isso usamos a
estratégia epsilon-greedy:

- com probabilidade `epsilon`, sorteia uma ação permitida;
- no restante das vezes, usa a ação com maior valor Q.

No início, epsilon vale `1.0`: praticamente tudo é exploração. Depois de cada
episódio ele diminui, até o mínimo configurado.

Exploração aleatória não é um segundo agente. É uma parte indispensável do
próprio Q-Learning.

No cenário reto, as ações permitidas são `0 andar`, `1 correr`, `2 correr_pulo`
e `3 andar_pulo`. O salto andando percorre menos distância horizontal e pode
ser melhor para vãos curtos ou apoios pequenos.

## 4. A equação de Bellman

A atualização usada em `q_learning.py` é:

```text
Q(s,a) ← Q(s,a) + α × [r + γ × max Q(s',a') − Q(s,a)]
```

Significado dos símbolos:

- `s`: estado atual;
- `a`: ação executada;
- `r`: recompensa recebida agora;
- `s'`: próximo estado;
- `α` ou alfa: taxa de aprendizado;
- `γ` ou gama: desconto das recompensas futuras.

### Exemplo numérico

Considere:

```text
Q atual = 2,0
recompensa = 1,0
melhor valor futuro = 5,0
alfa = 0,2
gama = 0,9
```

Primeiro calculamos o alvo:

```text
alvo = 1,0 + 0,9 × 5,0
alvo = 5,5
```

O erro da previsão atual é:

```text
erro = 5,5 − 2,0 = 3,5
```

O agente corrige somente 20% desse erro:

```text
novo Q = 2,0 + 0,2 × 3,5
novo Q = 2,7
```

O valor não salta diretamente para 5,5. Ele se aproxima à medida que situações
parecidas são experimentadas novamente.

Quando o episódio realmente termina, não existe recompensa futura. O alvo é
somente a recompensa imediata.

## 5. Estado

Q-Learning tabular exige um número inteiro para identificar o estado. O arquivo
`estado.py` converte várias informações em um único índice.

No cenário `frente_1`, o estado considera:

- existência de piso nas quatro células seguintes;
- altura do próximo apoio: queda longa, queda curta, mesmo nível, subida
  pulável ou alto demais;
- posição dentro do bloco atual;
- subida, descida ou contato com o chão;
- faixa de velocidade.

Essa representação possui 3.456 estados. Ela continua pequena para uma tabela
Q, mas evita tratar um bloco acima e uma queda de quatro blocos como se fossem
a mesma situação. Essa diferença é indispensável em `frente_2`.

No mapa oficial, considera:

- faixa lateral ocupada;
- distância do próximo obstáculo;
- faixas livres à frente;
- contato com o chão;
- altura aproximada do obstáculo.

Se o estado tiver informação de menos, situações que exigem ações diferentes
parecerão iguais. Se tiver informação demais, a tabela ficará enorme e muitos
estados quase nunca serão visitados.

## 6. Recompensa

O arquivo `recompensa.py` soma sinais simples:

- avanço: recompensa positiva proporcional ao progresso;
- passo: pequeno custo para evitar demora;
- parado: custo adicional quando não há avanço;
- queda: penalidade grande;
- meta: recompensa grande.

O progresso usa deslocamento líquido. Andar para frente e voltar não gera uma
recompensa infinita, porque o retorno cancela o avanço.

Nas três frentes de treino, o avanço só entra na recompensa quando o bot pousa
em um apoio pertencente ao percurso. O deslocamento bruto continua no CSV para
diagnóstico, mas atravessar a pista no ar ou correr por baixo dela não conta
como aprendizado útil. Essa mudança é a versão 2 da recompensa e cria modelos
novos com o sufixo `_recompensa_v2`.

## 7. Episódio

Um episódio começa com `reset()` e termina por:

- `meta`: chegou ao final;
- `queda`: caiu do percurso;
- `travado`: não consegue avançar no jogo;
- `tempo`: atingiu o limite de passos.

Depois do episódio, epsilon diminui. A tabela, porém, continua existindo e é
usada no episódio seguinte.
Com `exploracao_decaimento=0.9995`, um treino de 7.000 episódios ainda explora
durante a maior parte da execução; o valor anterior `0.98` chegava ao mínimo em
aproximadamente 150 episódios.

## 8. Arquivo para estudar primeiro

Leia `src/parkour/q_learning.py` nesta ordem:

1. `__init__` cria os parâmetros e a tabela;
2. `escolher_acao` implementa epsilon-greedy;
3. `_melhor_acao` consulta a tabela;
4. `aprender` implementa Bellman;
5. `fim_de_episodio` reduz epsilon;
6. `salvar` e `carregar` persistem o aprendizado.

Depois leia `rodar_episodio` em `src/parkour/treinar.py`. Esse laço mostra como
o algoritmo recebe experiências produzidas pelo Minecraft.
