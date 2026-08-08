"""Exporta a geometria de um percurso de parkour para JSON.

Le os arquivos .mca do mundo salvo e grava um arquivo pequeno que o simulador
carrega em memoria. Isso substitui as chamadas bot.blockAt() durante o treino:
a ponte JSPyBridge faz uma ida-e-volta entre processos a cada acesso, o que
tornaria o treinamento lento demais.

Uso tipico:

    python -m tools.mapear_mundo
    python -m tools.mapear_mundo --perfil
    python -m tools.mapear_mundo --mundo Servidor-BOT/world_labirinto \\
        --saida config/mapas/world_labirinto.json
"""

import argparse
import collections
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import blocos as classificacao
from tools.nbt import Mundo
from src.parkour import geometria

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def detectar_pistas(mundo, centro_x, z_min, z_max, y_min, y_max, raio=16):
    """Descobre quais colunas de x formam o piso do corredor.

    Uma coluna e considerada pista quando tem chao solido na maior parte dos z
    do intervalo. Assim a ferramenta funciona em outros mapas, nao so neste.
    """
    total_z = z_max - z_min + 1
    caixa = mundo.blocos_na_caixa(centro_x - raio, centro_x + raio, y_min, y_max, z_min, z_max)

    # Para cada altura candidata, conta em quantas colunas (x, z) existe um
    # bloco solido logo abaixo com espaco livre acima: e o formato de um piso.
    votos_altura = collections.Counter()
    for x in range(centro_x - raio, centro_x + raio + 1):
        for z in range(z_min, z_max + 1):
            for y in range(y_min + 1, y_max):
                abaixo = caixa.get((x, y - 1, z))
                if not abaixo or classificacao.altura_colisao(abaixo) < 1.0:
                    continue
                aqui = caixa.get((x, y, z))
                acima = caixa.get((x, y + 1, z))
                if (aqui is None or classificacao.altura_colisao(aqui) == 0.0) and \
                   (acima is None or classificacao.altura_colisao(acima) == 0.0):
                    votos_altura[y] += 1
                    break

    if not votos_altura:
        raise SystemExit("nenhum piso encontrado na area indicada; confira as coordenadas")

    y_pe = votos_altura.most_common(1)[0][0]

    votos_x = collections.Counter()
    for x in range(centro_x - raio, centro_x + raio + 1):
        for z in range(z_min, z_max + 1):
            abaixo = caixa.get((x, y_pe - 1, z))
            if abaixo and classificacao.altura_colisao(abaixo) >= 1.0:
                votos_x[x] += 1

    # O limite e relativo a melhor coluna, nao ao intervalo pedido: assim pedir
    # um intervalo de z maior que o corredor nao quebra a deteccao.
    if not votos_x:
        raise SystemExit("nenhuma pista encontrada; confira o centro e o intervalo de z")
    limite = max(votos_x.values()) * 0.6
    candidatas = sorted(x for x, votos in votos_x.items() if votos >= limite)

    # Fica so com o trecho continuo que contem o centro.
    pistas = [centro_x] if centro_x in candidatas else [candidatas[0]]
    x = pistas[0] - 1
    while x in candidatas:
        pistas.insert(0, x)
        x -= 1
    x = pistas[-1] + 1
    while x in candidatas:
        pistas.append(x)
        x += 1

    return pistas, y_pe


def ler_estagios(mundo, x_min, x_max, z_min, z_max):
    """Descobre os estagios a partir das placas do mapa."""
    placas = []
    for entidade in mundo.entidades_de_bloco(x_min, x_max, z_min, z_max):
        if entidade.get('id') != 'minecraft:sign':
            continue
        linhas = entidade.get('front_text', {}).get('messages', [])
        texto = ' '.join(linha for linha in linhas if linha).strip()
        if texto:
            placas.append((entidade['z'], entidade['x'], entidade['y'], texto))

    placas.sort()
    estagios = []
    for indice, (z, x, y, texto) in enumerate(placas):
        z_fim = placas[indice + 1][0] - 1 if indice + 1 < len(placas) else z_max
        estagios.append({
            'nome': texto,
            'z_inicio': z + 1,
            'z_fim': z_fim,
            'placa': [x, y, z],
        })
    return estagios


