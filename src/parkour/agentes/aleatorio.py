"""Politica aleatoria: a referencia contra a qual tudo e comparado.

Etapa 2 do plano do PDF (pag. 6). Ela nao aprende nada, e esse e o ponto: sem
saber o que um agente que nao aprendeu consegue fazer, dizer que outro
"aprendeu" nao significa nada. A pergunta da pag. 3 e literalmente "como medir
se um agente treinado e realmente melhor?".
"""

import random

from .base import Agente


class AgenteAleatorio(Agente):
    nome = 'aleatorio'

    def __init__(self, quantidade_acoes, semente=None):
        self.quantidade_acoes = quantidade_acoes
        self.sorteador = random.Random(semente)

    def escolher(self, estado, ambiente=None):
        return self.sorteador.randrange(self.quantidade_acoes)
