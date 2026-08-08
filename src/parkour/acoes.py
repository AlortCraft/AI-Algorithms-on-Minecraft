"""O que o agente pode fazer.

Cada acao e uma combinacao de controles mantida por varios ticks seguidos
(`ticks_por_acao` no config, 4 por padrao). Decidir a cada 4 ticks em vez de a
cada tick reduz o tamanho do problema em quatro vezes e ainda deixa controle
suficiente: 4 ticks sao 200 ms, e um pulo inteiro dura cerca de 25 ticks.

A pergunta que a pag. 4 do PDF manda investigar e justamente esta: "as acoes
serao simples, combinadas ou terao duracao?". Este catalogo e uma resposta
inicial, nao a definitiva. Mexer aqui e um experimento valido, desde que
registrado em docs/registro_experimentos.md.
"""

from .fisica import Entradas

# (nome, controles). A ordem define o indice numerico de cada acao, que e o
# que os agentes usam. Nao reordene sem retreinar: uma tabela Q salva antes
# da mudanca passaria a significar outra coisa.
CATALOGO = (
    ('andar',        dict(frente=True)),
    ('correr',       dict(frente=True, correr=True)),
    ('correr_pulo',  dict(frente=True, correr=True, pular=True)),
    ('esquerda',     dict(frente=True, esquerda=True)),
    ('direita',      dict(frente=True, direita=True)),
    ('parar',        dict()),
    # As quatro abaixo entraram em 08/08/2026, ao abrir o projeto para o mapa
    # inteiro. Sem elas o bot nao vence a estrutura mais comum do percurso:
    # subir num bloco que esta ao lado, e nao a frente.
    #
    # - com so `esquerda` (frente+esquerda) e `correr_pulo` (frente+pular), nao
    #   existia nenhuma acao que pulasse E fosse para o lado. Um apoio na
    #   diagonal era inalcancavel, e o bot ficava empurrando a parede ate o
    #   episodio truncar - foi o que travou os trechos end e end2;
    # - toda acao lateral tambem empurrava para frente, entao desviar de um
    #   obstaculo levava o corpo contra a quina dele. E o "quase desviar" que
    #   apareceu na validacao em jogo.
    ('esquerda_pulo', dict(frente=True, esquerda=True, pular=True)),
    ('direita_pulo',  dict(frente=True, direita=True, pular=True)),
    ('lado_esquerdo', dict(esquerda=True)),
    ('lado_direito',  dict(direita=True)),
)

NOMES = tuple(nome for nome, _ in CATALOGO)
QUANTIDADE = len(CATALOGO)

# Objetos Entradas prontos: sao imutaveis na pratica e criados uma vez so,
# porque o laco de treino chama isto milhoes de vezes.
ENTRADAS = tuple(Entradas(**controles) for _, controles in CATALOGO)


def entradas_de(acao):
    """Converte o indice da acao nos controles correspondentes."""
    return ENTRADAS[acao]


def nome_de(acao):
    return NOMES[acao]


def descrever():
    linhas = []
    for indice, (nome, controles) in enumerate(CATALOGO):
        ativos = ', '.join(sorted(controles)) or 'nenhum'
        linhas.append(f"  {indice}  {nome:<12} {ativos}")
    return '\n'.join(linhas)
