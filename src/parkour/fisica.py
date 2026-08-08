"""Fisica de movimento do jogador do Minecraft Java Edition.

Reimplementa o subconjunto que um corredor de parkour exige: andar, correr,
pular, cair e bater nas coisas. Isso e o que permite treinar fora do jogo, e
ganhar umas quatro ordens de grandeza em velocidade.

As constantes abaixo sao a versao documentada da fisica do jogo. **Elas sao
hipotese, nao verdade.** O numero que decide se o simulador presta e o erro
medido contra o bot real, e nao a confianca em qualquer uma destas linhas. O
procedimento esta em docs/sim_para_real.md e o comando e `parkour calibrar`.

Convencao de eixos: o bot olha sempre para +z. "Frente" e +z e "direita" e +x.
Isso tambem precisa ser conferido em jogo, porque depende do yaw do mineflayer.
"""

import math

# Um tick do servidor. Tudo aqui acontece nessa cadencia.
SEGUNDOS_POR_TICK = 0.05
TICKS_POR_SEGUNDO = 20

# Tamanho maximo de cada sub-passo do movimento. Precisa ser menor que a caixa
# mais estreita do mapa (a haste de bambu, 0.19), senao o jogador atravessaria
# obstaculos finos em vez de bater neles.
SUBPASSO = 0.04


class Constantes:
    """Os numeros da fisica, num objeto so, para poder perturba-los."""

    __slots__ = ('velocidade_pulo', 'gravidade', 'arrasto_vertical',
                 'atrito_bloco', 'arrasto_ar', 'aceleracao_chao',
                 'aceleracao_ar', 'multiplicador_corrida',
                 'impulso_corrida_pulo', 'largura', 'altura', 'degrau')

    def __init__(self, **ajustes):
        self.velocidade_pulo = 0.42       # impulso vertical de um pulo
        self.gravidade = 0.08             # perda de velocidade vertical por tick
        self.arrasto_vertical = 0.98
        self.atrito_bloco = 0.6           # escorregadio de blocos comuns
        self.arrasto_ar = 0.91
        self.aceleracao_chao = 0.1
        self.aceleracao_ar = 0.02
        self.multiplicador_corrida = 1.3
        self.impulso_corrida_pulo = 0.2   # empurrao ao pular correndo
        self.largura = 0.6                # caixa do jogador
        self.altura = 1.8
        self.degrau = 0.6                 # altura que sobe sem pular
        for nome, valor in ajustes.items():
            setattr(self, nome, valor)

    def copia(self):
        return Constantes(**{nome: getattr(self, nome) for nome in self.__slots__})

    def perturbadas(self, sorteador, ruido_relativo):
        """Copia com ruido nas constantes, para randomizacao de dominio.

        Treinar com as constantes tremendo um pouco produz uma politica que
        aguenta erro de modelo, em vez de uma que decorou o simulador.
        As medidas do corpo do jogador nao tremem: elas sao exatas.
        """
        if ruido_relativo <= 0.0:
            return self
        fixas = {'largura', 'altura', 'degrau'}
        ajustes = {}
        for nome in self.__slots__:
            valor = getattr(self, nome)
            if nome in fixas:
                ajustes[nome] = valor
            else:
                ajustes[nome] = valor * (1.0 + sorteador.uniform(-ruido_relativo,
                                                                 ruido_relativo))
        return Constantes(**ajustes)


class Entradas:
    """Os controles que o bot pode acionar, iguais aos do mineflayer."""

    __slots__ = ('frente', 'tras', 'esquerda', 'direita', 'pular', 'correr')

    def __init__(self, frente=False, tras=False, esquerda=False,
                 direita=False, pular=False, correr=False):
        self.frente = frente
        self.tras = tras
        self.esquerda = esquerda
        self.direita = direita
        self.pular = pular
        self.correr = correr

    def direcao(self):
        """Vetor (dx, dz) unitario da direcao pedida."""
        dx = (1.0 if self.direita else 0.0) - (1.0 if self.esquerda else 0.0)
        dz = (1.0 if self.frente else 0.0) - (1.0 if self.tras else 0.0)
        if dx and dz:
            norma = math.sqrt(dx * dx + dz * dz)
            dx /= norma
            dz /= norma
        return dx, dz


class Corpo:
    """Posicao e velocidade do jogador."""

    __slots__ = ('x', 'y', 'z', 'vx', 'vy', 'vz', 'no_chao')

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.no_chao = True

    def copia(self):
        outro = Corpo(self.x, self.y, self.z)
        outro.vx, outro.vy, outro.vz = self.vx, self.vy, self.vz
        outro.no_chao = self.no_chao
        return outro

    def __repr__(self):
        return (f"Corpo(x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f}, "
                f"no_chao={self.no_chao})")


def livre(percurso, constantes, x, y, z):
    """Diz se a caixa do jogador nessa posicao nao encosta em nada.

    A caixa do jogador tem 0.6 de largura e 1.8 de altura, com a posicao no
    centro da base. A caixa de cada bloco vem do mapa exportado: pode ser o
    cubo inteiro, meio bloco, uma cerca de 1.5, ou a haste fina do bambu.
    """
    meia_largura = constantes.largura / 2
    x0, x1 = x - meia_largura, x + meia_largura
    y0, y1 = y, y + constantes.altura
    z0, z1 = z - meia_largura, z + meia_largura

    for celula_x in range(math.floor(x0), math.floor(x1) + 1):
        for celula_z in range(math.floor(z0), math.floor(z1) + 1):
            for bloco_y, altura, largura_bloco in percurso.blocos_na_coluna(celula_x, celula_z):
                if bloco_y >= y1:
                    break  # a coluna vem ordenada: daqui para cima nao encosta
                if bloco_y + altura <= y0:
                    continue
                meia = largura_bloco / 2
                if x0 < celula_x + 0.5 + meia and x1 > celula_x + 0.5 - meia and \
                   z0 < celula_z + 0.5 + meia and z1 > celula_z + 0.5 - meia:
                    return False
    return True


