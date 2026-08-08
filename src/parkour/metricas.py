"""Agregacao dos CSVs de experimento e geracao dos graficos.

Frente do integrante 5 (metodo experimental, pag. 5 do PDF). A pag. 6 pede
graficos e criterios de avaliacao; este modulo transforma os CSVs crus em
tabelas e figuras que entram no relatorio.

Funciona sem nenhuma dependencia externa: a tabela sai sempre. Se matplotlib
estiver instalado, saem tambem os graficos. Isso e de proposito, para que a
analise nao trave quando alguem do grupo ainda nao instalou tudo.

Uso:

    python -m src.parkour.metricas                    # resume tudo
    python -m src.parkour.metricas --graficos
    python -m src.parkour.metricas --arquivos resultados/metricas/q_A_*.csv
"""

import argparse
import csv
import glob
import math
import os

from . import config as configuracao_modulo

PASTA_METRICAS = os.path.join(configuracao_modulo.RAIZ, 'resultados', 'metricas')
PASTA_GRAFICOS = os.path.join(configuracao_modulo.RAIZ, 'resultados', 'graficos')

NUMERICAS = ('recompensa', 'passos', 'z_maximo', 'progresso', 'chegou')


def ler(caminhos):
    linhas = []
    for caminho in caminhos:
        with open(caminho, newline='', encoding='utf-8') as arquivo:
            for linha in csv.DictReader(arquivo):
                for chave in NUMERICAS:
                    linha[chave] = float(linha[chave])
                linha['episodio'] = int(linha['episodio'])
                linha['semente'] = int(linha['semente'])
                linhas.append(linha)
    return linhas


def media(valores):
    return sum(valores) / len(valores) if valores else 0.0


def desvio(valores):
    """Desvio padrao amostral. E ele que diz se uma diferenca entre dois
    agentes e maior que a variacao entre sementes, ou se e so ruido."""
    if len(valores) < 2:
        return 0.0
    m = media(valores)
    return math.sqrt(sum((valor - m) ** 2 for valor in valores) / (len(valores) - 1))


def agrupar(linhas, chaves):
    grupos = {}
    for linha in linhas:
        chave = tuple(linha[nome] for nome in chaves)
        grupos.setdefault(chave, []).append(linha)
    return grupos


def resumo_por_semente(linhas):
    """Media por semente, e depois media e desvio entre as sementes.

    Esta ordem importa: a media direta de todos os episodios daria mais peso
    a sementes com episodios mais longos, e esconderia a variacao que a gente
    justamente quer enxergar.
    """
    por_semente = agrupar(linhas, ('semente',))
    conclusoes = [media([linha['chegou'] for linha in grupo])
                  for grupo in por_semente.values()]
    recompensas = [media([linha['recompensa'] for linha in grupo])
                   for grupo in por_semente.values()]
    progressos = [media([linha['progresso'] for linha in grupo])
                  for grupo in por_semente.values()]
    quedas = [media([1.0 if linha['motivo'] == 'queda' else 0.0 for linha in grupo])
              for grupo in por_semente.values()]
    return {
        'sementes': len(por_semente),
        'episodios': len(linhas),
        'conclusao': media(conclusoes),
        'conclusao_desvio': desvio(conclusoes),
        'recompensa': media(recompensas),
        'recompensa_desvio': desvio(recompensas),
        'progresso': media(progressos),
        'quedas': media(quedas),
        'passos': media([linha['passos'] for linha in linhas]),
    }


def tabela(linhas, apenas_fase=None):
    """Tabela comparativa: uma linha por (agente, trecho, fase)."""
    if apenas_fase:
        linhas = [linha for linha in linhas if linha['fase'] == apenas_fase]

    cabecalho = (f"{'agente':<12} {'trecho':<12} {'fase':<22} {'n':>4} "
                 f"{'conclusao':>18} {'recompensa':>18} {'quedas':>8} {'passos':>8}")
    saida = [cabecalho, '-' * len(cabecalho)]

    for chave in sorted(agrupar(linhas, ('agente', 'trecho', 'fase'))):
        agente, trecho, fase = chave
        grupo = [linha for linha in linhas
                 if (linha['agente'], linha['trecho'], linha['fase']) == chave]
        resumo = resumo_por_semente(grupo)
        saida.append(
            f"{agente:<12} {trecho:<12} {fase:<22} {resumo['sementes']:>4} "
            f"{resumo['conclusao']:>10.1%} +-{resumo['conclusao_desvio']:>5.1%} "
            f"{resumo['recompensa']:>10.2f} +-{resumo['recompensa_desvio']:>5.2f} "
            f"{resumo['quedas']:>7.1%} {resumo['passos']:>8.1f}")
    return '\n'.join(saida)


