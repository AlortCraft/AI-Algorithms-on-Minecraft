"""DQN: Q-Learning com uma rede neural no lugar da tabela. Etapa 4 do PDF.

A pag. 3 do PDF pede que este passo so venha depois de "o ambiente ja estar
estavel e o grupo entender o treinamento tabular". A ordem importa: se o DQN
for a primeira coisa a rodar, qualquer resultado ruim pode ser do ambiente, da
recompensa, do estado ou da rede, e nao da para separar.

O que muda em relacao ao q_learning.py:

  tabular   Q[s][a], uma celula por combinacao. Estados parecidos nao
            compartilham nada: aprender que "faixa 2 com vao a direita" e bom
            nao ensina nada sobre "faixa 3 com vao a direita".
  DQN       Q(s, a) = rede(s)[a]. A rede recebe o estado continuo e generaliza
            entre situacoes parecidas por construcao.

Duas pecas existem por causa de um problema so, que e o alvo se mover enquanto
a rede aprende:

  memoria de repeticao  guarda transicoes passadas e sorteia lotes delas. Sem
                        isso a rede treina em amostras seguidas e muito
                        parecidas, e esquece o que aprendeu antes.
  rede-alvo             uma copia congelada da rede, usada para calcular o
                        alvo. Sem isso a rede persegue a propria estimativa e
                        o treino oscila.

torch e opcional: so este arquivo depende dele. Instale a versao de CPU, que e
bem menor e suficiente (a rede tem 11 entradas e duas camadas de 64):

    python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
"""

import collections
import os
import random

from .base import Agente

MENSAGEM_SEM_TORCH = (
    "o agente DQN precisa do PyTorch, que nao esta instalado.\n"
    "Instale a versao de CPU (uns 200 MB, contra ~2,5 GB da versao com GPU):\n"
    "    python -m pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
    "GPU nao ajudaria aqui: a rede e minuscula e o gargalo e o simulador.\n"
    "Enquanto isso, o Q-Learning tabular roda com Python puro:\n"
    "    python -m src.parkour.experimento --agente q")


class AgenteDQN(Agente):
    nome = 'dqn'

    def __init__(self, tamanho_entrada, quantidade_acoes, parametros=None,
                 semente=None):
        try:
            import torch
            import torch.nn as nn
        except ImportError:
            raise SystemExit(MENSAGEM_SEM_TORCH)

        self.torch = torch
        parametros = parametros or {}

        self.tamanho_entrada = tamanho_entrada
        self.quantidade_acoes = quantidade_acoes
        self.desconto = parametros.get('desconto', 0.97)
        self.lote = parametros.get('lote', 64)
        self.atualizar_alvo_a_cada = parametros.get('atualizar_alvo_a_cada', 500)
        self.exploracao = parametros.get('exploracao_inicial', 1.0)
        self.exploracao_final = parametros.get('exploracao_final', 0.05)
        self.decaimento = parametros.get('exploracao_decaimento', 0.9995)

        if semente is not None:
            torch.manual_seed(semente)
        self.sorteador = random.Random(semente)

        camadas_ocultas = parametros.get('camadas', [64, 64])
        self.rede = self._montar(nn, tamanho_entrada, camadas_ocultas, quantidade_acoes)
        self.rede_alvo = self._montar(nn, tamanho_entrada, camadas_ocultas, quantidade_acoes)
        self.rede_alvo.load_state_dict(self.rede.state_dict())

        self.otimizador = torch.optim.Adam(
            self.rede.parameters(), lr=parametros.get('taxa_aprendizado', 5e-4))
        self.perda = nn.SmoothL1Loss()

        self.memoria = collections.deque(maxlen=parametros.get('memoria', 50000))
        self.passos = 0
        self.ultima_perda = 0.0

    @staticmethod
    def _montar(nn, entrada, ocultas, saida):
        camadas, anterior = [], entrada
        for largura in ocultas:
            camadas.append(nn.Linear(anterior, largura))
            camadas.append(nn.ReLU())
            anterior = largura
        camadas.append(nn.Linear(anterior, saida))
        return nn.Sequential(*camadas)

    # ------------------------------------------------------------------

    def escolher(self, estado, ambiente=None):
        if self.sorteador.random() < self.exploracao:
            return self.sorteador.randrange(self.quantidade_acoes)
        with self.torch.no_grad():
            entrada = self.torch.tensor([estado], dtype=self.torch.float32)
            return int(self.rede(entrada).argmax(dim=1).item())

    def aprender(self, estado, acao, recompensa, proximo_estado, terminou):
        self.memoria.append((estado, acao, recompensa, proximo_estado, terminou))
        self.passos += 1

        if len(self.memoria) < self.lote:
            return

        torch = self.torch
        amostra = self.sorteador.sample(list(self.memoria), self.lote)
        estados, acoes, recompensas, proximos, finais = zip(*amostra)

        estados = torch.tensor(estados, dtype=torch.float32)
        proximos = torch.tensor(proximos, dtype=torch.float32)
        acoes = torch.tensor(acoes, dtype=torch.int64).unsqueeze(1)
        recompensas = torch.tensor(recompensas, dtype=torch.float32)
        finais = torch.tensor(finais, dtype=torch.float32)

        valores = self.rede(estados).gather(1, acoes).squeeze(1)
        with torch.no_grad():
            # A rede-alvo, congelada, e quem estima o valor do proximo estado.
            melhores = self.rede_alvo(proximos).max(dim=1).values
            alvo = recompensas + self.desconto * melhores * (1.0 - finais)

        perda = self.perda(valores, alvo)
        self.otimizador.zero_grad()
        perda.backward()
        self.otimizador.step()
        self.ultima_perda = float(perda.item())

        if self.passos % self.atualizar_alvo_a_cada == 0:
            self.rede_alvo.load_state_dict(self.rede.state_dict())

    def fim_de_episodio(self, episodio):
        self.exploracao = max(self.exploracao_final,
                              self.exploracao * self.decaimento)

    def modo_avaliacao(self):
        self.exploracao = 0.0
        self.rede.eval()

    # ------------------------------------------------------------------

    def salvar(self, caminho):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        # Os pesos vao para .pt (que o .gitignore ja ignora) e o resto para
        # .json, para dar para conferir a configuracao sem carregar o torch.
        caminho_pesos = caminho.replace('.json', '.pt')
        self.torch.save(self.rede.state_dict(), caminho_pesos)

        import json
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            json.dump({
                'agente': self.nome,
                'tamanho_entrada': self.tamanho_entrada,
                'quantidade_acoes': self.quantidade_acoes,
                'pesos': os.path.basename(caminho_pesos),
                'exploracao': self.exploracao,
            }, arquivo, indent=2)

    def carregar(self, caminho):
        import json
        with open(caminho, encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
        if dados['tamanho_entrada'] != self.tamanho_entrada:
            raise SystemExit(
                f"a rede salva espera {dados['tamanho_entrada']} entradas e o "
                f"ambiente atual da {self.tamanho_entrada}. Ela foi treinada com "
                f"outra configuracao de estado.")
        caminho_pesos = os.path.join(os.path.dirname(caminho), dados['pesos'])
        self.rede.load_state_dict(self.torch.load(caminho_pesos))
        self.rede_alvo.load_state_dict(self.rede.state_dict())

    def diagnostico(self):
        return {
            'exploracao': round(self.exploracao, 4),
            'memoria': len(self.memoria),
            'perda': round(self.ultima_perda, 5),
        }
