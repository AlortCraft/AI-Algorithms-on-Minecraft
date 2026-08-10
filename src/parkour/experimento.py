"""O laco de treino e avaliacao, e a gravacao dos resultados.

Todo agente passa exatamente pelo mesmo laco. E isso que torna a comparacao
justa: se o aleatorio e o Q-Learning rodassem em codigos diferentes, qualquer
diferenca de resultado poderia vir do laco, e nao do algoritmo.

Regras que valem para todos os experimentos, vindas da pag. 4 e 6 do PDF:

- avaliar sempre com exploracao zero, e em episodios separados do treino;
- rodar varias sementes, porque uma so nao distingue aprendizado de sorte;
- gravar tudo por episodio, para poder refazer os graficos sem retreinar.

Uso:

    python -m src.parkour.experimento --agente aleatorio
    python -m src.parkour.experimento --agente q --episodios 4000
    python -m src.parkour.experimento --agente q --trecho A --avaliar-em sand mud
"""

import argparse
import csv
import datetime
import os
import time

from . import config as configuracao_modulo
from .agentes.aleatorio import AgenteAleatorio
from .agentes.guloso import AgenteGuloso
from .agentes.q_learning import AgenteQLearning
from .ambiente_sim import AmbienteParkour
from .percurso import Percurso

COLUNAS = ('agente', 'trecho', 'semente', 'fase', 'episodio', 'recompensa',
           'passos', 'z_maximo', 'progresso', 'chegou', 'motivo', 'exploracao')


def criar_agente(nome, ambiente, configuracao, semente):
    if nome in ('aleatorio', 'random'):
        return AgenteAleatorio(ambiente.quantidade_acoes, semente=semente)
    if nome == 'guloso':
        return AgenteGuloso()
    if nome in ('q', 'q_learning'):
        return AgenteQLearning(ambiente.quantidade_estados,
                               ambiente.quantidade_acoes,
                               configuracao_modulo.parametros_q_learning(
                                   configuracao),
                               semente=semente)
    if nome == 'dqn':
        from .agentes.dqn import AgenteDQN
        return AgenteDQN(ambiente.tamanho_vetor, ambiente.quantidade_acoes,
                         configuracao.get('dqn', {}), semente=semente)
    raise SystemExit(f"agente desconhecido: {nome}")


def usa_vetor(agente):
    """O DQN recebe o estado continuo; os tabulares recebem o indice."""
    return getattr(agente, 'nome', '') == 'dqn'


def rodar_episodio(ambiente, agente, aprender=True):
    """Um episodio do inicio ao fim. Devolve as metricas dele."""
    vetorial = usa_vetor(agente)
    ambiente.reset()
    estado = ambiente.observar_vetor() if vetorial else ambiente.observar()

    recompensa_total = 0.0
    while True:
        acao = agente.escolher(estado, ambiente)
        _, recompensa, terminou, truncou, informacoes = ambiente.passo(acao)
        proximo = ambiente.observar_vetor() if vetorial else ambiente.observar()

        if aprender:
            # `terminou` e diferente de `truncou`: um episodio cortado por
            # tempo nao teve um final de verdade, e tratar os dois como iguais
            # ensinaria o agente que o mundo acaba ali.
            agente.aprender(estado, acao, recompensa, proximo, terminou)

        recompensa_total += recompensa
        estado = proximo
        if terminou or truncou:
            break

    informacoes['recompensa'] = recompensa_total
    return informacoes


def rodar_fase(ambientes, agente, episodios, fase, aprender, nome_agente,
               nome_trecho, semente, registros, a_cada=0):
    """Roda uma fase inteira. `ambientes` pode ser um so ou uma lista.

    Uma lista faz o agente ver um percurso diferente a cada episodio, que e
    como se treina numa distribuicao de mapas em vez de num mapa so. E a
    diferenca entre decorar um trecho e aprender a atravessar corredores.
    """
    if not isinstance(ambientes, (list, tuple)):
        ambientes = [ambientes]

    inicio = time.time()
    for episodio in range(episodios):
        ambiente = ambientes[episodio % len(ambientes)]
        informacoes = rodar_episodio(ambiente, agente, aprender=aprender)
        if aprender:
            agente.fim_de_episodio(episodio)

        registros.append({
            'agente': nome_agente,
            'trecho': nome_trecho,
            'semente': semente,
            'fase': fase,
            'episodio': episodio,
            'recompensa': round(informacoes['recompensa'], 4),
            'passos': informacoes['passos'],
            'z_maximo': round(informacoes['z_maximo'], 3),
            'progresso': round(informacoes['progresso'], 4),
            'chegou': int(informacoes['chegou']),
            'motivo': informacoes['motivo'],
            'exploracao': agente.diagnostico().get('exploracao', ''),
        })

        if a_cada and (episodio + 1) % a_cada == 0:
            recentes = registros[-a_cada:]
            taxa = sum(linha['chegou'] for linha in recentes) / len(recentes)
            media = sum(linha['recompensa'] for linha in recentes) / len(recentes)
            print(f"    ep {episodio + 1:>6}  conclusao {taxa:6.1%}  "
                  f"recompensa {media:8.2f}  {agente.diagnostico()}")

    duracao = time.time() - inicio
    passos = sum(linha['passos'] for linha in registros[-episodios:])
    if episodios and duracao > 0:
        print(f"    {fase}: {episodios} episodios em {duracao:.1f}s "
              f"({passos / duracao:,.0f} decisoes/s)")
    return registros


