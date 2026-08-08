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
    verificador.verdadeiro(informacoes['chegou'],
                           'correr e pular para frente conclui o treino simples')


def main():
    verificador = Verificador("ambiente")
    for nome, funcao in sorted(globals().items()):
        if nome.startswith('teste_'):
            verificador.secao(nome)
            funcao(verificador)
    return verificador.encerrar()


if __name__ == '__main__':
    sys.exit(main())
