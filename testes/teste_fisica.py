"""Testes da fisica simulada.

Roda sem Minecraft, em segundos. Nao depende de pytest de proposito: basta

    python -m testes.teste_fisica

Estes testes checam que o simulador e coerente consigo mesmo e bate com os
valores documentados do jogo. Eles **nao** provam que o simulador bate com o
jogo de verdade: quem faz isso e `parkour calibrar`, contra o bot real.
"""

import math
import sys

from src.parkour import fisica
from src.parkour.percurso import Percurso
from testes.apoio import Verificador, percurso_plano


def andar_ticks(percurso, corpo, entradas, quantidade, constantes=None):
    constantes = constantes or fisica.Constantes()
    for _ in range(quantidade):
        fisica.passo_tick(percurso, constantes, corpo, entradas)
    return corpo


def teste_queda_livre(verificador):
    """Sem chao embaixo, o jogador cai e acelera."""
    percurso = percurso_plano(990, 1010)
    corpo = fisica.Corpo(x=1000.5, y=101.0, z=1000.5)
    corpo.no_chao = False
    corpo.y = 110.0

    alturas = []
    constantes = fisica.Constantes()
    for _ in range(10):
        fisica.passo_tick(percurso, constantes, corpo, fisica.Entradas())
        alturas.append(corpo.y)

    quedas = [alturas[i] - alturas[i + 1] for i in range(len(alturas) - 1)]
    verificador.verdadeiro(all(b > a for a, b in zip(quedas, quedas[1:])),
                           "a queda acelera a cada tick")
    # O primeiro tick nao desce nada: a gravidade so entra depois do
    # movimento. Somando os 10 ticks, a queda e de 3.342 blocos.
    verificador.perto(corpo.y, 110.0 - 3.342, 0.02,
                      "queda de 10 ticks a partir do repouso")


def teste_altura_do_pulo(verificador):
    """O pulo do Minecraft sobe 1.25 bloco: sobe em um bloco, nao em dois."""
    percurso = percurso_plano(990, 1010)
    corpo = fisica.Corpo(x=1000.5, y=101.0, z=1000.5)

    maior = 101.0
    entradas = fisica.Entradas(pular=True)
    constantes = fisica.Constantes()
    for tick in range(30):
        fisica.passo_tick(percurso, constantes, corpo,
                          entradas if tick == 0 else fisica.Entradas())
        maior = max(maior, corpo.y)

    verificador.perto(maior - 101.0, 1.2522, 0.03, "altura maxima do pulo")
    verificador.verdadeiro(maior - 101.0 > 1.0, "o pulo vence um bloco de altura")
    verificador.verdadeiro(maior - 101.0 < 2.0, "o pulo nao vence dois blocos")
    verificador.perto(corpo.y, 101.0, 0.001, "volta ao chao e para")
    verificador.verdadeiro(corpo.no_chao, "termina com os pes no chao")


def teste_velocidade_andando(verificador):
    """Andar reto chega perto de 4.3 blocos por segundo."""
    percurso = percurso_plano(990, 1100)
    corpo = fisica.Corpo(x=1000.5, y=101.0, z=1000.5)
    andar_ticks(percurso, corpo, fisica.Entradas(frente=True), 60)

    z_antes = corpo.z
    andar_ticks(percurso, corpo, fisica.Entradas(frente=True), 20)
    velocidade = (corpo.z - z_antes) / 20 * fisica.TICKS_POR_SEGUNDO

    verificador.perto(velocidade, 4.317, 0.25, "velocidade andando (blocos/s)")


def teste_velocidade_correndo(verificador):
    """Correr chega perto de 5.6 blocos por segundo."""
    percurso = percurso_plano(990, 1100)
    corpo = fisica.Corpo(x=1000.5, y=101.0, z=1000.5)
    entradas = fisica.Entradas(frente=True, correr=True)
    andar_ticks(percurso, corpo, entradas, 60)

    z_antes = corpo.z
    andar_ticks(percurso, corpo, entradas, 20)
    velocidade = (corpo.z - z_antes) / 20 * fisica.TICKS_POR_SEGUNDO

    verificador.perto(velocidade, 5.612, 0.3, "velocidade correndo (blocos/s)")
    verificador.verdadeiro(velocidade > 4.317, "correr e mais rapido que andar")


def teste_parede_bloqueia(verificador):
    """Um bloco cheio na frente para o jogador, sem atravessar."""
    mapa = percurso_plano(990, 1010, devolver_mapa=True)
    for nivel in range(2):
        mapa['solidos']['1005'].append([1000, 101 + nivel, 1.0, 1.0])
    percurso = Percurso(mapa, 990, 1010)

    corpo = fisica.Corpo(x=1000.5, y=101.0, z=1000.5)
    andar_ticks(percurso, corpo, fisica.Entradas(frente=True, correr=True), 100)

    verificador.verdadeiro(corpo.z < 1005.0,
                           f"parou antes da parede (z={corpo.z:.2f})")
    verificador.perto(corpo.z, 1004.7, 0.1, "encostou na face da parede")


