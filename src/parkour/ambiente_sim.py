"""O ambiente de treino: parkour sem Minecraft.

Mesma assinatura do ambiente que roda no jogo (ambiente_mc.py), para que
trocar um pelo outro seja uma linha. E essa simetria que torna possivel medir
a diferenca entre o simulador e o jogo, que e o que sustenta todo o resto.

    ambiente = AmbienteParkour(percurso, configuracao)
    estado, info = ambiente.reset()
    estado, recompensa, terminou, truncou, info = ambiente.passo(acao)

A assinatura segue o padrao do Gymnasium de proposito, sem depender do pacote:
se um dia o grupo quiser comparar com uma implementacao pronta, basta um
adaptador fino.
"""

import random

from . import acoes as catalogo_acoes
from . import fisica
from .estado import Discretizador
from .recompensa import Recompensa


class AmbienteParkour:
    def __init__(self, percurso, configuracao, semente=None, randomizar=None):
        self.percurso = percurso
        self.configuracao = configuracao

        episodio = configuracao.get('episodio', {})
        self.ticks_por_acao = episodio.get('ticks_por_acao', 4)
        self.passos_maximos = episodio.get('passos_maximos', 120)
        self.queda_abaixo_de = episodio.get('queda_abaixo_de', 3.0)
        self.variar_inicio = episodio.get('variar_inicio', True)

        parametros_estado = configuracao.get('estado', {})
        self.discretizador = Discretizador(
            percurso,
            faixas_x=parametros_estado.get('faixas_x', 6),
            distancia_maxima=parametros_estado.get('distancia_maxima', 4),
            modo=parametros_estado.get('modo', 'mascara'))

        self.recompensa = Recompensa(configuracao.get('recompensa', {}))

        randomizacao = configuracao.get('randomizacao_de_dominio', {})
        self.randomizar = (randomizacao.get('ativa', False)
                           if randomizar is None else randomizar)
        self.ruido = randomizacao.get('ruido_relativo', 0.0)

        self.sorteador = random.Random(semente)
        self.constantes_base = fisica.Constantes()
        self.constantes = self.constantes_base

        self.corpo = None
        self.passos = 0
        self.z_maximo = percurso.z_inicio
        self.motivo = None

    # ------------------------------------------------------------------

    @property
    def quantidade_estados(self):
        return self.discretizador.quantidade

    @property
    def quantidade_acoes(self):
        return catalogo_acoes.QUANTIDADE

    @property
    def tamanho_vetor(self):
        return self.discretizador.tamanho_vetor

    # ------------------------------------------------------------------

    def reset(self, semente=None):
        """Comeca um episodio novo, sempre do mesmo jeito.

        Reprodutibilidade e o criterio da etapa 1 do PDF: sem um reset
        confiavel, comparar dois agentes nao quer dizer nada.
        """
        if semente is not None:
            self.sorteador.seed(semente)

        # A randomizacao de dominio sorteia constantes novas por episodio,
        # nao por passo: dentro de um episodio a fisica precisa ser coerente.
        if self.randomizar and self.ruido > 0.0:
            self.constantes = self.constantes_base.perturbadas(self.sorteador, self.ruido)
        else:
            self.constantes = self.constantes_base

        x = self._x_de_partida()
        self.corpo = fisica.Corpo(
            x=x,
            y=self._altura_de_partida(x),
            z=self.percurso.z_inicio + 0.5)
        self.passos = 0
        self.z_maximo = self.corpo.z
        self.motivo = None

        return self.observar(), self.informacoes()

    def passo(self, acao):
        entradas = catalogo_acoes.entradas_de(acao)
        # ``corpo.z`` e o progresso local. No mapa oficial coincide com Z do
        # mundo; num percurso em X ele ja chega transformado.
        progresso_antes = self.corpo.z

        for _ in range(self.ticks_por_acao):
            fisica.passo_tick(self.percurso, self.constantes, self.corpo, entradas)
            if self._caiu():
                break

        self.passos += 1
        self.z_maximo = max(self.z_maximo, self.corpo.z)

        terminou = False
        if self._caiu():
            self.motivo = 'queda'
            terminou = True
        elif self.corpo.z >= self.percurso.z_meta:
            self.motivo = 'meta'
            terminou = True

        truncou = not terminou and self.passos >= self.passos_maximos
        if truncou:
            self.motivo = 'tempo'

        valor = self.recompensa.calcular(progresso_antes, self.corpo.z,
                                         self.motivo if terminou else None)

        return self.observar(), valor, terminou, truncou, self.informacoes()

    # ------------------------------------------------------------------

    def _x_de_partida(self):
        """Onde o bot nasce no eixo lateral.

        Com o ponto de partida sempre igual, o ambiente e a politica avaliada
        sao os dois deterministicos, e os 200 episodios de avaliacao viram 200
        copias do mesmo episodio: o n informado seria 200 e o real, 1. Sortear
        a posicao dentro da faixa viavel devolve sentido a media, e de quebra
        mede o que interessa saber - se a politica aguenta comecar de um lugar
        um pouco diferente.
        """
        if not self.variar_inicio:
            return self.percurso.x_partida

        # Filtrado pela altura de nascimento: sem isso o sorteio pega x que so
        # e valido em cima de um bloco, e o bot nasce dentro da parede - o
        # episodio comeca perdido e a media do experimento vira ruido.
        opcoes = self.percurso.posicoes_no_nivel(self.percurso.z_inicio,
                                                 self.percurso.nivel_de_partida())
        if not opcoes:
            return self.percurso.x_partida

        # Sorteia proporcional a largura, para faixas maiores nao ficarem
        # sub-representadas so por serem menos numerosas.
        larguras = [max(1e-6, fim - inicio) for inicio, fim in opcoes]
        sorteio = self.sorteador.uniform(0.0, sum(larguras))
        for (inicio, fim), largura in zip(opcoes, larguras):
            if sorteio <= largura:
                return inicio + (fim - inicio) * self.sorteador.random()
            sorteio -= largura
        return self.percurso.x_partida

    def _altura_de_partida(self, x):
        """Assenta o corpo em cima do que houver no chao do ponto de partida.

        A analise de passagens ignora obstaculos baixos, porque o jogador sobe
        neles andando. Mas o reset coloca o corpo parado, e nascer dentro de
        uma laje ou de um alcapao travava o episodio inteiro: nenhuma acao
        conseguia sair dali. Sobe ate encontrar espaco livre.
        """
        # Parte do nivel viavel de partida, que nem sempre e o piso do estagio.
        y = float(self.percurso.nivel_de_partida())
        limite = y + 2.0
        while y < limite:
            if fisica.livre(self.percurso, self.constantes, x, y,
                            self.percurso.z_inicio + 0.5):
                return y
            y += 0.0625
        return float(self.percurso.nivel_de_partida())

    def _caiu(self):
        return self.corpo.y < self.percurso.y_pe - self.queda_abaixo_de

    def observar(self):
        return self.discretizador.indice(self.corpo)

    def observar_vetor(self):
        return self.discretizador.vetor(self.corpo)

    def informacoes(self):
        return {
            'x': self.corpo.x,
            'y': self.corpo.y,
            'z': self.corpo.z,
            'z_maximo': self.z_maximo,
            'passos': self.passos,
            'motivo': self.motivo,
            'progresso': ((self.z_maximo - self.percurso.z_inicio)
                          / max(1e-9, self.percurso.comprimento())),
            'chegou': self.motivo == 'meta',
        }
