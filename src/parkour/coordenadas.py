"""Conversao entre coordenadas do Minecraft e coordenadas do percurso.

O simulador nasceu para uma ponte que segue +Z: X e lateral e Z e progresso.
Os treinos simples construidos em ``world_labirinto`` seguem -X. Em vez de
espalhar quatro casos (+X, -X, +Z, -Z) pelo projeto, esta classe transforma
qualquer corredor reto em um sistema local unico:

    local.x  = posicao lateral
    local.y  = altura, sem alteracao
    local.z  = progresso em direcao a meta

Assim fisica, estado, recompensa e agentes continuam trabalhando como antes.
"""

import math


class TransformacaoPercurso:
    """Rotacao de 90 graus (e, quando preciso, reflexao) de um corredor reto."""

    DIRECOES = {
        (0, 1): ('+Z', 0.0),
        (-1, 0): ('-X', 90.0),
        (0, -1): ('-Z', 180.0),
        (1, 0): ('+X', -90.0),
    }

    def __init__(self, inicio=None, fim=None):
        self.inicio = dict(inicio) if inicio is not None else None
        self.fim = dict(fim) if fim is not None else None
        self.identidade = inicio is None and fim is None

        if self.identidade:
            self.frente_x, self.frente_z = 0, 1
            self.lateral_x, self.lateral_z = 1, 0
            self.comprimento = None
            self.nome_direcao = '+Z'
            self.yaw = 0.0
            self._projecao_inicio = 0.0
            return

        if inicio is None or fim is None:
            raise ValueError("'inicio' e 'fim' precisam aparecer juntos")

        faltantes = [eixo for eixo in ('x', 'y', 'z')
                     if eixo not in inicio or eixo not in fim]
        if faltantes:
            raise ValueError(f"inicio/fim sem coordenadas: {', '.join(faltantes)}")

        dx = float(fim['x']) - float(inicio['x'])
        dz = float(fim['z']) - float(inicio['z'])
        if abs(dx) > 1e-9 and abs(dz) > 1e-9:
            raise ValueError(
                'o percurso precisa ser reto e alinhado a X ou Z; '
                f'recebido dx={dx:g}, dz={dz:g}')
        if abs(dx) <= 1e-9 and abs(dz) <= 1e-9:
            raise ValueError('inicio e fim do percurso sao o mesmo ponto')

        if abs(dx) > 1e-9:
            self.frente_x, self.frente_z = (1 if dx > 0 else -1), 0
            self.comprimento = abs(dx)
        else:
            self.frente_x, self.frente_z = 0, (1 if dz > 0 else -1)
            self.comprimento = abs(dz)

        # +local.x conserva a convencao antiga do simulador. Para +Z ele e
        # exatamente +X do mundo. A mesma rotacao vale nas outras direcoes.
        self.lateral_x = self.frente_z
        self.lateral_z = -self.frente_x
        self.nome_direcao, self.yaw = self.DIRECOES[
            (self.frente_x, self.frente_z)]

        inicio_centro_x = float(inicio['x']) + 0.5
        inicio_centro_z = float(inicio['z']) + 0.5
        self._projecao_inicio = (
            self.frente_x * inicio_centro_x
            + self.frente_z * inicio_centro_z)

    @classmethod
    def identidade_padrao(cls):
        return cls()

    def para_local(self, x, y, z):
        """Converte uma posicao continua do Minecraft para (lateral, y, progresso)."""
        if self.identidade:
            return float(x), float(y), float(z)
        lateral = self.lateral_x * float(x) + self.lateral_z * float(z)
        progresso = (self.frente_x * float(x) + self.frente_z * float(z)
                     - self._projecao_inicio + 0.5)
        return lateral, float(y), progresso

    def para_mundo(self, lateral, y, progresso):
        """Faz a conversao inversa, das coordenadas locais para o Minecraft."""
        if self.identidade:
            return float(lateral), float(y), float(progresso)
        projecao_frente = float(progresso) - 0.5 + self._projecao_inicio
        x = self.lateral_x * float(lateral) + self.frente_x * projecao_frente
        z = self.lateral_z * float(lateral) + self.frente_z * projecao_frente
        return x, float(y), z

    def velocidade_local(self, vx, vy, vz):
        """Rotaciona uma velocidade; translacao nao participa de vetores."""
        if self.identidade:
            return float(vx), float(vy), float(vz)
        lateral = self.lateral_x * float(vx) + self.lateral_z * float(vz)
        frente = self.frente_x * float(vx) + self.frente_z * float(vz)
        return lateral, float(vy), frente

    def celula_para_local(self, x, z):
        """Converte a celula inteira de um bloco usando o centro dela."""
        local_x, _, local_z = self.para_local(float(x) + 0.5, 0.0,
                                              float(z) + 0.5)
        return math.floor(local_x + 1e-9), math.floor(local_z + 1e-9)

    def celula_para_mundo(self, lateral, progresso):
        """Converte uma celula local para a celula correspondente no mundo."""
        x, _, z = self.para_mundo(float(lateral) + 0.5, 0.0,
                                 float(progresso) + 0.5)
        return math.floor(x + 1e-9), math.floor(z + 1e-9)

    def progresso_de(self, x, z):
        return self.para_local(x, 0.0, z)[2]

    def descricao(self):
        if self.identidade:
            return 'coordenadas originais (+Z)'
        return (f"{self.nome_direcao}, {self.comprimento:g} blocos, "
                f"yaw={self.yaw:g}")
