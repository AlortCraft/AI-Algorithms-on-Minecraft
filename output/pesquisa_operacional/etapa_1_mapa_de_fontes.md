# Etapa 1 — Mapa de fontes de Pesquisa Operacional

Data da análise: 9 de agosto de 2026  
Fonte principal: portal **Pesquisa Operacional — UFPB**, Prof. Teobaldo Bulhões  
Escopo prioritário: dicionários, Simplex, cobertura por vértices, atribuição, cobertura máxima, mochila e bin packing.

## 1. Critério de leitura

O portal foi tratado como um conjunto de fontes complementares, não como uma sequência de páginas independentes. Foram cruzados:

- videoaulas e transcrições do YouTube;
- slides de Método Gráfico, Forma Padrão e Simplex;
- listas e resoluções de Soluções Básicas e Simplex;
- lista de modelagem inteira, sua resolução comentada e a lista-base do Prof. Marcone;
- notebooks teóricos de Atribuição e Cobertura Máxima;
- páginas e notebooks das aulas práticas, com leitura aprofundada das práticas relacionadas aos conteúdos prioritários;
- bibliografia indicada no portal.

As transcrições automáticas foram usadas como apoio para recuperar a explicação oral, mas equações, sinais e índices foram conferidos nos slides, PDFs ou notebooks. Isso é essencial porque a transcrição contém erros pontuais de reconhecimento.

## 2. Arquitetura do material do curso

### 2.1 Aulas teóricas do portal

O portal organiza o curso na seguinte sequência:

1. sintaxe de Programação Linear;
2. quantificador universal e somatórios;
3. transporte;
4. fluxo em redes — introdução e modelo geral;
5. método gráfico;
6. forma padrão;
7. soluções básicas;
8. dicionários;
9. Simplex;
10. cobertura por vértices;
11. atribuição;
12. cobertura máxima;
13. mochila e bin packing;
14. Branch and Bound;
15. caixeiro viajante.

Para a apostila solicitada, os itens 5 a 13 formam o corpus central. Os itens anteriores entram apenas como pré-requisitos de linguagem e modelagem; Branch and Bound e Caixeiro Viajante ficam fora do escopo principal.

### 2.2 Aulas práticas

| Prática | Tema declarado | Relação com a apostila |
|---|---|---|
| 1 | Mix de produção | Pré-requisito de modelagem linear; não central. |
| 2 | Fluxo em redes | Fora do escopo principal; útil como antecedente da atribuição. |
| 3 | Programação Linear Inteira | Ponte geral entre PL e PLI. |
| 4 | Atribuição de tarefas | A solução disponível trata, na verdade, de destinação de produtos a fábricas; é uma extensão de atribuição/alocação com capacidade. |
| 5 | Localização de facilidades | Modela cobertura total com número mínimo de UPAs; serve para contrastar com Cobertura Máxima. |
| 6 | Bin Packing | Transfere a estrutura de bin packing para agendamento de provas. |
| 7 | Caixeiro Viajante | Fora do escopo solicitado. |

### 2.3 Listas de exercícios

- **Soluções Básicas:** uma instância completa, do desenho da região viável até a enumeração das bases e a correspondência entre soluções básicas viáveis e vértices.
- **Simplex:** três exercícios que cobrem maximização, minimização e problema ilimitado, com resolução por dicionários.
- **Modelagem com PLI:** remete aos exercícios 1, 5, 6, 7, 9, 11, 13, 14 e 17 da lista do Prof. Marcone; a resolução comentada trabalha custos fixos, padrões de corte, dimensionamento de equipe, escalas, múltiplas mochilas e localização capacitada.

## 3. Mapa detalhado por núcleo conceitual

## 3.1 Método gráfico — pré-requisito geométrico

**Fontes**

- videoaula 07 — Método Gráfico;
- slides `3-MetodoGrafico.pdf`.

**Conceitos apresentados**

- solução como ponto no espaço das variáveis;
- região viável como interseção de semiespaços;
- restrições ativas;
- pontos extremos/vértices;
- curvas de nível e vetor gradiente da função objetivo;
- solução ótima em vértice;
- múltiplas soluções ótimas;
- problema ilimitado e problema inviável;
- limite didático do método gráfico a duas variáveis.

**Exemplo principal**

Mix de produção de portas de madeira e alumínio:

