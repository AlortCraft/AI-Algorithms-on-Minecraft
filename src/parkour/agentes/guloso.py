"""Politica gulosa escrita a mao: um teto de referencia, nao um agente de IA.

Ela le a geometria do percurso e anda em direcao a passagem mais proxima. Nao
aprende nada e nao conta como resposta do trabalho. Serve para duas coisas:

1. **Provar que o trecho tem solucao.** Antes de gastar horas treinando, vale
   saber se existe alguma sequencia de acoes que chega ao fim. Se nem o guloso
   passa, o problema esta no trecho ou na fisica, nao no algoritmo.
2. **Dar um teto de comparacao.** O aleatorio da o piso, o guloso da uma
   referencia superior. Um agente aprendido que fica entre os dois esta
   aprendendo; um que passa do guloso descobriu algo que nao programamos.
"""

from .base import Agente

ACAO_CORRER = 1
ACAO_CORRER_PULO = 2
ACAO_ESQUERDA = 3
ACAO_DIREITA = 4
ACAO_ESQUERDA_PULO = 6
ACAO_DIREITA_PULO = 7

# Folga para nao ficar oscilando em torno do alvo. Precisa ser menor que a
# margem de mira abaixo, senao o agente se declara alinhado ainda fora do vao.
TOLERANCIA = 0.03
# Nunca mirar a borda exata de uma passagem: com 0.08 de tolerancia e vaos de
# 0.21 entre bambus, o bot parava a 4 centimetros da abertura e seguia reto
# contra a quina, para sempre.
MARGEM_DE_MIRA = 0.12
# Acima disto o alvo esta num degrau que exige pulo, e nao um desnivel que o
# proprio motor sobe sozinho.
DESNIVEL_QUE_EXIGE_PULO = 0.6


def _mirar(x_atual, inicio, fim):
    """Ponto da faixa mais perto de x, sem encostar na borda.

    Mirar a borda exata e o mesmo que mirar o obstaculo que a define: qualquer
    imprecisao da fisica encosta na quina. A margem encolhe junto com a faixa,
    para continuar valendo nos vaos estreitos entre bambus.
    """
    margem = min(MARGEM_DE_MIRA, max(0.0, (fim - inicio) / 3.0))
    return min(max(x_atual, inicio + margem), fim - margem)


