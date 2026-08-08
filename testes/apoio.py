"""Apoio para os testes: um verificador simples e mapas de brinquedo.

Nao usamos pytest para os testes rodarem com o Python puro, sem instalar nada.
"""

import sys

from src.parkour.percurso import Percurso
from tools.gerar_percurso import corredor_plano


class Verificador:
    """Acumula resultados e imprime um relatorio no fim."""

    def __init__(self, titulo):
        self.titulo = titulo
        self.passaram = 0
        self.falharam = []
        self.secao_atual = ''
        print(f"\n=== testes de {titulo} ===")

    def secao(self, nome):
        self.secao_atual = nome
        print(f"\n  {nome}")

    def verdadeiro(self, condicao, descricao):
        if condicao:
            self.passaram += 1
            print(f"    ok    {descricao}")
        else:
            self.falharam.append(f"{self.secao_atual}: {descricao}")
            print(f"    FALHA {descricao}")

    def perto(self, obtido, esperado, tolerancia, descricao):
        diferenca = abs(obtido - esperado)
        texto = f"{descricao}: {obtido:.4f} (esperado {esperado:.4f} +- {tolerancia})"
        self.verdadeiro(diferenca <= tolerancia, texto)

    def encerrar(self):
        total = self.passaram + len(self.falharam)
        print(f"\n=== {self.titulo}: {self.passaram}/{total} passaram ===")
        for falha in self.falharam:
            print(f"    FALHOU: {falha}")
        return 1 if self.falharam else 0


def percurso_plano(z_inicio, z_fim, devolver_mapa=False):
    """Ponte reta sem obstaculos, para testar a fisica isolada."""
    mapa = corredor_plano(z_inicio, z_fim)
    if devolver_mapa:
        return mapa
    return Percurso(mapa, z_inicio, z_fim)


def rodar_modulos(modulos):
    """Roda varios modulos de teste e devolve o codigo de saida."""
    codigo = 0
    for modulo in modulos:
        codigo |= modulo.main()
    return codigo
