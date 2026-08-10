"""Testes do ambiente, do estado e da recompensa.

Rodam no mapa de verdade, sem Minecraft:

    python -m testes.teste_ambiente

O teste mais importante daqui e o de reward hacking. A pag. 4 do PDF pede
explicitamente para "verificar se o bot consegue acumular recompensa sem
realmente progredir", e essa e a falha classica de uma recompensa mal escrita.
"""

import sys

from src.parkour import acoes, config as configuracao_modulo
from src.parkour.agentes.aleatorio import AgenteAleatorio
from src.parkour.agentes.guloso import AgenteGuloso
from src.parkour.agentes.q_learning import AgenteQLearning
from src.parkour.ambiente_mc import AmbienteMinecraft
from src.parkour.ambiente_sim import AmbienteParkour
from src.parkour.coordenadas import TransformacaoPercurso
from src.parkour.percurso import Percurso
from testes.apoio import Verificador


def montar(nome_trecho='A', randomizar=False, semente=0):
    configuracao = configuracao_modulo.carregar()
    definicao = configuracao_modulo.trecho(configuracao, nome_trecho)
    percurso = Percurso.carregar(
        configuracao_modulo.caminho_absoluto(configuracao['mapa']), definicao)
    return AmbienteParkour(percurso, configuracao, semente=semente,
                           randomizar=randomizar)


def rodar(ambiente, agente, maximo=500):
    ambiente.reset()
    estado = ambiente.observar()
    total = 0.0
    for _ in range(maximo):
        acao = agente.escolher(estado, ambiente)
        _, recompensa, terminou, truncou, informacoes = ambiente.passo(acao)
        estado = ambiente.observar()
        total += recompensa
        if terminou or truncou:
            break
    informacoes['recompensa'] = total
    return informacoes


def teste_reset_reprodutivel(verificador):
    """Sem reset confiavel, comparar dois agentes nao quer dizer nada.

    E o criterio de avanco da etapa 1 do PDF. Reprodutivel aqui quer dizer
    "a mesma semente da o mesmo episodio", e nao "todo episodio e igual": o
    ponto de partida varia de proposito, senao a avaliacao repetiria o mesmo
    episodio 200 vezes e informaria isso como se fossem 200 amostras.
    """
    def sequencia(semente):
        ambiente = montar(semente=semente)
        posicoes = []
        for _ in range(5):
            ambiente.reset(semente=semente)
            ambiente.passo(1)
            ambiente.passo(1)
            posicoes.append((round(ambiente.corpo.x, 9), round(ambiente.corpo.z, 9)))
        return posicoes

    verificador.verdadeiro(sequencia(42) == sequencia(42),
                           "a mesma semente reproduz a mesma sequencia")
    verificador.verdadeiro(sequencia(42) != sequencia(7),
                           "sementes diferentes dao sequencias diferentes")

    # Sem variacao, todo reset cai no mesmo lugar.
    fixo = montar()
    fixo.variar_inicio = False
    posicoes = set()
    for _ in range(5):
        fixo.reset()
        posicoes.add((round(fixo.corpo.x, 9), round(fixo.corpo.z, 9)))
    verificador.verdadeiro(len(posicoes) == 1,
                           f"com variar_inicio desligado o reset e fixo: {posicoes}")

    ambiente = montar()
    ambiente.reset()
    verificador.perto(ambiente.corpo.z, ambiente.percurso.z_inicio + 0.5, 1e-9,
                      "comeca no inicio do trecho")
    verificador.verdadeiro(ambiente.corpo.no_chao, "comeca com os pes no chao")
    verificador.verdadeiro(ambiente.passos == 0, "zera a contagem de passos")

    # O sorteio nao pode colocar o bot num lugar sem saida.
    fora = 0
    for _ in range(50):
        ambiente.reset()
        viaveis = ambiente.percurso.posicoes_viaveis(ambiente.percurso.z_inicio)
        if not any(inicio <= ambiente.corpo.x <= fim for inicio, fim in viaveis):
            fora += 1
    verificador.verdadeiro(fora == 0,
                           "o inicio sorteado cai sempre numa faixa viavel")