\[
\max 4x_{mad}+6x_{al}
\]

com três recursos: corte, montagem e acabamento. Os vértices avaliados são \((0,0)\), \((0,6)\), \((7,0)\), \((3{,}2,4{,}8)\) e \((6,2)\); o ótimo é \((3{,}2,4{,}8)\), com valor \(41{,}6\).

**Notação e abordagem**

O professor alterna a escrita da função objetivo como \(f(x)\) ou \(z\). A exposição parte da geometria e usa a “última curva de nível que toca a região viável” para construir a intuição do ótimo.

**Relação com outros conteúdos**

É a base visual para entender por que soluções básicas viáveis correspondem a vértices e por que o Simplex se move de vértice em vértice.

**Lacuna a preencher na apostila**

Os slides anunciam resultados geométricos, mas não desenvolvem plenamente a ponte entre restrições ativas, escolha de base e dicionário. Essa ponte deverá ser construída em prosa.

## 3.2 Forma padrão — pré-requisito algébrico

**Fontes**

- videoaula 08 — Forma Padrão;
- slides `4-FormaPadrão.pdf`.

**Conceitos apresentados**

- formas cartesiana, matricial e vetorial;
- forma padrão do curso:

\[
\max c^Tx \quad \text{s.a. } Ax=b,\;x\ge 0;
\]

- inclusão de variáveis de folga em restrições \(\le\);
- subtração de variáveis de excesso em restrições \(\ge\);
- substituição de variável não positiva;
- decomposição de variável livre em diferença de duas variáveis não negativas;
- poliedro, convexidade, hiperplanos e semiespaços;
- hipótese \(m\le n\) após remoção de linhas redundantes;
- preparação para soluções básicas.

**Notação e abordagem**

\(A\in\mathbb{R}^{m\times n}\), \(x,c\in\mathbb{R}^n\) e \(b\in\mathbb{R}^m\). A variável de folga mede recurso não utilizado; a transformação produz um problema equivalente, embora não literalmente idêntico ao original.

**Relação com outros conteúdos**

Sem a forma padrão, não há uma definição uniforme de base, solução básica, dicionário ou pivoteamento.

**Lacunas**

- A equivalência entre o modelo original e o transformado merece um exemplo de ida e volta entre soluções.
- O efeito de uma variável de excesso sobre uma base inicial viável não é desenvolvido nessa etapa e reaparece como dificuldade de inicialização no Simplex.

## 3.3 Soluções básicas e soluções básicas viáveis

**Fontes**

- videoaula 09 — Soluções Básicas;
- seção correspondente dos slides de Forma Padrão;
- lista e resolução de Soluções Básicas.

**Conceitos apresentados**

- escolha de \(m\) colunas linearmente independentes de \(A\), quando \(A\) tem \(m\) linhas e \(n\) colunas;
- matriz básica \(B\), vetor de variáveis básicas \(x_B\) e variáveis não básicas;
- fixação de \(x_N=0\);
- resolução de \(Bx_B=b\), isto é, \(x_B=B^{-1}b\);
- base como matriz quadrada invertível;
- solução básica viável quando todos os componentes são não negativos;
- solução básica inviável quando alguma variável básica é negativa;
- correspondência solução básica viável ↔ vértice;
- inviabilidade de enumerar todas as bases em instâncias grandes.

**Exemplo principal**

\[
\max 3x_1+5x_2
\]

com \(x_1\le4\), \(x_2\le6\), \(3x_1+2x_2\le18\), convertido com \(x_3,x_4,x_5\). A lista enumera bases viáveis e inviáveis e associa as cinco soluções básicas viáveis aos cinco vértices da região viável.

**Abordagem oral importante**

O professor usa Álgebra Linear de modo operacional: três vetores linearmente independentes de \(\mathbb{R}^3\) geram qualquer vetor de \(\mathbb{R}^3\). Esse é o motivo, e não uma mera regra, para selecionar exatamente \(m\) colunas.

**Lacunas e cautelas**

- A resolução da lista omite visualmente um dos zeros no vetor \(c\); o vetor correto tem cinco componentes: \((3,5,0,0,0)^T\).
- Degenerescência, na qual bases distintas podem corresponder ao mesmo vértice, só aparece depois nos materiais de Simplex.

## 3.4 Dicionários do Simplex

