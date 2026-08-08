"""O ambiente que roda dentro do Minecraft, via mineflayer.

Mesma assinatura do ambiente simulado, de proposito. E o instrumento de
validacao, nao o de treino: o servidor roda a 20 ticks por segundo e nao
existe forma suportada de acelerar isso, o que da umas 5 decisoes por segundo
contra alguns milhares no simulador.

Ele serve para tres coisas:

1. a etapa 1 do plano do PDF (observar, agir, detectar queda e reiniciar);
2. gravar trajetorias reais para calibrar a fisica (docs/sim_para_real.md);
3. rodar no jogo a politica treinada offline, e medir quanto se perde.

Este arquivo e o unico do pacote que depende de Node.js e do servidor. Todo o
resto roda com Python puro, e e por isso que quatro dos cinco integrantes
conseguem trabalhar sem o servidor ligado.
"""

import time

from . import acoes as catalogo_acoes
from .estado import Discretizador
from .recompensa import Recompensa

SEGUNDOS_POR_TICK = 0.05

# Os nomes dos controles no mineflayer.
#
# ATENCAO ao par lateral: ele ja custou caro. O simulador fala em coordenadas
# do mundo - "direita" e +x. O mineflayer fala no corpo do bot - "right" e a
# mao direita dele. Com yaw=0 o bot olha para +z, que no Minecraft e o sul, e
# quem olha para o sul tem o oeste (-x) a direita. Portanto:
#
#     simulador 'direita'  (+x)  ->  mineflayer 'left'
#     simulador 'esquerda' (-x)  ->  mineflayer 'right'
#
# Medido em jogo em 08/08/2026, com yaw=0 e 20 ticks de cada: 'left' deu
# dx = +3.785 e 'right' deu dx = -3.785. Com o mapeamento ingenuo
# (direita->right), a politica desviava para o lado certo no simulador e para
# o lado errado no jogo, saia da ponte e caia - e era essa a causa dos 28%.
CONTROLES = ('forward', 'back', 'left', 'right', 'jump', 'sprint')

MAPA_CONTROLES = {
    'frente': 'forward',
    'tras': 'back',
    'esquerda': 'right',
    'direita': 'left',
    'pular': 'jump',
    'correr': 'sprint',
}