def comparar(linhas, referencia='aleatorio', fase='avaliacao'):
    """Diz se a diferenca para a referencia e maior que a variacao entre sementes.

    Criterio de sucesso do plano: o agente treinado precisa superar a politica
    aleatoria por margem maior que o desvio entre as sementes. Sem isso, a
    diferenca pode ser sorte de sorteio.
    """
    da_fase = [linha for linha in linhas if linha['fase'] == fase]
    por_agente = agrupar(da_fase, ('agente', 'trecho'))

    base = {}
    for (agente, trecho), grupo in por_agente.items():
        if agente == referencia:
            base[trecho] = resumo_por_semente(grupo)

    saida = []
    for (agente, trecho), grupo in sorted(por_agente.items()):
        if agente == referencia or trecho not in base:
            continue
        resumo = resumo_por_semente(grupo)
        referencia_trecho = base[trecho]
        diferenca = resumo['conclusao'] - referencia_trecho['conclusao']
        margem = resumo['conclusao_desvio'] + referencia_trecho['conclusao_desvio']
        veredito = 'SUPERA' if diferenca > margem else 'inconclusivo'
        saida.append(
            f"  {agente} vs {referencia} em {trecho}: "
            f"{referencia_trecho['conclusao']:.1%} -> {resumo['conclusao']:.1%} "
            f"(diferenca {diferenca:+.1%}, variacao entre sementes +-{margem:.1%})  {veredito}")
    return '\n'.join(saida) or '  (sem par para comparar)'


# ----------------------------------------------------------------------
# graficos

def media_movel(valores, janela):
    if janela <= 1 or len(valores) < janela:
        return list(valores)
    saida, soma = [], 0.0
    for indice, valor in enumerate(valores):
        soma += valor
        if indice >= janela:
            soma -= valores[indice - janela]
        saida.append(soma / min(indice + 1, janela))
    return saida


