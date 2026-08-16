"""Testes pequenos e numericos do algoritmo de Q-Learning."""

import os
import sys
import tempfile
import threading

from src.parkour import acoes, config as parkour_config, estado
from src.parkour.ambiente_mc import AmbienteMinecraft
from src.parkour.main import GrupoParkour, nomes_dos_bots
from src.parkour.percurso import Percurso
from src.parkour.q_learning import QLearning
from src.parkour.recompensa import Recompensa
from src.parkour.treinar import (acrescentar_resultado, caminho_padrao_modelo,
                                 rodar_episodio)
from testes.apoio import Verificador


def teste_equacao_de_bellman(verificador):
    agente = QLearning(3, 2, {
        'taxa_aprendizado': 0.5,
        'desconto': 0.9,
        'exploracao_inicial': 0.0,
    })
    agente.tabela[1] = [4.0, 1.0]
    agente.aprender(0, 1, recompensa=2.0, proximo_estado=1, terminou=False)

    # alvo = 2 + 0.9 * 4 = 5.6
    # novo = 0 + 0.5 * (5.6 - 0) = 2.8
    verificador.perto(agente.tabela[0][1], 2.8, 1e-9,
                      'a atualizacao segue a equacao de Bellman')


def teste_estado_terminal_nao_tem_futuro(verificador):
    agente = QLearning(2, 2, {
        'taxa_aprendizado': 1.0,
        'desconto': 0.99,
        'exploracao_inicial': 0.0,
    })
    agente.tabela[1] = [100.0, 100.0]
    agente.aprender(0, 0, recompensa=-10.0, proximo_estado=1, terminou=True)
    verificador.perto(agente.tabela[0][0], -10.0, 1e-9,
                      'o final usa somente a recompensa imediata')


def teste_acoes_permitidas(verificador):
    agente = QLearning(1, 5, {
        'exploracao_inicial': 1.0,
        'acoes_permitidas': [1, 3],
    }, semente=0)
    escolhidas = {agente.escolher_acao(0) for _ in range(100)}
    verificador.verdadeiro(escolhidas == {1, 3},
                           'a exploracao respeita as acoes do cenario')


def teste_catalogo_de_acoes_versionado(verificador):
    verificador.verdadeiro(
        acoes.NOMES[:4] == (
            'andar', 'correr', 'correr_pulo', 'andar_pulo'
        ) and acoes.VERSAO_CATALOGO == 2,
        'andar_pulo ocupa o indice 3 no catalogo novo',
    )
    caminho = caminho_padrao_modelo(
        {'cenario': 'labirinto_parkours'}, 'frente_1'
    )
    verificador.verdadeiro(
        caminho.endswith(
            'q_learning_labirinto_parkours_frente_1_acoes_v2_estado_v2.json'
        ),
        'as novas acoes e o novo estado ignoram modelos antigos',
    )


def teste_exploracao_dura_o_treino_inteiro(verificador):
    configuracao = parkour_config.carregar()
    decaimento = configuracao['q_learning']['exploracao_decaimento']
    epsilon_na_metade = decaimento ** 3500
    verificador.verdadeiro(
        decaimento == 0.9995 and epsilon_na_metade > 0.15,
        'o epsilon ainda permite explorar depois de metade de 7000 episodios',
    )


def teste_tres_frentes_em_ordem_de_dificuldade(verificador):
    configuracao = parkour_config.carregar(cenario='labirinto_parkours')
    trechos = configuracao['trechos']
    percursos = []
    for nome in trechos:
        definicao = parkour_config.trecho(configuracao, nome)
        percursos.append(Percurso.carregar(
            parkour_config.caminho_mapa(configuracao, definicao), definicao
        ))
    verificador.verdadeiro(
        list(trechos) == ['frente_1', 'frente_2', 'frente_3']
        and trechos['frente_2']['inicio'] == {'x': 87, 'y': 125, 'z': 65}
        and trechos['frente_3']['inicio'] == {'x': 87, 'y': 125, 'z': 56}
        and all(percurso.tem_solucao() for percurso in percursos),
        'as tres frentes mantem geometria separada e uma rota valida',
    )


