"""O que o agente enxerga.

Esta e a decisao mais delicada do projeto, e a pag. 4 do PDF pergunta
exatamente isso: "o estado diferencia duas situacoes que exigem acoes
diferentes?" e "o que e necessario para decidir um salto sem dar informacao
excessiva?".

Por isso existem dois modos, para o grupo comparar em vez de escolher no chute:

  'mascara'  diz quais faixas do corredor estao bloqueadas a frente. E o dado
             cru: o agente precisa descobrir sozinho para onde ir.
  'vao'      diz qual faixa contem a passagem mais proxima. E dado mastigado:
             aprende bem mais rapido, mas boa parte da decisao ja veio pronta.

O modo 'mascara' e o padrao justamente por ser o mais honesto. Comparar os dois
e um experimento previsto em docs/registro_experimentos.md.

Cuidado com a ideia de "tres pistas": ela nao vale aqui. Entre duas hastes de
bambu existe um vao de 0.81 bloco que nao coincide com nenhuma pista inteira.
A posicao em x e continua e a discretizacao usa faixas mais finas.
"""

from . import geometria

# Nada, degrau, pulavel, parede. Ver Discretizador.classe_de_altura.
CLASSES_DE_ALTURA = 4
# Um pulo do Minecraft sobe 1.2522; abaixo disso da para pousar em cima.
ALTURA_MAXIMA_DE_PULO = 1.25


