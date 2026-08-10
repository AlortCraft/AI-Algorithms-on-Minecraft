# Etapa 2 — Estrutura pedagógica proposta

Esta proposta mantém a espinha dorsal do curso, mas reorganiza alguns blocos para que cada capítulo tenha um objetivo de aprendizagem completo e para que as comparações entre modelos ocorram somente depois da construção individual de cada formulação.

## 1. Ordem de estudo recomendada

1. **Da região viável à forma padrão**
2. **Bases, soluções básicas e vértices**
3. **Dicionários: a linguagem algébrica do Simplex**
4. **Simplex: melhoria sucessiva entre soluções básicas viáveis**
5. **Simplex em situações especiais e consolidação**
6. **Da Programação Linear à Programação Linear Inteira**
7. **Cobertura por Vértices**
8. **Problema da Atribuição**
9. **Cobertura Máxima**
10. **Problema da Mochila**
11. **Bin Packing**
12. **Comparação, reconhecimento e modelagem mista**
13. **Soluções comentadas e caderno de erros**

## 2. Alterações em relação à sequência do professor

A ordem conceitual principal foi preservada. As alterações são:

- **Método Gráfico e Forma Padrão** serão reunidos no capítulo inicial, porque funcionam como duas perspectivas do mesmo ponto de partida: geometria e álgebra.
- **Simplex** será dividido em dois capítulos: um para construir e executar o algoritmo; outro para situações especiais, consolidação e exercícios. Isso evita interromper a primeira compreensão do pivoteamento.
- Será criado um capítulo curto e explícito de **transição PL → PLI**, embora a aula de Vertex Cover faça essa passagem oralmente. Ele reunirá integridade, binariedade e padrões de modelagem.
- As comparações Cobertura por Vértices × Cobertura Máxima, Mochila × Bin Packing e Atribuição × Bin Packing serão concentradas após os capítulos individuais, conforme solicitado.
- Soluções comentadas ficarão separadas dos enunciados, formando um capítulo/parte de consulta posterior.

## 3. Índice detalhado da apostila

## Capítulo 1 — Da região viável à forma padrão

**Objetivo de aprendizagem:** interpretar geometricamente um PL de duas variáveis e convertê-lo para a forma padrão usada pelo curso, entendendo o papel de cada transformação.

1. O que uma solução de um PL representa
2. Restrições como regiões do espaço
3. Região viável, fronteira e restrições ativas
4. Curvas de nível e direção de melhoria
5. Por que vértices importam
6. Múltiplos ótimos, ilimitado e inviável — reconhecimento geométrico
7. Da forma cartesiana à forma matricial
8. A forma padrão \(\max c^Tx\), \(Ax=b\), \(x\ge0\)
9. Variáveis de folga e interpretação de recurso não utilizado
10. Restrições \(\ge\), variáveis não positivas e variáveis livres
11. Exemplo guiado: mix de produção
12. Checkpoint de compreensão
13. Exercícios graduados
14. Revisão rápida

## Capítulo 2 — Bases, soluções básicas e vértices

**Objetivo de aprendizagem:** construir uma solução básica a partir de colunas de \(A\), testar sua viabilidade e explicar a correspondência com vértices.

1. Por que precisamos de uma descrição algébrica dos vértices
2. Revisão mínima de independência linear
3. Escolha de \(m\) colunas e formação de \(B\)
4. Variáveis básicas e não básicas
5. Por que fixamos \(x_N=0\)
6. Resolução de \(Bx_B=b\)
7. Solução básica viável e inviável
8. O que significa uma variável básica negativa
9. Soluções básicas viáveis e pontos extremos
10. Exemplo guiado completo da lista
11. Exemplo parcialmente guiado: outra base
12. Por que enumerar todas as bases é ineficiente
13. Checkpoint
14. Exercícios graduados
15. Revisão rápida

## Capítulo 3 — Dicionários: a linguagem algébrica do Simplex

**Objetivo de aprendizagem:** ler, construir e interpretar um dicionário, extraindo dele base, solução, viabilidade e direções de melhoria.

1. O problema que o dicionário resolve
2. Estrutura de um dicionário
3. Partição \(A=[B\mid N]\)
4. Derivação de \(x_B=B^{-1}b-B^{-1}Nx_N\)
5. Derivação da linha da função objetivo
6. Forma matricial × substituição linha a linha
7. Como obter a solução básica representada
8. Como verificar viabilidade
9. Como interpretar os termos constantes
10. Como interpretar os custos reduzidos
11. Exemplo guiado com a base \(\{x_1,x_4,x_5\}\)
12. Construção de um segundo dicionário
13. Erros comuns: misturar base, solução e valor objetivo
14. Checkpoint
15. Exercícios graduados
16. Revisão rápida

## Capítulo 4 — Simplex: melhoria sucessiva entre soluções básicas viáveis

**Objetivo de aprendizagem:** executar o Simplex por dicionários compreendendo por que cada variável entra ou sai e o que o pivoteamento significa.

