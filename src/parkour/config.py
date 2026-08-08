"""Leitura dos arquivos de configuracao.

Sao dois arquivos, de proposito:

- config/parkour.json  versionado, e o que o grupo edita para experimentar;
- config/bot.json      ignorado pelo Git, guarda o IP de cada integrante.

Chaves que comecam com '_' sao comentarios e somem na leitura.
"""

import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAMINHO_PARKOUR = os.path.join(RAIZ, 'config', 'parkour.json')
CAMINHO_BOT = os.path.join(RAIZ, 'config', 'bot.json')
CAMINHO_BOT_EXEMPLO = os.path.join(RAIZ, 'config', 'bot.json.exemplo')


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


def carregar(caminho=None):
    """Le config/parkour.json."""
    return carregar_json(caminho or CAMINHO_PARKOUR)


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


def trecho(configuracao, nome=None):
    """Devolve a definicao de um trecho pelo nome, ou o trecho padrao."""
    nome = nome or configuracao.get('trecho_padrao', 'A')
    trechos = configuracao['trechos']
    if nome not in trechos:
        disponiveis = ', '.join(sorted(trechos))
        raise SystemExit(f"trecho '{nome}' nao existe. Disponiveis: {disponiveis}")
    definicao = dict(trechos[nome])
    definicao['nome'] = nome
    return definicao