**Fonte principal**

- videoaula 10 — Dicionários.

**Conceitos apresentados**

- dicionário como reescrita em que variáveis básicas ficam isoladas à esquerda;
- constantes e variáveis não básicas aparecem à direita;
- linha da função objetivo escrita apenas com variáveis não básicas;
- decomposição matricial

\[
Bx_B+Nx_N=b;
\]

- isolamento

\[
x_B=B^{-1}b-B^{-1}Nx_N;
\]

- substituição na função objetivo:

\[
z=c_B^TB^{-1}b+\left(c_N^T-c_B^TB^{-1}N\right)x_N;
\]

- obtenção da solução básica ao zerar todas as variáveis não básicas;
- leitura de viabilidade pelos termos constantes das linhas básicas;
- leitura de possibilidades de melhoria pelos coeficientes da função objetivo.

**Exemplo do professor**

Para a base \(\{x_1,x_4,x_5\}\), com não básicas \(x_2,x_3\):

\[
\begin{aligned}
x_1 &= 4-x_3,\\
x_4 &= 6-x_2,\\
x_5 &= 6-2x_2+3x_3,\\
z &= 12+5x_2-3x_3.
\end{aligned}
\]

Zerando \(x_2=x_3=0\), obtém-se \((x_1,x_2,x_3,x_4,x_5)=(4,0,0,6,6)\) e \(z=12\).

**Conexões**

- O dicionário codifica simultaneamente uma base, uma solução básica e as direções locais de mudança.
- O Simplex é apresentado como passagem de um dicionário para outro.

**Lacunas a preencher**

- A videoaula é longa e a derivação matricial pode esconder a interpretação. A apostila deve alternar a forma compacta com a substituição linha a linha.
- É preciso explicitar que um coeficiente positivo na linha de \(z\), em maximização e na convenção usada, indica potencial de melhoria apenas enquanto a viabilidade puder ser preservada.

## 3.5 Método Simplex

**Fontes**

- videoaula 11 — Simplex;
- slides `Simplex.pdf`;
- lista e resolução de Simplex.

**Ideia central**

O método evita enumerar todas as bases. Parte de uma solução básica viável, troca uma variável por vez, preserva viabilidade e busca uma função objetivo não pior. Geometricamente, move-se entre vértices adjacentes.

**Exemplo completo das aulas**

\[
\max z=3x_1+5x_2
\]

\[
x_1\le4,\quad 2x_2\le12,\quad 3x_1+2x_2\le18,\quad x_1,x_2\ge0.
\]

Dicionário inicial:

\[
\begin{aligned}
x_3&=4-x_1,\\
x_4&=12-2x_2,\\
x_5&=18-3x_1-2x_2,\\
z&=3x_1+5x_2.
\end{aligned}
\]

Solução inicial: \((x_1,x_2,x_3,x_4,x_5)=(0,0,4,12,18)\), \(z=0\).

Primeira troca: \(x_2\) entra por ter o maior custo reduzido positivo. As linhas de \(x_4\) e \(x_5\) limitam seu crescimento; o teste da razão mínima dá \(12/2=6\) e \(18/2=9\), logo \(x_4\) sai. A nova solução é \((0,6,4,0,6)\), com \(z=30\).

Segunda troca: \(x_1\) entra. As razões relevantes são \(4/1=4\) e \(6/3=2\), então \(x_5\) sai. O dicionário final representa \((2,6,2,0,0)\), com \(z=36\), e sua linha objetivo é

\[
z=36-\frac32x_4-x_5.
\]

Como \(x_4,x_5\ge0\), nenhuma delas pode aumentar \(z\); a solução é ótima.

**Critérios na convenção do curso**

- maximização: ótimo quando todos os custos reduzidos são não positivos;
- minimização: ótimo quando todos os custos reduzidos são não negativos;
- variável entrante: qualquer custo reduzido com sinal de melhoria; o professor usa a escolha gulosa do maior coeficiente positivo nos primeiros exemplos;
- variável sainte: a variável básica que primeiro atingiria zero ao aumentar a entrante.

**Situações especiais presentes nas fontes**