def mapear(pasta_mundo, centro_x, z_min, z_max, y_min, y_max, margem_x):
    mundo = Mundo(pasta_mundo)
    pistas, y_pe = detectar_pistas(mundo, centro_x, z_min, z_max, y_min, y_max)

    x_min = min(pistas) - margem_x
    x_max = max(pistas) + margem_x
    caixa = mundo.blocos_na_caixa(x_min, x_max, y_min, y_max, z_min, z_max)

    solidos = collections.defaultdict(list)
    avisos = collections.Counter()
    nomes = {}
    for (x, y, z), nome in sorted(caixa.items(), key=lambda item: (item[0][2], item[0][0], item[0][1])):
        # O aviso vem antes do filtro: blocos sem colisao tambem podem estar
        # mal classificados, e a escada e o exemplo obvio disso.
        if classificacao.precisa_validar(nome):
            avisos[nome.split(':')[-1]] += 1
        altura, largura = classificacao.caixa_colisao(nome)
        if altura <= 0.0:
            continue
        solidos[str(z)].append([x, y, round(altura, 4), round(largura, 4)])
        nomes[f'{x},{y},{z}'] = nome.split(':')[-1]

    # O fim do percurso e o ultimo z que ainda tem construcao.
    z_construido = [int(z) for z in solidos]
    z_fim_real = max(z_construido) if z_construido else z_max

    estagios = ler_estagios(mundo, x_min, x_max, z_min, z_max)
    for estagio in estagios:
        estagio['z_fim'] = min(estagio['z_fim'], z_fim_real)

    mapa = {
        'meta': {
            'mundo': os.path.basename(os.path.normpath(pasta_mundo)),
            'gerado_por': 'tools/mapear_mundo.py',
            'gerado_em': datetime.datetime.now().isoformat(timespec='seconds'),
            'caixa': {'x': [x_min, x_max], 'y': [y_min, y_max], 'z': [z_min, z_fim_real]},
        },
        'eixo': 'z',
        'pistas': pistas,
        'y_pe': y_pe,
        'estagios': estagios,
        'blocos_a_validar': dict(avisos),
        'nomes': nomes,
        'solidos': dict(solidos),
    }

    # Cada estagio tem a propria altura de chao e o proprio trecho andavel.
    for estagio in mapa['estagios']:
        estagio['y_pe'] = calcular_y_pe(mapa, estagio['z_inicio'], estagio['z_fim'])
        estagio['trechos_andaveis'] = trechos_andaveis(
            mapa, estagio['z_inicio'], estagio['z_fim'], estagio['y_pe'])

    return mapa


def calcular_y_pe(mapa, z_inicio, z_fim):
    """Descobre a altura de caminhada de um trecho.

    Cada estagio deste mapa comeca num portico elevado, entao a altura do chao
    muda de estagio para estagio. Um y_pe unico so serviria para o primeiro.
    """
    votos = collections.Counter()
    for z in range(z_inicio, z_fim + 1):
        por_coluna = collections.defaultdict(dict)
        for x, y, altura, largura in mapa['solidos'].get(str(z), []):
            por_coluna[x][y] = altura
        for x in mapa['pistas']:
            alturas = por_coluna[x]
            for y, altura in alturas.items():
                if altura < 1.0:
                    continue
                if alturas.get(y + 1, 0.0) == 0.0 and alturas.get(y + 2, 0.0) == 0.0:
                    votos[y + 1] += 1
    return votos.most_common(1)[0][0] if votos else mapa['y_pe']


def vaos_livres(mapa, z, y_pe=None):
    """Intervalos de x por onde da para passar andando, num dado z.

    So repassa para src/parkour/geometria.py: a ferramenta e o simulador
    precisam usar exatamente a mesma definicao de "o jogador cabe aqui".
    """
    return geometria.vaos_livres(
        mapa['solidos'].get(str(z), []),
        min(mapa['pistas']), max(mapa['pistas']) + 1,
        mapa['y_pe'] if y_pe is None else y_pe)


def posicoes_validas(mapa, z, y_pe=None):
    """Onde o centro do jogador pode ficar, num dado z."""
    return geometria.posicoes_validas(
        mapa['solidos'].get(str(z), []),
        min(mapa['pistas']), max(mapa['pistas']) + 1,
        mapa['y_pe'] if y_pe is None else y_pe)


