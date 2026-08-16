"""O que o agente enxerga.

Esta e a decisao mais delicada do projeto, e a pag. 4 do PDF pergunta
exatamente isso: "o estado diferencia duas situacoes que exigem acoes
diferentes?" e "o que e necessario para decidir um salto sem dar informacao
excessiva?".

Existem somente os dois modos usados pelos mapas mantidos no projeto:

  'mascara'  informa quais faixas do corredor estao livres a frente. E usado
             no mapa oficial, que possui obstaculos laterais.
  'piso'     olha apoios e buracos nas quatro celulas seguintes. E usado nos
             treinos retos construidos no mundo do labirinto.

Cuidado com a ideia de "tres pistas": ela nao vale aqui. Entre duas hastes de
bambu existe um vao de 0.81 bloco que nao coincide com nenhuma pista inteira.
A posicao em x e continua e a discretizacao usa faixas mais finas.
"""

from . import geometria

# Incrementada quando o significado ou a quantidade dos estados muda. O nome
# padrao do modelo inclui esta versao para nunca carregar uma tabela antiga com
# indices que agora representam outra situacao.
VERSAO_ESTADO = 2

# Nada, degrau, pulavel, parede. Ver Discretizador.classe_de_altura.
CLASSES_DE_ALTURA = 4
# Sem apoio, queda longa, queda curta, mesma altura, subida pulavel, alto demais.
CLASSES_ALTURA_APOIO = 6
# Um pulo do Minecraft sobe 1.2522; abaixo disso da para pousar em cima.
ALTURA_MAXIMA_DE_PULO = 1.25


class Discretizador:
    def __init__(self, percurso, faixas_x=6, distancia_maxima=4, modo='mascara'):
        if modo not in ('mascara', 'piso'):
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
        mapeamento e o estado precisam concordar sobre onde o jogador cabe.
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

    def faixa_de(self, x):
        indice = int((x - self.percurso.x_min) / self.largura_faixa)
        return max(0, min(self.faixas_x - 1, indice))

    # ------------------------------------------------------------------
    # estado discreto, para a tabela Q

    @property
    def quantidade(self):
        """Quantos estados diferentes existem."""
        if self.modo == 'piso':
            # 4 bits de piso, altura relativa do apoio mais proximo, 4 partes
            # do bloco atual, 3 fases verticais e 3 faixas de velocidade. No
            # corredor reto a posicao lateral nao muda a decisao.
            return (2 ** 4) * CLASSES_ALTURA_APOIO * 4 * 3 * 3
        alternativas_frente = 2 ** self.faixas_x
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
        if self.modo == 'piso':
            return self._indice_piso(corpo)

        faixa, distancia, livres, no_chao, classe = self._leitura(corpo)

        frente = 0
        for posicao, livre in enumerate(livres):
            if livre:
                frente |= 1 << posicao
        alternativas_frente = 2 ** self.faixas_x

        indice = faixa
        indice = indice * (self.distancia_maxima + 1) + distancia
        indice = indice * alternativas_frente + frente
        indice = indice * 2 + (1 if no_chao else 0)
        indice = indice * CLASSES_DE_ALTURA + classe
        return indice

    def _indice_piso(self, corpo):
        """Estado pequeno para corredores cujo desafio sao vaos no chao.

        A mascara olha as quatro celulas seguintes no sentido do progresso.
        Um bit 1 significa que existe uma superficie onde o centro do jogador
        cabe. A altura do primeiro apoio diferencia descidas, piso nivelado,
        subida pulavel e obstaculo alto. A parte fracionaria de ``z`` informa
        se o corpo esta no inicio ou perto da borda do bloco atual.
        """
        celula = int(corpo.z // 1)
        mascara_piso = 0
        classe_proximo_apoio = 0
        for distancia in range(1, 5):
            classe = self._classe_apoio(corpo, celula + distancia)
            if classe:
                mascara_piso |= 1 << (distancia - 1)
                if classe_proximo_apoio == 0:
                    classe_proximo_apoio = classe

        fracao = corpo.z - (corpo.z // 1)
        parte_do_bloco = min(3, max(0, int(fracao * 4)))

        if corpo.no_chao:
            fase_vertical = 0
        elif corpo.vy > 0.05:
            fase_vertical = 1
        else:
            fase_vertical = 2

        velocidade = abs(corpo.vz)
        if velocidade < 0.12:
            faixa_velocidade = 0
        elif velocidade < 0.25:
            faixa_velocidade = 1
        else:
            faixa_velocidade = 2

        indice = mascara_piso
        indice = indice * CLASSES_ALTURA_APOIO + classe_proximo_apoio
        indice = indice * 4 + parte_do_bloco
        indice = indice * 3 + fase_vertical
        indice = indice * 3 + faixa_velocidade
        return indice

    def _classe_apoio(self, corpo, celula):
        """Altura relativa do apoio da celula na linha lateral do corpo."""
        alturas = []
        for altura, faixas in self.percurso.superficies_em(celula):
            if any(inicio <= corpo.x <= fim for inicio, fim in faixas):
                alturas.append(altura)
        if not alturas:
            return 0

        # Se houver mais de uma superficie na mesma celula, a mais proxima da
        # altura atual e a candidata fisicamente relevante para o proximo pouso.
        altura = min(alturas, key=lambda valor: abs(valor - corpo.y))
        diferenca = altura - corpo.y
        if diferenca < -1.5:
            return 1   # queda de dois ou mais blocos
        if diferenca < -0.5:
            return 2   # queda de aproximadamente um bloco
        if diferenca <= 0.5:
            return 3   # apoio na mesma altura
        if diferenca <= ALTURA_MAXIMA_DE_PULO:
            return 4   # subida que um pulo consegue alcancar
        return 5       # superficie presente, mas alta demais neste instante
