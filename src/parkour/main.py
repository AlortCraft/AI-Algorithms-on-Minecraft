"""O bot de parkour dentro do Minecraft.

Conecta no servidor e escuta comandos no chat. **Nao e aqui que o treino
acontece**: o servidor roda a 20 ticks por segundo, o que da umas 5 decisoes
por segundo. O treino roda no simulador, com Python puro:

    python -m src.parkour.experimento --agente q --episodios 4000

Este arquivo serve para validar: conferir que a fisica simulada bate com a do
jogo, e rodar no jogo a politica treinada offline.

Antes de rodar:

1. copie config/bot.json.exemplo para config/bot.json e ajuste host e usuario;
2. suba o servidor e espere a mensagem `Done`;
3. no console do servidor, rode `op <usuario>` (sem a barra). Sem isso o /tp
   do reset nao funciona e nenhum episodio comeca.

    python -m src.parkour.main

Comandos no chat:

    parkour ajuda        lista os comandos
    parkour info         mostra o trecho carregado e a posicao do bot
    parkour teste        anda cinco blocos e para
    parkour reset        teleporta para o inicio do trecho
    parkour marcar       grava a posicao do jogador, para ajustar o trecho
    parkour calibrar     roda a sequencia fixa e grava a trajetoria real
    parkour guloso       roda a politica gulosa (nao aprende, so confere)
    parkour rodar        roda a politica treinada offline
    parkour parar        interrompe o que estiver rodando
"""

import argparse
import json
import os
import threading
import traceback

from . import acoes as catalogo_acoes
from . import calibracao
from . import config as configuracao_modulo
from .agentes.guloso import AgenteGuloso
from .agentes.q_learning import AgenteQLearning
from .ambiente_mc import AmbienteMinecraft
from .percurso import Percurso


