"""Comparacao entre a trajetoria simulada e a trajetoria real.

Esta e a medida que sustenta todo o resto do projeto. Treinar fora do jogo so
vale se o simulador se parecer com o jogo, e "se parecer" precisa ser um
numero, nao uma impressao.

O procedimento:

1. no jogo, `parkour calibrar` roda uma sequencia fixa de acoes e grava a
   posicao do bot a cada tick;
2. aqui, a mesma sequencia roda no simulador;
3. comparamos as duas trajetorias tick a tick.

O criterio proposto e erro abaixo de 0.2 bloco depois de 40 ticks. Se o erro
passar disso, as constantes de fisica.py precisam de ajuste, ou o plano B
entra em campo (usar prismarine-physics, o mesmo motor que o mineflayer ja usa
internamente, num processo Node).

Uso:

    python -m src.parkour.calibracao --real resultados/metricas/trajetoria_real.json
"""

import argparse
import json
import math
import os

from . import config as configuracao_modulo
from . import fisica
from .ambiente_sim import AmbienteParkour
from .percurso import Percurso

# Sequencia usada na calibracao. Exercita de proposito o que mais importa:
# arrancada, velocidade de cruzeiro, pulo parado, pulo correndo e desvio
# lateral. Nao mude sem regravar a trajetoria real.
#
# Os desvios laterais sao curtos e alternados de proposito: a ponte tem 3
# blocos de largura e uma sequencia lateral longa jogaria o bot no vazio. A
# partir da queda, a comparacao so mede gravidade, e as constantes de
# caminhada - que sao as que mais importam - deixam de ser exercitadas.
# O trecho lateral e ASSIMETRICO de proposito. A versao anterior era
# esquerda-direita-esquerda em partes iguais: o deslocamento lateral se
# cancelava e o erro em x terminava em zero mesmo com os eixos trocados. Foi
# assim que a inversao de `direita`/`esquerda` entre o simulador e o mineflayer
# passou pela calibracao sem ser notada, ate a politica cair da ponte em jogo.
# Com 2 para um lado e 6 para o outro, uma inversao vira erro grande em x.
SEQUENCIA_PADRAO = (
    [0] * 10 +      # andar: aceleracao e velocidade de cruzeiro
    [1] * 10 +      # correr: velocidade maior
    [2] * 6 +       # correr e pular: altura e alcance do salto
    [3] * 2 +       # desviar para a esquerda
    [4] * 6 +       # e voltar para a direita, indo alem do meio
    [5] * 4         # parar: desaceleracao com atrito do chao
)


def percurso_plano(configuracao):
    """Monta, no simulador, a mesma pista lisa que existe no jogo.

    A calibracao mede fisica: arrancada, velocidade, salto, atrito. Obstaculo
    no meio do caminho nao mede nada disso, so mede colisao - e foi o que
    aconteceu na primeira tentativa em jogo, com o bot parado num pilar desde
    o tick 24. Aqui os dois lados correm em chao liso, e a unica coisa que
    pode divergir e a fisica.

    A geometria vem do config para que o /fill do jogo e este percurso nao
    possam discordar em silencio.
    """
    pista = configuracao['calibracao']['pista']
    x_min, x_max = int(pista['x_min']), int(pista['x_max'])
    y_piso = int(pista['y_piso'])
    z_inicio, z_meta = int(pista['z_inicio']), int(pista['z_meta'])

    pistas = list(range(x_min, x_max + 1))
    solidos = {
        str(z): [[x, y_piso, 1.0, 1.0] for x in pistas]
        for z in range(z_inicio - 3, z_meta + 4)
    }
    mapa = {'pistas': pistas, 'y_pe': y_piso + 1, 'solidos': solidos}
    return Percurso(mapa, z_inicio, z_meta, y_pe=y_piso + 1, nome='pista_calibracao')


def simular(sequencia, nome_trecho=None, plana=False):
    """Roda a sequencia no simulador, gravando a posicao a cada tick."""
    configuracao = configuracao_modulo.carregar()
    if plana:
        percurso = percurso_plano(configuracao)
    else:
        definicao = configuracao_modulo.trecho(configuracao, nome_trecho)
        percurso = Percurso.carregar(
            configuracao_modulo.caminho_absoluto(configuracao['mapa']), definicao)

    # Sem sorteio de posicao inicial e sem ruido na fisica: a comparacao so
    # faz sentido se as duas trajetorias comecarem no mesmo ponto. O bot no
    # jogo e teleportado para percurso.x_partida, que e fixo.
    ambiente = AmbienteParkour(percurso, configuracao, semente=0, randomizar=False)
    ambiente.variar_inicio = False
    ambiente.reset()

    amostras = [{'tick': 0, 'x': ambiente.corpo.x, 'y': ambiente.corpo.y,
                 'z': ambiente.corpo.z, 'acao': None}]
    tick = 0
    from . import acoes as catalogo
    for acao in sequencia:
        entradas = catalogo.entradas_de(acao)
        for _ in range(ambiente.ticks_por_acao):
            fisica.passo_tick(percurso, ambiente.constantes, ambiente.corpo, entradas)
            tick += 1
            amostras.append({'tick': tick, 'x': ambiente.corpo.x,
                             'y': ambiente.corpo.y, 'z': ambiente.corpo.z,
                             'acao': catalogo.nome_de(acao)})
    return amostras