def trechos_andaveis(mapa, z_inicio, z_fim, y_pe=None, minimo=8):
    """Devolve todos os trechos seguidos que da para vencer andando.

    Cada estagio comeca num portico que e solido na altura do chao: a passagem
    entre estagios acontece por cima dele. Por isso a busca nao para no
    primeiro obstaculo, e sim recolhe todos os trechos continuos.

    Serve para escolher o trecho de treino a partir dos dados, em vez de no
    olho: qualquer mudanca na classificacao dos blocos move estes limites
    sozinha.
    """
    y_pe = calcular_y_pe(mapa, z_inicio, z_fim) if y_pe is None else y_pe
    validas = {z: posicoes_validas(mapa, z, y_pe)
               for z in range(z_inicio, z_fim + 1)}

    def ate_onde_chega(partida):
        """Propaga quais passagens continuam alcancaveis, uma a uma.

        Perguntar "algum intervalo de z toca algum intervalo de z+1" nao
        basta: o estagio Copper tem passagem em z=1217 so pela esquerda e em
        z=1219 so pela direita, e o z=1218 do meio tem as duas. Comparando os
        z aos pares o caminho parece existir, mas quem entrou pela esquerda
        nunca alcanca a direita. E preciso arrastar o conjunto alcancavel.
        """
        alcancaveis = validas[partida]
        if not alcancaveis:
            return partida - 1
        ultimo = partida
        for z in range(partida + 1, z_fim + 1):
            adiante = [intervalo for intervalo in validas[z]
                       if geometria.intervalos_se_cruzam([intervalo], alcancaveis)]
            if not adiante:
                break
            alcancaveis = adiante
            ultimo = z
        return ultimo

    trechos = []
    for partida in range(z_inicio, z_fim + 1):
        chegada = ate_onde_chega(partida)
        if chegada - partida + 1 >= minimo:
            trechos.append([partida, chegada])

    # Fica so com os trechos maximos: um contido em outro nao acrescenta nada.
    maximos = []
    for inicio, fim in trechos:
        if not any(outro_inicio <= inicio and fim <= outro_fim
                   for outro_inicio, outro_fim in trechos
                   if (outro_inicio, outro_fim) != (inicio, fim)):
            maximos.append([inicio, fim])
    return maximos


def imprimir_perfil(mapa, z_inicio=None, z_fim=None):
    """Mostra uma tabela legivel para conferir o mapa contra o jogo."""
    y_pe = mapa['y_pe']
    z_inicio = z_inicio if z_inicio is not None else mapa['meta']['caixa']['z'][0]
    z_fim = z_fim if z_fim is not None else mapa['meta']['caixa']['z'][1]

    print(f"pistas x={mapa['pistas']}  y_pe={y_pe}"
          f"  largura do jogador={geometria.LARGURA_JOGADOR}")
    print(f"{'z':>6}  {'vaos livres em x':<34}  {'largura':>7}  situacao")
    intransponiveis = []
    for z in range(z_inicio, z_fim + 1):
        tem_obstaculo = any(y >= y_pe for _, y, _, _ in mapa['solidos'].get(str(z), []))
        if not tem_obstaculo:
            continue

        vaos = vaos_livres(mapa, z)
        if not vaos:
            intransponiveis.append(z)
            print(f"{z:>6}  {'(nenhum)':<34}  {0.0:>7.2f}  INTRANSPONIVEL andando")
            continue

        texto = ' '.join(f"[{inicio:.2f},{fim:.2f}]" for inicio, fim in vaos)
        maior = max(fim - inicio for inicio, fim in vaos)
        print(f"{z:>6}  {texto:<34}  {maior:>7.2f}  {len(vaos)} vao(s)")

    if intransponiveis:
        print(f"\n{len(intransponiveis)} valores de z sem passagem andando: {intransponiveis}")
        print("esses exigem pular por cima, escalar, ou indicam bloco mal classificado")


def _trechos_fora_do_alcance(z_min, z_max):
    """Trechos do config que uma varredura z_min..z_max deixaria de fora."""
    caminho = os.path.join(RAIZ, 'config', 'parkour.json')
    try:
        with open(caminho, encoding='utf-8') as arquivo:
            trechos = json.load(arquivo).get('trechos', {})
    except (OSError, ValueError):
        return []       # sem config legivel nao ha o que verificar
    faltantes = []
    for nome, definicao in sorted(trechos.items()):
        if not isinstance(definicao, dict) or nome.startswith('_'):
            continue
        z_inicio, z_meta = definicao.get('z_inicio'), definicao.get('z_meta')
        if z_inicio is None or z_meta is None:
            continue
        if z_inicio < z_min or z_meta > z_max:
            faltantes.append((nome, z_inicio, z_meta))
    return faltantes


