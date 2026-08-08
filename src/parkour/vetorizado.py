"""Treino em paralelo, um processo por nucleo.

O simulador e puro Python e nao usa entrada e saida, entao ele fica preso no
GIL: threads nao ajudam em nada. Processos ajudam, e a medida desta maquina
com 8 nucleos e de umas 2.500 decisoes por segundo por nucleo.

Onde isso vale a pena e onde nao vale:

  varredura de hiperparametros   vale muito. Cada combinacao e independente e
                                 nao precisa conversar com as outras.
  varias sementes                vale muito, pelo mesmo motivo.
  um treino unico mais rapido    vale pouco. O Q-Learning e sequencial por
                                 natureza; paralelizar exigiria juntar
                                 tabelas, e o Trecho A ja treina em 17
                                 segundos.

Por isso este modulo paraleliza **experimentos inteiros**, e nao os passos de
um treino so. Uma varredura de 24 combinacoes cai de uns 7 minutos para menos
de 1 numa maquina de 8 nucleos.

Uso:

    python -m src.parkour.vetorizado --taxas 0.1 0.2 0.4 --descontos 0.9 0.97 0.99
    python -m src.parkour.vetorizado --sementes 0 1 2 3 4 --processos 8
"""

import argparse
import itertools
import multiprocessing
import os
import time

from . import config as configuracao_modulo
from .agentes.q_learning import AgenteQLearning
from .ambiente_sim import AmbienteParkour
from .experimento import rodar_episodio
from .percurso import Percurso


def _rodar_uma(tarefa):
    """Um experimento completo, dentro de um processo.

    Recebe e devolve so tipos simples, porque tudo precisa atravessar o pickle
    entre os processos.
    """
    (nome_trecho, semente, ajustes, episodios, episodios_avaliacao) = tarefa

    configuracao = configuracao_modulo.carregar()
    parametros = dict(configuracao.get('q_learning', {}))
    parametros.update(ajustes)

    definicao = configuracao_modulo.trecho(configuracao, nome_trecho)
    percurso = Percurso.carregar(
        configuracao_modulo.caminho_absoluto(configuracao['mapa']), definicao)

    ambiente = AmbienteParkour(percurso, configuracao, semente=semente)
    agente = AgenteQLearning(ambiente.quantidade_estados,
                             ambiente.quantidade_acoes, parametros, semente=semente)

    for episodio in range(episodios):
        rodar_episodio(ambiente, agente, aprender=True)
        agente.fim_de_episodio(episodio)

    agente.modo_avaliacao()
    avaliacao = AmbienteParkour(percurso, configuracao,
                                semente=1000 + semente, randomizar=False)
    chegadas, recompensa = 0, 0.0
    for _ in range(episodios_avaliacao):
        informacoes = rodar_episodio(avaliacao, agente, aprender=False)
        chegadas += int(informacoes['chegou'])
        recompensa += informacoes['recompensa']

    return {
        'trecho': nome_trecho,
        'semente': semente,
        'ajustes': ajustes,
        'conclusao': chegadas / episodios_avaliacao,
        'recompensa': recompensa / episodios_avaliacao,
        'cobertura': agente.diagnostico()['cobertura'],
    }


def varrer(tarefas, processos=None):
    processos = processos or min(os.cpu_count() or 1, len(tarefas))
    inicio = time.time()
    with multiprocessing.Pool(processos) as piscina:
        resultados = piscina.map(_rodar_uma, tarefas)
    return resultados, time.time() - inicio


def main():
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument('--trecho', default=None)
    analisador.add_argument('--sementes', type=int, nargs='*', default=[0, 1, 2])
    analisador.add_argument('--episodios', type=int, default=4000)
    analisador.add_argument('--avaliacao', type=int, default=100)
    analisador.add_argument('--taxas', type=float, nargs='*', default=None,
                            help='valores de taxa_aprendizado a comparar')
    analisador.add_argument('--descontos', type=float, nargs='*', default=None)
    analisador.add_argument('--decaimentos', type=float, nargs='*', default=None)
    analisador.add_argument('--processos', type=int, default=None)
    argumentos = analisador.parse_args()

    configuracao = configuracao_modulo.carregar()
    padroes = configuracao.get('q_learning', {})
    taxas = argumentos.taxas or [padroes.get('taxa_aprendizado', 0.2)]
    descontos = argumentos.descontos or [padroes.get('desconto', 0.97)]
    decaimentos = argumentos.decaimentos or [padroes.get('exploracao_decaimento', 0.999)]

    tarefas = []
    for taxa, desconto, decaimento in itertools.product(taxas, descontos, decaimentos):
        ajustes = {'taxa_aprendizado': taxa, 'desconto': desconto,
                   'exploracao_decaimento': decaimento}
        for semente in argumentos.sementes:
            tarefas.append((argumentos.trecho, semente, ajustes,
                            argumentos.episodios, argumentos.avaliacao))

    combinacoes = len(taxas) * len(descontos) * len(decaimentos)
    print(f"{combinacoes} combinacoes x {len(argumentos.sementes)} sementes "
          f"= {len(tarefas)} treinos")
    resultados, duracao = varrer(tarefas, argumentos.processos)
    print(f"terminou em {duracao:.1f}s\n")

    # Junta as sementes de cada combinacao: uma semente sozinha nao distingue
    # aprendizado de sorte.
    agrupados = {}
    for resultado in resultados:
        chave = tuple(sorted(resultado['ajustes'].items()))
        agrupados.setdefault(chave, []).append(resultado)

    print(f"{'taxa':>6} {'desconto':>9} {'decaimento':>11} "
          f"{'conclusao':>18} {'recompensa':>11} {'cobertura':>10}")
    print('-' * 70)
    linhas = []
    for chave, grupo in agrupados.items():
        ajustes = dict(chave)
        conclusoes = [item['conclusao'] for item in grupo]
        media = sum(conclusoes) / len(conclusoes)
        espalhamento = max(conclusoes) - min(conclusoes)
        linhas.append((media, ajustes, espalhamento, grupo))

    for media, ajustes, espalhamento, grupo in sorted(linhas, reverse=True,
                                                      key=lambda item: item[0]):
        recompensa = sum(item['recompensa'] for item in grupo) / len(grupo)
        cobertura = sum(item['cobertura'] for item in grupo) / len(grupo)
        print(f"{ajustes['taxa_aprendizado']:>6.2f} "
              f"{ajustes['desconto']:>9.3f} "
              f"{ajustes['exploracao_decaimento']:>11.4f} "
              f"{media:>11.1%} (var {espalhamento:>4.1%}) "
              f"{recompensa:>11.2f} {cobertura:>10.1%}")

    print("\nLembrete da pag. 4 do PDF: um numero melhor aqui so vira")
    print("configuracao oficial depois de virar linha em docs/registro_experimentos.md.")


if __name__ == '__main__':
    main()