class AmbienteMinecraft:
    # Um passo sao 4 ticks; andando, mesmo devagar, o bot avanca bem mais que
    # isto. Abaixo disso ele nao esta andando devagar, esta parado.
    PARADO_EPSILON = 0.02
    PASSOS_PARADO_MAXIMO = 8

    def __init__(self, bot, percurso, configuracao, vec3=None):
        self.bot = bot
        self.vec3 = vec3
        self.percurso = percurso
        self.configuracao = configuracao

        episodio = configuracao.get('episodio', {})
        self.ticks_por_acao = episodio.get('ticks_por_acao', 4)
        self.passos_maximos = episodio.get('passos_maximos', 120)
        self.queda_abaixo_de = episodio.get('queda_abaixo_de', 3.0)

        parametros_estado = configuracao.get('estado', {})
        self.discretizador = Discretizador(
            percurso,
            faixas_x=parametros_estado.get('faixas_x', 6),
            distancia_maxima=parametros_estado.get('distancia_maxima', 4),
            modo=parametros_estado.get('modo', 'mascara'))

        self.recompensa = Recompensa(configuracao.get('recompensa', {}))

        self.passos = 0
        self.passos_parado = 0
        self.z_maximo = percurso.z_inicio
        self.motivo = None
        self.corpo = _CorpoDoBot(bot, percurso.transformacao)

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

    def soltar_controles(self):
        for controle in CONTROLES:
            self.bot.setControlState(controle, False)

    def aplicar(self, entradas):
        for nome_pt, nome_js in MAPA_CONTROLES.items():
            self.bot.setControlState(nome_js, bool(getattr(entradas, nome_pt)))

    def esperar_ticks(self, quantidade):
        """Espera N ticks do servidor.

        Prefere o waitForTicks do mineflayer, que acompanha o relogio do
        servidor de verdade. O sleep e so uma reserva: se o servidor engasgar,
        dormir pelo relogio local dessincroniza a contagem de passos.
        """
        try:
            self.bot.waitForTicks(quantidade)
        except Exception:
            time.sleep(quantidade * SEGUNDOS_POR_TICK)

    # ------------------------------------------------------------------

    def reset(self):
        """Teleporta o bot para o inicio e espera ele assentar.

        Reprodutibilidade e o criterio de avanco da etapa 1 do PDF: sem um
        reset confiavel, comparar dois agentes nao mede nada.
        """
        self.soltar_controles()
        destino_local = (self.percurso.x_partida, self.percurso.y_pe,
                         self.percurso.z_inicio + 0.5)
        destino_x, destino_y, destino_z = self.percurso.transformacao.para_mundo(
            *destino_local)
        yaw = self.percurso.transformacao.yaw
        self.bot.chat(f"/tp {self.bot.username} {destino_x:.3f} "
                      f"{destino_y:.3f} {destino_z:.3f} {yaw:.1f} 0")
        self.esperar_ticks(10)

        self.passos = 0
        self.passos_parado = 0
        self.z_maximo = self.corpo.z
        self.motivo = None
        return self.observar(), self.informacoes()

    def passo(self, acao):
        entradas = catalogo_acoes.entradas_de(acao)
        progresso_antes = self.corpo.z

        self.aplicar(entradas)
        self.esperar_ticks(self.ticks_por_acao)
        self.soltar_controles()

        self.passos += 1
        progresso_depois = self.corpo.z
        self.z_maximo = max(self.z_maximo, progresso_depois)

        # Deteccao de travamento. Prensado contra um obstaculo, o bot para de
        # responder ao pulo: medido em jogo em 08/08/2026, no pilar de z=1004,
        # o `jump` deixa de ter efeito enquanto ele estiver ali, e volta a
        # funcionar assim que e teleportado para fora. Sem isto o episodio
        # gasta os 120 passos parado no mesmo lugar, e a metrica registra
        # "tempo" como se fosse indecisao do agente, e nao um beco.
        if abs(progresso_depois - progresso_antes) < self.PARADO_EPSILON:
            self.passos_parado += 1
        else:
            self.passos_parado = 0

        terminou = False
        if self.corpo.y < self.percurso.y_pe - self.queda_abaixo_de:
            self.motivo = 'queda'
            terminou = True
        elif progresso_depois >= self.percurso.z_meta:
            self.motivo = 'meta'
            terminou = True
        elif self.passos_parado >= self.PASSOS_PARADO_MAXIMO:
            self.motivo = 'travado'
            terminou = True

        truncou = not terminou and self.passos >= self.passos_maximos
        if truncou:
            self.motivo = 'tempo'

        valor = self.recompensa.calcular(progresso_antes, self.corpo.z,
                                         self.motivo if terminou else None)
        return self.observar(), valor, terminou, truncou, self.informacoes()

    # ------------------------------------------------------------------

    def observar(self):
        return self.discretizador.indice(self.corpo)

    def observar_vetor(self):
        return self.discretizador.vetor(self.corpo)

    def informacoes(self):
        mundo_x, mundo_y, mundo_z = self.corpo.posicao_mundo
        return {
            'x': self.corpo.x,
            'y': self.corpo.y,
            'z': self.corpo.z,
            'mundo_x': mundo_x,
            'mundo_y': mundo_y,
            'mundo_z': mundo_z,
            'z_maximo': self.z_maximo,
            'passos': self.passos,
            'motivo': self.motivo,
            'progresso': ((self.z_maximo - self.percurso.z_inicio)
                          / max(1e-9, self.percurso.comprimento())),
            'chegou': self.motivo == 'meta',
        }

    def verificar_geometria(self, limite=16):
        """Compara uma amostra do JSON com os blocos carregados no Mineflayer.

        O treino continua usando o JSON local por velocidade. Esta verificacao
        roda uma vez, no jogo, para detectar o erro perigoso: selecionar um
        mundo e observar a geometria exportada de outro.
        """
        if self.vec3 is None or not self.percurso.nomes_blocos:
            return {
                'verificados': 0,
                'diferencas': [],
                'aviso': 'o mapa antigo nao guarda nomes de blocos para comparar',
            }

        posicoes = sorted(
            (posicao, nome) for posicao, nome in self.percurso.nomes_blocos.items()
            if self.percurso.z_inicio <= posicao[2] <= self.percurso.z_meta
            and self.percurso.x_min <= posicao[0] < self.percurso.x_max)
        if len(posicoes) > limite:
            # Espalha as amostras pelo percurso em vez de olhar so a largada.
            indices = [round(i * (len(posicoes) - 1) / (limite - 1))
                       for i in range(limite)]
            posicoes = [posicoes[indice] for indice in indices]

        diferencas = []
        for (local_x, y, local_z), esperado in posicoes:
            mundo_x, mundo_z = self.percurso.transformacao.celula_para_mundo(
                local_x, local_z)
            bloco = self.bot.blockAt(self.vec3(mundo_x, y, mundo_z))
            obtido = str(bloco.name) if bloco is not None else '(nao carregado)'
            if obtido != esperado:
                diferencas.append({
                    'local': (local_x, y, local_z),
                    'mundo': (mundo_x, y, mundo_z),
                    'esperado': esperado,
                    'obtido': obtido,
                })
        return {'verificados': len(posicoes), 'diferencas': diferencas,
                'aviso': None}

    # ------------------------------------------------------------------

    def gravar_trajetoria(self, sequencia_de_acoes, origem=None):
        """Roda uma sequencia fixa de acoes e grava a posicao a cada tick.

        E a materia-prima da calibracao: a mesma sequencia roda no simulador e
        aqui, e a diferenca entre as duas trajetorias e o erro do simulador.
        Ver docs/sim_para_real.md.

        `origem` e (x, y, z). Sem ela a gravacao comeca no inicio do percurso,
        que e onde a primeira tentativa em jogo deu errado: o bot bate no pilar
        de z=1004 no tick 24 e o resto da sequencia mede colisao em vez de
        fisica. A calibracao de verdade passa a pista lisa aqui.
        """
        if origem is None:
            self.reset()
        else:
            self.soltar_controles()
            x, y, z = origem
            self.bot.chat(f"/tp {self.bot.username} {x:.3f} {y:.3f} {z:.3f} 0 0")
            self.esperar_ticks(20)

        # O tick vem do contador do laco, e nao de bot.time.age: o servidor so
        # manda a hora do mundo uma vez por segundo, entao time.age anda de 20
        # em 20 e nao serve de relogio por tick. O waitForTicks do mineflayer,
        # medido em 08/08/2026, entrega 24 ticks em 1.21 s - 50.4 ms por tick,
        # ou seja, confiavel.
        amostras = [{'tick': 0, 'x': self.corpo.x, 'y': self.corpo.y,
                     'z': self.corpo.z, 'acao': None}]

        inicio = time.time()
        tick = 0
        for acao in sequencia_de_acoes:
            entradas = catalogo_acoes.entradas_de(acao)
            self.aplicar(entradas)
            for _ in range(self.ticks_por_acao):
                self.esperar_ticks(1)
                tick += 1
                amostras.append({'tick': tick, 'x': self.corpo.x,
                                 'y': self.corpo.y, 'z': self.corpo.z,
                                 'acao': catalogo_acoes.nome_de(acao)})
        self.soltar_controles()

        # Se o laco tivesse perdido ticks, a gravacao teria durado mais que o
        # esperado e cada amostra estaria rotulada com o tick errado - o que
        # apareceria na calibracao como erro de fisica. Melhor avisar aqui.
        decorrido = time.time() - inicio
        esperado = tick * SEGUNDOS_POR_TICK
        if decorrido > esperado * 1.15:
            print(f"[aviso] a gravacao levou {decorrido:.2f}s para {tick} ticks "
                  f"(esperado ~{esperado:.2f}s). O rotulo de tick de cada "
                  f"amostra pode estar adiantado; a calibracao vai culpar a "
                  f"fisica por isso.")
        return amostras


