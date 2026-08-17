"""Agente de Q-Learning tabular usado no parkour.

O arquivo contem somente o algoritmo. Ele nao conhece Minecraft, fisica ou
mapas: recebe um estado, escolhe uma acao e atualiza a tabela Q.
"""

import json
import os
import random
import shutil
import threading
import time


TENTATIVAS_SUBSTITUICAO = 12
ESPERA_SUBSTITUICAO_INICIAL = 0.02


def _substituir_com_tentativas(temporario, destino):
    """Troca o checkpoint mesmo sob bloqueios breves do Windows/OneDrive."""
    espera = ESPERA_SUBSTITUICAO_INICIAL
    for tentativa in range(1, TENTATIVAS_SUBSTITUICAO + 1):
        try:
            os.replace(temporario, destino)
            return
        except PermissionError:
            if tentativa == TENTATIVAS_SUBSTITUICAO:
                raise
            time.sleep(espera)
            espera = min(0.5, espera * 2)


class QLearning:
    """Aprende o valor de cada par ``estado, acao`` em uma tabela."""

    def __init__(self, quantidade_estados, quantidade_acoes, parametros=None,
                 semente=None):
        parametros = parametros or {}
        self.quantidade_estados = quantidade_estados
        self.quantidade_acoes = quantidade_acoes

        self.taxa_aprendizado = parametros.get('taxa_aprendizado', 0.2)
        self.desconto = parametros.get('desconto', 0.97)
        self.exploracao = parametros.get('exploracao_inicial', 1.0)
        self.exploracao_final = parametros.get('exploracao_final', 0.05)
        self.decaimento = parametros.get('exploracao_decaimento', 0.9995)
        self.exploracao_ao_expandir_acoes = parametros.get(
            'exploracao_ao_expandir_acoes', 0.30
        )

        permitidas = parametros.get('acoes_permitidas', range(quantidade_acoes))
        self.acoes_permitidas = tuple(dict.fromkeys(permitidas))
        if not self.acoes_permitidas:
            raise ValueError('acoes_permitidas nao pode ficar vazia')
        if any(not isinstance(acao, int) or not 0 <= acao < quantidade_acoes
               for acao in self.acoes_permitidas):
            raise ValueError(
                f'as acoes devem estar entre 0 e {quantidade_acoes - 1}')

        self.sorteador = random.Random(semente)
        self._bloqueio = threading.RLock()
        self._bloqueio_salvamento = threading.Lock()
        self.tabela = [
            [0.0] * quantidade_acoes for _ in range(quantidade_estados)
        ]
        self.visitas = [0] * quantidade_estados
        self.acoes_adicionadas_ao_carregar = ()
        self.backup_migracao = None

    def escolher_acao(self, estado):
        """Escolhe uma acao com a estrategia epsilon-greedy.

        ``exploracao`` e o epsilon: com essa probabilidade o agente testa uma
        acao aleatoria; no restante das vezes usa o melhor valor conhecido.
        """
        with self._bloqueio:
            if self.sorteador.random() < self.exploracao:
                return self.sorteador.choice(self.acoes_permitidas)
            return self._melhor_acao(estado)

    def _melhor_acao(self, estado):
        valores = self.tabela[estado]
        melhor_valor = max(valores[acao] for acao in self.acoes_permitidas)
        empatadas = [acao for acao in self.acoes_permitidas
                     if valores[acao] == melhor_valor]
        return self.sorteador.choice(empatadas)

    def aprender(self, estado, acao, recompensa, proximo_estado, terminou):
        """Aplica uma atualizacao da equacao de Bellman.

        novo Q = Q atual + alfa * (alvo - Q atual)
        alvo   = recompensa + gama * melhor Q do proximo estado

        Quando o episodio terminou, nao existe estado futuro e o alvo e
        somente a recompensa recebida.
        """
        with self._bloqueio:
            self.visitas[estado] += 1
            alvo = recompensa
            if not terminou:
                melhor_futuro = max(
                    self.tabela[proximo_estado][acao]
                    for acao in self.acoes_permitidas
                )
                alvo += self.desconto * melhor_futuro

            valor_atual = self.tabela[estado][acao]
            erro = alvo - valor_atual
            self.tabela[estado][acao] += self.taxa_aprendizado * erro

    def fim_de_episodio(self):
        """Diminui a exploracao depois de cada episodio de treino."""
        with self._bloqueio:
            self.exploracao = max(
                self.exploracao_final,
                self.exploracao * self.decaimento,
            )

    def iniciar_avaliacao(self):
        """Desliga sorteios e devolve o epsilon anterior para restauracao."""
        with self._bloqueio:
            exploracao_anterior = self.exploracao
            self.exploracao = 0.0
            return exploracao_anterior

    def iniciar_treino(self, exploracao=None):
        """Prepara o agente para continuar aprendendo, inclusive no jogo."""
        with self._bloqueio:
            if exploracao is None:
                exploracao = max(self.exploracao, self.exploracao_final)
            self.exploracao = exploracao

    def salvar(self, caminho):
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        temporario = caminho + '.tmp'
        with self._bloqueio_salvamento:
            # Copiar sob o bloqueio cria uma fotografia consistente. A escrita
            # mais lenta acontece depois, sem parar os outros bots de aprender.
            with self._bloqueio:
                dados = {
                    'algoritmo': 'q_learning',
                    'quantidade_estados': self.quantidade_estados,
                    'quantidade_acoes': self.quantidade_acoes,
                    'taxa_aprendizado': self.taxa_aprendizado,
                    'desconto': self.desconto,
                    'exploracao': self.exploracao,
                    'acoes_permitidas': list(self.acoes_permitidas),
                    'tabela': [linha[:] for linha in self.tabela],
                    'visitas': self.visitas[:],
                }
            with open(temporario, 'w', encoding='utf-8') as arquivo:
                json.dump(dados, arquivo)
            _substituir_com_tentativas(temporario, caminho)

    def carregar(self, caminho):
        with open(caminho, encoding='utf-8') as arquivo:
            dados = json.load(arquivo)

        if dados['quantidade_estados'] != self.quantidade_estados:
            raise ValueError('a tabela foi criada com outra quantidade de estados')
        if dados['quantidade_acoes'] != self.quantidade_acoes:
            raise ValueError('a tabela foi criada com outra quantidade de acoes')
        acoes_salvas = tuple(dados.get('acoes_permitidas', ()))
        self.acoes_adicionadas_ao_carregar = ()
        self.backup_migracao = None
        if acoes_salvas != self.acoes_permitidas:
            conjunto_salvo = set(acoes_salvas)
            conjunto_atual = set(self.acoes_permitidas)
            # Uma expansao e segura porque o catalogo e a largura da tabela
            # nao mudaram: as colunas novas ja existem e continuam zeradas.
            # Remover ou trocar acoes poderia mudar a politica silenciosamente.
            if not conjunto_salvo or not conjunto_salvo < conjunto_atual:
                raise ValueError(
                    'a tabela foi criada com outro conjunto de acoes que nao '
                    'pode ser migrado automaticamente'
                )
            self.acoes_adicionadas_ao_carregar = tuple(
                acao for acao in self.acoes_permitidas
                if acao not in conjunto_salvo
            )
            base, extensao = os.path.splitext(caminho)
            self.backup_migracao = base + '_antes_da_migracao' + extensao
            if not os.path.exists(self.backup_migracao):
                shutil.copy2(caminho, self.backup_migracao)

        with self._bloqueio:
            self.tabela = dados['tabela']
            self.visitas = dados.get('visitas', [0] * self.quantidade_estados)
            self.exploracao = dados.get('exploracao', self.exploracao_final)
            if self.acoes_adicionadas_ao_carregar:
                self.exploracao = max(
                    self.exploracao, self.exploracao_ao_expandir_acoes
                )

    def diagnostico(self):
        with self._bloqueio:
            visitados = sum(total > 0 for total in self.visitas)
            return {
                'exploracao': round(self.exploracao, 4),
                'estados_visitados': visitados,
                'cobertura': round(visitados / self.quantidade_estados, 4),
            }