class AgenteGuloso(Agente):
    nome = 'guloso'

    def escolher(self, estado, ambiente=None):
        if ambiente is None:
            raise ValueError("o agente guloso precisa do ambiente para enxergar o mapa")

        corpo = ambiente.corpo
        percurso = ambiente.percurso

        alvo = self._alvo(percurso, corpo.x, corpo.z, corpo.y)
        if alvo is None:
            return ACAO_CORRER

        x_alvo, altura_alvo, distancia = alvo
        precisa_subir = altura_alvo - corpo.y > DESNIVEL_QUE_EXIGE_PULO

        if x_alvo < corpo.x - TOLERANCIA:
            return ACAO_ESQUERDA_PULO if precisa_subir else ACAO_ESQUERDA
        if x_alvo > corpo.x + TOLERANCIA:
            return ACAO_DIREITA_PULO if precisa_subir else ACAO_DIREITA

        # Alinhado. Pula por dois motivos: para subir, ou para vencer um vao.
        # O segundo caso e o que faltava - com o alvo sempre em z+1, um buraco
        # a frente nao tinha como ser representado, e o agente andava para
        # dentro dele.
        if precisa_subir or distancia > 1:
            return ACAO_CORRER_PULO
        return ACAO_CORRER

    @staticmethod
    def _alvo(percurso, x_atual, z_atual, y_atual):
        """Para onde ir: (x, altura, distancia em z) do proximo apoio viavel.

        Segue o mesmo grafo de viabilidade que `Percurso` retropropagou, com
        as mesmas regras de alcance. Enquanto este agente olhava so a celula
        seguinte, ele nao conseguia executar caminhos que a analise provava
        existir - o modelo dizia que dava, e o agente empacava. Divergencia
        entre o que se prova e o que se faz e o pior tipo de bug num projeto
        que usa o guloso justamente para atestar que o trecho tem solucao.

        A distancia devolvida e o que informa se e passo ou salto.
        """
        celula = int(z_atual // 1)
        bolso = AgenteGuloso._bolso(percurso, x_atual, celula, y_atual)

        for adiante in range(celula + 1, celula + 1 + percurso.SALTO_ALCANCE):
            estados = [(altura, faixa)
                       for altura, faixa in percurso.estados_viaveis(adiante)
                       if altura - y_atual <= percurso.SALTO_SUBIDA]
            if adiante > celula + 1:
                # Salto longo nao vence subida grande ao mesmo tempo; e a
                # mesma restricao que a analise de viabilidade aplica.
                estados = [(altura, faixa) for altura, faixa in estados
                           if altura - y_atual <= DESNIVEL_QUE_EXIGE_PULO]
            # So vale o que o corpo alcanca sem atravessar parede: na fronteira
            # entre duas celulas ele ocupa as duas, entao o destino precisa
            # cruzar com a faixa onde ele esta agora.
            if bolso is not None:
                estados = [(altura, faixa) for altura, faixa in estados
                           if max(faixa[0], bolso[0]) <= min(faixa[1], bolso[1])]
            if not estados:
                continue

            # O apoio mais perto lateralmente; empate vai para o mais baixo,
            # que e o mais barato de alcancar.
            #
            # O alvo e recortado pelo bolso atual, e nao so pela faixa de
            # destino: para sair de z o corpo precisa caber em z tambem. Sem
            # este recorte o agente mirava o meio de uma faixa larga adiante,
            # dava "ja estou alinhado" e seguia reto contra a borda do vao
            # estreito onde ainda estava - travando por 5 centimetros.
            melhor, custo_melhor = None, None
            for altura, (inicio, fim) in estados:
                if bolso is not None:
                    inicio, fim = max(inicio, bolso[0]), min(fim, bolso[1])
                    if inicio > fim:
                        continue
                candidato = _mirar(x_atual, inicio, fim)
                custo = (abs(candidato - x_atual), max(0.0, altura - y_atual))
                if custo_melhor is None or custo < custo_melhor:
                    melhor, custo_melhor = (candidato, altura), custo
            if melhor is not None:
                return melhor[0], melhor[1], adiante - celula

        # Nada alcancavel a frente: resta subir num apoio ao lado, no mesmo z.
        # E a estrutura mais comum do percurso - o pilar que marca onde pular -
        # e sem ela o bot fica empurrando a parede do bolso onde caiu.
        return AgenteGuloso._subir_ao_lado(percurso, x_atual, celula, y_atual, bolso)

    @staticmethod
    def _bolso(percurso, x_atual, celula, y_atual):
        """A faixa de x onde o corpo esta agora, na altura em que esta.

        Dentro dela o bot anda de lado a vontade; para sair precisa subir ou
        avancar. Sem esta nocao o agente mirava a faixa do outro lado de um
        bloco e empurrava o bloco para sempre.
        """
        for altura, faixas in percurso.superficies_em(celula):
            if abs(altura - y_atual) > DESNIVEL_QUE_EXIGE_PULO:
                continue
            for inicio, fim in faixas:
                if inicio - 0.35 <= x_atual <= fim + 0.35:
                    return (inicio, fim)
        return None

    @staticmethod
    def _subir_ao_lado(percurso, x_atual, celula, y_atual, bolso):
        """Apoio mais alto no mesmo z, encostado no bolso atual."""
        candidatos = []
        for altura, faixa in percurso.estados_viaveis(celula):
            subida = altura - y_atual
            if subida <= DESNIVEL_QUE_EXIGE_PULO or subida > percurso.SALTO_SUBIDA:
                continue
            if bolso is not None and (faixa[0] > bolso[1] + 1.0
                                      or faixa[1] < bolso[0] - 1.0):
                continue        # longe demais para alcancar de um pulo
            candidatos.append((altura, faixa))
        if not candidatos:
            return None

        melhor, custo_melhor = None, None
        for altura, (inicio, fim) in candidatos:
            candidato = _mirar(x_atual, inicio, fim)
            custo = (abs(candidato - x_atual), altura - y_atual)
            if custo_melhor is None or custo < custo_melhor:
                melhor, custo_melhor = (candidato, altura), custo
        return melhor[0], melhor[1], 0
