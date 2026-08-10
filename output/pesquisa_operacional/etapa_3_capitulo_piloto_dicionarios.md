# Capítulo piloto — Dicionários do Simplex

## Como usar este capítulo

Este capítulo foi escrito para substituir o consumo passivo repetido da videoaula, não o trabalho ativo necessário para aprender. Leia com papel ao lado. Sempre que aparecer a indicação **Pare e tente**, faça a manipulação antes de continuar. Nos checkpoints, responda sem consultar o texto. As respostas e soluções comentadas estão reunidas somente no final.

O capítulo preserva a forma padrão, a notação matricial e o exemplo empregados pelo Prof. Teobaldo Bulhões. Analogias, perguntas de diagnóstico e exercícios adicionais são complementações pedagógicas e não são atribuídos ao professor.

## Objetivos de aprendizagem

Ao terminar o capítulo, você deverá conseguir:

- explicar, com suas palavras, o que é um dicionário e por que ele é útil;
- distinguir problema, base, dicionário e solução básica;
- identificar variáveis básicas e não básicas;
- construir um dicionário por substituição algébrica;
- derivar a forma geral de um dicionário usando as matrizes \(B\) e \(N\);
- obter a solução básica representada por um dicionário;
- verificar se essa solução básica é viável;
- interpretar os termos constantes das linhas básicas;
- interpretar a linha da função objetivo e reconhecer direções com potencial de melhoria;
- explicar o que precisa ser preservado quando uma variável não básica aumenta;
- reconhecer erros comuns de construção e leitura de dicionários;
- preparar o raciocínio necessário para estudar pivoteamento e Simplex.

## Pré-requisitos

Você precisará lembrar que:

1. o curso utiliza a forma padrão

\[
\max c^Tx
\]

\[
Ax=b,\qquad x\ge 0;
\]

2. uma restrição \(\le\) pode ser transformada em igualdade com uma variável de folga não negativa;
3. uma base é formada por \(m\) colunas linearmente independentes de \(A\), quando existem \(m\) restrições de igualdade;
4. as variáveis associadas às colunas escolhidas são básicas; as demais são não básicas;
5. a solução básica associada a uma base é obtida fixando as variáveis não básicas em zero e resolvendo o sistema para as básicas.

Se algum desses pontos ainda parecer apenas uma frase decorada, não há problema: eles serão reconstruídos enquanto o dicionário for desenvolvido.

---

## 1. O problema que o dicionário resolve

Considere um problema linear na forma padrão. As restrições são um sistema de equações. Se escolhermos uma base, poderíamos encontrar a solução básica resolvendo diretamente um sistema linear. Isso funciona para obter uma única solução. Entretanto, o Simplex precisa fazer mais do que isso.

Ele precisa responder, repetidamente, a perguntas como:

- Qual solução a base atual representa?
- Essa solução é viável?
- Se uma variável atualmente igual a zero começar a aumentar, como as outras variáveis precisarão mudar?
- A função objetivo melhorará ou piorará?
- Até onde essa mudança pode continuar sem produzir uma variável negativa?

Resolver um novo sistema do zero para cada pergunta esconderia a estrutura do problema. O dicionário reorganiza as mesmas equações para tornar essas respostas visíveis.

Um dicionário não cria novas soluções e não altera as restrições. Ele é uma reescrita algébrica do problema em relação a uma base escolhida.

Em um dicionário:

- cada variável básica fica isolada no lado esquerdo de uma equação;
- no lado direito aparecem apenas constantes e variáveis não básicas;
- a função objetivo também é escrita apenas em função das variáveis não básicas.

Essa organização é útil porque as variáveis não básicas funcionam como entradas livres da representação. Depois que seus valores são escolhidos, as equações informam os valores obrigatórios das variáveis básicas e da função objetivo.

### 1.1 Uma analogia cuidadosamente limitada

Como complemento pedagógico, imagine um painel de controle. Os seletores do painel são as variáveis não básicas. As variáveis básicas são mostradores cujo valor é determinado pela posição dos seletores. A linha da função objetivo é outro mostrador: ela informa o efeito das mesmas escolhas sobre \(z\).

A analogia tem um limite importante. Não podemos mover os seletores arbitrariamente: todas as variáveis devem continuar não negativas. Por isso, as linhas básicas não apenas calculam valores; elas também revelam limites para os movimentos.

### 1.2 O que o dicionário não é

O dicionário não é:

- uma nova formulação independente do problema original;
- uma lista de valores já escolhidos para todas as variáveis;
- apenas a linha da função objetivo;
- sinônimo de solução básica;
- uma tabela de Simplex disfarçada.

Um dicionário representa uma família de soluções das equações. A solução básica correspondente é apenas um ponto especial dessa família: o ponto obtido quando todas as variáveis não básicas valem zero.

### Checkpoint 1 — Antes de continuar, você deveria conseguir responder

1. Por que isolar as variáveis básicas é útil?
2. Quais variáveis aparecem no lado direito de um dicionário?
3. Um dicionário é uma solução ou uma representação de várias soluções das equações?
4. Qual escolha particular produz a solução básica do dicionário?

Não consulte respostas agora. Se uma pergunta estiver incerta, volte apenas à subseção correspondente.

---

## 2. Do problema original à forma padrão

Usaremos o exemplo central da aula de Dicionários:

\[
\max z=3x_1+5x_2
\]

sujeito a

\[
\begin{aligned}
x_1 &\le 4,\\
x_2 &\le 6,\\
3x_1+2x_2 &\le 18,\\
x_1,x_2&\ge0.
\end{aligned}
\]

As variáveis \(x_1\) e \(x_2\) são as variáveis de decisão originais. Para transformar as desigualdades em igualdades, introduzimos as variáveis de folga \(x_3,x_4,x_5\):

\[
\begin{aligned}
x_1+x_3 &=4,\\
x_2+x_4 &=6,\\
3x_1+2x_2+x_5 &=18,\\
x_1,x_2,x_3,x_4,x_5&\ge0.
\end{aligned}
\]

Cada folga tem significado concreto:

- \(x_3=4-x_1\) mede quanto resta do limite da primeira restrição;
- \(x_4=6-x_2\) mede quanto resta do limite da segunda;
- \(x_5=18-3x_1-2x_2\) mede a folga da terceira.