class Discretizador:
    def __init__(self, percurso, faixas_x=6, distancia_maxima=4, modo='mascara'):
        if modo not in ('mascara', 'vao'):
            raise ValueError(f"modo de estado desconhecido: {modo}")

        self.percurso = percurso
        self.faixas_x = faixas_x
        self.distancia_maxima = distancia_maxima
        self.modo = modo

        self.largura_faixa = (percurso.x_max - percurso.x_min) / faixas_x
        self.centros = [percurso.x_min + (indice + 0.5) * self.largura_faixa
                        for indice in range(faixas_x)]

        # Pre-calcula, para cada z, quais faixas o jogador consegue ocupar.
        # E consultado a cada passo e nunca muda durante o episodio.
        self._faixas_livres = {}

    # ------------------------------------------------------------------
    # leitura do mundo

    def posicoes_validas(self, z):
        """Intervalos de x onde o centro do jogador pode ficar, num dado z.

        Repassa para o percurso, que ja pre-calculou isso: a ferramenta de
        mapeamento, o simulador e o estado precisam concordar sobre onde o
        jogador cabe, senao um diz que ha passagem e o outro nao.
        """
        return self.percurso.posicoes_validas_em(z)

    def faixas_livres(self, z, altura=None):
        """Tupla de booleanos: em quais faixas o jogador cabe, neste z.

        A faixa conta como livre quando **alguma parte** dela serve, e nao
        quando o centro dela serve. A diferenca nao e detalhe: a janela util
        de uma passagem de 1 bloco tem 0.4 de largura e a faixa tem 0.5,
        entao exigir o centro faria passagens reais sumirem do estado. Com o
        criterio do centro, o proprio ponto onde o bot nasce aparecia como
        bloqueado.
        """
        chave = (z, round(altura * 2) / 2) if altura is not None else z
        if chave not in self._faixas_livres:
            validos = (self.percurso.posicoes_validas_na_altura(z, altura)
                       if altura is not None else self.posicoes_validas(z))
            faixas = []
            for indice in range(self.faixas_x):
                inicio_faixa = self.percurso.x_min + indice * self.largura_faixa
                fim_faixa = inicio_faixa + self.largura_faixa
                faixas.append(any(inicio <= fim_faixa and fim >= inicio_faixa
                                  for inicio, fim in validos))
            self._faixas_livres[chave] = tuple(faixas)
        return self._faixas_livres[chave]

    def melhor_posicao(self, z, x_atual):
        """Posicao em x mais proxima da atual onde o jogador cabe, neste z.

        Serve para a politica gulosa e para depurar: responde "para onde eu
        teria que ir", com precisao continua em vez de por faixa.
        """
        melhor, distancia_melhor = None, float('inf')
        for inicio, fim in self.posicoes_validas(z):
            alvo = min(max(x_atual, inicio), fim)
            distancia = abs(alvo - x_atual)
            if distancia < distancia_melhor:
                melhor, distancia_melhor = alvo, distancia
        return melhor

    def faixa_de(self, x):
        indice = int((x - self.percurso.x_min) / self.largura_faixa)
        return max(0, min(self.faixas_x - 1, indice))

    # ------------------------------------------------------------------
    # estado discreto, para a tabela Q

    @property
    def quantidade(self):
        """Quantos estados diferentes existem."""
        if self.modo == 'mascara':
            alternativas_frente = 2 ** self.faixas_x
        else:
            alternativas_frente = self.faixas_x + 1   # +1 para "nenhum vao"
        return (self.faixas_x * (self.distancia_maxima + 1)
                * alternativas_frente * 2 * CLASSES_DE_ALTURA)

    def _leitura(self, corpo):
        faixa = self.faixa_de(corpo.x)
        meia = geometria.LARGURA_JOGADOR / 2

        # Tudo relativo a altura em que o bot esta, e nao ao piso do estagio.
        # Em cima de um bloco o mundo e outro: o que era parede vira chao.
        z_obstaculo = self.percurso.obstaculo_a_frente_na_altura(
            corpo.z, corpo.y, corpo.x - meia, corpo.x + meia)

        if z_obstaculo is None:
            distancia = self.distancia_maxima
            livres = (True,) * self.faixas_x
            classe = 0
        else:
            distancia = min(self.distancia_maxima,
                            max(0, int(z_obstaculo - corpo.z)))
            livres = self.faixas_livres(z_obstaculo, corpo.y)
            classe = self.classe_de_altura(
                self.percurso.altura_do_obstaculo_em(
                    z_obstaculo, corpo.y, corpo.x - meia, corpo.x + meia))

        return faixa, distancia, livres, bool(corpo.no_chao), classe

    @staticmethod
    def classe_de_altura(altura):
        """Em que categoria cai o obstaculo a frente.

        Sem isto o agente ve um bit - "bloqueado" - e as tres situacoes
        abaixo ficam indistinguiveis, embora exijam acoes opostas. Era a
        razao de ele pular no chute: tinha as acoes certas e nenhuma
        informacao para escolher entre elas.
        """
        if altura <= geometria.ALTURA_DEGRAU:
            return 1 if altura > 0.0 else 0     # 0 nada, 1 sobe andando
        if altura <= ALTURA_MAXIMA_DE_PULO:
            return 2                            # da para pular e pousar em cima
        return 3                                # parede: tem que contornar

    def indice(self, corpo):
        """Numero unico do estado, usado como linha da tabela Q."""
        faixa, distancia, livres, no_chao, classe = self._leitura(corpo)

        if self.modo == 'mascara':
            frente = 0
            for posicao, livre in enumerate(livres):
                if livre:
                    frente |= 1 << posicao
            alternativas_frente = 2 ** self.faixas_x
        else:
            # Faixa livre mais proxima da posicao atual; faixas_x se nao houver.
            candidatas = [posicao for posicao, livre in enumerate(livres) if livre]
            if candidatas:
                frente = min(candidatas, key=lambda posicao: abs(posicao - faixa))
            else:
                frente = self.faixas_x
            alternativas_frente = self.faixas_x + 1

        indice = faixa
        indice = indice * (self.distancia_maxima + 1) + distancia
        indice = indice * alternativas_frente + frente
        indice = indice * 2 + (1 if no_chao else 0)
        indice = indice * CLASSES_DE_ALTURA + classe
        return indice

    # ------------------------------------------------------------------
    # estado continuo, para a rede neural

    @property
    def tamanho_vetor(self):
        return 6 + self.faixas_x

    def vetor(self, corpo):
        """Mesma informacao, sem discretizar. E o que o DQN recebe.

        Comparar este vetor com o indice discreto e o experimento 2 do plano:
        a discretizacao perde informacao que importa?
        """
        faixa, distancia, livres, no_chao, classe = self._leitura(corpo)
        largura = self.percurso.x_max - self.percurso.x_min

        valores = [
            (corpo.x - self.percurso.x_min) / largura,     # posicao lateral 0..1
            corpo.vx * 10.0,                               # velocidade lateral
            corpo.vz * 10.0,                               # velocidade a frente
            1.0 if no_chao else 0.0,
            distancia / self.distancia_maxima,
            classe / (CLASSES_DE_ALTURA - 1),          # altura do que vem a frente
        ]
        valores.extend(1.0 if livre else 0.0 for livre in livres)
        return valores