- **ilimitado:** há direção de melhoria e nenhuma linha básica limita o crescimento da entrante;
- **degenerescência:** a variável entrante só pode crescer zero, não melhorando o objetivo;
- **ciclagem:** dicionários podem se repetir em sequência;
- **inicialização:** a base de folgas pode não ser viável;
- **múltiplos ótimos:** aparecem geometricamente no Método Gráfico e computacionalmente no notebook de Cobertura Máxima, mas não são desenvolvidos como critério completo no dicionário.

**Cautelas de fonte**

- A transcrição automática diz “problema limitado” em um trecho cujo raciocínio e slides demonstram “problema ilimitado”.
- O arquivo de slides possui metadados/título de documento incompatíveis com o conteúdo, mas as páginas internas identificam corretamente a disciplina e o professor.
- A escolha do maior custo reduzido é uma regra de seleção usada no exemplo, não garantia de maior ganho total, pois o passo admissível também importa.

## 3.6 Cobertura por Vértices

**Fonte**

- videoaula 12 — Problema da Cobertura por Vértices.

**Situação concreta**

Interseções de corredores de um museu são vértices; corredores são arestas; um guarda em uma interseção cobre todos os corredores incidentes. Deseja-se cobrir todos os corredores com o menor número de guardas.

**Construção do modelo**

- conjunto de vértices \(V=\{1,\ldots,n\}\);
- conjunto de arestas \(E\subseteq V\times V\);
- \(x_j=1\) se o vértice \(j\) for escolhido;
- objetivo: \(\min\sum_{j\in V}x_j\);
- para cada aresta \((i,j)\), ao menos uma extremidade deve ser escolhida:

\[
x_i+x_j\ge1;
\]

- \(x_j\in\{0,1\}\).

**Exemplo**

Grafo de 7 vértices e 11 arestas, com uma solução candidata de 5 vértices. Cobertura múltipla de uma aresta é permitida.

**Abordagem distintiva**

O professor introduz PLI como a mesma linguagem linear acrescida da capacidade de impor indivisibilidade. A heurística de modelagem é transformar perguntas de seleção — “escolher este vértice?” — em variáveis binárias.

**Lacunas**

- A aula não explora a versão ponderada \(\min\sum c_jx_j\), útil para generalizar “quantidade/custo”.
- Não há lista específica do portal para Vertex Cover; a apostila precisará criar a progressão guiado → parcialmente guiado → independente.

## 3.7 Problema da Atribuição

**Fontes**

- videoaula 13 — Problema da Atribuição;
- notebook `Problema_da_Atribuicao.ipynb`;
- aula prática 4 e sua solução, como extensão de alocação com capacidade.

**Construção central**

- conjuntos \(F\) de funcionários e \(T\) de tarefas, com \(|F|=|T|\) na versão ensinada;
- parâmetro \(a_{ij}\): aptidão do funcionário \(i\) para a tarefa \(j\);
- variável \(x_{ij}=1\) se \(i\) recebe \(j\);
- objetivo:

\[
\max\sum_{i\in F}\sum_{j\in T}a_{ij}x_{ij};
\]

- uma pessoa por tarefa:

\[
\sum_{i\in F}x_{ij}=1 \quad \forall j\in T;
\]

- uma tarefa por pessoa:

\[
\sum_{j\in T}x_{ij}=1 \quad \forall i\in F;
\]

- \(x_{ij}\in\{0,1\}\).

**Exemplos que não devem ser misturados**

- A videoaula usa a matriz \((3,4,6;\ 7,1,4;\ 6,8,9)\) e compara atribuições de valores 13, 20 e 21.
- O notebook usa \((5,4,3;\ 8,7,6;\ 3,7,5)\), obtendo ótimo 18, e depois uma instância \(4\times4\) com ótimo 30.

São exemplos diferentes do mesmo modelo; a apostila deverá identificá-los separadamente.

**Contribuição do notebook**

O notebook mostra a implementação em `python-mip`, primeiro de forma expandida e depois com uma função genérica. Reforça a correspondência entre matriz de parâmetros e matriz de variáveis.

**Contribuição da prática 4**

A página chama-se “Atribuição de tarefas”, mas a solução trata de destinar quatro produtos a três fábricas. A primeira versão permite divisão e usa variáveis inteiras de quantidade; a segunda proíbe divisão e usa binárias, acrescentando capacidade e a exigência de que cada fábrica receba ao menos um produto. É uma boa extensão após o modelo clássico, não uma fonte para a primeira definição.

**Lacunas**

