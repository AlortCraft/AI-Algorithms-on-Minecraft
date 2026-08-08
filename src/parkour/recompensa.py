"""O sinal que o agente tenta maximizar.

A pag. 4 do PDF pede duas coisas antes de escolher numeros: listar os
comportamentos desejados e indesejados, e "verificar se o bot consegue
acumular recompensa sem realmente progredir". Os pesos ficam todos no
config/parkour.json para que mudar um deles seja um experimento registrado, e
nao uma edicao de codigo esquecida.

Comportamentos desejados        sinal
  avancar em direcao a meta     + progresso * peso
  chegar na meta                + meta
Comportamentos indesejados
  cair da ponte                 - queda
  demorar                       - por_passo a cada decisao
  ficar parado batendo na parede - parado

Risco conhecido de recompensa mal calibrada (reward hacking): se `progresso`
contasse valor absoluto em vez de deslocamento liquido, o agente poderia
oscilar para frente e para tras e somar recompensa sem sair do lugar. Por isso
o progresso e a diferenca liquida na direcao da meta, e existe teste automatico
para isso. No mapa oficial ele coincide com +Z; em outros cenarios pode ser X.
"""


class Recompensa:
    def __init__(self, pesos):
        self.progresso = pesos.get('progresso', 1.0)
        self.por_passo = pesos.get('por_passo', -0.02)
        self.queda = pesos.get('queda', -10.0)
        self.meta = pesos.get('meta', 20.0)
        self.parado = pesos.get('parado', -0.05)
        self.limite_parado = pesos.get('limite_parado', 0.05)

    def calcular(self, progresso_antes, progresso_depois, motivo):
        """Recompensa de um passo.

        motivo e None enquanto o episodio segue, ou 'queda' / 'meta' no passo
        que o encerra.
        """
        avanco = progresso_depois - progresso_antes
        valor = avanco * self.progresso + self.por_passo

        if abs(avanco) < self.limite_parado:
            valor += self.parado

        if motivo == 'queda':
            valor += self.queda
        elif motivo == 'meta':
            valor += self.meta

        return valor

    def descrever(self):
        return (f"progresso={self.progresso} por_passo={self.por_passo} "
                f"queda={self.queda} meta={self.meta} parado={self.parado}")