def resumir(registros, fase):
    linhas = [linha for linha in registros if linha['fase'] == fase]
    if not linhas:
        return None
    return {
        'episodios': len(linhas),
        'conclusao': sum(linha['chegou'] for linha in linhas) / len(linhas),
        'recompensa': sum(linha['recompensa'] for linha in linhas) / len(linhas),
        'progresso': sum(linha['progresso'] for linha in linhas) / len(linhas),
        'passos': sum(linha['passos'] for linha in linhas) / len(linhas),
        'quedas': sum(1 for linha in linhas if linha['motivo'] == 'queda') / len(linhas),
    }


def gravar_csv(registros, caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'w', newline='', encoding='utf-8') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(registros)
    return caminho


def main():
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument('--agente', default='aleatorio',
                            help='aleatorio, guloso, q ou dqn')
    analisador.add_argument('--cenario', default=None,
                            help='parkour_oficial ou labirinto_parkours')
    analisador.add_argument('--trecho', default=None, help='trecho de treino')
    analisador.add_argument('--avaliar-em', nargs='*', default=None,
                            help='trechos onde avaliar sem retreinar (generalizacao)')
    analisador.add_argument('--episodios', type=int, default=None)
    analisador.add_argument('--avaliacao', type=int, default=None)
    analisador.add_argument('--sementes', type=int, nargs='*', default=None)
    analisador.add_argument('--saida', default=None)
    analisador.add_argument('--sem-randomizacao', action='store_true',
                            help='desliga o ruido nas constantes da fisica')
    analisador.add_argument('--a-cada', type=int, default=0,
                            help='mostra o andamento a cada N episodios')
    analisador.add_argument('--gerados', type=int, default=0,
                            help='treina em N corredores gerados, em vez do trecho')
    analisador.add_argument('--comprimento-gerado', type=int, default=18)
    argumentos = analisador.parse_args()

    configuracao = configuracao_modulo.carregar(cenario=argumentos.cenario)
    definicao = configuracao_modulo.trecho(configuracao, argumentos.trecho)
    caminho_mapa = configuracao_modulo.caminho_mapa(configuracao, definicao)

    sementes = argumentos.sementes or configuracao.get('sementes', [0])
    episodios_avaliacao = (argumentos.avaliacao
                           or configuracao.get('avaliacao', {}).get('episodios', 100))

    parametros = configuracao.get(
        'q_learning' if argumentos.agente in ('q', 'q_learning') else argumentos.agente, {})
    episodios_treino = argumentos.episodios or parametros.get('episodios', 0)

    randomizar = None if not argumentos.sem_randomizacao else False

    percurso_treino = Percurso.carregar(caminho_mapa, definicao)
    nome_treino = definicao['nome']
    rotulo_treino = configuracao_modulo.rotulo_modelo(configuracao, nome_treino)

    percursos_treino = [percurso_treino]
    percursos_avaliacao = [percurso_treino]
    if argumentos.gerados:
        # Corredores gerados: treinar numa distribuicao em vez de num percurso
        # so. So da para fazer isso porque o treino e offline; no servidor
        # real, cada mapa novo exigiria construir o mapa.
        from tools.gerar_percurso import corredor_aleatorio
        percursos_treino = []
        for indice in range(argumentos.gerados):
            mapa = corredor_aleatorio(999, 999 + argumentos.comprimento_gerado,
                                      semente=indice, nome=f'gerado_{indice:03d}')
            percursos_treino.append(Percurso(
                mapa, 999, 999 + argumentos.comprimento_gerado,
                nome=f'gerado_{indice:03d}'))
        percursos_treino = [p for p in percursos_treino if p.tem_solucao()]

        # Avaliacao em corredores da mesma familia, mas que o agente nunca viu.
        # Avaliar nos mesmos corredores do treino mediria memorizacao, que e
        # justamente o que este experimento quer evitar.
        percursos_avaliacao = []
        for indice in range(10000, 10000 + max(5, argumentos.gerados // 4)):
            mapa = corredor_aleatorio(999, 999 + argumentos.comprimento_gerado,
                                      semente=indice, nome=f'novo_{indice}')
            percurso = Percurso(mapa, 999, 999 + argumentos.comprimento_gerado,
                                nome=f'novo_{indice}')
            if percurso.tem_solucao():
                percursos_avaliacao.append(percurso)

        nome_treino = f'gerados_{len(percursos_treino)}'
        rotulo_treino = configuracao_modulo.rotulo_modelo(configuracao, nome_treino)
        print(f"treinando em {len(percursos_treino)} corredores gerados "
              f"(dos {argumentos.gerados} sorteados, os que tem solucao)")
        print(f"avaliando em {len(percursos_avaliacao)} corredores novos, "
              f"nunca vistos no treino")

    print(f"cenario={configuracao.get('cenario', 'padrao')}")
    print(percurso_treino.resumo())
    print(f"agente={argumentos.agente}  sementes={sementes}  "
          f"treino={episodios_treino}  avaliacao={episodios_avaliacao}")

    registros = []
    for semente in sementes:
        print(f"\n  semente {semente}")
        ambientes_treino = [AmbienteParkour(percurso, configuracao,
                                            semente=semente, randomizar=randomizar)
                            for percurso in percursos_treino]
        agente = criar_agente(argumentos.agente, ambientes_treino[0],
                              configuracao, semente)

        if episodios_treino:
            rodar_fase(ambientes_treino, agente, episodios_treino, 'treino', True,
                       argumentos.agente, nome_treino, semente, registros,
                       argumentos.a_cada)

        # A avaliacao roda com exploracao zero, no ambiente sem ruido: o que se
        # quer medir e a politica aprendida, nao a sorte do sorteio.
        agente.modo_avaliacao()
        ambientes_avaliacao = [
            AmbienteParkour(percurso, configuracao,
                            semente=1000 + semente, randomizar=False)
            for percurso in percursos_avaliacao]
        rotulo_avaliacao = (definicao['nome'] if len(percursos_avaliacao) == 1
                            else f'novos_{len(percursos_avaliacao)}')
        rodar_fase(ambientes_avaliacao, agente, episodios_avaliacao, 'avaliacao',
                   False, argumentos.agente, rotulo_avaliacao, semente, registros)

        for nome_trecho in (argumentos.avaliar_em or []):
            outra_definicao = configuracao_modulo.trecho(configuracao, nome_trecho)
            outro = Percurso.carregar(
                configuracao_modulo.caminho_mapa(configuracao, outra_definicao),
                outra_definicao)
            ambiente_outro = AmbienteParkour(outro, configuracao,
                                             semente=2000 + semente, randomizar=False)
            rodar_fase(ambiente_outro, agente, episodios_avaliacao,
                       f'generalizacao:{nome_trecho}', False, argumentos.agente,
                       nome_trecho, semente, registros)

        if hasattr(agente, 'salvar') and argumentos.agente in ('q', 'q_learning', 'dqn'):
            modelo = os.path.join(
                configuracao_modulo.RAIZ, 'resultados', 'modelos',
                f"{argumentos.agente}_{rotulo_treino}_s{semente}.json")
            agente.salvar(modelo)

    carimbo = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_arquivo = argumentos.saida or os.path.join(
        configuracao_modulo.RAIZ, 'resultados', 'metricas',
        f"{argumentos.agente}_{rotulo_treino}_{carimbo}.csv")
    gravar_csv(registros, nome_arquivo)

    print("\n  resultados (media das sementes):")
    fases = []
    for linha in registros:
        if linha['fase'] not in fases:
            fases.append(linha['fase'])
    for fase in fases:
        resumo = resumir(registros, fase)
        print(f"    {fase:<24} conclusao {resumo['conclusao']:6.1%}  "
              f"recompensa {resumo['recompensa']:8.2f}  "
              f"progresso {resumo['progresso']:6.1%}  "
              f"quedas {resumo['quedas']:6.1%}")
    print(f"\n  csv: {os.path.relpath(nome_arquivo, configuracao_modulo.RAIZ)}")


if __name__ == '__main__':
    main()