Na forma matricial,

\[
A=
\begin{bmatrix}
1&0&1&0&0\\
0&1&0&1&0\\
3&2&0&0&1
\end{bmatrix},
\quad
x=
\begin{bmatrix}
x_1\\x_2\\x_3\\x_4\\x_5
\end{bmatrix},
\quad
b=
\begin{bmatrix}
4\\6\\18
\end{bmatrix}.
\]

Assim, as restrições são \(Ax=b\), com \(x\ge0\).

Observe que há três equações. Portanto, uma base deverá conter três colunas linearmente independentes de \(A\).

---

## 3. Escolher uma base é escolher uma perspectiva algébrica

Para construir o primeiro dicionário, escolheremos como básicas as variáveis

\[
x_1,\quad x_4,\quad x_5.
\]

As colunas correspondentes formam

\[
B=
\begin{bmatrix}
1&0&0\\
0&1&0\\
3&0&1
\end{bmatrix}.
\]

Essa matriz é invertível; portanto, as três colunas formam uma base. As variáveis restantes,

\[
x_2,\quad x_3,
\]

são não básicas. Suas colunas formam

\[
N=
\begin{bmatrix}
0&1\\
1&0\\
2&0
\end{bmatrix},
\]

se mantivermos a ordem \(x_N=(x_2,x_3)^T\).

É importante perceber que “básica” e “não básica” não são características permanentes de uma variável. \(x_2\) é não básica nesta base, mas poderá ser básica em outra. A classificação descreve o papel da variável na representação atual.

### 3.1 Base, dicionário e solução: três objetos diferentes

Antes de fazer contas, fixe a distinção:

- **Base:** conjunto ordenado de colunas linearmente independentes, ou a matriz \(B\) formada por elas.
- **Dicionário:** reescrita das variáveis básicas e de \(z\) em termos das não básicas.
- **Solução básica:** valores obtidos ao fixar as não básicas em zero no dicionário.

Uma base determina um dicionário. O dicionário determina uma solução básica. Esses objetos estão ligados, mas não são a mesma coisa.

### 3.2 Por que a base precisa ser invertível

Queremos isolar as variáveis básicas. Na forma matricial, isso exigirá multiplicar por \(B^{-1}\). Se \(B\) não possuir inversa, não haverá uma maneira única de expressar \(x_B\) em função de \(x_N\).

Por isso, não basta selecionar três colunas quaisquer. Elas precisam ser linearmente independentes.

### Pare e tente 1

Localize na matriz \(A\) as colunas de \(x_1,x_4,x_5\). Confirme que são exatamente as colunas mostradas em \(B\). Depois localize as colunas de \(x_2,x_3\) e confirme a matriz \(N\).

---

## 4. Construção do dicionário por substituição

Comecemos pelas equações na forma padrão:

\[
\begin{aligned}
x_1+x_3 &=4,\\
x_2+x_4 &=6,\\
3x_1+2x_2+x_5 &=18.
\end{aligned}
\]

Como \(x_1,x_4,x_5\) são básicas, cada uma delas deve ficar isolada à esquerda. Como \(x_2,x_3\) são não básicas, elas deverão aparecer à direita.

### 4.1 Primeira linha

Da equação

\[
x_1+x_3=4,
\]

isolamos \(x_1\):

\[
x_1=4-x_3.
\]

### 4.2 Segunda linha

Da equação

\[
x_2+x_4=6,
\]

isolamos \(x_4\):

\[
x_4=6-x_2.
\]

### 4.3 Terceira linha

Na terceira equação,

\[
3x_1+2x_2+x_5=18,
\]

isolamos inicialmente \(x_5\):

\[
x_5=18-3x_1-2x_2.
\]

Essa expressão ainda não serve como linha do dicionário, porque contém \(x_1\), que é básica. Um dicionário deve ter somente variáveis não básicas à direita. Substituímos \(x_1=4-x_3\):

\[
x_5=18-3(4-x_3)-2x_2.
\]

Distribuindo o \(-3\):

\[
x_5=18-12+3x_3-2x_2.
\]

Finalmente,

\[
x_5=6-2x_2+3x_3.
\]

### 4.4 Linha da função objetivo

A função objetivo original é

\[
z=3x_1+5x_2.
\]

Ela ainda contém a variável básica \(x_1\). Substituímos novamente \(x_1=4-x_3\):

\[
z=3(4-x_3)+5x_2.
\]

Distribuindo o 3,

\[
z=12-3x_3+5x_2.
\]

Reordenando os termos na ordem \(x_2,x_3\):

\[
z=12+5x_2-3x_3.
\]

### 4.5 O dicionário completo

Portanto,

\[
\boxed{
\begin{aligned}
x_1 &=4-x_3,\\
x_4 &=6-x_2,\\
x_5 &=6-2x_2+3x_3,\\
z   &=12+5x_2-3x_3.
\end{aligned}}
\]

Faça uma verificação estrutural:

- à esquerda aparecem apenas \(x_1,x_4,x_5\), as variáveis básicas;
- à direita aparecem apenas \(x_2,x_3\), as variáveis não básicas, além das constantes;
- a linha de \(z\) também depende apenas de \(x_2,x_3\).

Se uma variável básica permanecesse no lado direito de qualquer linha, a construção ainda não estaria concluída.

### Checkpoint 2

1. Por que foi necessário substituir \(x_1\) na linha de \(x_5\)?
2. Por que também foi necessário substituir \(x_1\) em \(z\)?
3. Qual teste visual rápido permite verificar se a estrutura de um dicionário está correta?
4. Se \(x_2\) se tornasse básica em outra base, ela continuaria obrigatoriamente no lado direito?

---

## 5. Construção matricial do mesmo dicionário

A substituição linha a linha mostra concretamente o que acontece. A forma matricial revela a estrutura geral.

Partimos de

\[
Ax=b.
\]

Depois de separar as colunas básicas e não básicas, escrevemos

\[
Bx_B+Nx_N=b.
\]

Queremos isolar \(x_B\). Primeiro, passamos o termo não básico para o lado direito:

\[
Bx_B=b-Nx_N.
\]