def main():
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument('--mundo', default='Servidor-BOT/world_parkour',
                            help='pasta do mundo, relativa a raiz do repositorio')
    analisador.add_argument('--permitir-parcial', action='store_true',
                            help='grava mesmo que a varredura nao cubra todos '
                                 'os trechos de config/parkour.json')
    analisador.add_argument('--saida', default=None,
                            help='arquivo JSON de saida (padrao: config/mapas/<mundo>.json)')
    analisador.add_argument('--centro-x', type=int, default=1000,
                            help='x aproximado do meio do corredor')
    # O padrao precisa cobrir TODOS os trechos de config/parkour.json. Ja
    # custou caro: com o antigo [996, 1290], rodar a ferramenta sem --z
    # reexportava o mapa sem os estagios Nether e End, e os trechos nether,
    # end e end2 passavam a apontar para z inexistente. O sintoma aparecia
    # longe da causa, como tres testes falhando com "o guloso chega ao fim".
    analisador.add_argument('--z', type=int, nargs=2, default=[996, 1400], metavar=('MIN', 'MAX'),
                            help='intervalo de z a varrer')
    analisador.add_argument('--y', type=int, nargs=2, default=[96, 124], metavar=('MIN', 'MAX'),
                            help='intervalo de y a varrer')
    analisador.add_argument('--margem-x', type=int, default=1,
                            help='colunas extras exportadas de cada lado das pistas')
    analisador.add_argument('--perfil', action='store_true',
                            help='imprime a tabela de obstaculos para conferencia')
    argumentos = analisador.parse_args()

    pasta_mundo = os.path.join(RAIZ, argumentos.mundo)
    saida = argumentos.saida or os.path.join(
        RAIZ, 'config', 'mapas', os.path.basename(os.path.normpath(pasta_mundo)) + '.json')

    mapa = mapear(pasta_mundo, argumentos.centro_x,
                  argumentos.z[0], argumentos.z[1],
                  argumentos.y[0], argumentos.y[1],
                  argumentos.margem_x)

    # Trava contra o erro que este arquivo ja cometeu: sobrescrever o mapa com
    # uma varredura curta demais, deixando trechos do config apontando para z
    # que nao existe mais. Melhor recusar do que gravar um mapa mutilado.
    faltantes = _trechos_fora_do_alcance(argumentos.z[0], argumentos.z[1])
    if faltantes and not argumentos.permitir_parcial:
        print(f"[ERRO] a varredura z={argumentos.z[0]}..{argumentos.z[1]} nao cobre "
              f"estes trechos de config/parkour.json:")
        for nome, z_inicio, z_meta in faltantes:
            print(f"        {nome}: z {z_inicio}-{z_meta}")
        print("       Gravar assim quebraria esses trechos. Amplie --z, ou use")
        print("       --permitir-parcial se a reducao for intencional.")
        return 1

    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, 'w', encoding='utf-8') as arquivo:
        json.dump(mapa, arquivo, ensure_ascii=False, separators=(',', ':'))

    caixa = mapa['meta']['caixa']
    total = sum(len(lista) for lista in mapa['solidos'].values())
    print(f"mundo   : {mapa['meta']['mundo']}")
    print(f"pistas  : x={mapa['pistas']}   y_pe={mapa['y_pe']}")
    print(f"caixa   : x={caixa['x']}  y={caixa['y']}  z={caixa['z']}")
    print(f"solidos : {total} blocos em {len(mapa['solidos'])} valores de z")
    print(f"saida   : {os.path.relpath(saida, RAIZ)}")

    print("\nestagios (o trecho andavel e o que da para vencer sem escalar):")
    for estagio in mapa['estagios']:
        comprimento = estagio['z_fim'] - estagio['z_inicio'] + 1
        texto = '  '.join(f"{inicio}-{fim} ({fim - inicio + 1})"
                          for inicio, fim in estagio['trechos_andaveis']) or '(nenhum)'
        print(f"  {estagio['nome']:<18} z {estagio['z_inicio']:>4}-{estagio['z_fim']:<4}"
              f" ({comprimento:>3} blocos)  y_pe={estagio['y_pe']}   andaveis: {texto}")

    if mapa['blocos_a_validar']:
        print("\nblocos cuja colisao ainda e um palpite (validar em jogo):")
        for nome, quantidade in sorted(mapa['blocos_a_validar'].items(),
                                       key=lambda item: -item[1]):
            print(f"  {quantidade:>5}x {nome:<20} {classificacao.motivo_validacao(nome)}")

    if argumentos.perfil:
        print()
        imprimir_perfil(mapa)


if __name__ == '__main__':
    raise SystemExit(main() or 0)
