"""O que o agente pode fazer.

Cada acao e uma combinacao de controles mantida por varios ticks seguidos
(`ticks_por_acao` no config, 4 por padrao). Decidir a cada 4 ticks em vez de a
cada tick reduz o tamanho do problema em quatro vezes e ainda deixa controle
suficiente: 4 ticks sao 200 ms, e um pulo inteiro dura cerca de 25 ticks.

O cenario simples restringe o Q-Learning a ``andar``, ``correr``,
``correr_pulo`` e ``andar_pulo``.
O mapa oficial libera o catalogo completo porque exige desvios laterais.
"""

class Entradas:
    """Controles booleanos que serao enviados ao Mineflayer."""

    def __init__(self, frente=False, tras=False, esquerda=False,
                 direita=False, pular=False, correr=False):
        self.frente = frente
        self.tras = tras
        self.esquerda = esquerda
        self.direita = direita
        self.pular = pular
        self.correr = correr


# A versao muda quando indices existentes passam a significar outra acao.
# Ela faz o caminho padrao apontar para uma tabela nova e impede que modelos
# antigos sejam interpretados com a ordem abaixo.
VERSAO_CATALOGO = 2


# (nome, controles). A ordem define o indice numerico de cada acao, que e o
# que os agentes usam. Nao reordene sem retreinar: uma tabela Q salva antes
# da mudanca passaria a significar outra coisa.
CATALOGO = (
    ('andar',        dict(frente=True)),
    ('correr',       dict(frente=True, correr=True)),
    ('correr_pulo',  dict(frente=True, correr=True, pular=True)),
    ('andar_pulo',   dict(frente=True, pular=True)),
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