def _cabe(percurso, constantes, corpo, eixo, valor):
    if eixo == 'x':
        return livre(percurso, constantes, valor, corpo.y, corpo.z)
    if eixo == 'z':
        return livre(percurso, constantes, corpo.x, corpo.y, valor)
    return livre(percurso, constantes, corpo.x, valor, corpo.z)


def _mover_eixo(percurso, constantes, corpo, eixo, distancia):
    """Move num eixo em sub-passos. Devolve True se bateu em alguma coisa.

    O passo pequeno evita atravessar obstaculos finos como a haste de bambu.
    Quando bate, refina o ultimo trecho por bisseccao para encostar de verdade
    na superficie, em vez de parar ate 4 cm antes dela.
    """
    if distancia == 0.0:
        return False

    quantidade = max(1, math.ceil(abs(distancia) / SUBPASSO))
    incremento = distancia / quantidade
    atual = getattr(corpo, eixo)

    for _ in range(quantidade):
        candidato = atual + incremento
        if _cabe(percurso, constantes, corpo, eixo, candidato):
            atual = candidato
            setattr(corpo, eixo, atual)
            continue

        # Bateu: procura o ponto mais longe que ainda cabe.
        baixo, alto = 0.0, incremento
        for _ in range(8):
            meio = (baixo + alto) / 2
            if _cabe(percurso, constantes, corpo, eixo, atual + meio):
                baixo = meio
            else:
                alto = meio
        setattr(corpo, eixo, atual + baixo)
        return True

    return False


def _tentar_degrau(percurso, constantes, corpo, eixo, distancia):
    """Sobe um degrau baixo quando o caminho esta bloqueado no nivel dos pes.

    E o que deixa o jogador subir em laje, alcapao e meio bloco sem pular.
    """
    y_original = corpo.y
    subida = 0.0
    while subida < constantes.degrau:
        subida += 0.1
        if not livre(percurso, constantes, corpo.x, y_original + subida, corpo.z):
            break
        corpo.y = y_original + subida
        if not _mover_eixo(percurso, constantes, corpo, eixo, distancia):
            return True
    corpo.y = y_original
    return False


def passo_tick(percurso, constantes, corpo, entradas):
    """Avanca um tick do jogo. Modifica o corpo no lugar.

    A ordem das etapas importa e nao e obvia: o Minecraft **move primeiro** e
    so depois aplica gravidade e arrasto. Inverter isso rouba um tick de
    subida do pulo e derruba a altura de 1.25 para 0.83 bloco, que e a
    diferenca entre vencer um bloco de altura e nao vencer.
    """
    direcao_x, direcao_z = entradas.direcao()
    # O pulo nao tira os pes do chao na mesma hora: a aceleracao e o atrito
    # deste tick ainda sao os do chao. E dai que vem o ganho do pulo correndo.
    estava_no_chao = corpo.no_chao

    # 1. Pulo.
    if entradas.pular and estava_no_chao:
        corpo.vy = constantes.velocidade_pulo
        if entradas.correr and (direcao_x or direcao_z):
            corpo.vx += direcao_x * constantes.impulso_corrida_pulo
            corpo.vz += direcao_z * constantes.impulso_corrida_pulo

    # 2. Aceleracao pedida pelos controles. No ar ela e bem menor: e por isso
    #    que da para corrigir a direcao no meio do pulo, mas so um pouco.
    aceleracao = constantes.aceleracao_chao if estava_no_chao else constantes.aceleracao_ar
    if entradas.correr:
        aceleracao *= constantes.multiplicador_corrida
    corpo.vx += direcao_x * aceleracao
    corpo.vz += direcao_z * aceleracao

    # 3. Movimento com colisao, um eixo de cada vez.
    corpo.no_chao = False
    if _mover_eixo(percurso, constantes, corpo, 'y', corpo.vy):
        if corpo.vy <= 0.0:
            corpo.no_chao = True
        corpo.vy = 0.0

    if _mover_eixo(percurso, constantes, corpo, 'x', corpo.vx):
        if not (corpo.no_chao and _tentar_degrau(percurso, constantes, corpo, 'x', corpo.vx)):
            corpo.vx = 0.0

    if _mover_eixo(percurso, constantes, corpo, 'z', corpo.vz):
        if not (corpo.no_chao and _tentar_degrau(percurso, constantes, corpo, 'z', corpo.vz)):
            corpo.vz = 0.0

    # 4. Gravidade, depois do movimento.
    corpo.vy = (corpo.vy - constantes.gravidade) * constantes.arrasto_vertical

    # 5. Arrasto. No chao o atrito do bloco entra junto, por isso parar em
    #    terra firme e muito mais rapido do que parar no ar.
    arrasto = constantes.arrasto_ar
    if corpo.no_chao:
        arrasto *= constantes.atrito_bloco
    corpo.vx *= arrasto
    corpo.vz *= arrasto

    return corpo