1. Da enumeração ao movimento local
2. Estado atual: solução, base e valor de \(z\)
3. Existe uma direção de melhoria?
4. Escolha da variável entrante
5. Por que o maior custo reduzido é apenas uma regra possível
6. O que limita o crescimento da entrante
7. Derivação do teste da razão mínima
8. Por que uma variável precisa sair
9. A equação-pivô
10. Isolamento da variável entrante
11. Substituição nas demais linhas
12. Atualização da função objetivo
13. Extração da nova base e da nova solução
14. Exemplo totalmente guiado — primeira iteração
15. Exemplo parcialmente guiado — segunda iteração
16. Condição de otimalidade em maximização
17. Condição de otimalidade em minimização
18. Interpretação geométrica de cada pivô
19. Checkpoint
20. Exercícios graduados
21. Revisão rápida

## Capítulo 5 — Simplex: situações especiais e consolidação

**Objetivo de aprendizagem:** reconhecer nos dicionários os casos especiais presentes no curso e resolver problemas sem depender de um roteiro mecânico.

1. Problema ilimitado: direção de melhoria sem variável limitante
2. Degenerescência: passo de tamanho zero
3. Ciclagem: o risco de repetir dicionários
4. Múltiplas soluções ótimas: conexão geometria–álgebra
5. Inviabilidade e dificuldade de inicialização
6. Limite do escopo: o que o curso não desenvolve sobre Fase I
7. Exemplo resolvido de maximização
8. Exemplo parcialmente guiado de minimização
9. Exemplo de problema ilimitado da lista
10. Diagnóstico de dicionários com erros
11. Checkpoint cumulativo
12. Exercícios níveis 1–4
13. Revisão rápida do bloco de Simplex

## Capítulo 6 — Da Programação Linear à Programação Linear Inteira

**Objetivo de aprendizagem:** reconhecer decisões indivisíveis e escolher corretamente entre variáveis contínuas, inteiras e binárias.

1. O que muda quando a divisibilidade deixa de valer
2. Variáveis contínuas, inteiras e binárias
3. Perguntas sim/não como origem de variáveis binárias
4. Variáveis com um índice e com dois índices
5. Igualdade, “no máximo” e “pelo menos”
6. Padrão seleção
7. Padrão atribuição
8. Padrão ativação–ligação
9. O solver entende sintaxe, não o significado do enunciado
10. Como testar um modelo com soluções candidatas
11. Checkpoint
12. Exercícios curtos de escolha de domínio

## Capítulo 7 — Cobertura por Vértices

**Objetivo de aprendizagem:** derivar a formulação de Vertex Cover a partir do significado de cobrir uma aresta e justificar cada restrição.

1. Situação concreta: guardas em corredores de museu
2. Grafo, vértices e arestas
3. Quais decisões precisam ser tomadas?
4. Variável binária por vértice
5. Objetivo verbal: selecionar o menor número de vértices
6. Como uma aresta é coberta
7. Derivação de \(x_i+x_j\ge1\)
8. Teste dos quatro casos \((0,0),(0,1),(1,0),(1,1)\)
9. O que dá errado sem a restrição de uma aresta
10. Modelo completo da instância
11. Formulação geral com \(V\) e \(E\)
12. Variante ponderada — complemento identificado como tal
13. Exemplo parcialmente guiado
14. Reconhecimento de enunciados
15. Checkpoint
16. Exercícios níveis 1–4
17. Revisão rápida

## Capítulo 8 — Problema da Atribuição

**Objetivo de aprendizagem:** construir um modelo de correspondência um-para-um, entendendo a necessidade dos dois índices e das duas famílias de igualdades.

1. Situação concreta: funcionários e tarefas
2. Por que uma variável única por funcionário é insuficiente
3. Derivação de \(x_{ij}\)
4. Matriz de aptidões e matriz de decisões
5. Objetivo de maximizar aptidão total
6. Exatamente um funcionário por tarefa
7. Exatamente uma tarefa por funcionário
8. O que ocorre se retirarmos uma das famílias
9. Igualdade × no máximo um × capacidade
10. Teste manual de atribuições candidatas
11. Formulação geral
12. Implementação do notebook como leitura de modelo
13. Extensão: destinação a fábricas com capacidade
14. Exemplo parcialmente guiado
15. Reconhecimento de enunciados
16. Checkpoint
17. Exercícios níveis 1–4
18. Revisão rápida

## Capítulo 9 — Cobertura Máxima

**Objetivo de aprendizagem:** distinguir seleção de facilidades de contabilização de clientes cobertos e construir corretamente a restrição de ligação.