Multiplicamos os dois lados **à esquerda** por \(B^{-1}\):

\[
B^{-1}Bx_B=B^{-1}(b-Nx_N).
\]

Como \(B^{-1}B=I\),

\[
x_B=B^{-1}b-B^{-1}Nx_N.
\]

Esta é a parte das restrições de qualquer dicionário:

\[
\boxed{x_B=B^{-1}b-B^{-1}Nx_N.}
\]

### 5.1 Por que a ordem da multiplicação importa

No material do curso, o professor chama atenção para o fato de que multiplicação matricial não é comutativa. Em geral,

\[
B^{-1}N\ne NB^{-1},
\]

e a segunda expressão pode nem estar definida. A operação correta é multiplicar \(Bx_B=b-Nx_N\) à esquerda por \(B^{-1}\), porque queremos produzir \(B^{-1}B=I\).

### 5.2 Derivação da linha objetivo

Particionamos também os coeficientes da função objetivo:

\[
z=c_B^Tx_B+c_N^Tx_N.
\]

Substituímos a expressão de \(x_B\):

\[
z=c_B^T\left(B^{-1}b-B^{-1}Nx_N\right)+c_N^Tx_N.
\]

Distribuímos \(c_B^T\):

\[
z=c_B^TB^{-1}b-c_B^TB^{-1}Nx_N+c_N^Tx_N.
\]

Agrupamos os termos que multiplicam \(x_N\):

\[
\boxed{
z=c_B^TB^{-1}b+left(c_N^T-c_B^TB^{-1}N\right)x_N.}
\]

Essa expressão tem duas partes:

- \(c_B^TB^{-1}b\): valor de \(z\) quando \(x_N=0\), isto é, na solução básica;
- \(c_N^T-c_B^TB^{-1}N\): coeficientes que mostram como \(z\) varia quando as não básicas mudam, mantendo as igualdades.

Esses coeficientes são chamados custos reduzidos na exposição de Simplex do curso.

### 5.3 Notação compacta de leitura

Podemos definir

\[
\bar b=B^{-1}b,
\qquad
\bar A=B^{-1}N,
\qquad
\bar c^T=c_N^T-c_B^TB^{-1}N,
\qquad
z_0=c_B^TB^{-1}b.
\]

O dicionário assume então a forma

\[
x_B=\bar b-\bar A x_N
\]

e

\[
z=z_0+\bar c^Tx_N.
\]

Essa escrita é eficiente, mas não deve esconder os significados:

- \(\bar b\) contém os valores básicos quando \(x_N=0\);
- cada coluna de \(-\bar A\) mostra como todas as básicas reagem ao aumento de uma não básica;
- \(z_0\) é o valor atual da função objetivo;
- cada componente de \(\bar c\) mostra a variação de \(z\) por unidade da não básica correspondente, antes de considerar até onde ela pode aumentar.

### Pare e tente 2

Sem olhar a fórmula final, refaça a derivação de \(x_B\) a partir de \(Bx_B+Nx_N=b\). Diga em voz alta por que \(B^{-1}\) existe e em qual lado ela deve multiplicar a equação.

---

## 6. Como extrair a solução básica do dicionário

Retomemos:

\[
\begin{aligned}
x_1 &=4-x_3,\\
x_4 &=6-x_2,\\
x_5 &=6-2x_2+3x_3,\\
z   &=12+5x_2-3x_3.
\end{aligned}
\]

As variáveis não básicas são \(x_2\) e \(x_3\). Para obter a solução básica correspondente, fixamos

\[
x_2=0,qquad x_3=0.
\]

Substituindo:

\[
\begin{aligned}
x_1&=4,\\
x_4&=6,\\
x_5&=6,\\
z&=12.
\end{aligned}
\]

Na ordem completa das variáveis,

\[
(x_1,x_2,x_3,x_4,x_5)=(4,0,0,6,6).
\]

### 6.1 Por que zerar as não básicas?

Isso não é um truque inventado depois que o dicionário ficou pronto. É a própria definição da solução básica associada à base. As variáveis fora da base são fixadas em zero; as equações determinam os valores das variáveis dentro da base.

### 6.2 Verificação no sistema original

Substituindo na forma padrão:

\[
x_1+x_3=4+0=4,
\]

\[
x_2+x_4=0+6=6,
\]

\[
3x_1+2x_2+x_5=3(4)+2(0)+6=18.
\]

Todas as igualdades são satisfeitas e todas as variáveis são não negativas. Logo, essa é uma solução básica viável.

### 6.3 Interpretação nas variáveis originais

Nas variáveis de decisão, a solução é

\[
(x_1,x_2)=(4,0).
\]

As folgas dizem:

- \(x_3=0\): a primeira restrição está ativa;
- \(x_4=6\): a segunda possui folga 6;
- \(x_5=6\): a terceira possui folga 6.

A função objetivo vale

\[
z=3(4)+5(0)=12.
\]

Observe como a leitura do dicionário e a leitura do problema original se completam. O vetor com cinco variáveis é necessário para a álgebra; o par \((x_1,x_2)\) e as folgas recuperam o significado do modelo.

---

## 7. Como verificar a viabilidade da solução básica

Em um dicionário da forma

\[
x_B=\bar b-\bar A x_N,
\]

a solução básica é

\[
x_N=0,qquad x_B=\bar b.
\]

As igualdades são satisfeitas por construção. Resta verificar a não negatividade. Portanto:

\[
\boxed{\text{A solução básica do dicionário é viável se }\bar b\ge0.}
\]

A desigualdade é componente a componente.

No exemplo, os termos constantes das linhas básicas são \(4,6,6\). Todos são não negativos; a solução básica é viável.

### 7.1 Um dicionário com solução básica inviável

Escolha agora como básicas \(x_1,x_2,x_5\) e como não básicas \(x_3,x_4\).

Das duas primeiras equações,

\[
x_1=4-x_3
\]

e

\[
x_2=6-x_4.
\]

Na terceira,

\[
x_5=18-3x_1-2x_2.
\]

Substituindo as expressões de \(x_1\) e \(x_2\):

\[
x_5=18-3(4-x_3)-2(6-x_4).
\]

Logo,

\[
x_5=-6+3x_3+2x_4.
\]

