"""Conecta varios bots a uma unica tabela de Q-Learning no Minecraft.

Exemplo:

    python -m src.parkour.main --cenario labirinto_parkours --bots 4

Comandos no chat:

    parkour ajuda | info | reset | rodar | avaliar N | treinar N | parar
"""

import argparse
import os
import re
import signal
import threading
import time
import traceback

from . import acoes, config as configuracao_modulo
from .ambiente_mc import AmbienteMinecraft
from .percurso import Percurso
from .treinar import (acrescentar_resultado, caminho_padrao_modelo,
                      caminho_resultados, criar_agente, rodar_episodio)


NOME_EQUIPE = 'bots_parkour'


def nomes_dos_bots(nome_base, quantidade):
    """Mantem o primeiro nome e cria sufixos dentro do limite de 16 caracteres."""
    if quantidade < 1:
        raise ValueError('a quantidade de bots deve ser positiva')
    nomes = []
    for numero in range(1, quantidade + 1):
        sufixo = '' if numero == 1 else str(numero)
        nome = nome_base[:16 - len(sufixo)] + sufixo
        if not nome or nome in nomes:
            raise ValueError('nao foi possivel criar nomes unicos para os bots')
        nomes.append(nome)
    return nomes


class AtorMinecraft:
    """Um bot que coleta experiencias para a tabela compartilhada."""

    def __init__(self, grupo, nome, mineflayer):
        self.grupo = grupo
        self.nome = nome
        dados = grupo.dados_bot
        self.bot = mineflayer.createBot({
            'host': dados['host'],
            'port': dados['porta'],
            'username': nome,
            'hideErrors': dados.get('esconder_erros', False),
        })
        self.ambiente = None
        self.pronto = threading.Event()

    def preparar_ambiente(self):
        if self.ambiente is None:
            self.ambiente = AmbienteMinecraft(
                self.bot,
                self.grupo.percurso,
                self.grupo.configuracao,
                emissor_comandos=self.grupo.executar_comando,
            )
        return self.ambiente

    def soltar_controles(self):
        if self.ambiente is not None:
            self.ambiente.soltar_controles()