def teste_ambiente_mc_sincroniza_reset_e_controles(verificador):
    """Latencia do servidor nao pode liberar um episodio antes do /tp."""
    class Objeto:
        pass

    class BotFalso:
        def __init__(self):
            self.username = 'LucidioBot'
            self.entity = Objeto()
            self.entity.position = Objeto()
            self.entity.position.x = 0.0
            self.entity.position.y = 0.0
            self.entity.position.z = 0.0
            self.entity.onGround = False
            self.entity.velocity = Objeto()
            self.entity.velocity.x = 0.0
            self.entity.velocity.y = 0.0
            self.entity.velocity.z = 0.0
            self.controles = {}
            self.ticks = 0
            self.destino = None
            self.teleportar_no_tick = None

        def chat(self, mensagem):
            partes = mensagem.split()
            self.destino = tuple(float(valor) for valor in partes[2:5])
            self.teleportar_no_tick = self.ticks + 3

        def waitForTicks(self, quantidade):
            for _ in range(quantidade):
                self.ticks += 1
                if (self.destino is not None
                        and self.ticks >= self.teleportar_no_tick):
                    posicao = self.entity.position
                    posicao.x, posicao.y, posicao.z = self.destino
                    self.entity.onGround = True

        def setControlState(self, nome, valor):
            self.controles[nome] = bool(valor)

    configuracao = configuracao_modulo.carregar(cenario='labirinto_parkours')
    definicao = configuracao_modulo.trecho(configuracao, 'frente_1')
    percurso = Percurso.carregar(
        configuracao_modulo.caminho_mapa(configuracao, definicao), definicao)
    bot = BotFalso()
    ambiente = AmbienteMinecraft(bot, percurso, configuracao)

    ambiente.reset()
    mundo_x, mundo_y, mundo_z = ambiente.corpo.posicao_mundo
    verificador.verdadeiro(bot.ticks >= 5,
                           'reset esperou o teleporte e o assentamento')
    verificador.perto(mundo_x, 87.5, 1e-9,
                      'reset confirmou X no inicio real')
    verificador.perto(mundo_y, 125.0, 1e-9,
                      'reset confirmou Y sobre o piso')
    verificador.perto(mundo_z, 74.5, 1e-9,
                      'reset confirmou Z no centro da pista')

    ambiente.passo(2)  # correr_pulo
    verificador.verdadeiro(
        bot.controles.get('forward') and bot.controles.get('sprint')
        and bot.controles.get('jump'),
        'controles continuam ativos entre duas decisoes')
    ambiente.soltar_controles()
    verificador.verdadeiro(not any(bot.controles.values()),
                           'controles sao soltos ao encerrar')


def teste_ambiente_mc_sincroniza_cada_salto(verificador):
    """O guloso prepara o salto na descida, sem depender de onGround."""
    class Objeto:
        pass

    class BotFalso:
        def __init__(self):
            self.username = 'LucidioBot'
            self.entity = Objeto()
            self.entity.position = Objeto()
            self.entity.position.x = 87.5
            self.entity.position.y = 125.0
            self.entity.position.z = 74.5
            self.entity.onGround = True
            self.entity.velocity = Objeto()
            self.entity.velocity.x = 0.0
            self.entity.velocity.y = 0.0
            self.entity.velocity.z = 0.0
            self.controles = {}
            self.saltos = 0
            self.ticks_no_ar = 0

        def chat(self, mensagem):
            partes = mensagem.split()
            posicao = self.entity.position
            posicao.x, posicao.y, posicao.z = (
                float(valor) for valor in partes[2:5])
            self.entity.onGround = True

        def waitForTicks(self, quantidade):
            for _ in range(quantidade):
                if self.controles.get('forward'):
                    self.entity.position.x -= 0.5
                if self.controles.get('jump') and self.entity.onGround:
                    self.entity.onGround = False
                    self.entity.position.y = 126.0
                    self.entity.velocity.y = 0.42
                    self.ticks_no_ar = 6
                if not self.entity.onGround:
                    self.ticks_no_ar -= 1
                    if self.ticks_no_ar <= 3:
                        self.entity.velocity.y = -0.2
                    if self.ticks_no_ar <= 0:
                        self.entity.onGround = True
                        self.entity.position.y = 125.0
                        self.entity.velocity.y = 0.0

        def setControlState(self, nome, valor):
            valor = bool(valor)
            if (nome == 'jump' and valor
                    and not self.controles.get('jump', False)):
                self.saltos += 1
            self.controles[nome] = valor

    configuracao = configuracao_modulo.carregar(cenario='labirinto_parkours')
    definicao = configuracao_modulo.trecho(configuracao, 'frente_1')
    percurso = Percurso.carregar(
        configuracao_modulo.caminho_mapa(configuracao, definicao), definicao)
    bot = BotFalso()
    ambiente = AmbienteMinecraft(bot, percurso, configuracao)

    ambiente.reset()
    informacoes = ambiente.correr_com_saltos_sincronizados()

    verificador.verdadeiro(informacoes['chegou'],
                           'saltos sincronizados chegam ao fim do corredor')
    verificador.verdadeiro(bot.saltos > 10,
                           'o pulo e rearmado entre subida e descida')
    verificador.verdadeiro(not any(bot.controles.values()),
                           'controles sincronizados sao soltos ao terminar')