def comparar(reais, simuladas):
    """Erro entre as duas trajetorias, tick a tick."""
    por_tick = {amostra['tick']: amostra for amostra in simuladas}
    linhas = []
    for real in reais:
        simulada = por_tick.get(real['tick'])
        if simulada is None:
            continue
        dx = real['x'] - simulada['x']
        dy = real['y'] - simulada['y']
        dz = real['z'] - simulada['z']
        linhas.append({
            'tick': real['tick'],
            'acao': real.get('acao'),
            'erro': math.sqrt(dx * dx + dy * dy + dz * dz),
            'erro_x': dx,
            'erro_y': dy,
            'erro_z': dz,
        })
    return linhas


def por_fase(linhas):
    """Agrupa o erro por acao, na ordem em que as acoes aparecem.

    O erro de um tick isolado nao diz muito, porque a comparacao e de laco
    aberto: um atraso de um tick no comeco vira erro em todos os seguintes.
    O que interessa e onde o erro *cresce* - a fase que cresce e a fisica que
    esta errada.
    """
    # Agrupa por trecho contiguo, nao por nome: a sequencia usa `esquerda`
    # duas vezes, em momentos diferentes, e junta-las num grupo so produzia
    # uma linha com intervalo de ticks sobreposto ao da `direita` - ilegivel,
    # e pior, escondia que o erro cresce num trecho e cai no outro.
    grupos = []
    for linha in linhas:
        nome = linha['acao'] or 'inicio'
        if not grupos or grupos[-1][0] != nome:
            grupos.append((nome, [linha]))
        else:
            grupos[-1][1].append(linha)
    return grupos


def relatorio(linhas, limite=0.2):
    if not linhas:
        return "nenhum tick em comum entre as duas trajetorias"

    saida = [f"{'fase':<14} {'ticks':>9} {'erro no fim':>12} {'cresceu':>9} "
             f"{'pior':>8}", '-' * 56]

    pior_global, fase_pior = 0.0, '?'
    for nome, grupo in por_fase(linhas):
        entrada, saida_ = grupo[0]['erro'], grupo[-1]['erro']
        pior = max(item['erro'] for item in grupo)
        if pior > pior_global:
            pior_global, fase_pior = pior, nome
        saida.append(f"{nome:<14} {grupo[0]['tick']:>4}-{grupo[-1]['tick']:<4} "
                     f"{saida_:>12.4f} {saida_ - entrada:>+9.4f} {pior:>8.4f}")

    final = linhas[-1]
    saida.append('')
    saida.append(f"erro no fim da sequencia: {final['erro']:.4f} bloco "
                 f"(dx {final['erro_x']:+.4f}  dy {final['erro_y']:+.4f}  "
                 f"dz {final['erro_z']:+.4f})")
    saida.append(f"pior erro:                {pior_global:.4f} bloco, "
                 f"na fase '{fase_pior}'")
    saida.append(f"criterio: pior erro abaixo de {limite} bloco")
    saida.append('')

    # O criterio olha o pior erro da sequencia inteira, nao um tick escolhido.
    # A versao antiga media o tick 40, que caia no meio da caminhada: dava
    # APROVADO sem nunca ter comparado um salto. Ver docs/sim_para_real.md.
    if pior_global <= limite:
        saida.append("APROVADO: o simulador esta perto o bastante do jogo.")
    else:
        saida.append("REPROVADO: ajustar as constantes em src/parkour/fisica.py,")
        saida.append("ou passar ao plano B com prismarine-physics.")
        saida.append("A coluna 'cresceu' aponta a fase culpada. Erro so em z")
        saida.append("sugere velocidade; so em y, gravidade ou pulo; em x com")
        saida.append("dz certo, eixo trocado.")
    return '\n'.join(saida)


def main():
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument('--real', required=True,
                            help='JSON gravado em jogo por `parkour calibrar`')
    analisador.add_argument('--trecho', default=None)
    analisador.add_argument('--limite', type=float, default=0.2)
    argumentos = analisador.parse_args()

    with open(configuracao_modulo.caminho_absoluto(argumentos.real),
              encoding='utf-8') as arquivo:
        dados = json.load(arquivo)

    reais = dados['amostras'] if isinstance(dados, dict) else dados
    sequencia = dados.get('sequencia', SEQUENCIA_PADRAO) if isinstance(dados, dict) \
        else SEQUENCIA_PADRAO

    # A gravacao diz em que pista rodou. Comparar uma corrida feita na pista
    # lisa contra um simulador cheio de obstaculos mediria colisao, nao fisica.
    plana = bool(dados.get('pista_plana')) if isinstance(dados, dict) else False
    simuladas = simular(sequencia,
                        argumentos.trecho or
                        (dados.get('trecho') if isinstance(dados, dict) else None),
                        plana=plana)
    linhas = comparar(reais, simuladas)
    if plana:
        print("pista lisa de calibracao (nao o percurso)\n")
    print(relatorio(linhas, argumentos.limite))

    destino = os.path.join(configuracao_modulo.RAIZ, 'resultados', 'metricas',
                           'calibracao.json')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'w', encoding='utf-8') as arquivo:
        json.dump({'comparacao': linhas}, arquivo, indent=2)
    print(f"\ndetalhe: {os.path.relpath(destino, configuracao_modulo.RAIZ)}")


if __name__ == '__main__':
    main()