class PercursoPisoFalso:
    x_min = -0.5
    x_max = 0.5

    def __init__(self, apoios):
        self.apoios = apoios

    def superficies_em(self, z):
        return self.apoios.get(z, [])


class CorpoEstadoFalso:
    x = 0.0
    y = 10.0
    z = 0.25
    vy = 0.0
    vz = 0.2
    no_chao = True


def teste_estado_distingue_altura_do_apoio(verificador):
    faixa = [(-0.4, 0.4)]
    corpo = CorpoEstadoFalso()
    mesmo_nivel = estado.Discretizador(
        PercursoPisoFalso({1: [(10.0, faixa)]}), modo='piso'
    )
    um_acima = estado.Discretizador(
        PercursoPisoFalso({1: [(11.0, faixa)]}), modo='piso'
    )
    queda_longa = estado.Discretizador(
        PercursoPisoFalso({1: [(6.0, faixa)]}), modo='piso'
    )

    indices = {
        mesmo_nivel.indice(corpo),
        um_acima.indice(corpo),
        queda_longa.indice(corpo),
    }
    verificador.verdadeiro(
        len(indices) == 3 and mesmo_nivel.quantidade == 3456
        and estado.VERSAO_ESTADO == 2,
        'o estado diferencia nivel, subida e queda longa sem ficar enorme',
    )


def teste_meta_exige_pouso(verificador):
    ambiente = AmbienteMinecraft.__new__(AmbienteMinecraft)
    ambiente.percurso = type('Percurso', (), {
        'y_pe': 125,
        'z_meta': 53,
        'z_chegada': 51,
        'superficies_em': lambda _self, z: (
            [(125.0, [(-0.4, 0.4)])] if z == 51 else []
        ),
    })()
    ambiente.queda_abaixo_de = 3.0
    ambiente.passos_parado = 0
    ambiente.corpo = type('Corpo', (), {
        'x': 0.0,
        'y': 125.0,
        'z': 51.5,
        'no_chao': False,
    })()

    no_ar = ambiente._motivo_terminal(51.5)
    ambiente.corpo.no_chao = True
    pousado = ambiente._motivo_terminal(51.5)
    ambiente.corpo.x = 2.0
    fora_da_pista = ambiente._motivo_terminal(51.5)
    verificador.verdadeiro(
        no_ar is None and pousado == 'meta' and fora_da_pista is None,
        'a meta exige pouso sobre uma superficie mapeada da pista',
    )


def teste_volume_sobre_plataforma_completa_meta(verificador):
    ambiente = AmbienteMinecraft.__new__(AmbienteMinecraft)
    ambiente.percurso = type('Percurso', (), {
        'plataforma_meta': {
            'inicio': {'x': 32, 'y': 124, 'z': 54},
            'fim': {'x': 36, 'y': 127, 'z': 77},
        },
    })()
    corpo = type('Corpo', (), {
        'no_chao': False,
        'posicao_mundo': (34.5, 125.0, 74.5),
    })()
    ambiente.corpo = corpo

    dentro_no_ar = ambiente._atingiu_meta()
    corpo.posicao_mundo = (34.5, 127.9, 74.5)
    acima_da_plataforma = ambiente._atingiu_meta()
    corpo.posicao_mundo = (34.5, 128.0, 74.5)
    alto_demais = ambiente._atingiu_meta()
    corpo.posicao_mundo = (37.0, 125.0, 74.5)
    fora_lateral = ambiente._atingiu_meta()

    verificador.verdadeiro(
        (dentro_no_ar and acima_da_plataforma
         and not alto_demais and not fora_lateral),
        'entrar no volume de tres blocos sobre a plataforma conta como chegada',
    )