def teste_estado_dentro_dos_limites(verificador):
    """Nenhum indice de estado pode estourar o tamanho da tabela Q."""
    ambiente = montar()
    agente = AgenteAleatorio(ambiente.quantidade_acoes, semente=7)

    menor, maior = None, None
    for _ in range(40):
        ambiente.reset()
        for _ in range(60):
            indice = ambiente.observar()
            menor = indice if menor is None else min(menor, indice)
            maior = indice if maior is None else max(maior, indice)
            _, _, terminou, truncou, _ = ambiente.passo(agente.escolher(indice))
            if terminou or truncou:
                break

    verificador.verdadeiro(menor >= 0, f"indice minimo valido ({menor})")
    verificador.verdadeiro(maior < ambiente.quantidade_estados,
                           f"indice maximo {maior} < {ambiente.quantidade_estados}")

    ambiente.reset()
    vetor = ambiente.observar_vetor()
    verificador.verdadeiro(len(vetor) == ambiente.tamanho_vetor,
                           f"o vetor do DQN tem {ambiente.tamanho_vetor} valores")
    verificador.verdadeiro(all(-50 <= valor <= 50 for valor in vetor),
                           "os valores do vetor estao em escala razoavel")


def teste_estado_piso_e_acoes_restritas_do_labirinto(verificador):
    """O cenario simples enxerga vaos sem alterar o mapa oficial."""
    configuracao = configuracao_modulo.carregar(cenario='labirinto_parkours')
    definicao = configuracao_modulo.trecho(configuracao, 'frente_1')
    percurso = Percurso.carregar(
        configuracao_modulo.caminho_mapa(configuracao, definicao), definicao)
    ambiente = AmbienteParkour(percurso, configuracao, semente=0,
                               randomizar=False)
    ambiente.reset()
    discretizador = ambiente.discretizador

    verificador.verdadeiro(discretizador.modo == 'piso',
                           'labirinto ativa o estado de piso')
    verificador.verdadeiro(ambiente.quantidade_estados == 576,
                           'estado de piso possui somente 576 combinacoes')

    corpo = ambiente.corpo
    estado_inicio = ambiente.observar()
    corpo.z = 0.9
    estado_borda = ambiente.observar()
    corpo.no_chao = False
    corpo.vy = 0.3
    estado_subindo = ambiente.observar()
    corpo.vy = -0.3
    estado_descendo = ambiente.observar()

    verificador.verdadeiro(estado_inicio != estado_borda,
                           'meio e borda do bloco sao estados diferentes')
    verificador.verdadeiro(estado_borda != estado_subindo,
                           'chao e subida sao estados diferentes')
    verificador.verdadeiro(estado_subindo != estado_descendo,
                           'subida e descida sao estados diferentes')

    parametros = configuracao_modulo.parametros_q_learning(configuracao)
    agente = AgenteQLearning(ambiente.quantidade_estados,
                             ambiente.quantidade_acoes, parametros, semente=0)
    escolhas = {agente.escolher(estado_inicio) for _ in range(100)}
    verificador.verdadeiro(escolhas <= {1, 2} and escolhas == {1, 2},
                           'Q explora somente correr e correr_pulo')
    agente.modo_avaliacao()
    agente.tabela[estado_inicio][9] = 999.0
    verificador.verdadeiro(agente.escolher(estado_inicio) in {1, 2},
                           'Q guloso ignora acao proibida mesmo se ela vale mais')
    agente.tabela[estado_inicio][1] = 0.0
    agente.tabela[estado_inicio][2] = 0.0
    agente.tabela[estado_borda][1] = 2.0
    agente.tabela[estado_borda][2] = 3.0
    agente.tabela[estado_borda][9] = 999.0
    agente.aprender(estado_inicio, 1, 0.0, estado_borda, False)
    esperado = agente.taxa_aprendizado * agente.desconto * 3.0
    verificador.perto(agente.tabela[estado_inicio][1], esperado, 1e-9,
                      'Bellman usa somente o melhor futuro permitido')

    oficial = configuracao_modulo.carregar()
    ambiente_oficial = montar()
    agente_oficial = AgenteQLearning(
        ambiente_oficial.quantidade_estados,
        ambiente_oficial.quantidade_acoes,
        configuracao_modulo.parametros_q_learning(oficial), semente=0)
    verificador.verdadeiro(ambiente_oficial.discretizador.modo == 'mascara',
                           'mapa oficial preserva o estado mascara')
    verificador.verdadeiro(
        agente_oficial.acoes_permitidas == tuple(range(acoes.QUANTIDADE)),
        'mapa oficial preserva todas as dez acoes')