- A diferença entre “exatamente uma”, “no máximo uma” e capacidade maior que um deve ser explicitada.
- A hipótese \(|F|=|T|\) é simplificadora; casos não balanceados podem ser mencionados como complemento, sem atribuí-los à aula.

## 3.8 Cobertura Máxima

**Fontes**

- videoaula 14 — Problema da Cobertura Máxima;
- notebook `Problema_Cobertura_Maxima.ipynb`;
- prática 5, usada como contraste com cobertura total mínima.

**Situação concreta**

Há locais candidatos para instalar facilidades, clientes com demandas e um raio de atendimento. Só é possível abrir \(P\) facilidades; deseja-se maximizar a demanda coberta, sem contar duas vezes um cliente atendido por mais de uma facilidade.

**Modelo geral**

- \(L\): locais candidatos;
- \(C\): clientes;
- \(h_j>0\): demanda do cliente \(j\);
- \(d_{ij}\): distância entre local \(i\) e cliente \(j\);
- \(R\): raio de cobertura;
- \(x_i\): local \(i\) selecionado;
- \(y_j\): cliente \(j\) coberto;
- objetivo:

\[
\max\sum_{j\in C}h_jy_j;
\]

- orçamento:

\[
\sum_{i\in L}x_i\le P
\]

ou \(=P\) quando o enunciado exige exatamente \(P\);

- ligação escolha–cobertura:

\[
y_j\le\sum_{i\in L:\ d_{ij}\le R}x_i \quad \forall j\in C;
\]

- \(x_i,y_j\in\{0,1\}\).

**Explicação oral decisiva**

A restrição de ligação apenas permite \(y_j=1\) quando existe uma facilidade aberta que cobre \(j\). Como \(h_j>0\) e o objetivo maximiza, o próprio objetivo força \(y_j=1\) quando isso é permitido. Usar igualdade seria errado quando duas facilidades abertas cobrem o mesmo cliente, pois o lado direito poderia valer 2.

**Exemplos**

- Videoaula: instância maior com 7 locais, 30 clientes, \(P=3\); os locais 3, 6 e 7 cobrem demanda 2207 para \(R=300\) e 4279 para \(R=500\).
- Notebook: 4 terrenos, 10 bairros, 2 escolas e raio 3; locais 2 e 3 cobrem 7 bairros. O notebook também registra que podem existir duas soluções ótimas diferentes.

**Contraste com a prática 5**

A prática 5 exige que todo distrito esteja a distância máxima \(R\) de alguma UPA e minimiza o número de UPAs:

\[
\min\sum_i x_i \quad\text{s.a.}\quad
\sum_{j:d_{ij}\le R}x_j\ge1\quad\forall i.
\]

Trata-se de localização por cobertura total mínima, não de Cobertura Máxima.

**Erro material identificado**

Na solução da prática 5, a seção “Resolução para \(R=40\)” executa novamente `R = 20` e repete a solução de 9 UPAs. Esse resultado não deve ser usado como solução para \(R=40\).

## 3.9 Problema da Mochila

**Fonte**

- primeira parte da videoaula 15 — Problema da Mochila / Bin Packing;
- questão 14 da lista-base e resolução de Modelagem PLI, como variante de múltiplas mochilas.

**Exemplo da aula**

Quatro itens com valores \((10,20,25,8)\), pesos \((5,3,8,4)\) e capacidade \(C=13\). Escolher itens 1 e 3 dá peso 13 e valor 35; escolher 3 e 4 dá peso 12 e valor 33.

**Modelo 0–1**

- conjunto de itens \(I\);
- valor \(v_j>0\), peso \(w_j>0\), capacidade \(C>0\);
- \(x_j=1\) se o item \(j\) for levado;
- objetivo:

\[
\max\sum_{j\in I}v_jx_j;
\]

- capacidade:

\[
\sum_{j\in I}w_jx_j\le C;
\]

- \(x_j\in\{0,1\}\).

**Relações**

- O modelo seleciona um subconjunto; nem todos os itens precisam ser levados.
- A resolução da lista de PLI inclui a variante de múltiplas mochilas, com \(x_{ij}\) indicando se o objeto \(j\) vai para a mochila \(i\).

**Lacunas**