class BotParkour:
    def __init__(self, cenario=None, nome_trecho=None):
        self.configuracao = configuracao_modulo.carregar(cenario=cenario)
        self.dados_bot = configuracao_modulo.carregar_bot()
        configuracao_modulo.validar_mundo_local(self.configuracao, self.dados_bot)

        definicao = configuracao_modulo.trecho(self.configuracao, nome_trecho)
        self.percurso = Percurso.carregar(
            configuracao_modulo.caminho_mapa(self.configuracao, definicao), definicao)

        print("Inicializando o bot de parkour...")
        print(f"  cenario: {self.configuracao.get('cenario', 'padrao')}")
        print(f"  {self.percurso.resumo()}")

        # A ponte so e necessaria para conectar. Importa-la aqui permite usar
        # --listar-cenarios e outras operacoes offline sem instalar Mineflayer.
        from javascript import require
        self.mineflayer = require('mineflayer')
        self.vec3 = require('vec3')
        self.bot = self.mineflayer.createBot({
            'host': self.dados_bot['host'],
            'port': self.dados_bot['porta'],
            'username': self.dados_bot['usuario'],
            'hideErrors': self.dados_bot.get('esconder_erros', False),
        })

        self.ambiente = None
        self.tarefa = None
        self.parar_pedido = threading.Event()

    # ------------------------------------------------------------------

    def preparar_ambiente(self):
        if self.ambiente is None:
            self.ambiente = AmbienteMinecraft(self.bot, self.percurso,
                                              self.configuracao, self.vec3)
        return self.ambiente

    def falar(self, texto):
        print(texto)
        self.bot.chat(texto)

    def em_segundo_plano(self, funcao, *argumentos):
        """Roda uma tarefa longa fora do laco de eventos.

        Sem isto, um treino ou uma corrida travaria o tratamento do chat e nem
        daria para mandar `parkour parar`.
        """
        if self.tarefa is not None and self.tarefa.is_alive():
            self.falar("ja tem algo rodando. Use: parkour parar")
            return

        self.parar_pedido.clear()

        def embrulho():
            try:
                funcao(*argumentos)
            except Exception:
                traceback.print_exc()
                self.falar("deu erro; veja o console do Python")
            finally:
                if self.ambiente is not None:
                    self.ambiente.soltar_controles()

        self.tarefa = threading.Thread(target=embrulho, daemon=True)
        self.tarefa.start()

    # ------------------------------------------------------------------
    # comandos

    def comando_ajuda(self):
        for linha in ("parkour info / teste / reset / marcar / verificar",
                      "parkour calibrar | guloso | rodar | parar"):
            self.falar(linha)

    def comando_info(self):
        ambiente = self.preparar_ambiente()
        corpo = ambiente.corpo
        mundo_x, mundo_y, mundo_z = corpo.posicao_mundo
        self.falar(f"{self.percurso.resumo()}")
        self.falar(f"mundo x={mundo_x:.2f} y={mundo_y:.2f} z={mundo_z:.2f}")
        self.falar(f"local lateral={corpo.x:.2f} altura={corpo.y:.2f} "
                   f"progresso={corpo.z:.2f} "
                   f"no_chao={corpo.no_chao}")
        self.falar(f"estado={ambiente.observar()} de {ambiente.quantidade_estados}")

    def comando_teste(self):
        """Anda cinco blocos. E o primeiro teste de que a ponte funciona."""
        ambiente = self.preparar_ambiente()
        progresso_inicial = ambiente.corpo.z
        self.falar("andando cinco blocos...")
        ambiente.aplicar(catalogo_acoes.entradas_de(0))
        for _ in range(100):
            if (ambiente.corpo.z - progresso_inicial >= 5.0
                    or self.parar_pedido.is_set()):
                break
            ambiente.esperar_ticks(2)
        ambiente.soltar_controles()
        self.falar(f"avancou {ambiente.corpo.z - progresso_inicial:.2f} blocos")

    def comando_reset(self):
        ambiente = self.preparar_ambiente()
        ambiente.reset()
        mundo_x, _, mundo_z = ambiente.corpo.posicao_mundo
        self.falar(f"no inicio: mundo x={mundo_x:.2f} z={mundo_z:.2f}; "
                   f"progresso={ambiente.corpo.z:.2f}")

    def comando_verificar(self):
        """Confere se o JSON selecionado descreve os blocos do mundo aberto."""
        ambiente = self.preparar_ambiente()
        ambiente.reset()
        resultado = ambiente.verificar_geometria()
        if resultado['aviso']:
            self.falar(f"nao foi possivel verificar: {resultado['aviso']}")
            return
        diferencas = resultado['diferencas']
        if not diferencas:
            self.falar(f"mapa conferido: {resultado['verificados']} blocos coincidem")
            return
        self.falar(f"ERRO DE MAPA: {len(diferencas)} de "
                   f"{resultado['verificados']} amostras diferem")
        for diferenca in diferencas[:3]:
            self.falar(f"em {diferenca['mundo']}: esperado "
                       f"{diferenca['esperado']}, obtido {diferenca['obtido']}")

    def comando_marcar(self, nome_jogador):
        """Grava a posicao do jogador, para reconfigurar o trecho sem o F3."""
        jogador = self.bot.players[nome_jogador]
        if jogador is None or jogador.entity is None:
            self.falar(f"nao consigo ver {nome_jogador}; chegue mais perto")
            return

        posicao = jogador.entity.position
        marca = {'x': float(posicao.x), 'y': float(posicao.y), 'z': float(posicao.z)}
        destino = os.path.join(configuracao_modulo.RAIZ, 'resultados', 'marcas.json')
        os.makedirs(os.path.dirname(destino), exist_ok=True)

        marcas = []
        if os.path.exists(destino):
            with open(destino, encoding='utf-8') as arquivo:
                marcas = json.load(arquivo)
        marcas.append(marca)
        with open(destino, 'w', encoding='utf-8') as arquivo:
            json.dump(marcas, arquivo, indent=2)

        self.falar(f"marcado x={marca['x']:.2f} y={marca['y']:.2f} z={marca['z']:.2f}")

    def comando_calibrar(self):
        """Grava a trajetoria real para comparar com o simulador.

        Roda na pista lisa descrita no config, e nao no percurso. Medir fisica
        em cima de obstaculo mede colisao: na primeira tentativa em jogo o bot
        parou no pilar de z=1004 no tick 24 e os 128 ticks seguintes nao
        mediram nada. Ver docs/sim_para_real.md.
        """
        calibracao_config = self.configuracao.get('calibracao', {})
        if not calibracao_config.get('disponivel', True):
            self.falar("este cenario nao possui pista de calibracao")
            return
        ambiente = self.preparar_ambiente()
        pista = calibracao_config['pista']
        origem = ((pista['x_min'] + pista['x_max'] + 1) / 2.0,
                  float(pista['y_piso'] + 1),
                  pista['z_inicio'] + 0.5)
        self.falar(f"gravando {len(calibracao.SEQUENCIA_PADRAO)} acoes "
                   f"na pista lisa (z {pista['z_inicio']}..{pista['z_meta']})...")

        amostras = ambiente.gravar_trajetoria(calibracao.SEQUENCIA_PADRAO,
                                              origem=origem)
        destino = os.path.join(configuracao_modulo.RAIZ, 'resultados', 'metricas',
                               'trajetoria_real.json')
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, 'w', encoding='utf-8') as arquivo:
            json.dump({
                'trecho': self.percurso.nome,
                'pista_plana': True,
                'ticks_por_acao': ambiente.ticks_por_acao,
                'sequencia': list(calibracao.SEQUENCIA_PADRAO),
                'amostras': amostras,
            }, arquivo, indent=2)

        self.falar(f"{len(amostras)} amostras gravadas")
        self.falar("agora rode: python -m src.parkour.calibracao "
                   "--real resultados/metricas/trajetoria_real.json")

    def _rodar_politica(self, agente, rotulo):
        ambiente = self.preparar_ambiente()
        _, informacoes = ambiente.reset()
        estado = ambiente.observar()

        while not self.parar_pedido.is_set():
            acao = agente.escolher(estado, ambiente)
            _, _, terminou, truncou, informacoes = ambiente.passo(acao)
            estado = ambiente.observar()
            if terminou or truncou:
                break

        self.falar(f"{rotulo}: {informacoes['motivo'] or 'interrompido'} em "
                   f"{informacoes['passos']} passos, "
                   f"progresso {informacoes['progresso']:.0%}")

    def comando_guloso(self):
        self._rodar_politica(AgenteGuloso(), 'guloso')

    def comando_rodar(self):
        """Roda no jogo a politica treinada offline.

        A diferenca entre o resultado daqui e o do simulador e o custo de sair
        do simulador, e e um resultado do trabalho.
        """
        ambiente = self.preparar_ambiente()
        rotulo = configuracao_modulo.rotulo_modelo(
            self.configuracao, self.percurso.nome)
        modelo = os.path.join(configuracao_modulo.RAIZ, 'resultados', 'modelos',
                              f"q_{rotulo}_s0.json")
        if not os.path.exists(modelo):
            self.falar("nao achei a tabela treinada. Rode antes, fora do jogo:")
            cenario = self.configuracao.get('cenario')
            sufixo = f" --cenario {cenario}" if cenario else ''
            self.falar("python -m src.parkour.experimento --agente q "
                       f"--episodios 4000{sufixo}")
            return

        agente = AgenteQLearning(ambiente.quantidade_estados,
                                 ambiente.quantidade_acoes)
        agente.carregar(modelo)
        agente.modo_avaliacao()
        self._rodar_politica(agente, 'politica treinada')

    def comando_parar(self):
        self.parar_pedido.set()
        if self.ambiente is not None:
            self.ambiente.soltar_controles()
        self.falar("parando")