def teste_recompensa_segue_o_progresso(verificador):
    """Avancar tem que valer mais que ficar parado, e cair tem que doer."""
    ambiente = montar()

    ambiente.reset()
    _, andando, _, _, _ = ambiente.passo(1)      # correr para frente
    ambiente.reset()
    _, parado, _, _, _ = ambiente.passo(5)       # nao fazer nada

    verificador.verdadeiro(andando > parado,
                           f"avancar ({andando:.3f}) vale mais que parar ({parado:.3f})")
    verificador.verdadeiro(parado < 0, f"ficar parado e penalizado ({parado:.3f})")

    # Andar de lado ate cair.
    ambiente.reset()
    recompensa_queda = 0.0
    for _ in range(60):
        _, recompensa, terminou, truncou, informacoes = ambiente.passo(4)
        recompensa_queda = recompensa
        if terminou or truncou:
            break
    verificador.verdadeiro(informacoes['motivo'] == 'queda', "o episodio acabou em queda")
    verificador.verdadeiro(recompensa_queda < -5.0,
                           f"a queda e bem penalizada ({recompensa_queda:.2f})")


def teste_sem_reward_hacking(verificador):
    """Ir e voltar nao pode render recompensa.

    Se o progresso contasse o deslocamento absoluto em vez do liquido, o
    agente aprenderia a oscilar no lugar para sempre. Este teste amarra isso.
    """
    ambiente = montar()
    ambiente.reset()

    total = 0.0
    for ciclo in range(20):
        for _ in range(3):
            _, recompensa, terminou, truncou, _ = ambiente.passo(1)   # frente
            total += recompensa
            if terminou or truncou:
                break
        for _ in range(3):
            _, recompensa, terminou, truncou, _ = ambiente.passo(5)   # parar
            total += recompensa
            if terminou or truncou:
                break
        if terminou or truncou:
            break

    z_liquido = ambiente.corpo.z - (ambiente.percurso.z_inicio + 0.5)
    verificador.verdadeiro(
        total <= z_liquido * ambiente.recompensa.progresso + 1e-6,
        f"a recompensa ({total:.2f}) nao passa do progresso liquido "
        f"({z_liquido:.2f} blocos)")