A função objetivo torna-se

\[
z=3(4-x_3)+5(6-x_4)=42-3x_3-5x_4.
\]

O dicionário é

\[
\begin{aligned}
x_1&=4-x_3,\\
x_2&=6-x_4,\\
x_5&=-6+3x_3+2x_4,\\
z&=42-3x_3-5x_4.
\end{aligned}
\]

Zerando \(x_3=x_4=0\), obtemos

\[
(x_1,x_2,x_3,x_4,x_5)=(4,6,0,0,-6).
\]

A solução satisfaz as três igualdades, mas viola \(x_5\ge0\). É uma solução básica inviável.

### 7.2 Por que o valor \(z=42\) não interessa como solução do problema

Seria um erro concluir que essa solução é melhor que a solução viável de valor 12 apenas porque \(42>12\). Otimização ocorre dentro da região viável. Um valor objetivo associado a um ponto inviável não compete com valores de soluções viáveis.

Essa distinção é fundamental no Simplex: primeiro precisamos de viabilidade; depois buscamos melhoria sem perdê-la.

### Checkpoint 3

1. Por que as igualdades estão satisfeitas mesmo na solução básica inviável?
2. Qual parte da forma padrão foi violada?
3. Onde a inviabilidade aparece imediatamente no dicionário?
4. Por que não devemos comparar \(z=42\) com os valores das soluções viáveis?

---

## 8. Como ler as linhas básicas como relações de causa e efeito

O dicionário não serve apenas para obter a solução quando \(x_N=0\). Ele informa o que acontece se uma não básica deixar o zero.

Retomemos o dicionário viável:

\[
\begin{aligned}
x_1 &=4-x_3,\\
x_4 &=6-x_2,\\
x_5 &=6-2x_2+3x_3,\\
z   &=12+5x_2-3x_3.
\end{aligned}
\]

### 8.1 Se aumentarmos \(x_2\)

Mantendo \(x_3=0\), temos

\[
\begin{aligned}
x_1&=4,\\
x_4&=6-x_2,\\
x_5&=6-2x_2,\\
z&=12+5x_2.
\end{aligned}
\]

Cada unidade adicionada a \(x_2\):

- não altera \(x_1\);
- reduz \(x_4\) em 1;
- reduz \(x_5\) em 2;
- aumenta \(z\) em 5.

Mas \(x_2\) não pode crescer indefinidamente. Precisamos manter

\[
x_4=6-x_2\ge0,
\]

o que implica \(x_2\le6\), e também

\[
x_5=6-2x_2\ge0,
\]

o que implica \(x_2\le3\).

A condição mais restritiva é \(x_2\le3\). Se aumentarmos \(x_2\) até 3, \(x_5\) chega a zero primeiro:

\[
(x_1,x_2,x_3,x_4,x_5)=(4,3,0,3,0),
\]

com

\[
z=12+5(3)=27.
\]

Ainda não estamos formalizando uma iteração do Simplex, mas o raciocínio essencial já apareceu: uma não básica com potencial de melhoria cresce até que uma básica atinja o limite de não negatividade.

### 8.2 Se aumentarmos \(x_3\)

Mantendo \(x_2=0\):

\[
\begin{aligned}
x_1&=4-x_3,\\
x_4&=6,\\
x_5&=6+3x_3,\\
z&=12-3x_3.
\end{aligned}
\]

Cada unidade adicionada a \(x_3\):

- reduz \(x_1\) em 1;
- não altera \(x_4\);
- aumenta \(x_5\) em 3;
- reduz \(z\) em 3.

Como o problema é de maximização, essa direção piora o valor objetivo a partir da solução atual.

### 8.3 Coeficiente da função objetivo não é a história completa

O coeficiente \(+5\) de \(x_2\) informa o ganho por unidade de \(x_2\). Ele não informa quantas unidades podem ser acrescentadas. Esse limite vem das linhas básicas e da não negatividade.

Assim, para avaliar um movimento, precisamos combinar duas leituras:

1. **linha de \(z\):** a direção melhora o objetivo?
2. **linhas básicas:** até onde podemos avançar sem perder viabilidade?

Essa combinação será o núcleo da escolha de variável entrante e variável sainte no Simplex.

### 8.4 Sinais na convenção usada neste curso

O curso escreve a função objetivo como

\[
z=z_0+\bar c^Tx_N.
\]

Para maximização:

- custo reduzido positivo: aumentar a variável não básica pode melhorar \(z\);
- custo reduzido negativo: aumentar a variável reduz \(z\);
- custo reduzido zero: a primeira ordem de leitura indica que \(z\) não muda nessa direção; se houver movimento viável, isso pode estar relacionado a outra solução ótima.

Para minimização, os sinais de melhoria se invertem.

A palavra “pode” é importante. Um coeficiente favorável não garante um passo positivo. Pode ocorrer de alguma variável básica já estar em zero e impedir qualquer aumento, caso associado à degenerescência.

### Pare e tente 3

No dicionário do exemplo, fixe \(x_3=1\) e \(x_2=0\). Calcule todas as variáveis e \(z\). A solução é viável? Ela melhora a solução básica?

---

## 9. Interpretação geométrica

O problema original possui duas variáveis de decisão, então podemos visualizar sua região viável no plano \((x_1,x_2)\). A solução básica do primeiro dicionário é

\[
(x_1,x_2)=(4,0).
\]

Ela é um vértice da região viável. Quando mantemos \(x_3=0\) e aumentamos \(x_2\), a equação

\[
x_1=4-x_3
\]

mantém \(x_1=4\). Geometricamente, movemo-nos ao longo da fronteira \(x_1=4\). O movimento termina em \((4,3)\), quando a terceira restrição se torna ativa e \(x_5=0\).

No dicionário inicial:

- \(x_3=0\) significa que a restrição \(x_1\le4\) está ativa;
- durante o movimento, \(x_5\) diminui até zero;
- no ponto final, duas restrições estão ativas: \(x_1=4\) e \(3x_1+2x_2=18\).

Isso conecta três linguagens:

- **geométrica:** movimento entre vértices por uma aresta do poliedro;
- **algébrica:** aumento de uma não básica até uma básica chegar a zero;
- **matricial:** troca de uma coluna na base.