1. Situação concreta: escolas e bairros
2. Locais candidatos, clientes, demandas e raio
3. Duas decisões diferentes: abrir e contabilizar cobertura
4. Variáveis \(x_i\) e \(y_j\)
5. Objetivo de maximizar demanda coberta
6. Limite “até \(P\)” × exigência “exatamente \(P\)”
7. Quem pode cobrir o cliente \(j\)?
8. Derivação de \(y_j\le\sum_{i:d_{ij}\le R}x_i\)
9. Por que o objetivo força \(y_j=1\) quando permitido
10. Por que igualdade pode estar errada
11. Cobertura múltipla sem contagem duplicada
12. Teste manual da instância pequena
13. Formulação geral ponderada
14. Múltiplas soluções ótimas no notebook
15. Contraste com cobertura total mínima da prática 5
16. Reconhecimento de enunciados
17. Checkpoint
18. Exercícios níveis 1–4
19. Revisão rápida

## Capítulo 10 — Problema da Mochila

**Objetivo de aprendizagem:** modelar seleção sob capacidade limitada e justificar por que a função objetivo e a restrição de capacidade produzem o subconjunto desejado.

1. Situação concreta: quais itens levar
2. Peso, valor e capacidade
3. Decisão binária por item
4. Objetivo de maximizar valor total
5. Derivação da restrição de capacidade
6. Por que nem todo item precisa ser escolhido
7. Teste manual da instância de quatro itens
8. Por que maior valor individual não basta
9. Valor por peso: intuição útil, não solução universal da mochila 0–1
10. Formulação geral
11. Variante de múltiplas mochilas da lista — complemento
12. Reconhecimento de enunciados
13. Checkpoint
14. Exercícios níveis 1–4
15. Revisão rápida

## Capítulo 11 — Bin Packing

**Objetivo de aprendizagem:** representar simultaneamente a atribuição de itens e a ativação de recipientes, distinguindo Bin Packing de Mochila.

1. Situação concreta: todos os itens precisam ser empacotados
2. O que muda em relação à Mochila
3. Conjunto candidato de recipientes e limite superior
4. Variável \(x_{jk}\): onde cada item vai
5. Variável \(y_k\): quais recipientes são usados
6. Objetivo de minimizar recipientes ativos
7. Cada item em exatamente um recipiente
8. Capacidade de cada recipiente
9. Derivação da ligação \(\sum_jw_jx_{jk}\le Cy_k\)
10. Contramodelo sem a variável de ativação
11. Teste manual da instância pequena
12. Formulação geral
13. Transferência estrutural: agendamento de provas
14. Limites: 1D, 2D e 3D
15. Reconhecimento de enunciados
16. Checkpoint
17. Exercícios níveis 1–4
18. Revisão rápida

## Capítulo 12 — Comparação, reconhecimento e modelagem mista

**Objetivo de aprendizagem:** identificar a estrutura de um problema novo antes de escrever fórmulas e evitar confusões entre modelos parecidos.

1. Roteiro de leitura de enunciados
2. O que é decisão, parâmetro e consequência
3. Cobertura por Vértices × Cobertura Máxima
4. Cobertura Máxima × cobertura total mínima
5. Mochila × Bin Packing
6. Atribuição × Bin Packing
7. Padrões seleção, atribuição e ativação–ligação
8. Enunciados curtos de identificação
9. Falsos amigos: problemas semelhantes com modelos diferentes
10. Problemas mistos sem indicação do modelo
11. Checklist de validação
12. Revisão cumulativa

## Capítulo 13 — Soluções comentadas e caderno de erros

**Objetivo de aprendizagem:** conferir tentativas somente após resolução independente e transformar erros recorrentes em alvos de revisão.

1. Como usar as soluções comentadas
2. Soluções dos capítulos 1–2
3. Soluções dos capítulos 3–5
4. Soluções dos capítulos 6–9
5. Soluções dos capítulos 10–12
6. Classificação de erros: conceito, domínio, objetivo, restrição, sinal, pivô e interpretação
7. Registro pessoal de erros
8. Exercícios de recuperação direcionada

## 4. Padrão interno de cada capítulo

Cada capítulo seguirá, quando aplicável:

1. motivação e situação concreta;
2. intuição antes da notação;
3. construção do raciocínio;
4. formalização matemática comentada;
5. exemplo totalmente guiado;
6. checkpoint sem respostas imediatas;
7. exemplo parcialmente guiado;
8. exercício independente;
9. exercícios em quatro níveis;
10. revisão rápida posterior à explicação;
11. soluções comentadas em seção separada.

Nos capítulos de Simplex, o eixo será estado atual → direção de melhoria → limitação → troca de base → novo dicionário → interpretação. Nos capítulos de modelagem, o eixo será situação → decisões → variáveis → objetivo → restrições → teste manual → generalização.

## 5. Proposta de capítulo piloto

Recomenda-se usar o **Capítulo 3 — Dicionários: a linguagem algébrica do Simplex** como piloto. Ele testa simultaneamente:

- profundidade conceitual;
- conexão entre Álgebra Linear e interpretação;
- derivação matemática sem saltos;
- preservação da notação do professor;
- equilíbrio entre prosa, equações e exemplo;
- preparação direta para o capítulo de Simplex.

Nenhum capítulo foi redigido nesta etapa. A produção do capítulo piloto depende da aprovação desta estrutura.