def teste_episodio_sempre_termina(verificador):
    """Nenhuma sequencia de acoes pode prender o laco para sempre."""
    ambiente = montar()
    agente = AgenteAleatorio(ambiente.quantidade_acoes, semente=3)

    maiores = 0
    for _ in range(30):
        informacoes = rodar(ambiente, agente, maximo=1000)
        maiores = max(maiores, informacoes['passos'])
        if informacoes['motivo'] is None:
            break

    verificador.verdadeiro(maiores <= ambiente.passos_maximos,
                           f"nenhum episodio passou de {ambiente.passos_maximos} "
                           f"passos (maior: {maiores})")


def teste_trecho_tem_solucao(verificador):
    """Antes de treinar, e preciso saber que existe caminho ate o fim.

    Se nem a politica gulosa passa, o problema esta no trecho ou na fisica, e
    nenhum algoritmo de RL vai resolver isso.
    """
    guloso = AgenteGuloso()
    configuracao = configuracao_modulo.carregar()
    for nome_trecho in sorted(configuracao['trechos']):
        ambiente = montar(nome_trecho)
        verificador.verdadeiro(
            ambiente.percurso.tem_solucao(),
            f"trecho {nome_trecho}: a analise de viabilidade acha caminho")
        # Nos trechos de escalada a garantia e so a geometrica: o guloso e um
        # planejador miope, resolve os trechos planos sempre e os de escalada
        # so em parte (medido: 28% no bamboo_escalada, 52% no end_escalada).
        # Exigir o contrario seria fingir que a heuristica e um solucionador.
        if configuracao['trechos'][nome_trecho].get('escalada'):
            continue
        informacoes = rodar(ambiente, guloso)
        verificador.verdadeiro(
            informacoes['chegou'],
            f"trecho {nome_trecho}: o guloso chega ao fim "
            f"({informacoes['passos']} passos)")


def teste_guloso_supera_aleatorio(verificador):
    """O piso e o teto de comparacao precisam estar na ordem certa."""
    ambiente = montar()
    guloso = AgenteGuloso()
    aleatorio = AgenteAleatorio(ambiente.quantidade_acoes, semente=11)

    chegadas_guloso = sum(rodar(ambiente, guloso)['chegou'] for _ in range(20))
    chegadas_aleatorio = sum(rodar(ambiente, aleatorio)['chegou'] for _ in range(20))

    verificador.verdadeiro(chegadas_guloso == 20,
                           f"o guloso chega sempre ({chegadas_guloso}/20)")
    verificador.verdadeiro(chegadas_guloso > chegadas_aleatorio,
                           f"o guloso ({chegadas_guloso}/20) supera o aleatorio "
                           f"({chegadas_aleatorio}/20)")


def teste_randomizacao_muda_o_resultado(verificador):
    """Com ruido ligado, dois episodios iguais nao dao exatamente o mesmo fim."""
    com_ruido = montar(randomizar=True, semente=5)
    finais = set()
    for _ in range(8):
        com_ruido.reset()
        for _ in range(10):
            com_ruido.passo(1)
        finais.add(round(com_ruido.corpo.z, 6))

    verificador.verdadeiro(len(finais) > 1,
                           f"o ruido produz trajetorias diferentes ({len(finais)} finais)")

    sem_ruido = montar(randomizar=False, semente=5)
    finais = set()
    for _ in range(8):
        sem_ruido.reset()
        for _ in range(10):
            sem_ruido.passo(1)
        finais.add(round(sem_ruido.corpo.z, 6))

    verificador.verdadeiro(len(finais) == 1,
                           "sem ruido, a trajetoria e sempre a mesma")


def teste_catalogo_de_acoes(verificador):
    ambiente = montar()
    verificador.verdadeiro(ambiente.quantidade_acoes == len(acoes.CATALOGO),
                           f"{len(acoes.CATALOGO)} acoes no catalogo")
    verificador.verdadeiro(len(set(acoes.NOMES)) == len(acoes.NOMES),
                           "nenhum nome de acao repetido")


