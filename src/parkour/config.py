"""Leitura dos arquivos de configuracao.

Sao dois arquivos, de proposito:

- config/parkour.json  parametros comuns do treinamento no jogo;
- config/cenarios/     mundo, mapa e trechos escolhidos para uma execucao;
- config/bot.json      ignorado pelo Git, guarda o IP de cada integrante.

Chaves que comecam com '_' sao comentarios e somem na leitura.
"""

import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAMINHO_PARKOUR = os.path.join(RAIZ, 'config', 'parkour.json')
PASTA_CENARIOS = os.path.join(RAIZ, 'config', 'cenarios')
CAMINHO_BOT = os.path.join(RAIZ, 'config', 'bot.json')
CAMINHO_BOT_EXEMPLO = os.path.join(RAIZ, 'config', 'bot.json.exemplo')
CAMINHO_SERVIDOR = os.path.join(RAIZ, 'Servidor-BOT', 'server.properties')


def _sem_comentarios(valor):
    if isinstance(valor, dict):
        return {chave: _sem_comentarios(item)
                for chave, item in valor.items() if not chave.startswith('_')}
    if isinstance(valor, list):
        return [_sem_comentarios(item) for item in valor]
    return valor


def carregar_json(caminho):
    with open(caminho, encoding='utf-8') as arquivo:
        return _sem_comentarios(json.load(arquivo))


def caminho_cenario(nome):
    """Resolve um nome curto, sem permitir que ele escape de config/cenarios."""
    if not nome or nome != os.path.basename(nome):
        raise SystemExit(f"nome de cenario invalido: {nome!r}")
    if not nome.endswith('.json'):
        nome += '.json'
    caminho = os.path.join(PASTA_CENARIOS, nome)
    if not os.path.isfile(caminho):
        disponiveis = ', '.join(cenarios_disponiveis()) or '(nenhum)'
        raise SystemExit(
            f"cenario '{os.path.splitext(nome)[0]}' nao existe. "
            f"Disponiveis: {disponiveis}")
    return caminho


def cenarios_disponiveis():
    if not os.path.isdir(PASTA_CENARIOS):
        return []
    return sorted(os.path.splitext(nome)[0]
                  for nome in os.listdir(PASTA_CENARIOS)
                  if nome.endswith('.json'))


def carregar(caminho=None, cenario=None):
    """Le os parametros comuns e, opcionalmente, sobrepoe um cenario.

    A sobreposicao e feita por chave de primeiro nivel. Assim um cenario troca
    ``mapa`` e ``trechos`` por inteiro. A secao ``recompensa`` e combinada para
    permitir uma regra especifica do cenario sem perder os pesos comuns.
    Sem ``cenario`` o comportamento antigo e preservado para compatibilidade.
    """
    configuracao = carregar_json(caminho or CAMINHO_PARKOUR)
    if cenario is None:
        return configuracao

    dados_cenario = carregar_json(caminho_cenario(cenario))
    if 'recompensa' in dados_cenario:
        recompensa_combinada = dict(configuracao.get('recompensa', {}))
        recompensa_combinada.update(dados_cenario['recompensa'])
        dados_cenario['recompensa'] = recompensa_combinada
    configuracao.update(dados_cenario)
    configuracao['cenario'] = cenario
    return configuracao


def carregar_bot():
    """Le config/bot.json, com uma mensagem util se ele ainda nao existe."""
    if not os.path.exists(CAMINHO_BOT):
        raise SystemExit(
            "config/bot.json nao existe.\n"
            f"Copie o modelo e ajuste o host e o usuario:\n"
            f"    cp {os.path.relpath(CAMINHO_BOT_EXEMPLO, RAIZ)} "
            f"{os.path.relpath(CAMINHO_BOT, RAIZ)}")
    return carregar_json(CAMINHO_BOT)


def caminho_absoluto(caminho_relativo):
    """Resolve um caminho do JSON em relacao a raiz do repositorio."""
    if os.path.isabs(caminho_relativo):
        return caminho_relativo
    return os.path.join(RAIZ, caminho_relativo)


def caminho_mapa(configuracao, definicao_trecho=None):
    """Mapa do trecho; um trecho pode sobrescrever o mapa geral do cenario."""
    caminho = None
    if definicao_trecho is not None:
        caminho = definicao_trecho.get('mapa')
    caminho = caminho or configuracao.get('mapa')
    if not caminho:
        raise SystemExit('o cenario/trecho nao informa o arquivo de mapa')
    return caminho_absoluto(caminho)


def trecho(configuracao, nome=None):
    """Devolve a definicao de um trecho pelo nome, ou o trecho padrao."""
    nome = nome or configuracao.get('trecho_padrao', 'A')
    trechos = configuracao['trechos']
    if nome not in trechos:
        disponiveis = ', '.join(sorted(trechos))
        raise SystemExit(f"trecho '{nome}' nao existe. Disponiveis: {disponiveis}")
    definicao = dict(trechos[nome])
    definicao['nome'] = nome
    if configuracao.get('mundo'):
        definicao.setdefault('mundo', configuracao['mundo'])
    return definicao


def mundo_servidor_local():
    """Le ``level-name`` do PaperMC local, sem iniciar nem alterar o servidor."""
    try:
        with open(CAMINHO_SERVIDOR, encoding='utf-8') as arquivo:
            for linha in arquivo:
                if linha.startswith('level-name='):
                    return linha.split('=', 1)[1].strip()
    except OSError:
        return None
    return None


def cenario_para_mundo(mundo):
    """Encontra o cenario que declara o mundo informado, se houver um unico."""
    encontrados = []
    for nome in cenarios_disponiveis():
        try:
            if carregar_json(caminho_cenario(nome)).get('mundo') == mundo:
                encontrados.append(nome)
        except (OSError, ValueError):
            continue
    return encontrados[0] if len(encontrados) == 1 else None


def validar_mundo_local(configuracao, dados_bot):
    """Impede executar um cenario no mundo local errado.

    Para servidor remoto nao ha como confiar no ``server.properties`` desta
    copia do repositorio, entao a verificacao e feita apenas para localhost.
    """
    esperado = configuracao.get('mundo')
    host = str(dados_bot.get('host', '')).lower()
    if not esperado or host not in ('localhost', '127.0.0.1', '::1'):
        return
    atual = mundo_servidor_local()
    if atual and atual != esperado:
        cenario = configuracao.get('cenario', 'padrao')
        raise SystemExit(
            f"cenario '{cenario}' espera o mundo '{esperado}', mas "
            f"Servidor-BOT/server.properties usa '{atual}'.\n"
            "Pare o PaperMC com 'stop', ajuste level-name e so entao reinicie.")


def rotulo_modelo(configuracao, nome_trecho):
    """Evita carregar uma tabela Q de outro mundo com o mesmo nome de trecho."""
    cenario = configuracao.get('cenario')
    return f'{cenario}_{nome_trecho}' if cenario else nome_trecho


def parametros_q_learning(configuracao):
    """Parametros do Q mais restricoes opcionais especificas do cenario."""
    parametros = dict(configuracao.get('q_learning', {}))
    if 'acoes_q_learning' in configuracao:
        parametros['acoes_permitidas'] = configuracao['acoes_q_learning']
    return parametros