def teste_meta_detectada_no_tick_do_pouso(verificador):
    ambiente = AmbienteMinecraft.__new__(AmbienteMinecraft)
    ambiente.percurso = type('Percurso', (), {
        'y_pe': 125.0,
        'z_inicio': 0.0,
        'z_meta': 53.0,
        'z_chegada': 51.0,
        'comprimento': lambda _self: 53.0,
        'superficies_em': lambda _self, z: (
            [(125.0, [(-0.4, 0.4)])] if z == 51 else []
        ),
    })()
    corpo = type('Corpo', (), {
        'x': 0.0,
        'y': 125.0,
        'z': 50.5,
        'no_chao': False,
        'posicao_mundo': (0.0, 125.0, 50.5),
    })()
    controles = []
    ambiente.bot = type('Bot', (), {
        'setControlState': lambda _self, nome, valor: controles.append(
            (nome, valor)
        ),
    })()
    ambiente.corpo = corpo
    ambiente.discretizador = type('Estado', (), {
        'indice': lambda _self, _corpo: 0,
    })()
    ambiente.recompensa = Recompensa({})
    ambiente.ticks_por_acao = 4
    ambiente.passos_maximos = 80
    ambiente.queda_abaixo_de = 3.0
    ambiente.passos = 0
    ambiente.passos_parado = 0
    ambiente.z_maximo = 50.5
    ambiente.z_maximo_valido = 50.5
    ambiente.motivo = None
    ticks = []

    def esperar(_quantidade):
        ticks.append(1)
        if len(ticks) == 1:
            corpo.z = 50.9
        else:
            corpo.z = 51.1
            corpo.no_chao = True
        corpo.posicao_mundo = (0.0, corpo.y, corpo.z)

    ambiente._esperar_ticks = esperar
    _estado, _recompensa, terminou, _truncou, informacoes = ambiente.passo(0)

    verificador.verdadeiro(
        terminou and informacoes['motivo'] == 'meta' and len(ticks) == 2,
        'a acao para no tick exato em que o bot pousa na plataforma final',
    )


def teste_reset_recupera_dano_e_fome(verificador):
    ambiente = AmbienteMinecraft.__new__(AmbienteMinecraft)
    ambiente.bot = type('Bot', (), {
        'username': 'BotTeste',
        'health': 12.0,
        'food': 8.0,
    })()
    comandos = []
    esperas = []
    ambiente.emitir_comando = comandos.append
    ambiente._esperar_ticks = esperas.append

    ambiente._restaurar_condicao()

    verificador.verdadeiro(
        len(comandos) == 2
        and 'instant_health' in comandos[0]
        and 'saturation' in comandos[1]
        and esperas == [1],
        'o reset restaura vida e fome acumuladas no parkour com queda',
    )


def teste_salvar_e_carregar(verificador):
    original = QLearning(2, 2, {'exploracao_inicial': 0.4}, semente=0)
    original.tabela[0][1] = 7.5
    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, 'tabela.json')
        original.salvar(caminho)
        copia = QLearning(2, 2, {'exploracao_inicial': 1.0}, semente=1)
        copia.carregar(caminho)
    verificador.perto(copia.tabela[0][1], 7.5, 1e-9,
                      'a tabela salva volta com os mesmos valores')
    verificador.perto(copia.exploracao, 0.4, 1e-9,
                      'o epsilon tambem e restaurado')


def teste_migracao_ao_adicionar_acao(verificador):
    antigo = QLearning(2, 4, {
        'exploracao_inicial': 0.05,
        'acoes_permitidas': [1, 2],
    })
    antigo.tabela[0][1] = 4.5
    antigo.tabela[0][2] = 8.0

    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, 'tabela.json')
        antigo.salvar(caminho)
        migrado = QLearning(2, 4, {
            'exploracao_inicial': 1.0,
            'exploracao_ao_expandir_acoes': 0.30,
            'acoes_permitidas': [0, 1, 2],
        })
        migrado.carregar(caminho)
        backup_existe = os.path.isfile(migrado.backup_migracao)

    verificador.verdadeiro(
        migrado.acoes_adicionadas_ao_carregar == (0,)
        and migrado.tabela[0] == [0.0, 4.5, 8.0, 0.0]
        and backup_existe,
        'a migracao preserva valores e cria backup antes de liberar andar',
    )
    verificador.perto(
        migrado.exploracao, 0.30, 1e-9,
        'a migracao reativa a exploracao para aprender a nova acao',
    )