O próximo capítulo usará essa conexão para explicar o pivoteamento. Aqui, o objetivo é perceber que o dicionário já contém a geometria, mesmo quando não conseguimos desenhar o problema.

### Complemento pedagógico: por que isso importa em dimensões maiores

Com cinco, cinquenta ou mil variáveis, não conseguimos desenhar a região viável. Ainda assim, as linhas do dicionário continuam indicando direções, limites e soluções básicas. A álgebra preserva a lógica geométrica sem depender da visualização.

---

## 10. Exemplo parcialmente guiado

Considere novamente o mesmo problema na forma padrão, mas escolha como básicas

\[
x_2,x_3,x_5
\]

e como não básicas

\[
x_1,x_4.
\]

### Pergunta 1

Qual equação permite isolar imediatamente \(x_2\)?

**Pare e tente.**

Da segunda restrição,

\[
x_2+x_4=6,
\]

obtemos

\[
x_2=6-x_4.
\]

### Pergunta 2

Qual equação permite isolar \(x_3\)?

Da primeira,

\[
x_1+x_3=4,
\]

obtemos

\[
x_3=4-x_1.
\]

### Pergunta 3

Construa a linha de \(x_5\) usando apenas \(x_1,x_4\) à direita.

Partimos de

\[
x_5=18-3x_1-2x_2.
\]

Substituindo \(x_2=6-x_4\):

\[
x_5=18-3x_1-2(6-x_4),
\]

portanto

\[
x_5=6-3x_1+2x_4.
\]

### Pergunta 4

Reescreva a função objetivo.

\[
z=3x_1+5(6-x_4)=30+3x_1-5x_4.
\]

O dicionário é

\[
\begin{aligned}
x_2&=6-x_4,\\
x_3&=4-x_1,\\
x_5&=6-3x_1+2x_4,\\
z&=30+3x_1-5x_4.
\end{aligned}
\]

### Pergunta 5

Qual solução básica ele representa? Ela é viável?

Zerando \(x_1=x_4=0\):

\[
(x_1,x_2,x_3,x_4,x_5)=(0,6,4,0,6).
\]

Todos os valores são não negativos. A solução é básica viável e \(z=30\).

### Pergunta 6

Qual não básica tem sinal de melhoria para maximização? Quais linhas limitariam seu crescimento?

\(x_1\) tem coeficiente \(+3\) em \(z\). Mantendo \(x_4=0\), as linhas relevantes são

\[
x_3=4-x_1\ge0
\]

e

\[
x_5=6-3x_1\ge0.
\]

Logo, \(x_1\le4\) pela primeira e \(x_1\le2\) pela segunda. A segunda é mais restritiva; \(x_5\) chegaria a zero primeiro.

Note a progressão: você já está lendo do dicionário quase toda a lógica de uma iteração do Simplex, ainda que o pivoteamento formal seja assunto do capítulo seguinte.

---

## 11. Diagnóstico de erros comuns

### 11.1 Chamar toda variável de folga de não básica

Uma variável de folga descreve como o modelo foi convertido para igualdade. Uma variável não básica descreve seu papel em uma base específica. Folgas podem ser básicas ou não básicas.

### 11.2 Zerar as variáveis básicas

Na solução básica associada a um dicionário, zeramos as **não básicas**. Os valores das básicas são então dados pelos termos constantes.

### 11.3 Deixar uma básica no lado direito

Se \(x_1\) é básica e aparece no lado direito da linha de \(x_5\), ainda não temos um dicionário completo para essa base. É preciso substituí-la.

### 11.4 Ver um termo constante negativo e declarar o problema inviável

Um termo constante negativo mostra que a **solução básica atual** é inviável. Isso não prova que o problema inteiro não possui soluções viáveis.

### 11.5 Comparar valores objetivos de pontos inviáveis

O valor da função objetivo só participa da otimização depois que a solução satisfaz todas as restrições.

### 11.6 Olhar apenas a linha de \(z\)

Um custo reduzido favorável mostra potencial de melhoria por unidade. As linhas básicas determinam se existe passo viável e qual é seu tamanho máximo.

### 11.7 Trocar o sinal ao substituir

Em

\[
x_5=18-3(4-x_3)-2x_2,
\]

o termo \(-3(4-x_3)\) resulta em \(-12+3x_3\), não \(-12-3x_3\).

### 11.8 Multiplicar matrizes na ordem errada

Para isolar \(x_B\), usamos \(B^{-1}Bx_B\). Não podemos simplesmente mover matrizes como escalares.

### 11.9 Confundir coeficiente original com custo reduzido

O coeficiente de uma variável na função objetivo original não é necessariamente seu coeficiente na linha objetivo do dicionário. O custo reduzido incorpora o efeito indireto da variável sobre as básicas.

### 11.10 Achar que uma variável é básica para sempre

O papel muda quando a base muda. O Simplex funciona justamente trocando uma variável básica por uma não básica.

---

## 12. Revisão rápida — somente depois do estudo

### Definição operacional

Um dicionário associado a uma base é uma reescrita de um PL em forma padrão na qual:

- as básicas ficam isoladas à esquerda;
- apenas não básicas e constantes aparecem à direita;
- \(z\) é escrito em função das não básicas.

### Fórmulas essenciais

\[
Bx_B+Nx_N=b
\]

\[
x_B=B^{-1}b-B^{-1}Nx_N
\]

\[
z=c_B^TB^{-1}b+\left(c_N^T-c_B^TB^{-1}N\right)x_N.
\]

### Como obter a solução básica

1. identifique \(x_N\);
2. fixe \(x_N=0\);
3. leia \(x_B\) nos termos constantes;
4. leia \(z\) no termo constante da linha objetivo.

### Como testar viabilidade

Na forma padrão, a solução básica é viável se todos os valores básicos forem não negativos.

### Como ler uma possível melhoria

Na convenção \(z=z_0+\bar c^Tx_N\):

- maximização procura custo reduzido positivo;
- minimização procura custo reduzido negativo;
- as linhas básicas determinam se e até onde o movimento é viável.

### Perguntas de recuperação ativa

Sem consultar o capítulo, explique:

1. por que uma base determina um dicionário;
2. por que a solução básica é obtida com \(x_N=0\);
3. por que \(B\) precisa ser invertível;
4. o significado de \(B^{-1}b\);
5. o significado de uma coluna de \(-B^{-1}N\);
6. por que um custo reduzido favorável não basta para garantir melhoria efetiva;
7. como um movimento algébrico no dicionário corresponde a um movimento geométrico.

---

## 13. Exercícios

Tente os exercícios antes de consultar as soluções comentadas. Registre não apenas o resultado, mas a justificativa de cada escolha.

## Nível 1 — Compreensão

### Exercício 1

Explique a diferença entre base, dicionário e solução básica.

### Exercício 2

Por que uma variável de folga não é necessariamente uma variável básica?

### Exercício 3

Considere

\[
x_3=5-2x_1+x_2,
\qquad
x_4=7+x_1-3x_2,
\qquad
z=10+4x_1-x_2.
\]

Identifique as variáveis básicas e não básicas e obtenha a solução básica.

### Exercício 4

No exercício anterior, a solução básica é viável? Justifique usando a forma padrão.

### Exercício 5

Em um problema de maximização escrito na convenção deste capítulo, o que significa um custo reduzido positivo? O que ele não garante?

### Exercício 6

Um dicionário possui uma linha básica com termo constante \(-2\). O que é possível concluir e o que não é possível concluir?

### Exercício 7

Por que comparar o valor objetivo de uma solução básica inviável com o de uma solução viável é conceitualmente errado?

### Exercício 8

Explique a relação entre uma variável não básica que aumenta e uma variável básica que chega a zero.

## Nível 2 — Aplicação direta

### Exercício 9

Considere

\[
\max z=4x_1+3x_2
\]

\[
\begin{aligned}
x_1+x_2&\le5,\\
2x_1+x_2&\le8,\\
x_1,x_2&\ge0.
\end{aligned}
\]

1. Introduza \(x_3,x_4\) como folgas.
2. Use a base \(\{x_3,x_4\}\).
3. Escreva o dicionário.
4. Obtenha a solução básica e teste sua viabilidade.
5. Identifique as direções com potencial de melhoria.

### Exercício 10

Para o mesmo problema, use a base \(\{x_1,x_4\}\), deixando \(x_2,x_3\) não básicas. Construa o dicionário e interprete a solução básica.

### Exercício 11

Considere o dicionário

\[
\begin{aligned}
x_3&=8-2x_1-x_2,\\
x_4&=6+x_1-2x_2,\\
z&=14+3x_1+2x_2.
\end{aligned}
\]

Mantendo uma das não básicas em zero por vez:

1. determine o maior aumento viável de \(x_1\);
2. determine o maior aumento viável de \(x_2\);
3. calcule o valor de \(z\) no final de cada movimento;
4. explique por que o maior custo reduzido não determina sozinho o maior ganho total.

### Exercício 12

Considere

\[
\begin{aligned}
x_2&=3-x_4,\\
x_3&=-1+2x_1+x_4,\\
z&=9+x_1-4x_4.
\end{aligned}
\]

1. identifique a base;
2. obtenha a solução básica;
3. classifique-a;
4. escolha valores de \(x_1,x_4\) que produzam uma solução viável das equações, se possível.

## Nível 3 — Construção e diagnóstico

### Exercício 13

Considere

\[
\max z=2x_1+x_2
\]

\[
\begin{aligned}
x_1+x_2+x_3&=4,\\
2x_1+x_2+x_4&=5,\\
x&\ge0.
\end{aligned}
\]

Use a base \(\{x_1,x_3\}\). Antes de calcular, verifique se as colunas escolhidas são linearmente independentes. Depois construa e interprete o dicionário.

### Exercício 14

Um estudante propôs o seguinte “dicionário” para uma base em que \(x_1,x_4,x_5\) são básicas:

\[
\begin{aligned}
x_1&=4-x_3,\\
x_4&=6-x_2,\\
x_5&=18-3x_1-2x_2,\\
z&=3x_1+5x_2.
\end{aligned}
\]

Identifique o problema estrutural e complete corretamente a construção.

### Exercício 15

Em um PL na forma padrão, um estudante seleciona \(m\) colunas de \(A\), mas descobre que a matriz quadrada formada tem determinante zero. Explique:

1. por que a seleção não é uma base;
2. por que não é possível obter um dicionário único com essas variáveis básicas;
3. o que o estudante deve fazer.

### Exercício 16

Crie um pequeno problema com duas variáveis originais e duas restrições \(\le\). Converta-o para a forma padrão, escolha uma base diferente da base inicial de folgas e construa o dicionário. Explique o significado da solução básica nas variáveis originais.

## Nível 4 — Problemas mistos

### Exercício 17

Três dicionários são apresentados para problemas de maximização na convenção deste capítulo:

**A**

\[
\begin{aligned}
x_3&=4-x_1,\\
x_4&=2+x_1,\\
z&=7-3x_1.
\end{aligned}
\]

**B**

\[
\begin{aligned}
x_3&=0-x_1,\\
x_4&=5+2x_1,\\
z&=8+4x_1.
\end{aligned}
\]

**C**

\[
\begin{aligned}
x_3&=4+x_1,\\
x_4&=2+3x_1,\\
z&=7+2x_1.
\end{aligned}
\]

Para cada um, responda:

1. a solução básica é viável?
2. há direção de melhoria indicada por \(x_1\)?
3. existe passo positivo viável?
4. o comportamento sugere ótimo atual, degenerescência ou ilimitabilidade nessa direção?

### Exercício 18

No dicionário

\[
\begin{aligned}
x_3&=5-x_1-2x_2,\\
x_4&=4-2x_1-x_2,\\
z&=6+4x_1+3x_2,
\end{aligned}
\]

um estudante escolhe \(x_1\) porque seu custo reduzido é maior. Outro estudante afirma que \(x_2\) pode produzir ganho total maior. Avalie as duas afirmações calculando o melhor passo isolado em cada direção.

### Exercício 19

Explique, sem efetuar um pivoteamento completo, o que deverá acontecer com a base quando uma variável não básica aumenta até uma variável básica chegar a zero. Relacione a resposta às três perspectivas: algébrica, matricial e geométrica.