class _CorpoDoBot:
    """Le o bot real e o apresenta nas coordenadas locais do simulador.

    Cada atributo lido aqui atravessa a ponte JSPyBridge, que custa uma
    ida-e-volta entre processos. Por isso o codigo do ambiente le a posicao o
    minimo possivel, e a geometria do mapa vem de um JSON local em vez de
    chamadas bot.blockAt().
    """

    __slots__ = ('bot', 'transformacao')

    def __init__(self, bot, transformacao):
        self.bot = bot
        self.transformacao = transformacao

    @property
    def _posicao(self):
        return self.bot.entity.position

    @property
    def posicao_mundo(self):
        posicao = self._posicao
        return float(posicao.x), float(posicao.y), float(posicao.z)

    @property
    def _local(self):
        return self.transformacao.para_local(*self.posicao_mundo)

    @property
    def x(self):
        return self._local[0]

    @property
    def y(self):
        return self._local[1]

    @property
    def z(self):
        return self._local[2]

    @property
    def _velocidade_local(self):
        velocidade = self.bot.entity.velocity
        return self.transformacao.velocidade_local(
            velocidade.x, velocidade.y, velocidade.z)

    @property
    def vx(self):
        return self._velocidade_local[0]

    @property
    def vy(self):
        return self._velocidade_local[1]

    @property
    def vz(self):
        return self._velocidade_local[2]

    @property
    def no_chao(self):
        return bool(self.bot.entity.onGround)