def teste_migracao_rejeita_troca_de_acoes(verificador):
    antigo = QLearning(1, 4, {
        'acoes_permitidas': [1, 2],
    })
    rejeitou = False
    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, 'tabela.json')
        antigo.salvar(caminho)
        incompativel = QLearning(1, 4, {
            'acoes_permitidas': [0, 2],
        })
        try:
            incompativel.carregar(caminho)
        except ValueError:
            rejeitou = True

    verificador.verdadeiro(
        rejeitou,
        'a migracao recusa remover ou trocar uma acao ja treinada',
    )


def teste_nomes_de_varios_bots(verificador):
    nomes = nomes_dos_bots('NomeMuitoCompridoBot', 4)
    verificador.verdadeiro(len(set(nomes)) == 4,
                           'todos os bots recebem nomes diferentes')
    verificador.verdadeiro(all(len(nome) <= 16 for nome in nomes),
                           'os nomes respeitam o limite do Minecraft')


def teste_respawn_nao_duplica_conexao(verificador):
    ator = AtorFalso('Controlador')
    ator.pronto.clear()
    grupo = GrupoParkour.__new__(GrupoParkour)
    grupo.atores = [ator]
    grupo.controlador = ator
    preparacoes = []
    mensagens = []
    grupo._preparar_equipe = lambda candidato: preparacoes.append(candidato)
    grupo.falar = lambda mensagem: mensagens.append(mensagem)

    grupo._marcar_como_pronto(ator)
    grupo._marcar_como_pronto(ator)

    verificador.verdadeiro(
        len(preparacoes) == 1 and len(mensagens) == 1,
        'respawn nao e contado como uma nova conexao',
    )


def teste_atualizacao_concorrente(verificador):
    agente = QLearning(2, 1, {
        'taxa_aprendizado': 0.2,
        'exploracao_inicial': 0.0,
    })

    def aprender_muitas_vezes():
        for _ in range(500):
            agente.aprender(0, 0, 1.0, 1, True)

    tarefas = [threading.Thread(target=aprender_muitas_vezes)
               for _ in range(8)]
    for tarefa in tarefas:
        tarefa.start()
    for tarefa in tarefas:
        tarefa.join()

    verificador.verdadeiro(
        agente.visitas[0] == 4000,
        'nenhuma experiencia simultanea e perdida',
    )


def teste_salvamento_concorrente(verificador):
    agente = QLearning(20, 2, {'exploracao_inicial': 0.5})
    erros = []
    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, 'compartilhada.json')

        def salvar_muitas_vezes():
            try:
                for _ in range(10):
                    agente.salvar(caminho)
            except Exception as erro:
                erros.append(erro)

        tarefas = [threading.Thread(target=salvar_muitas_vezes)
                   for _ in range(4)]
        for tarefa in tarefas:
            tarefa.start()
        for tarefa in tarefas:
            tarefa.join()
        copia = QLearning(20, 2, {'exploracao_inicial': 1.0})
        copia.carregar(caminho)

    verificador.verdadeiro(not erros,
                           'salvamentos simultaneos nao disputam o arquivo')
    verificador.perto(copia.exploracao, 0.5, 1e-9,
                      'o arquivo concorrente permanece valido')


def teste_penalidade_de_travamento(verificador):
    recompensa = Recompensa({
        'progresso': 0.0,
        'por_passo': 0.0,
        'parado': 0.0,
        'travado': -7.0,
    })
    verificador.perto(
        recompensa.calcular(0.0, 0.0, 'travado'), -7.0, 1e-9,
        'ficar travado recebe a penalidade configurada',
    )