def teste_passa_entre_bambus(verificador):
    """Duas hastes finas em celulas vizinhas deixam um vao de 0.81.

    Este e o teste que sustenta o estagio Bamboo inteiro: se as hastes
    bloqueassem a celula toda, o percurso seria intransponivel.
    """
    mapa = percurso_plano(990, 1040, devolver_mapa=True)
    for nivel in range(3):
        mapa['solidos']['1005'].append([999, 101 + nivel, 1.0, 0.1875])
        mapa['solidos']['1005'].append([1000, 101 + nivel, 1.0, 0.1875])
    percurso = Percurso(mapa, 990, 1040)

    # O vao fica entre as duas hastes, centrado em x=1000.0.
    corpo = fisica.Corpo(x=1000.0, y=101.0, z=1000.5)
    andar_ticks(percurso, corpo, fisica.Entradas(frente=True), 80)

    verificador.verdadeiro(corpo.z > 1006.0,
                           f"passou entre as hastes (z={corpo.z:.2f})")

    # Indo pelo meio de uma haste, tem que bater. A haste ocupa z a partir de
    # 1005.406 e o jogador tem 0.3 de raio, entao ele para perto de 1005.11.
    corpo = fisica.Corpo(x=999.5, y=101.0, z=1000.5)
    andar_ticks(percurso, corpo, fisica.Entradas(frente=True), 80)
    verificador.perto(corpo.z, 1005.106, 0.02,
                      "bateu de frente na haste")


def teste_sobe_degrau(verificador):
    """Meio bloco e vencido andando, sem precisar pular."""
    mapa = percurso_plano(990, 1040, devolver_mapa=True)
    for z in range(1005, 1041):
        mapa['solidos'][str(z)].append([1000, 101, 0.5, 1.0])
    percurso = Percurso(mapa, 990, 1040)

    corpo = fisica.Corpo(x=1000.5, y=101.0, z=1000.5)
    andar_ticks(percurso, corpo, fisica.Entradas(frente=True), 60)

    verificador.verdadeiro(corpo.z > 1006.0, f"subiu a laje (z={corpo.z:.2f})")
    verificador.perto(corpo.y, 101.5, 0.02, "ficou em cima da laje")


def teste_cai_da_ponte(verificador):
    """Andar de lado sai da ponte e o jogador despenca."""
    percurso = percurso_plano(990, 1010)
    corpo = fisica.Corpo(x=1000.5, y=101.0, z=1000.5)
    andar_ticks(percurso, corpo, fisica.Entradas(direita=True, correr=True), 60)

    verificador.verdadeiro(corpo.y < 95.0, f"despencou (y={corpo.y:.2f})")
    verificador.verdadeiro(percurso.fora_da_ponte(corpo.x),
                           f"saiu dos limites (x={corpo.x:.2f})")


def teste_determinismo(verificador):
    """A mesma sequencia de acoes leva sempre ao mesmo lugar."""
    def rodar():
        percurso = percurso_plano(990, 1100)
        corpo = fisica.Corpo(x=1000.5, y=101.0, z=1000.5)
        constantes = fisica.Constantes()
        for tick in range(200):
            entradas = fisica.Entradas(frente=True, correr=True,
                                       pular=(tick % 12 == 0),
                                       direita=(tick % 30 < 5))
            fisica.passo_tick(percurso, constantes, corpo, entradas)
        return (corpo.x, corpo.y, corpo.z)

    primeira, segunda = rodar(), rodar()
    verificador.verdadeiro(primeira == segunda,
                           "duas execucoes identicas dao o mesmo resultado")


def teste_randomizacao_de_dominio(verificador):
    """O ruido muda a fisica, mas nao as medidas do corpo."""
    import random
    base = fisica.Constantes()
    ruidosa = base.perturbadas(random.Random(0), 0.03)

    verificador.verdadeiro(ruidosa.velocidade_pulo != base.velocidade_pulo,
                           "o ruido muda a velocidade do pulo")
    verificador.perto(ruidosa.velocidade_pulo, base.velocidade_pulo,
                      base.velocidade_pulo * 0.03 + 1e-9,
                      "o ruido fica dentro do limite pedido")
    verificador.verdadeiro(ruidosa.largura == base.largura,
                           "a largura do jogador nao muda")


def main():
    verificador = Verificador("fisica")
    for nome, funcao in sorted(globals().items()):
        if nome.startswith('teste_'):
            verificador.secao(nome)
            funcao(verificador)
    return verificador.encerrar()


if __name__ == '__main__':
    sys.exit(main())
