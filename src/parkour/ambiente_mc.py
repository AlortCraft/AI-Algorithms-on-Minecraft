"""Ambiente em que o Q-Learning aprende executando acoes no Minecraft."""

import time

from . import acoes, geometria
from .estado import Discretizador
from .recompensa import Recompensa

SEGUNDOS_POR_TICK = 0.05
CONTROLES = ('forward', 'back', 'left', 'right', 'jump', 'sprint')

# O bot olha na direcao do progresso. Nessa orientacao, +x local corresponde
# ao controle esquerdo do Mineflayer e -x ao direito.
MAPA_CONTROLES = {
    'frente': 'forward',
    'tras': 'back',
    'esquerda': 'right',
    'direita': 'left',
    'pular': 'jump',
    'correr': 'sprint',
}


class AmbienteMinecraft:
    PARADO_EPSILON = 0.02
    PASSOS_PARADO_MAXIMO = 8
    TELEPORTE_TOLERANCIA = 0.35
    TELEPORTE_TICKS_MAXIMO = 100

    def __init__(self, bot, percurso, configuracao, emissor_comandos=None):
        self.bot = bot
        self.percurso = percurso
        self.emitir_comando = emissor_comandos or bot.chat

        episodio = configuracao.get('episodio', {})
        self.ticks_por_acao = episodio.get('ticks_por_acao', 4)
        self.passos_maximos = episodio.get('passos_maximos', 120)
        self.queda_abaixo_de = episodio.get('queda_abaixo_de', 3.0)

        parametros_estado = configuracao.get('estado', {})
        self.discretizador = Discretizador(
            percurso,
            faixas_x=parametros_estado.get('faixas_x', 6),
            distancia_maxima=parametros_estado.get('distancia_maxima', 4),
            modo=parametros_estado.get('modo', 'mascara'),
        )
        self.recompensa = Recompensa(configuracao.get('recompensa', {}))
        self.corpo = _CorpoDoBot(bot, percurso.transformacao)

        self.passos = 0
        self.passos_parado = 0
        self.z_maximo = percurso.z_inicio
        self.z_maximo_valido = percurso.z_inicio
        self.motivo = None

    @property
    def quantidade_estados(self):
        return self.discretizador.quantidade

    @property
    def quantidade_acoes(self):
        return acoes.QUANTIDADE

    def soltar_controles(self):
        for controle in CONTROLES:
            self.bot.setControlState(controle, False)

    def _aplicar(self, entradas):
        for nome_pt, nome_js in MAPA_CONTROLES.items():
            self.bot.setControlState(nome_js, bool(getattr(entradas, nome_pt)))

    def _esperar_ticks(self, quantidade):
        try:
            self.bot.waitForTicks(quantidade)
        except Exception:
            time.sleep(quantidade * SEGUNDOS_POR_TICK)

    def reset(self):
        """Teleporta ao inicio e espera a chegada antes do primeiro passo."""
        self.soltar_controles()
        local = (self.percurso.x_partida, self.percurso.nivel_de_partida(),
                 self.percurso.z_inicio + 0.5)
        destino = self.percurso.transformacao.para_mundo(*local)
        yaw = self.percurso.transformacao.yaw
        self.emitir_comando(
            f'/tp {self.bot.username} {destino[0]:.3f} {destino[1]:.3f} '
            f'{destino[2]:.3f} {yaw:.1f} 0'
        )
        self._esperar_teleporte(destino)
        self._restaurar_condicao()

        self.passos = 0
        self.passos_parado = 0
        self.z_maximo = self.corpo.z
        self.z_maximo_valido = self.corpo.z
        self.motivo = None
        return self.observar(), self.informacoes()

    def _restaurar_condicao(self):
        """Evita acumular entre episodios dano e fome do percurso."""
        aplicou = False
        try:
            if float(self.bot.health) < 19.5:
                self.emitir_comando(
                    f'/effect give {self.bot.username} '
                    'minecraft:instant_health 1 10 true'
                )
                aplicou = True
        except Exception:
            pass
        try:
            if float(self.bot.food) < 19.5:
                self.emitir_comando(
                    f'/effect give {self.bot.username} '
                    'minecraft:saturation 1 10 true'
                )
                aplicou = True
        except Exception:
            pass
        if aplicou:
            self._esperar_ticks(1)

    def _esperar_teleporte(self, destino):
        ultima = None
        for _ in range(self.TELEPORTE_TICKS_MAXIMO):
            try:
                ultima = self.corpo.posicao_mundo
                distancia = sum((atual - alvo) ** 2
                                for atual, alvo in zip(ultima, destino)) ** 0.5
                if distancia <= self.TELEPORTE_TOLERANCIA and self.corpo.no_chao:
                    self._esperar_ticks(2)
                    return
            except Exception:
                pass
            self._esperar_ticks(1)
        raise RuntimeError(
            'o teleporte nao foi confirmado. Confira se o bot possui OP e '
            f'se o mundo terminou de carregar. Ultima posicao: {ultima}'
        )

    def passo(self, acao):
        """Executa uma acao por alguns ticks e calcula a recompensa real."""
        progresso_antes = self.corpo.z
        self._aplicar(acoes.entradas_de(acao))

        # Uma acao dura varios ticks, mas um pouso pode durar somente um deles.
        # Observar apenas no final fazia o bot atravessar a plataforma final e
        # cair antes que a chegada fosse registrada.
        progresso_depois = progresso_antes
        self.motivo = None
        for _ in range(self.ticks_por_acao):
            self._esperar_ticks(1)
            progresso_depois = self.corpo.z
            self.z_maximo = max(self.z_maximo, progresso_depois)
            pouso_valido = self._pouso_valido()
            if pouso_valido:
                self.z_maximo_valido = max(
                    self.z_maximo_valido, progresso_depois
                )
            if self.corpo.y < self.percurso.y_pe - self.queda_abaixo_de:
                self.motivo = 'queda'
                break
            if self._atingiu_meta(progresso_depois):
                self.z_maximo_valido = max(
                    self.z_maximo_valido, progresso_depois
                )
                self.motivo = 'meta'
                break

        self.passos += 1
        if abs(progresso_depois - progresso_antes) < self.PARADO_EPSILON:
            self.passos_parado += 1
        else:
            self.passos_parado = 0

        if self.motivo is None:
            self.motivo = self._motivo_terminal(progresso_depois)
        terminou = self.motivo is not None

        truncou = not terminou and self.passos >= self.passos_maximos
        if truncou:
            self.motivo = 'tempo'
        if terminou or truncou:
            self.soltar_controles()

        recompensa = self.recompensa.calcular(
            progresso_antes,
            progresso_depois,
            self.motivo if terminou else None,
        )
        return self.observar(), recompensa, terminou, truncou, self.informacoes()

    def _motivo_terminal(self, progresso):
        """Queda tem prioridade; a meta so vale depois de um pouso real."""
        if self.corpo.y < self.percurso.y_pe - self.queda_abaixo_de:
            return 'queda'
        if self._atingiu_meta(progresso):
            return 'meta'
        if self.passos_parado >= self.PASSOS_PARADO_MAXIMO:
            return 'travado'
        return None

    def _atingiu_meta(self, progresso=None):
        """Aceita entrada no volume final ou pouso na meta linear."""
        plataforma = getattr(self.percurso, 'plataforma_meta', None)
        if plataforma:
            mundo_x, mundo_y, mundo_z = self.corpo.posicao_mundo
            inicio = plataforma['inicio']
            fim = plataforma['fim']
            x_min, x_max = sorted((inicio['x'], fim['x']))
            y_min, y_max = sorted((inicio['y'], fim['y']))
            z_min, z_max = sorted((inicio['z'], fim['z']))
            return (
                x_min <= mundo_x < x_max + 1.0
                and y_min <= mundo_y < y_max + 1.0
                and z_min <= mundo_z < z_max + 1.0
            )

        if progresso is None:
            progresso = self.corpo.z
        return (progresso >= self.percurso.z_chegada
                and self._pouso_valido())

    def _pouso_valido(self):
        """Confirma contato com uma superficie que pertence ao percurso."""
        if not self.corpo.no_chao:
            return False
        celula = int(self.corpo.z // 1)
        for altura, faixas in self.percurso.superficies_em(celula):
            if abs(altura - self.corpo.y) > geometria.ALTURA_DEGRAU:
                continue
            if any(inicio <= self.corpo.x <= fim for inicio, fim in faixas):
                return True
        return False

    def observar(self):
        return self.discretizador.indice(self.corpo)

    def informacoes(self):
        mundo_x, mundo_y, mundo_z = self.corpo.posicao_mundo
        progresso = ((self.z_maximo - self.percurso.z_inicio)
                     / max(1e-9, self.percurso.comprimento()))
        progresso_valido = (
            (self.z_maximo_valido - self.percurso.z_inicio)
            / max(1e-9, self.percurso.comprimento())
        )
        if self.motivo == 'meta':
            progresso = 1.0
            progresso_valido = 1.0
        return {
            'x': self.corpo.x,
            'y': self.corpo.y,
            'z': self.corpo.z,
            'mundo_x': mundo_x,
            'mundo_y': mundo_y,
            'mundo_z': mundo_z,
            'z_maximo': self.z_maximo,
            'z_maximo_valido': self.z_maximo_valido,
            'passos': self.passos,
            'motivo': self.motivo,
            'progresso': min(1.0, max(0.0, progresso)),
            'progresso_valido': min(1.0, max(0.0, progresso_valido)),
            'chegou': self.motivo == 'meta',
        }


class _CorpoDoBot:
    """Expoe posicao e velocidade reais nas coordenadas locais do percurso."""

    def __init__(self, bot, transformacao):
        self.bot = bot
        self.transformacao = transformacao

    @property
    def posicao_mundo(self):
        posicao = self.bot.entity.position
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
            velocidade.x, velocidade.y, velocidade.z
        )

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
