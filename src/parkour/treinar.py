"""Laco de Q-Learning usado pelo bot dentro do Minecraft.

Este modulo nao simula o jogo e nao possui um comando proprio. O ponto de
entrada e ``python -m src.parkour.main``; aqui ficam apenas as funcoes pequenas
que organizam episodios e registram resultados.
"""

import csv
import os

from . import acoes, config as configuracao_modulo, estado
from .q_learning import QLearning


COLUNAS_RESULTADO = (
    'fase', 'episodio', 'recompensa', 'passos', 'progresso',
    'progresso_valido', 'altura_final', 'z_maximo_valido', 'chegou',
    'motivo', 'exploracao', 'acoes',
)


def caminho_padrao_modelo(configuracao, nome_trecho):
    rotulo = configuracao_modulo.rotulo_modelo(configuracao, nome_trecho)
    return os.path.join(
        configuracao_modulo.RAIZ,
        'resultados',
        'modelos',
        f'q_learning_{rotulo}_acoes_v{acoes.VERSAO_CATALOGO}'
        f'_estado_v{estado.VERSAO_ESTADO}.json',
    )


def caminho_resultados(caminho_modelo):
    return os.path.splitext(caminho_modelo)[0] + '_resultado.csv'


def criar_agente(ambiente, configuracao, semente=None):
    return QLearning(
        ambiente.quantidade_estados,
        ambiente.quantidade_acoes,
        configuracao_modulo.parametros_q_learning(configuracao),
        semente=semente,
    )


def rodar_episodio(ambiente, agente, aprender=True, parar_pedido=None):
    """Executa um episodio no jogo e devolve suas informacoes finais."""
    estado, _ = ambiente.reset()
    recompensa_total = 0.0
    contagem_acoes = [0] * agente.quantidade_acoes

    def finalizar(informacoes):
        informacoes['recompensa'] = recompensa_total
        informacoes['acoes'] = ';'.join(
            f'{acoes.nome_de(indice)}={quantidade}'
            for indice, quantidade in enumerate(contagem_acoes)
            if quantidade
        )
        return informacoes

    while True:
        if parar_pedido is not None and parar_pedido.is_set():
            if hasattr(ambiente, 'soltar_controles'):
                ambiente.soltar_controles()
            return finalizar({
                **ambiente.informacoes(),
                'motivo': 'interrompido',
            })

        acao = agente.escolher_acao(estado)
        contagem_acoes[acao] += 1
        proximo_estado, recompensa, terminou, truncou, informacoes = \
            ambiente.passo(acao)

        if aprender:
            # Fim por tempo ainda possui um estado fisicamente valido.
            agente.aprender(
                estado, acao, recompensa, proximo_estado, terminou
            )

        estado = proximo_estado
        recompensa_total += recompensa
        if terminou or truncou:
            break

    return finalizar(informacoes)


def acrescentar_resultado(caminho, fase, episodio, informacoes, exploracao):
    """Acrescenta um episodio ao CSV sem apagar sessoes anteriores."""
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    precisa_cabecalho = not os.path.isfile(caminho) or os.path.getsize(caminho) == 0
    linha = {
        'fase': fase,
        'episodio': episodio,
        'recompensa': round(informacoes['recompensa'], 4),
        'passos': informacoes['passos'],
        'progresso': round(informacoes['progresso'], 4),
        'progresso_valido': round(
            informacoes.get('progresso_valido', informacoes['progresso']), 4
        ),
        'altura_final': round(informacoes.get('y', 0.0), 4),
        'z_maximo_valido': round(
            informacoes.get('z_maximo_valido', 0.0), 4
        ),
        'chegou': int(informacoes['chegou']),
        'motivo': informacoes['motivo'],
        'exploracao': round(exploracao, 6),
        'acoes': informacoes.get('acoes', ''),
    }
    with open(caminho, 'a', newline='', encoding='utf-8') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_RESULTADO)
        if precisa_cabecalho:
            escritor.writeheader()
        escritor.writerow(linha)