- A aula menciona programação dinâmica como possível método mais eficiente, mas não a desenvolve.
- A afirmação “escolher maior valor individual” precisa ser refutada por exemplos construídos; a aula concreta favorece isso, mas não sistematiza razões valor/peso, empates e contraprovas.

## 3.10 Bin Packing

**Fontes**

- segunda parte da videoaula 15 — Mochila / Bin Packing;
- prática 6 e solução em notebook.

**Situação e modelo da aula**

Todos os itens devem ser acondicionados em recipientes idênticos de capacidade \(C\), minimizando o número usado. Adota-se um conjunto candidato \(K\) de recipientes, com \(|K|=|I|\), pois um recipiente por item é um limite superior quando \(w_j\le C\).

- \(x_{jk}=1\) se o item \(j\) for colocado no recipiente \(k\);
- \(y_k=1\) se o recipiente \(k\) for usado;
- objetivo:

\[
\min\sum_{k\in K}y_k;
\]

- cada item exatamente uma vez:

\[
\sum_{k\in K}x_{jk}=1\quad\forall j\in I;
\]

- capacidade e ligação:

\[
\sum_{j\in I}w_jx_{jk}\le Cy_k\quad\forall k\in K;
\]

- \(x_{jk},y_k\in\{0,1\}\).

**Exemplo da aula**

Itens de pesos 5, 6 e 7, recipientes de capacidade 10. A instância exige três recipientes e serve para introduzir a estrutura, embora seja trivial como otimização.

**Contribuição da prática 6**

O notebook reconhece a mesma estrutura em agendamento de provas. Disciplinas são “itens”, dias são “recipientes” e conflitos de alunos substituem a capacidade numérica. O modelo encontra três dias: \(\{E,F\}\), \(\{A,D\}\) e \(\{B,C\}\). Isso demonstra que a estrutura ativação–atribuição é transferível para além de caixas físicas.

**Lacunas**

- A aula distingue bin packing 1D, 2D e 3D, mas só modela 1D.
- A ligação \(Cy_k\) deve ser ensinada com o contramodelo: sem ela, o solver pode atribuir itens a recipientes com \(y_k=0\) e declarar custo zero.

## 4. Repetições produtivas e diferenças entre fontes

| Conceito | Onde se repete | Função de cada fonte |
|---|---|---|
| Forma padrão e folgas | videoaula 08, slides de Forma Padrão, aula 09, Dicionários, Simplex, listas | A primeira fonte define; as seguintes usam. A apostila deve explicar uma vez e recuperar apenas o necessário. |
| Base e solução básica | videoaula 09, slides, lista resolvida, Dicionários, Simplex | A aula 09 fornece o raciocínio; a lista dá enumeração; Dicionários dá representação; Simplex dá movimento entre bases. |
| Exemplo \(3x_1+5x_2\) | Soluções Básicas, Dicionários e Simplex | Os valores de RHS são escritos de formas equivalentes em trechos distintos; a apostila deve fixar uma instância por capítulo e avisar quando houver mudança. |
| Atribuição | videoaula, notebook teórico, prática 4 | Vídeo deriva o modelo; notebook implementa outra instância; prática acrescenta capacidade e divisão/não divisão. |
| Cobertura | Vertex Cover, Cobertura Máxima, notebook de Cobertura Máxima, prática 5 | Têm verbos parecidos, mas decisões e objetivos diferentes. Devem ser comparados somente depois do estudo individual. |
| Ativação e ligação | Cobertura Máxima, Bin Packing, localização capacitada, prática 6 | Padrão comum: uma variável indica decisão principal e outra só pode assumir 1 se a primeira decisão a habilitar. |
| Múltiplos ótimos | Método Gráfico, notebook de Cobertura Máxima | Primeiro como aresta inteira ótima; depois como soluções discretas distintas de mesmo valor. |
| Problema ilimitado | Método Gráfico, slides/lista de Simplex | A geometria mostra a direção infinita; o dicionário mostra ausência de limitante para a variável entrante. |

## 5. Registro de notação a preservar

