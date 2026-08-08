"""Interface comum dos agentes.

Todo agente responde as mesmas quatro perguntas. Isso permite que
experimento.py rode qualquer um deles sem saber qual e, que e o que torna as
comparacoes justas: o laco de treino e identico, so o agente muda.
"""


class Agente:
    nome = 'base'

    def escolher(self, estado, ambiente=None):
        """Devolve o indice da acao. `ambiente` so e usado por agentes que
        olham o mundo direto, como o guloso."""
        raise NotImplementedError

    def aprender(self, estado, acao, recompensa, proximo_estado, terminou):
        """Atualiza o que o agente sabe. Agentes que nao aprendem ignoram."""

    def fim_de_episodio(self, episodio):
        """Chamado ao fim de cada episodio, para decair a exploracao."""

    def modo_avaliacao(self):
        """Desliga a exploracao. A avaliacao roda sempre com exploracao zero:
        medir um agente enquanto ele ainda sorteia acoes mede outra coisa."""

    def salvar(self, caminho):
        """Grava o que foi aprendido. Agentes sem memoria ignoram."""

    def carregar(self, caminho):
        """Le o que foi aprendido."""

    def diagnostico(self):
        """Numeros para acompanhar o treino, como a exploracao atual."""
        return {}