### Exercício 20

Você recebe apenas a solução básica

\[
(x_1,x_2,x_3,x_4,x_5)=(4,0,0,6,6)
\]

do exemplo central. É possível reconstruir unicamente o dicionário sem saber qual é a base e sem conhecer as equações? Justifique. Indique quais informações adicionais seriam necessárias.

---

## 14. Soluções comentadas

## Respostas dos checkpoints e atividades “Pare e tente”

### Checkpoint 1

1. Isolar as básicas permite calcular seus valores diretamente a partir das não básicas e observar como reagem a mudanças.
2. Apenas constantes e variáveis não básicas.
3. É uma representação de todas as soluções das igualdades parametrizadas pelas não básicas; não é uma solução isolada.
4. Fixar todas as não básicas em zero.

### Pare e tente 1

As colunas 1, 4 e 5 de \(A\) são \((1,0,3)^T\), \((0,1,0)^T\) e \((0,0,1)^T\), formando \(B\). As colunas 2 e 3 são \((0,1,2)^T\) e \((1,0,0)^T\), formando \(N\) na ordem indicada.

### Checkpoint 2

1. Porque \(x_1\) é básica e não pode permanecer no lado direito.
2. Pela mesma razão: a linha objetivo deve depender apenas das não básicas.
3. Conferir se as básicas aparecem isoladas à esquerda e se somente não básicas aparecem à direita, inclusive em \(z\).
4. Não. Se \(x_2\) fosse básica, deveria ser isolada à esquerda.

### Pare e tente 2

\[
Bx_B+Nx_N=b
\Rightarrow Bx_B=b-Nx_N
\Rightarrow B^{-1}Bx_B=B^{-1}(b-Nx_N)
\Rightarrow x_B=B^{-1}b-B^{-1}Nx_N.
\]

\(B^{-1}\) existe porque as colunas de \(B\) são linearmente independentes. A multiplicação ocorre à esquerda para formar \(B^{-1}B\).

### Checkpoint 3

1. Porque \(x_B=B^{-1}b\) foi construído justamente para satisfazer \(Bx_B=b\).
2. A não negatividade, pois \(x_5=-6\).
3. No termo constante negativo da linha de \(x_5\).
4. Porque \(z=42\) pertence a um ponto fora da região viável.

### Pare e tente 3

Com \(x_3=1\) e \(x_2=0\):

\[
x_1=3,\quad x_4=6,\quad x_5=9,\quad z=9.
\]

Todas as variáveis são não negativas, então a solução é viável. Ela não melhora a solução básica de valor 12; reduz \(z\) para 9.

## Soluções do Nível 1

### Exercício 1

A base é a escolha de colunas linearmente independentes. O dicionário é a reescrita produzida por essa escolha. A solução básica é o ponto obtido no dicionário quando as variáveis não básicas são zeradas.

### Exercício 2

“Folga” descreve a origem e o significado da variável; “básica” descreve seu papel em uma base. Uma folga pode entrar ou sair da base.

### Exercício 3

As básicas são \(x_3,x_4\); as não básicas são \(x_1,x_2\). Zerando \(x_1=x_2=0\):

\[
x_3=5,\quad x_4=7,\quad z=10.
\]

### Exercício 4

Sim. As não básicas valem zero e as básicas valem 5 e 7, todas não negativas. As igualdades são satisfeitas pelo próprio dicionário.

### Exercício 5

Um custo reduzido positivo indica que cada unidade adicional da não básica aumentaria \(z\), na convenção usada. Ele não garante que exista passo positivo viável nem informa sozinho o ganho total.

### Exercício 6

Conclui-se que a solução básica desse dicionário é inviável. Não se pode concluir que o PL inteiro seja inviável.

### Exercício 7

O problema de otimização compara apenas pontos que satisfazem todas as restrições. Um ponto inviável não é candidato, qualquer que seja seu valor objetivo formal.

### Exercício 8

A não básica sai de zero e cresce. Para preservar as igualdades, as básicas mudam conforme suas linhas. Quando uma delas chega a zero, qualquer aumento adicional que a reduzisse produziria valor negativo; ela atingiu o limite do movimento e é candidata a sair da base.

## Soluções do Nível 2

### Exercício 9

Com folgas:

\[
x_1+x_2+x_3=5,
\qquad
2x_1+x_2+x_4=8.
\]

Usando \(x_3,x_4\) básicas:

\[
\begin{aligned}
x_3&=5-x_1-x_2,\\
x_4&=8-2x_1-x_2,\\
z&=4x_1+3x_2.
\end{aligned}
\]

A solução básica é \((x_1,x_2,x_3,x_4)=(0,0,5,8)\), viável, com \(z=0\). Tanto \(x_1\) quanto \(x_2\) possuem custos reduzidos positivos e potencial de melhoria.

### Exercício 10

As não básicas são \(x_2,x_3\). Da primeira equação:

\[
x_1=5-x_2-x_3.
\]

Na segunda:

\[
x_4=8-2x_1-x_2.
\]

Substituindo \(x_1\):

\[
x_4=8-2(5-x_2-x_3)-x_2=-2+x_2+2x_3.
\]

Na função objetivo:

\[
z=4(5-x_2-x_3)+3x_2=20-x_2-4x_3.
\]

O dicionário é

\[
\begin{aligned}
x_1&=5-x_2-x_3,\\
x_4&=-2+x_2+2x_3,\\
z&=20-x_2-4x_3.
\end{aligned}
\]

Zerando \(x_2=x_3=0\), obtemos \((5,0,0,-2)\), solução básica inviável por \(x_4=-2\).

### Exercício 11

Para aumentar \(x_1\) com \(x_2=0\):

\[
x_3=8-2x_1\ge0\Rightarrow x_1\le4.
\]

\(x_4=6+x_1\) não limita o crescimento. No passo 4,

\[
z=14+3(4)=26.
\]

Para aumentar \(x_2\) com \(x_1=0\):

\[
x_3=8-x_2\ge0\Rightarrow x_2\le8,
\]

\[
x_4=6-2x_2\ge0\Rightarrow x_2\le3.
\]

No passo 3,

\[
z=14+2(3)=20.
\]