def teste_cenarios_e_direcoes(verificador):
    """O mesmo ambiente deve aceitar corredores em qualquer eixo cardinal."""
    inicio = {'x': 10, 'y': 70, 'z': 20}
    casos = (
        ({'x': 15, 'y': 70, 'z': 20}, '+X', -90.0),
        ({'x': 5, 'y': 70, 'z': 20}, '-X', 90.0),
        ({'x': 10, 'y': 70, 'z': 25}, '+Z', 0.0),
        ({'x': 10, 'y': 70, 'z': 15}, '-Z', 180.0),
    )
    for fim, direcao, yaw in casos:
        transformacao = TransformacaoPercurso(inicio, fim)
        local_inicio = transformacao.para_local(10.5, 70, 20.5)
        mundo_inicio = transformacao.para_mundo(*local_inicio)
        local_fim = transformacao.para_local(fim['x'] + 0.5, 70,
                                             fim['z'] + 0.5)
        verificador.perto(local_inicio[2], 0.5, 1e-9,
                          f'{direcao}: inicio vira progresso 0.5')
        verificador.perto(local_fim[2], 5.5, 1e-9,
                          f'{direcao}: fim fica cinco blocos adiante')
        verificador.verdadeiro(mundo_inicio == (10.5, 70.0, 20.5),
                               f'{direcao}: conversao de ida e volta preserva posicao')
        verificador.perto(transformacao.yaw, yaw, 1e-9,
                          f'{direcao}: yaw aponta para a meta')

    menos_x = TransformacaoPercurso(inicio, {'x': 5, 'y': 70, 'z': 20})
    verificador.verdadeiro(menos_x.celula_para_local(7, 20) == (20, 3),
                           '-X: bloco real vira celula local correta')
    verificador.verdadeiro(menos_x.celula_para_mundo(20, 3) == (7, 20),
                           '-X: celula local volta ao bloco real correto')

    configuracao = configuracao_modulo.carregar(cenario='labirinto_parkours')
    definicao = configuracao_modulo.trecho(configuracao, 'frente_1')
    percurso = Percurso.carregar(
        configuracao_modulo.caminho_mapa(configuracao, definicao), definicao)
    ambiente = AmbienteParkour(percurso, configuracao, semente=0, randomizar=False)
    ambiente.reset()
    while True:
        _, _, terminou, truncou, informacoes = ambiente.passo(2)  # correr + pular
        if terminou or truncou:
            break

    verificador.verdadeiro(percurso.mundo == 'world_labirinto',
                           'cenario do labirinto usa o mundo correto')
    verificador.verdadeiro(percurso.transformacao.nome_direcao == '-X',
                           'frente_1 transforma -X em progresso positivo')
    verificador.perto(percurso.comprimento(), 53.0, 1e-9,
                      'frente_1 usa as coordenadas atualizadas')
    verificador.verdadeiro(
        AgenteGuloso().escolher(ambiente.observar(), ambiente) == 2,
        'guloso mantem correr_pulo no corredor simples')
    verificador.verdadeiro(informacoes['chegou'],
                           'correr e pular para frente conclui o treino simples')

    definicao_2 = configuracao_modulo.trecho(configuracao, 'frente_2')
    percurso_2 = Percurso.carregar(
        configuracao_modulo.caminho_mapa(configuracao, definicao_2), definicao_2)
    alturas_2 = [altura for z in range(percurso_2.z_inicio, percurso_2.z_meta + 1)
                 for altura, _ in percurso_2.superficies_em(z)]
    verificador.verdadeiro(percurso_2.transformacao.nome_direcao == '-X',
                           'frente_2 transforma -X em progresso positivo')
    verificador.perto(percurso_2.comprimento(), 53.0, 1e-9,
                      'frente_2 usa as coordenadas atualizadas')
    verificador.verdadeiro(max(alturas_2) > percurso_2.y_pe,
                           'frente_2 preserva os apoios em alturas diferentes')


def main():
    verificador = Verificador("ambiente")
    for nome, funcao in sorted(globals().items()):
        if nome.startswith('teste_'):
            verificador.secao(nome)
            funcao(verificador)
    return verificador.encerrar()


if __name__ == '__main__':
    sys.exit(main())