class AmbienteFalso:
    quantidade_estados = 2
    quantidade_acoes = 1

    def __init__(self):
        self.episodios = 0

    def reset(self):
        self.episodios += 1
        self.passos = 0
        return 0, self.informacoes()

    def passo(self, _acao):
        self.passos += 1
        return 1, 2.0, True, False, self.informacoes()

    def informacoes(self):
        return {
            'passos': self.passos,
            'progresso': float(self.passos > 0),
            'chegou': self.passos > 0,
            'motivo': 'meta' if self.passos > 0 else None,
        }


class AtorFalso:
    def __init__(self, nome):
        self.nome = nome
        self.pronto = threading.Event()
        self.pronto.set()
        self.ambiente = AmbienteFalso()

    def preparar_ambiente(self):
        return self.ambiente

    def soltar_controles(self):
        pass


def teste_laco_de_episodio(verificador):
    agente = QLearning(2, 1, {
        'taxa_aprendizado': 1.0,
        'exploracao_inicial': 0.0,
    })
    resultado = rodar_episodio(AmbienteFalso(), agente)
    verificador.verdadeiro(resultado['chegou'],
                           'o laco encerra quando o ambiente chega a meta')
    verificador.perto(agente.tabela[0][0], 2.0, 1e-9,
                      'o laco atualiza a tabela com a experiencia do ambiente')
    verificador.verdadeiro(
        resultado['acoes'] == 'andar=1',
        'o episodio registra quantas vezes cada acao foi usada',
    )


def teste_distribuicao_entre_bots(verificador):
    agente = QLearning(2, 1, {
        'taxa_aprendizado': 1.0,
        'exploracao_inicial': 0.0,
    })
    grupo = GrupoParkour.__new__(GrupoParkour)
    grupo.atores = [AtorFalso(f'Bot{numero}') for numero in range(4)]
    grupo.controlador = grupo.atores[0]
    grupo.agente = agente
    grupo.bloqueio_agente = threading.Lock()
    grupo.bloqueio_persistencia = threading.Lock()
    grupo.bloqueio_resultados = threading.Lock()
    grupo.parar_pedido = threading.Event()
    grupo.falar = lambda _mensagem: None

    with tempfile.TemporaryDirectory() as pasta:
        grupo.caminho_modelo = os.path.join(pasta, 'modelo.json')
        grupo.comando_treinar(5)
        caminho_csv = os.path.splitext(grupo.caminho_modelo)[0] + \
            '_resultado.csv'
        with open(caminho_csv, encoding='utf-8') as arquivo:
            linhas = arquivo.readlines()

    verificador.verdadeiro(
        agente.visitas[0] == 20
        and all(ator.ambiente.episodios == 5 for ator in grupo.atores),
        'cada bot executa a quantidade de rodadas pedida',
    )
    verificador.verdadeiro(
        len(linhas) == 21,
        'todos os episodios paralelos aparecem no historico',
    )


def teste_historico_csv(verificador):
    info = {
        'recompensa': 2.0,
        'passos': 1,
        'progresso': 1.0,
        'chegou': True,
        'motivo': 'meta',
    }
    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, 'resultado.csv')
        acrescentar_resultado(caminho, 'treino', 1, info, 0.5)
        acrescentar_resultado(caminho, 'treino', 2, info, 0.4)
        with open(caminho, encoding='utf-8') as arquivo:
            linhas = arquivo.readlines()
    verificador.verdadeiro(
        len(linhas) == 3
        and 'progresso_valido' in linhas[0]
        and 'altura_final' in linhas[0]
        and 'acoes' in linhas[0],
        'o CSV registra diagnosticos e acrescenta episodios',
    )


def main():
    verificador = Verificador('q_learning')
    for nome, funcao in sorted(globals().items()):
        if nome.startswith('teste_'):
            verificador.secao(nome)
            funcao(verificador)
    return verificador.encerrar()


if __name__ == '__main__':
    sys.exit(main())