Aqui, \(x_1\) possui maior custo reduzido e também maior ganho total. O ponto conceitual é que essa coincidência foi verificada usando o passo admissível; ela não decorre apenas de \(3>2\).

### Exercício 12

A base é \(\{x_2,x_3\}\); as não básicas são \(x_1,x_4\). A solução básica é

\[
(x_1,x_2,x_3,x_4)=(0,3,-1,0),
\]

inviável. É possível recuperar viabilidade, por exemplo, com \(x_1=\tfrac12\) e \(x_4=0\):

\[
x_2=3,qquad x_3=-1+2\left(\tfrac12\right)=0.
\]

Isso reforça que a solução básica ser inviável não implica que toda solução representada pelo dicionário seja inviável.

## Soluções do Nível 3

### Exercício 13

A matriz das restrições é

\[
A=
\begin{bmatrix}
1&1&1&0\\
2&1&0&1
\end{bmatrix}.
\]

As colunas de \(x_1\) e \(x_3\) formam

\[
B=
\begin{bmatrix}
1&1\\
2&0
\end{bmatrix},
\]

cujo determinante é \(-2\ne0\). A seleção é uma base. As não básicas são \(x_2,x_4\).

Da segunda equação,

\[
x_1=\frac{5-x_2-x_4}{2}
=\frac52-\frac12x_2-\frac12x_4.
\]

Na primeira,

\[
x_3=4-x_1-x_2
=\frac32-\frac12x_2+\frac12x_4.
\]

Na função objetivo,

\[
z=2x_1+x_2=5-x_4.
\]

O dicionário é

\[
\begin{aligned}
x_1&=\frac52-\frac12x_2-\frac12x_4,\\
x_3&=\frac32-\frac12x_2+\frac12x_4,\\
z&=5-x_4.
\end{aligned}
\]

A solução básica é \((\tfrac52,0,\tfrac32,0)\), viável, com \(z=5\). O custo reduzido de \(x_2\) é zero: variar \(x_2\) dentro da região viável não altera \(z\), sinal que merece investigação de soluções ótimas alternativas.

### Exercício 14

As linhas ainda contêm \(x_1\), uma variável básica, no lado direito de \(x_5\) e em \(z\). Substituindo \(x_1=4-x_3\):

\[
x_5=6-2x_2+3x_3
\]

e

\[
z=12+5x_2-3x_3.
\]

O dicionário correto é o exemplo central do capítulo.

### Exercício 15

1. Determinante zero significa que as colunas são linearmente dependentes; portanto, não formam uma base.
2. Sem inversa de \(B\), não podemos obter uma expressão única \(x_B=B^{-1}b-B^{-1}Nx_N\).
3. O estudante deve escolher outro conjunto de \(m\) colunas e verificar sua independência linear.

### Exercício 16

Há várias respostas possíveis. Uma resposta válida deve apresentar: modelo coerente; duas folgas; base invertível que não seja apenas a base das folgas; dicionário com somente não básicas à direita; solução básica e interpretação nas variáveis originais. A correção deve priorizar coerência, não coincidência com um único exemplo.

## Soluções do Nível 4

### Exercício 17

**A:** a solução básica \((x_1,x_3,x_4)=(0,4,2)\) é viável. O coeficiente de \(x_1\) em \(z\) é negativo, então não há direção de melhoria por \(x_1\) em maximização. O dicionário sugere ótimo atual em relação às não básicas disponíveis.

**B:** a solução básica \((0,0,5)\) é viável. O custo reduzido de \(x_1\) é positivo, mas \(x_3=-x_1\ge0\) impõe \(x_1\le0\). Não existe passo positivo: é o padrão de uma solução básica degenerada nessa direção.

**C:** a solução básica \((0,4,2)\) é viável. \(x_1\) melhora \(z\), e nenhuma linha básica limita seu crescimento, pois ambas aumentam com \(x_1\). O comportamento indica ilimitabilidade nessa direção.

### Exercício 18

Para \(x_1\), com \(x_2=0\):

\[
x_1\le5,qquad 2x_1\le4\Rightarrow x_1\le2.
\]

O ganho é \(4(2)=8\), levando \(z\) de 6 a 14.

Para \(x_2\), com \(x_1=0\):

\[
2x_2\le5\Rightarrow x_2\le2{,}5,
\qquad
x_2\le4.
\]

O ganho é \(3(2{,}5)=7{,}5\), levando \(z\) a \(13{,}5\). Neste caso, escolher \(x_1\) produz o maior ganho. A alegação do segundo estudante era possível em princípio, mas não se confirma nesta instância.

### Exercício 19

- **Algebricamente:** a não básica crescente deve ser isolada na equação da básica que chegou a zero; os papéis são trocados.
- **Matricialmente:** a coluna da entrante substitui a coluna da sainte em \(B\).
- **Geometricamente:** o movimento chega a um vértice adjacente, onde uma nova restrição se torna ativa.

O pivoteamento é a operação que realiza essas três descrições simultaneamente.

### Exercício 20

Não. O mesmo vetor pode aparecer em contextos diferentes e, em casos degenerados, pode estar associado a mais de uma base. Para reconstruir o dicionário, precisamos conhecer as equações \(A,b\), a função objetivo \(c\) e a base — ou, equivalentemente, a partição ordenada em \(B,N,c_B,c_N\).

---

## 15. Encerramento do capítulo

Um dicionário é a ponte entre a definição de solução básica e o movimento do Simplex. Ele transforma uma escolha de base em uma representação capaz de responder três perguntas fundamentais:

1. **Onde estamos?** — nos termos constantes e na solução obtida com \(x_N=0\);
2. **Podemos melhorar?** — nos custos reduzidos da linha de \(z\);
3. **Até onde podemos ir sem perder viabilidade?** — nas linhas das variáveis básicas.

Se essas três leituras estiverem claras, o pivoteamento deixa de parecer uma receita arbitrária. A variável entrante representa a direção escolhida; a variável sainte representa o primeiro limite atingido; o novo dicionário representa a mesma região viável vista a partir de uma nova base.

O próximo capítulo poderá então estudar o Simplex como raciocínio de melhoria sucessiva, e não como uma sequência de operações sem significado.
