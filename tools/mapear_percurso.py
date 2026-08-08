"""Exporta um corredor reto entre dois pontos, em qualquer eixo cardinal.

Ao contrario de ``mapear_mundo.py`` (feito para o parkour oficial em +Z), esta
ferramenta recebe inicio e fim. A saida ja vem rotacionada para o sistema local
usado pelo simulador: lateral em X e progresso em +Z.

Exemplo para o primeiro treino dentro de ``world_labirinto``::

    python -m tools.mapear_percurso \
        --mundo Servidor-BOT/world_labirinto \
        --inicio 87 125 74 --fim 35 125 74 \
        --saida config/mapas/world_labirinto_frente_1.json --perfil

Execute com o PaperMC desligado, depois de encerrar o servidor com ``stop``.
"""

import argparse
import collections
import datetime
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parkour.coordenadas import TransformacaoPercurso
from tools import blocos as classificacao
from tools.nbt import Mundo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _caixa_mundo(transformacao, lateral_min, lateral_max, progresso_min,
                 progresso_max):
    cantos = [transformacao.para_mundo(lateral, 0.0, progresso)
              for lateral in (lateral_min, lateral_max)
              for progresso in (progresso_min, progresso_max)]
    xs = [ponto[0] for ponto in cantos]
    zs = [ponto[2] for ponto in cantos]
    return (math.floor(min(xs)), math.floor(max(xs)),
            math.floor(min(zs)), math.floor(max(zs)))


def _grupo_de_pistas(candidatas, perto_de):
    """Escolhe o grupo contiguo de piso mais proximo do ponto inicial."""
    grupos = []
    for x in sorted(candidatas):
        if not grupos or x != grupos[-1][-1] + 1:
            grupos.append([x])
        else:
            grupos[-1].append(x)
    if not grupos:
        return []
    return min(grupos, key=lambda grupo: min(abs(x - perto_de) for x in grupo))


def mapear(pasta_mundo, inicio, fim, y_min=None, y_max=None, raio_lateral=8):
    transformacao = TransformacaoPercurso(inicio, fim)
    comprimento = int(round(transformacao.comprimento))
    y_pe = int(round(float(inicio['y'])))
    y_min = y_pe - 4 if y_min is None else y_min
    y_max = y_pe + 6 if y_max is None else y_max

    lateral_inicio = transformacao.para_local(
        float(inicio['x']) + 0.5, y_pe, float(inicio['z']) + 0.5)[0]
    centro_lateral = math.floor(lateral_inicio)
    lateral_min = centro_lateral - raio_lateral
    lateral_max = centro_lateral + raio_lateral

    mundo = Mundo(pasta_mundo)
    x_min, x_max, z_min, z_max = _caixa_mundo(
        transformacao, lateral_min, lateral_max + 1, -2, comprimento + 3)
    encontrados = mundo.blocos_na_caixa(x_min, x_max, y_min, y_max,
                                        z_min, z_max)

    solidos = collections.defaultdict(list)
    avisos = collections.Counter()
    nomes_por_posicao = {}
    for (x, y, z), nome in encontrados.items():
        local_x, local_z = transformacao.celula_para_local(x, z)
        if not (lateral_min <= local_x <= lateral_max
                and -2 <= local_z <= comprimento + 2):
            continue
        if classificacao.precisa_validar(nome):
            avisos[nome.split(':')[-1]] += 1
        altura, largura = classificacao.caixa_colisao(nome)
        if altura <= 0.0 or largura <= 0.0:
            continue
        solidos[str(local_z)].append(
            [local_x, y, round(altura, 4), round(largura, 4)])
        nomes_por_posicao[(local_x, y, local_z)] = nome.split(':')[-1]

    for blocos in solidos.values():
        blocos.sort(key=lambda bloco: (bloco[0], bloco[1]))

    # Uma pista tem apoio recorrente na altura dos pes. O limiar de 45% tambem
    # reconhece o padrao classico de parkour "um bloco, um vao": no primeiro
    # treino do labirinto ha apoio em 28 de 53 posicoes. Colunas do labirinto
    # que apenas cruzam a largada/chegada aparecem em poucas posicoes e ficam
    # abaixo desse valor.
    apoios = collections.Counter()
    total = comprimento + 1
    for progresso in range(0, comprimento + 1):
        vistos = set()
        for lateral, y, altura, largura in solidos.get(str(progresso), []):
            if largura >= 0.875 and abs((y + altura) - y_pe) <= 1e-4:
                vistos.add(lateral)
        apoios.update(vistos)

    candidatas = [lateral for lateral, quantidade in apoios.items()
                  if quantidade >= max(2, math.ceil(total * 0.45))]
    pistas = _grupo_de_pistas(candidatas, centro_lateral)
    if not pistas:
        melhores = ', '.join(f'{x}:{n}/{total}'
                             for x, n in apoios.most_common(8)) or '(nenhum apoio)'
        raise ValueError(
            f'nao foi possivel detectar o piso em y={y_pe}. '
            f'Melhores colunas laterais: {melhores}')

    return {
        'meta': {
            'mundo': os.path.basename(os.path.normpath(pasta_mundo)),
            'gerado_em': datetime.datetime.now().isoformat(timespec='seconds'),
            'gerado_por': 'tools/mapear_percurso.py',
            'coordenadas': 'locais',
            'inicio_mundo': inicio,
            'fim_mundo': fim,
            'direcao': transformacao.nome_direcao,
            'caixa_mundo': {'x': [x_min, x_max], 'y': [y_min, y_max],
                            'z': [z_min, z_max]},
        },
        'eixo': 'local',
        'pistas': pistas,
        'y_pe': y_pe,
        'estagios': [{
            'nome': 'corredor_reto',
            'z_inicio': 0,
            'z_fim': comprimento,
            'y_pe': y_pe,
        }],
        'blocos_a_validar': dict(avisos),
        'nomes': {f'{x},{y},{z}': nome
                  for (x, y, z), nome in sorted(nomes_por_posicao.items())},
        'solidos': dict(sorted(solidos.items(), key=lambda item: int(item[0]))),
    }


