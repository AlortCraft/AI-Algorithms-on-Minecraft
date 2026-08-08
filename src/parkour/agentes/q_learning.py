"""Q-Learning tabular. Etapa 3 do plano do PDF.

A ideia inteira cabe numa linha, a equacao de Bellman:

    Q[s][a]  <-  Q[s][a] + alfa * ( r + gama * max_a' Q[s'][a']  -  Q[s][a] )

Em palavras: o valor de fazer a acao `a` no estado `s` deveria ser a
recompensa recebida agora mais o melhor valor possivel do estado seguinte. A
diferenca entre o que a tabela dizia e essa conta e o erro; `alfa` diz o
quanto corrigir de cada vez.

A tabela e uma lista de listas de Python puro, sem numpy: sao 3840 estados por
6 acoes, uns 23 mil numeros. Numpy so passa a valer a pena no DQN.

Exploracao: comeca sorteando quase sempre e vai confiando cada vez mais na
tabela. A pag. 2 do PDF chama isso de exploracao versus aproveitamento, e pede
que o grupo observe o que acontece com exploracao demais ou de menos - e por
isso que os tres numeros ficam no config.
"""

import json
import os
import random

from .base import Agente


class AgenteQLearning(Agente):
    nome = 'q_learning'

    def __init__(self, quantidade_estados, quantidade_acoes, parametros=None,
                 semente=None):
        parametros = parametros or {}
        self.quantidade_estados = quantidade_estados
        self.quantidade_acoes = quantidade_acoes

        self.taxa_aprendizado = parametros.get('taxa_aprendizado', 0.2)
        self.desconto = parametros.get('desconto', 0.97)
        self.exploracao = parametros.get('exploracao_inicial', 1.0)
        self.exploracao_final = parametros.get('exploracao_final', 0.05)
        self.decaimento = parametros.get('exploracao_decaimento', 0.999)

        self.sorteador = random.Random(semente)
        self.tabela = [[0.0] * quantidade_acoes for _ in range(quantidade_estados)]
        self.visitas = [0] * quantidade_estados

    # ------------------------------------------------------------------

    def escolher(self, estado, ambiente=None):
        if self.sorteador.random() < self.exploracao:
            return self.sorteador.randrange(self.quantidade_acoes)
        return self._melhor_acao(estado)

    def _melhor_acao(self, estado):
        valores = self.tabela[estado]
        melhor = max(valores)
        # Desempate sorteado: sem isso, no comeco (tabela toda zerada) o agente
        # escolheria sempre a acao 0 e nunca veria as outras.
        empatadas = [acao for acao, valor in enumerate(valores) if valor == melhor]
        if len(empatadas) == 1:
            return empatadas[0]
        return self.sorteador.choice(empatadas)

    def aprender(self, estado, acao, recompensa, proximo_estado, terminou):
        self.visitas[estado] += 1

        alvo = recompensa
        if not terminou:
            alvo += self.desconto * max(self.tabela[proximo_estado])

        erro = alvo - self.tabela[estado][acao]
        self.tabela[estado][acao] += self.taxa_aprendizado * erro

    def fim_de_episodio(self, episodio):
        self.exploracao = max(self.exploracao_final,
                              self.exploracao * self.decaimento)

    def modo_avaliacao(self):
        self.exploracao = 0.0

    # ------------------------------------------------------------------

    def salvar(self, caminho):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            json.dump({
                'agente': self.nome,
                'quantidade_estados': self.quantidade_estados,
                'quantidade_acoes': self.quantidade_acoes,
                'taxa_aprendizado': self.taxa_aprendizado,
                'desconto': self.desconto,
                'exploracao': self.exploracao,
                'tabela': self.tabela,
                'visitas': self.visitas,
            }, arquivo)

    def carregar(self, caminho):
        with open(caminho, encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
        if dados['quantidade_estados'] != self.quantidade_estados:
            raise SystemExit(
                f"a tabela salva tem {dados['quantidade_estados']} estados e o "
                f"ambiente atual tem {self.quantidade_estados}. Ela foi treinada "
                f"com outra configuracao de estado e nao pode ser reaproveitada.")
        self.tabela = dados['tabela']
        self.visitas = dados.get('visitas', [0] * self.quantidade_estados)
        self.exploracao = dados.get('exploracao', 0.0)

    def diagnostico(self):
        visitados = sum(1 for total in self.visitas if total > 0)
        return {
            'exploracao': round(self.exploracao, 4),
            'estados_visitados': visitados,
            'cobertura': round(visitados / self.quantidade_estados, 4),
        }
