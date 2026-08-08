"""Gerador de corredores de parkour.

Serve a dois propositos:

1. dar mapas simples e previsiveis para os testes automaticos;
2. gerar variacoes infinitas do slalom para treinar numa distribuicao de
   mapas em vez de num mapa so. Treinar em varios percursos e o que de fato
   produz generalizacao, e so da para fazer isso porque o treino e offline.

Os mapas gerados usam o mesmo formato de tools/mapear_mundo.py, entao o
simulador nao sabe a diferenca entre um corredor gerado e o mapa real.
"""

import argparse
import json
import os
import random

PISTAS_PADRAO = [999, 1000, 1001]
Y_PE_PADRAO = 101

# Largura da haste de bambu do mapa original. Um obstaculo fino deixa passar
# alguem de 0.6 ao lado; um bloco cheio nao.
LARGURA_FINA = 0.1875


def _mapa_vazio(pistas, y_pe, nome):
    return {
        'meta': {'mundo': nome, 'gerado_por': 'tools/gerar_percurso.py'},
        'eixo': 'z',
        'pistas': list(pistas),
        'y_pe': y_pe,
        'estagios': [],
        'blocos_a_validar': {},
        'solidos': {},
    }


def corredor_plano(z_inicio, z_fim, pistas=PISTAS_PADRAO, y_pe=Y_PE_PADRAO,
                   nome='corredor_plano'):
    """Ponte reta sem nenhum obstaculo. Base de todos os testes."""
    mapa = _mapa_vazio(pistas, y_pe, nome)
    for z in range(z_inicio, z_fim + 1):
        mapa['solidos'][str(z)] = [[x, y_pe - 1, 1.0, 1.0] for x in pistas]
    return mapa


def corredor_aleatorio(z_inicio, z_fim, semente=0, pistas=PISTAS_PADRAO,
                       y_pe=Y_PE_PADRAO, espacamento=(3, 6),
                       proporcao_fina=0.4, nome='corredor_aleatorio'):
    """Slalom gerado, no mesmo estilo do estagio Bamboo.

    Garante que todo obstaculo deixa pelo menos uma passagem: um corredor
    impossivel nao ensina nada, so gera episodios perdidos.
    """
    sorteador = random.Random(semente)
    mapa = corredor_plano(z_inicio, z_fim, pistas, y_pe, nome)

    z = z_inicio + 2
    while z <= z_fim - 2:
        blocos = list(mapa['solidos'][str(z)])

        if sorteador.random() < proporcao_fina:
            # Hastes finas: bloqueiam o meio das celulas, mas sobra vao entre
            # elas. Escolhe quantas colocar deixando ao menos um vao largo.
            escolhidas = sorteador.sample(pistas, sorteador.randint(1, len(pistas)))
            altura = sorteador.randint(2, 4)
            for x in escolhidas:
                for nivel in range(altura):
                    blocos.append([x, y_pe + nivel, 1.0, LARGURA_FINA])
        else:
            # Blocos cheios: precisam deixar pelo menos uma pista livre.
            quantidade = sorteador.randint(1, len(pistas) - 1)
            escolhidas = sorteador.sample(pistas, quantidade)
            altura = sorteador.randint(1, 3)
            for x in escolhidas:
                for nivel in range(altura):
                    blocos.append([x, y_pe + nivel, 1.0, 1.0])

        mapa['solidos'][str(z)] = blocos
        z += sorteador.randint(*espacamento)

    mapa['estagios'] = [{
        'nome': nome,
        'z_inicio': z_inicio,
        'z_fim': z_fim,
        'y_pe': y_pe,
        'placa': None,
    }]
    return mapa


def main():
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument('--quantidade', type=int, default=1)
    analisador.add_argument('--semente', type=int, default=0)
    analisador.add_argument('--comprimento', type=int, default=18)
    analisador.add_argument('--saida', default='config/mapas/gerados')
    argumentos = analisador.parse_args()

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta = os.path.join(raiz, argumentos.saida)
    os.makedirs(pasta, exist_ok=True)

    for indice in range(argumentos.quantidade):
        semente = argumentos.semente + indice
        nome = f'gerado_{semente:03d}'
        mapa = corredor_aleatorio(999, 999 + argumentos.comprimento,
                                  semente=semente, nome=nome)
        caminho = os.path.join(pasta, nome + '.json')
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            json.dump(mapa, arquivo, separators=(',', ':'))
        obstaculos = sum(1 for blocos in mapa['solidos'].values() if len(blocos) > 3)
        print(f"{nome}: z 999-{999 + argumentos.comprimento}, {obstaculos} obstaculos")


if __name__ == '__main__':
    main()