def main():
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument('--mundo', required=True,
                            help='pasta do mundo relativa a raiz do repositorio')
    analisador.add_argument('--inicio', type=int, nargs=3, required=True,
                            metavar=('X', 'Y', 'Z'))
    analisador.add_argument('--fim', type=int, nargs=3, required=True,
                            metavar=('X', 'Y', 'Z'))
    analisador.add_argument('--saida', required=True)
    analisador.add_argument('--y', type=int, nargs=2, metavar=('MIN', 'MAX'))
    analisador.add_argument('--raio-lateral', type=int, default=8)
    analisador.add_argument('--perfil', action='store_true')
    argumentos = analisador.parse_args()

    inicio = dict(zip(('x', 'y', 'z'), argumentos.inicio))
    fim = dict(zip(('x', 'y', 'z'), argumentos.fim))
    pasta_mundo = os.path.join(RAIZ, argumentos.mundo)
    caminho_saida = (argumentos.saida if os.path.isabs(argumentos.saida)
                     else os.path.join(RAIZ, argumentos.saida))
    limites_y = argumentos.y or (None, None)

    mapa = mapear(pasta_mundo, inicio, fim, limites_y[0], limites_y[1],
                  argumentos.raio_lateral)
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    with open(caminho_saida, 'w', encoding='utf-8') as arquivo:
        json.dump(mapa, arquivo, ensure_ascii=False, separators=(',', ':'))

    total_blocos = sum(len(blocos) for blocos in mapa['solidos'].values())
    print(f"mundo     : {mapa['meta']['mundo']}")
    print(f"direcao   : {mapa['meta']['direcao']}")
    print(f"pistas    : {mapa['pistas']}  y_pe={mapa['y_pe']}")
    print(f"progresso : 0..{mapa['estagios'][0]['z_fim']}")
    print(f"solidos   : {total_blocos}")
    print(f"saida     : {os.path.relpath(caminho_saida, RAIZ)}")

    if argumentos.perfil:
        print('\n  progresso  blocos no nivel/ acima dos pes')
        for progresso in range(mapa['estagios'][0]['z_fim'] + 1):
            blocos = [b for b in mapa['solidos'].get(str(progresso), [])
                      if b[1] + b[2] > mapa['y_pe']]
            if blocos:
                laterais = ', '.join(str(bloco[0]) for bloco in blocos)
                print(f'  {progresso:>9}  {laterais}')


if __name__ == '__main__':
    raise SystemExit(main() or 0)