| Símbolo | Uso predominante no material |
|---|---|
| \(A,b,c,x\) | forma matricial de PL; \(Ax=b\), \(c^Tx\). |
| \(B,N\) | matrizes de colunas básicas e não básicas. |
| \(x_B,x_N\) | vetores de variáveis básicas e não básicas. |
| \(z\) | valor/função objetivo nos dicionários. |
| \(V,E\) | vértices e arestas de um grafo. |
| \(F,T\) | funcionários e tarefas no problema da atribuição. |
| \(L,C\) | locais candidatos e clientes na Cobertura Máxima. |
| \(x_i\) | seleção de vértice/local/item, conforme o modelo. |
| \(x_{ij}\) | atribuição de agente a tarefa ou de item a recipiente, com significado declarado localmente. |
| \(y_j\) | cliente coberto na Cobertura Máxima. |
| \(y_k\) | recipiente ativo em Bin Packing. |

A apostila deverá declarar o significado de cada símbolo em cada capítulo; não se deve assumir que um \(x_i\) possui o mesmo significado entre modelos.

## 6. Lacunas pedagógicas globais

1. **Dicionário como objeto semântico.** As fontes mostram a álgebra, mas o material final deverá reforçar que cada linha informa como uma variável básica reage à mudança das não básicas.
2. **Pivoteamento detalhado.** Os slides usam muitas páginas incrementais; em formato de capítulo, as substituições precisam aparecer em sequência legível, sem saltos.
3. **Condição de sinal.** A regra muda entre maximização e minimização e depende da convenção do dicionário; isso precisa ser fixado explicitamente.
4. **Múltiplos ótimos no dicionário.** As fontes mostram o fenômeno, mas não conectam plenamente custo reduzido zero, direção admissível e outra solução ótima.
5. **Inviabilidade.** Aparece em geometria e em soluções básicas inviáveis, mas não há desenvolvimento completo de Fase I; convém limitar a apostila ao reconhecimento, salvo necessidade posterior dos exercícios.
6. **Exercícios específicos de modelagem.** Vertex Cover, Cobertura Máxima e Mochila não possuem listas próprias no portal. Será necessário criar exercícios novos, claramente indicados como material complementar.
7. **Reconhecimento entre modelos.** O portal ensina modelos em sequência; a capacidade de identificar um modelo em enunciado misto deve ser construída pela apostila.
8. **Validação de modelos.** A fala do professor insiste corretamente que o solver não entende semântica. A apostila deverá sistematizar testes de soluções candidatas e contramodelos sem cada grupo de restrições.

## 7. Inconsistências e erros de fonte que não devem ser propagados

- transcrições automáticas confundem índices, sinais e palavras como “limitado/ilimitado”; equações foram conferidas nas fontes visuais;
- a matriz/vetor \(c\) na resolução de Soluções Básicas perde um zero na diagramação; o modelo tem cinco variáveis;
- o vídeo e o notebook de Atribuição usam matrizes diferentes;
- a página da prática 4 anuncia “Atribuição de tarefas”, mas a solução é “Destinação de Produtos a Fábricas”;
- a prática 5 é cobertura total mínima, não Cobertura Máxima;
- a célula “\(R=40\)” da prática 5 executa \(R=20\);
- o notebook de Cobertura Máxima usa igualdade para selecionar exatamente \(p\) locais, enquanto a videoaula admite \(\le P\) quando o limite é “até \(P\)”; a escolha depende do enunciado;
- o PDF de Simplex tem metadados de documento alheios ao conteúdo, embora as páginas estejam corretas.

## 8. Bibliografia indicada pelo curso

- Arenales et al., *Pesquisa Operacional*, 2ª ed., Elsevier, 2015.
- Chvátal, *Linear Programming*, W. H. Freeman, 1983.
- Hillier, Lieberman e Griesi, *Introdução à Pesquisa Operacional*, 9ª ed., AMGH, 2013.
- Taha e Scarpel, *Pesquisa Operacional*, 8ª ed., Pearson, 2008.

Essas obras são referências de apoio. O conteúdo da apostila deverá continuar distinguindo o que vem diretamente do curso e o que for complementação pedagógica.

## 9. Conclusão da Etapa 1

O corpus é suficiente para sustentar uma apostila aprofundada sobre os sete temas prioritários. A sequência do professor é conceitualmente coerente: geometria → forma padrão → soluções básicas → dicionários → Simplex → PLI e modelos clássicos. O principal trabalho autoral futuro não será acrescentar tópicos, mas reconstruir as passagens implícitas entre esses materiais, preservar os exemplos sem misturá-los e criar uma prática graduada onde o portal oferece apenas uma demonstração ou um notebook resolvido.