class GrupoParkour:
    """Coordena os atores e mantem uma unica tabela Q em memoria."""

    def __init__(self, cenario, nome_trecho=None, caminho_modelo=None,
                 quantidade_bots=None):
        self.configuracao = configuracao_modulo.carregar(cenario=cenario)
        self.dados_bot = configuracao_modulo.carregar_bot()
        configuracao_modulo.validar_mundo_local(
            self.configuracao, self.dados_bot
        )
        self.definicao = configuracao_modulo.trecho(
            self.configuracao, nome_trecho
        )
        self.percurso = Percurso.carregar(
            configuracao_modulo.caminho_mapa(
                self.configuracao, self.definicao
            ),
            self.definicao,
        )
        self.caminho_modelo = (
            configuracao_modulo.caminho_absoluto(caminho_modelo)
            if caminho_modelo else caminho_padrao_modelo(
                self.configuracao, self.definicao['nome']
            )
        )

        quantidade = quantidade_bots
        if quantidade is None:
            quantidade = self.dados_bot.get('quantidade_bots', 4)
        if not 1 <= quantidade <= 200:
            raise ValueError('use entre 1 e 200 bots')

        from javascript import require
        mineflayer = require('mineflayer')
        nomes = nomes_dos_bots(self.dados_bot['usuario'], quantidade)
        # Evita uma tempestade de login, chunks e pacotes quando dezenas de
        # clientes Mineflayer entram no mesmo tick do servidor.
        intervalo = float(self.dados_bot.get('intervalo_conexao', 0.05))
        self.atores = []
        for indice, nome in enumerate(nomes):
            self.atores.append(AtorMinecraft(self, nome, mineflayer))
            if indice + 1 < len(nomes) and intervalo > 0:
                time.sleep(intervalo)
        self.controlador = self.atores[0]

        self.agente = None
        self.bloqueio_agente = threading.Lock()
        self.bloqueio_persistencia = threading.Lock()
        self.bloqueio_comandos = threading.Lock()
        self.bloqueio_resultados = threading.Lock()
        self.parar_pedido = threading.Event()
        self.encerrado = threading.Event()
        self.tarefa = None
        self.colisao_preparada = False

    def registrar_eventos(self, On):
        for ator in self.atores:
            self._registrar_eventos_do_ator(ator, On)
        self._registrar_comandos(On)
        # Em localhost o primeiro bot pode concluir o login enquanto os demais
        # ainda estao sendo criados, antes de os eventos serem registrados.
        # Nesse caso nao chega um novo `spawn`; a entidade ja existente e a
        # confirmacao equivalente.
        for ator in self.atores:
            if getattr(ator.bot, 'entity', None) is not None:
                self._marcar_como_pronto(ator)

    def _registrar_eventos_do_ator(self, ator, On):
        @On(ator.bot, 'spawn')
        def ao_nascer(*_):
            self._marcar_como_pronto(ator)

        @On(ator.bot, 'end')
        def ao_sair(*argumentos):
            ator.pronto.clear()
            motivo = next(
                (item for item in reversed(argumentos)
                 if isinstance(item, str)), ''
            )
            detalhe = f': {motivo}' if motivo else ''
            print(f'[{ator.nome}] desconectado{detalhe}')

        @On(ator.bot, 'kicked')
        def ao_ser_expulso(*argumentos):
            motivo = next(
                (item for item in reversed(argumentos)
                 if isinstance(item, str)), 'motivo nao informado'
            )
            print(f'[{ator.nome}] expulso pelo servidor: {motivo}')

        @On(ator.bot, 'error')
        def ao_erro(*argumentos):
            detalhes = [str(item) for item in argumentos[1:]]
            print(f'[{ator.nome}] erro de conexao: '
                  f'{"; ".join(detalhes) or "nao informado"}')

    def _marcar_como_pronto(self, ator):
        """Registra login uma vez; `spawn` tambem ocorre apos morte/respawn."""
        if ator.pronto.is_set():
            return
        ator.pronto.set()
        print(f'[{ator.nome}] conectado')
        self._preparar_equipe(ator)
        if ator is self.controlador:
            self.falar(
                f'Q-Learning pronto com {len(self.atores)} bots. '
                'Digite parkour ajuda'
            )

    def _registrar_comandos(self, On):
        bot = self.controlador.bot

        @On(bot, 'messagestr')
        def ao_ouvir(*argumentos):
            mensagem = next(
                (item for item in argumentos[:2] if isinstance(item, str)), ''
            )
            texto = mensagem.strip().lower()
            falas_dos_bots = (f'<{ator.nome}>'.lower() for ator in self.atores)
            if ('parkour' not in texto
                    or any(nome in texto for nome in falas_dos_bots)):
                return

            if 'ajuda' in texto:
                self.falar(
                    'parkour info | reset | rodar | avaliar N | '
                    'treinar N | parar'
                )
            elif 'parar' in texto:
                self.comando_parar()
            elif 'info' in texto:
                self.executar_em_segundo_plano(self.comando_info)
            elif 'reset' in texto:
                self.executar_em_segundo_plano(self.comando_reset)
            elif 'avaliar' in texto:
                encontrado = re.search(r'parkour\s+avaliar\s+(\d+)', texto)
                if encontrado:
                    self.executar_em_segundo_plano(
                        self.comando_avaliar, int(encontrado.group(1))
                    )
                else:
                    self.falar('use: parkour avaliar TENTATIVAS')
            elif 'treinar' in texto:
                encontrado = re.search(r'parkour\s+treinar\s+(\d+)', texto)
                if encontrado:
                    self.executar_em_segundo_plano(
                        self.comando_treinar, int(encontrado.group(1))
                    )
                else:
                    self.falar('use: parkour treinar RODADAS_POR_BOT')
            elif 'rodar' in texto:
                self.executar_em_segundo_plano(self.comando_rodar)

    def _preparar_equipe(self, ator):
        if not self.dados_bot.get('sem_colisao', True):
            return
        if not self.controlador.pronto.is_set():
            return
        with self.bloqueio_comandos:
            if not self.colisao_preparada:
                # O primeiro comando pode avisar que a equipe ja existe; os
                # seguintes continuam validos e tornam a operacao repetivel.
                self.controlador.bot.chat(f'/team add {NOME_EQUIPE}')
                self.controlador.bot.chat(
                    f'/team modify {NOME_EQUIPE} collisionRule never'
                )
                self.controlador.bot.chat(
                    f'/team modify {NOME_EQUIPE} friendlyFire false'
                )
                self.controlador.bot.chat('/gamerule maxEntityCramming 0')
                self.colisao_preparada = True
                for candidato in self.atores:
                    if candidato.pronto.is_set():
                        self.controlador.bot.chat(
                            f'/team join {NOME_EQUIPE} {candidato.nome}'
                        )
            else:
                self.controlador.bot.chat(
                    f'/team join {NOME_EQUIPE} {ator.nome}'
                )

    def executar_comando(self, comando):
        if not self.controlador.pronto.is_set():
            raise RuntimeError('o bot controlador esta desconectado')
        with self.bloqueio_comandos:
            self.controlador.bot.chat(comando)

    def atores_prontos(self):
        return [ator for ator in self.atores if ator.pronto.is_set()]

    def falar(self, mensagem):
        texto = str(mensagem)[:250]
        print(texto)
        if self.controlador.pronto.is_set():
            self.controlador.bot.chat(texto)

    def executar_em_segundo_plano(self, funcao, *argumentos):
        if self.tarefa is not None and self.tarefa.is_alive():
            self.falar('ja existe uma tarefa em andamento; use parkour parar')
            return
        self.parar_pedido.clear()

        def executar():
            try:
                funcao(*argumentos)
            except Exception as erro:
                traceback.print_exc()
                self.falar(f'erro: {erro}')
            finally:
                for ator in self.atores:
                    ator.soltar_controles()

        self.tarefa = threading.Thread(target=executar, daemon=True)
        self.tarefa.start()

    def _obter_agente(self, criar_se_ausente=False):
        with self.bloqueio_agente:
            if self.agente is not None:
                return self.agente
            prontos = self.atores_prontos()
            if not prontos:
                raise RuntimeError('nenhum bot terminou de conectar')
            ambiente = prontos[0].preparar_ambiente()
            agente = criar_agente(ambiente, self.configuracao)
            if os.path.isfile(self.caminho_modelo):
                agente.carregar(self.caminho_modelo)
                if agente.acoes_adicionadas_ao_carregar:
                    nomes = ', '.join(
                        acoes.nome_de(indice)
                        for indice in agente.acoes_adicionadas_ao_carregar
                    )
                    self.falar(
                        f'modelo migrado: acao adicionada ({nomes}); '
                        f'epsilon reativado em {agente.exploracao:.2f}. '
                        f'Backup: {os.path.basename(agente.backup_migracao)}'
                    )
            elif not criar_se_ausente:
                relativo = os.path.relpath(
                    self.caminho_modelo, configuracao_modulo.RAIZ
                )
                raise FileNotFoundError(
                    f'tabela Q nao encontrada: {relativo}. Use primeiro '
                    '`parkour treinar N` dentro do jogo.'
                )
            self.agente = agente
            return agente

    def comando_info(self):
        prontos = self.atores_prontos()
        modelo = 'pronto' if os.path.isfile(self.caminho_modelo) else 'ausente'
        diagnostico = self.agente.diagnostico() if self.agente else None
        epsilon = (f", epsilon={diagnostico['exploracao']:.3f}"
                   if diagnostico else '')
        self.falar(
            f"trecho={self.definicao['nome']}, bots={len(prontos)}/"
            f'{len(self.atores)}, modelo={modelo}{epsilon}'
        )

    def comando_reset(self):
        if not self.controlador.pronto.is_set():
            raise RuntimeError('aguarde o bot controlador terminar de conectar')
        prontos = self.atores_prontos()
        if not prontos:
            raise RuntimeError('nenhum bot esta conectado')
        erros = []

        def resetar(ator):
            try:
                ator.preparar_ambiente().reset()
            except Exception as erro:
                erros.append(f'{ator.nome}: {erro}')

        tarefas = [threading.Thread(target=resetar, args=(ator,))
                   for ator in prontos]
        for tarefa in tarefas:
            tarefa.start()
        for tarefa in tarefas:
            tarefa.join()
        if erros:
            raise RuntimeError('; '.join(erros))
        self.falar(f'{len(prontos)} bots colocados no inicio do percurso')

    def comando_rodar(self):
        agente = self._obter_agente()
        ator = self.atores_prontos()[0]
        exploracao = agente.iniciar_avaliacao()
        try:
            resultado = rodar_episodio(
                ator.preparar_ambiente(), agente, aprender=False,
                parar_pedido=self.parar_pedido,
            )
        finally:
            agente.iniciar_treino(exploracao)
        self.falar(
            f"fim: {resultado['motivo']}, progresso "
            f"{resultado.get('progresso_valido', resultado['progresso']):.0%}, "
            f"{resultado['passos']} passos"
        )

    def comando_avaliar(self, tentativas):
        """Avalia a politica sem exploracao ou aprendizado e salva o CSV."""
        if tentativas < 1:
            raise ValueError('a quantidade de tentativas deve ser positiva')
        if not self.controlador.pronto.is_set():
            raise RuntimeError('aguarde o bot controlador terminar de conectar')
        atores = self.atores_prontos()
        if not atores:
            raise RuntimeError('nenhum bot esta conectado')

        agente = self._obter_agente()
        caminho_csv = caminho_resultados(self.caminho_modelo)
        resultados = []
        erros = []
        inicio = time.monotonic()
        exploracao_anterior = agente.iniciar_avaliacao()
        self.falar(
            f'iniciando avaliacao: {tentativas} tentativas com '
            f'{min(len(atores), tentativas)} bots; epsilon 0'
        )

        def trabalhar(indice_ator, ator):
            ambiente = ator.preparar_ambiente()
            for numero in range(indice_ator + 1, tentativas + 1, len(atores)):
                if self.parar_pedido.is_set():
                    return
                try:
                    resultado = rodar_episodio(
                        ambiente, agente, aprender=False,
                        parar_pedido=self.parar_pedido,
                    )
                    if resultado['motivo'] == 'interrompido':
                        return
                    with self.bloqueio_persistencia:
                        acrescentar_resultado(
                            caminho_csv, 'avaliacao', numero, resultado, 0.0
                        )
                    with self.bloqueio_resultados:
                        resultados.append(resultado)
                        concluidos = len(resultados)
                        if (concluidos == 1 or concluidos == tentativas
                                or concluidos % 5 == 0):
                            sucessos = sum(
                                item['chegou'] for item in resultados
                            )
                            self.falar(
                                f'avaliacao {concluidos}/{tentativas}: '
                                f'{sucessos} chegadas'
                            )
                except Exception as erro:
                    ator.soltar_controles()
                    with self.bloqueio_resultados:
                        erros.append(f'{ator.nome}: {erro}')
                    return

        tarefas = [
            threading.Thread(target=trabalhar, args=(indice, ator))
            for indice, ator in enumerate(atores[:tentativas])
        ]
        try:
            for tarefa in tarefas:
                tarefa.start()
            for tarefa in tarefas:
                tarefa.join()
        finally:
            agente.iniciar_treino(exploracao_anterior)

        duracao = max(1e-9, time.monotonic() - inicio)
        sucessos = sum(item['chegou'] for item in resultados)
        quantidade = len(resultados)
        taxa = sucessos / quantidade if quantidade else 0.0
        media_passos = (
            sum(item['passos'] for item in resultados) / quantidade
            if quantidade else 0.0
        )
        self.falar(
            f'avaliacao encerrada: {sucessos}/{quantidade} chegadas '
            f'({taxa:.0%}), media {media_passos:.1f} passos, '
            f'{quantidade * 60 / duracao:.1f} episodios/min; historico salvo'
        )
        if erros:
            print('Erros de bots: ' + '; '.join(erros))

    def comando_treinar(self, rodadas):
        """Executa a quantidade pedida de episodios em cada bot pronto."""
        if rodadas < 1:
            raise ValueError('a quantidade de rodadas deve ser positiva')
        if not self.controlador.pronto.is_set():
            raise RuntimeError('aguarde o bot controlador terminar de conectar')
        atores = self.atores_prontos()
        if not atores:
            raise RuntimeError('nenhum bot esta conectado')
        agente = self._obter_agente(criar_se_ausente=True)
        agente.iniciar_treino()
        caminho_csv = caminho_resultados(self.caminho_modelo)
        total_episodios = rodadas * len(atores)

        resultados = []
        erros = []
        inicio = time.monotonic()
        self.falar(
            f'iniciando {rodadas} rodadas por bot: {total_episodios} '
            f'episodios com {len(atores)} bots; '
            f"epsilon {agente.diagnostico()['exploracao']:.3f}"
        )

        def trabalhar(indice_ator, ator):
            ambiente = ator.preparar_ambiente()
            for rodada in range(1, rodadas + 1):
                if self.parar_pedido.is_set():
                    return
                numero = (rodada - 1) * len(atores) + indice_ator + 1
                try:
                    resultado = rodar_episodio(
                        ambiente, agente, aprender=True,
                        parar_pedido=self.parar_pedido,
                    )
                    if resultado['motivo'] == 'interrompido':
                        return
                    agente.fim_de_episodio()
                    diagnostico = agente.diagnostico()
                    with self.bloqueio_persistencia:
                        agente.salvar(self.caminho_modelo)
                        acrescentar_resultado(
                            caminho_csv, 'treino', numero, resultado,
                            diagnostico['exploracao'],
                        )
                    with self.bloqueio_resultados:
                        resultados.append(resultado)
                        concluidos = len(resultados)
                        if (concluidos == 1 or concluidos == total_episodios
                                or concluidos % 5 == 0):
                            self.falar(
                                f'treino {concluidos}/{total_episodios}: '
                                f'rodada {rodada}/{rodadas}, '
                                f'{resultado["motivo"]}, bot={ator.nome}, '
                                f'progresso valido '
                                f'{resultado.get("progresso_valido", resultado["progresso"]):.0%}'
                            )
                except Exception as erro:
                    ator.soltar_controles()
                    with self.bloqueio_resultados:
                        erros.append(f'{ator.nome}: {erro}')
                    return

        tarefas = [threading.Thread(target=trabalhar, args=(indice, ator))
                   for indice, ator in enumerate(atores)]
        for tarefa in tarefas:
            tarefa.start()
        for tarefa in tarefas:
            tarefa.join()

        duracao = max(1e-9, time.monotonic() - inicio)
        sucessos = sum(item['chegou'] for item in resultados)
        ritmo = len(resultados) * 60 / duracao
        self.falar(
            f'treino encerrado: {sucessos}/{len(resultados)} chegadas, '
            f'{len(resultados)}/{total_episodios} episodios, '
            f'{ritmo:.1f} episodios/min; tabela e historico salvos'
        )
        if erros:
            print('Erros de bots: ' + '; '.join(erros))

    def comando_parar(self):
        self.parar_pedido.set()
        for ator in self.atores:
            ator.soltar_controles()
        self.falar('parada solicitada para todos os bots')

    def encerrar(self):
        """Fecha as conexoes uma vez para nao deixar bots presos no servidor."""
        if self.encerrado.is_set():
            return
        self.encerrado.set()
        self.parar_pedido.set()
        # Encerrar cada proxy `bot.quit()` em sequencia pode bloquear a ponte
        # Python/Node durante Ctrl+C. Finalizar a ponte fecha todos os sockets
        # Mineflayer de uma vez e impede processos Node orfaos.
        try:
            from javascript import terminate
            terminate()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cenario', default=None)
    parser.add_argument('--trecho', default=None)
    parser.add_argument('--modelo', default=None)
    parser.add_argument('--bots', type=int, default=None)
    parser.add_argument('--listar-cenarios', action='store_true')
    args = parser.parse_args()

    if args.listar_cenarios:
        print('\n'.join(configuracao_modulo.cenarios_disponiveis()))
        return

    cenario = args.cenario
    if cenario is None:
        cenario = configuracao_modulo.cenario_para_mundo(
            configuracao_modulo.mundo_servidor_local()
        ) or 'parkour_oficial'

    from javascript import On
    grupo = GrupoParkour(
        cenario, args.trecho, args.modelo, quantidade_bots=args.bots
    )
    grupo.registrar_eventos(On)

    def ao_interromper(*_):
        print('\nEncerrando todos os bots...')
        grupo.encerrar()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, ao_interromper)
    # Nao depender do callback atexit da ponte Python/JavaScript: a funcao
    # principal permanece viva ate o usuario pedir o encerramento.
    grupo.encerrado.wait()


if __name__ == '__main__':
    main()