def gerar_graficos(linhas, pasta=PASTA_GRAFICOS, janela=100):
    try:
        import matplotlib
        matplotlib.use('Agg')       # sem janela: grava direto em arquivo
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib nao instalado: pulando os graficos.")
        print("  instale com: python -m pip install matplotlib")
        return []

    os.makedirs(pasta, exist_ok=True)
    gerados = []

    # 1. Curva de aprendizado, com faixa entre as sementes.
    treino = [linha for linha in linhas if linha['fase'] == 'treino']
    if treino:
        figura, eixo = plt.subplots(figsize=(9, 5))
        for (agente, trecho), grupo in sorted(agrupar(treino, ('agente', 'trecho')).items()):
            curvas = []
            for semente_grupo in agrupar(grupo, ('semente',)).values():
                ordenado = sorted(semente_grupo, key=lambda linha: linha['episodio'])
                curvas.append(media_movel([linha['recompensa'] for linha in ordenado], janela))
            if not curvas:
                continue
            comprimento = min(len(curva) for curva in curvas)
            eixo_x = list(range(comprimento))
            medias = [media([curva[i] for curva in curvas]) for i in eixo_x]
            minimos = [min(curva[i] for curva in curvas) for i in eixo_x]
            maximos = [max(curva[i] for curva in curvas) for i in eixo_x]
            linha_grafico, = eixo.plot(eixo_x, medias, label=f"{agente} ({trecho})")
            eixo.fill_between(eixo_x, minimos, maximos, alpha=0.2,
                              color=linha_grafico.get_color())

        eixo.set_xlabel('episodio de treino')
        eixo.set_ylabel(f'recompensa (media movel de {janela})')
        eixo.set_title('Curva de aprendizado (faixa = variacao entre sementes)')
        eixo.legend()
        eixo.grid(alpha=0.3)
        caminho = os.path.join(pasta, 'curva_aprendizado.png')
        figura.tight_layout()
        figura.savefig(caminho, dpi=130)
        plt.close(figura)
        gerados.append(caminho)

    # 2. Taxa de conclusao por agente, na avaliacao.
    avaliacao = [linha for linha in linhas if linha['fase'] == 'avaliacao']
    if avaliacao:
        figura, eixo = plt.subplots(figsize=(8, 5))
        rotulos, valores, erros = [], [], []
        for (agente, trecho), grupo in sorted(agrupar(avaliacao, ('agente', 'trecho')).items()):
            resumo = resumo_por_semente(grupo)
            rotulos.append(f"{agente}\n{trecho}")
            valores.append(resumo['conclusao'] * 100)
            erros.append(resumo['conclusao_desvio'] * 100)
        eixo.bar(rotulos, valores, yerr=erros, capsize=5)
        eixo.set_ylabel('taxa de conclusao (%)')
        eixo.set_ylim(0, 105)
        eixo.set_title('Avaliacao com exploracao zero (barra de erro = entre sementes)')
        eixo.grid(alpha=0.3, axis='y')
        caminho = os.path.join(pasta, 'conclusao_por_agente.png')
        figura.tight_layout()
        figura.savefig(caminho, dpi=130)
        plt.close(figura)
        gerados.append(caminho)

    # 3. Generalizacao: treinado num trecho, avaliado nos outros.
    generalizacao = [linha for linha in linhas if linha['fase'].startswith('generalizacao')]
    if generalizacao:
        figura, eixo = plt.subplots(figsize=(9, 5))
        for (agente,), grupo in sorted(agrupar(generalizacao, ('agente',)).items()):
            por_trecho = agrupar(grupo, ('trecho',))
            rotulos = sorted(chave[0] for chave in por_trecho)
            valores = [resumo_por_semente(por_trecho[(rotulo,)])['conclusao'] * 100
                       for rotulo in rotulos]
            erros = [resumo_por_semente(por_trecho[(rotulo,)])['conclusao_desvio'] * 100
                     for rotulo in rotulos]
            eixo.bar(rotulos, valores, yerr=erros, capsize=4, label=agente)
        eixo.set_ylabel('taxa de conclusao (%)')
        eixo.set_title('Generalizacao: treinado num trecho, avaliado em outros')
        eixo.legend()
        eixo.grid(alpha=0.3, axis='y')
        caminho = os.path.join(pasta, 'generalizacao.png')
        figura.tight_layout()
        figura.savefig(caminho, dpi=130)
        plt.close(figura)
        gerados.append(caminho)

    return gerados


def main():
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument('--arquivos', nargs='*', default=None)
    analisador.add_argument('--graficos', action='store_true')
    analisador.add_argument('--janela', type=int, default=100)
    argumentos = analisador.parse_args()

    padroes = argumentos.arquivos or [os.path.join(PASTA_METRICAS, '*.csv')]
    caminhos = sorted({caminho for padrao in padroes for caminho in glob.glob(padrao)})
    if not caminhos:
        raise SystemExit(f"nenhum CSV encontrado em {padroes}")

    print(f"lendo {len(caminhos)} arquivo(s):")
    for caminho in caminhos:
        print(f"  {os.path.relpath(caminho, configuracao_modulo.RAIZ)}")

    linhas = ler(caminhos)
    print(f"\n{len(linhas)} episodios\n")
    print(tabela(linhas))
    print("\ncriterio de sucesso (supera o aleatorio por mais que a variacao entre sementes):")
    print(comparar(linhas))

    if argumentos.graficos:
        print()
        for caminho in gerar_graficos(linhas, janela=argumentos.janela):
            print(f"  grafico: {os.path.relpath(caminho, configuracao_modulo.RAIZ)}")


if __name__ == '__main__':
    main()