def main():
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument('--cenario', default=None,
                            help='parkour_oficial ou labirinto_parkours')
    analisador.add_argument('--trecho', default=None)
    analisador.add_argument('--listar-cenarios', action='store_true')
    argumentos = analisador.parse_args()

    if argumentos.listar_cenarios:
        print('\n'.join(configuracao_modulo.cenarios_disponiveis()))
        return

    cenario = argumentos.cenario
    if cenario is None:
        cenario = configuracao_modulo.cenario_para_mundo(
            configuracao_modulo.mundo_servidor_local())
        if cenario:
            print(f"Cenario escolhido pelo level-name do servidor: {cenario}")
        else:
            cenario = 'parkour_oficial'

    from javascript import On
    parkour = BotParkour(cenario, argumentos.trecho)
    bot = parkour.bot

    # Versoes do JSPyBridge divergem sobre entregar ou nao o `this` do
    # JavaScript como primeiro argumento. ``*argumentos`` torna o evento de
    # spawn compativel com os dois formatos: ele nao precisa dos argumentos.
    @On(bot, 'spawn')
    def ao_nascer(*argumentos):
        print(f"[{bot.username}] conectado")
        bot.chat("bot de parkour pronto. Digite: parkour ajuda")

    @On(bot, 'messagestr')
    def ao_ouvir(*argumentos):
        if not argumentos:
            return
        # No formato atual, a mensagem e o primeiro argumento. Em versoes que
        # inserem `this`, ela e o segundo. O evento messagestr entrega a
        # mensagem como str, enquanto `this` e um proxy JavaScript.
        mensagem = next((item for item in argumentos[:2]
                         if isinstance(item, str)), argumentos[0])
        texto = str(mensagem).strip().lower()
        if 'parkour' not in texto:
            return

        # O bot escuta o proprio chat. Como as respostas dele contem a palavra
        # "parkour", responder a si mesmo viraria um laco infinito de mensagens
        # - `parkour ajuda` responderia, ouviria a resposta, e responderia de
        # novo. O chat renderizado vem como "<Nome> mensagem".
        if f"<{bot.username}>".lower() in texto:
            return

        print(f"chat: {mensagem}")

        jogador = parkour.dados_bot.get('jogador', '')

        if 'ajuda' in texto:
            parkour.comando_ajuda()
        elif 'parar' in texto:
            parkour.comando_parar()
        elif 'info' in texto:
            parkour.em_segundo_plano(parkour.comando_info)
        elif 'teste' in texto:
            parkour.em_segundo_plano(parkour.comando_teste)
        elif 'reset' in texto:
            parkour.em_segundo_plano(parkour.comando_reset)
        elif 'marcar' in texto:
            parkour.em_segundo_plano(parkour.comando_marcar, jogador)
        elif 'verificar' in texto:
            parkour.em_segundo_plano(parkour.comando_verificar)
        elif 'calibrar' in texto:
            parkour.em_segundo_plano(parkour.comando_calibrar)
        elif 'guloso' in texto:
            parkour.em_segundo_plano(parkour.comando_guloso)
        elif 'rodar' in texto:
            parkour.em_segundo_plano(parkour.comando_rodar)


if __name__ == '__main__':
    main()
