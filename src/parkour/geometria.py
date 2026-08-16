"""Geometria do corredor: onde o jogador cabe e onde nao cabe.

Este modulo e usado pelas ferramentas de exportacao e pelo estado discreto.
Manter a definicao num lugar so faz o mapa exportado e a observacao do bot
concordarem sobre onde existe passagem.
"""

# Medidas do jogador no Minecraft Java Edition.
LARGURA_JOGADOR = 0.6
ALTURA_JOGADOR = 1.8
ALTURA_DEGRAU = 0.6      # ate esta altura o jogador sobe sem pular


def caixas_horizontais(blocos_do_z, y_min, y_max):
    """Intervalos de x ocupados por blocos entre duas alturas.

    Cada bloco vira um intervalo centrado na celula, com a largura da caixa de
    colisao dele. E por isso que da para passar entre dois bambus: cada haste
    ocupa so 0.19 do meio da celula.
    """
    intervalos = []
    for x, y, altura, largura in blocos_do_z:
        if largura <= 0.0 or altura <= 0.0:
            continue
        if y + altura <= y_min or y >= y_max:
            continue
        meio = x + 0.5
        intervalos.append((meio - largura / 2, meio + largura / 2))
    return intervalos


def vaos_livres(blocos_do_z, x_min, x_max, y_pe,
                largura_necessaria=LARGURA_JOGADOR, altura_passagem=2):
    """Intervalos de x por onde o jogador passa andando, num dado z.

    Um obstaculo na altura dos pes que caiba embaixo do degrau nao conta: o
    jogador sobe nele sem pular.
    """
    atrapalham = []
    for x, y, altura, largura in blocos_do_z:
        if largura <= 0.0 or altura <= 0.0:
            continue
        topo = y + altura
        if topo <= y_pe + ALTURA_DEGRAU:
            continue
        if y >= y_pe + altura_passagem:
            continue
        meio = x + 0.5
        atrapalham.append((meio - largura / 2, meio + largura / 2))

    vaos, cursor = [], float(x_min)
    for inicio, fim in sorted(atrapalham):
        if inicio > cursor:
            vaos.append((cursor, min(inicio, float(x_max))))
        cursor = max(cursor, fim)
        if cursor >= x_max:
            break
    if cursor < x_max:
        vaos.append((cursor, float(x_max)))

    return [(inicio, fim) for inicio, fim in vaos
            if fim - inicio >= largura_necessaria]


def posicoes_validas(blocos_do_z, x_min, x_max, y_pe):
    """Onde o **centro** do jogador pode ficar, num dado z.

    Um vao de largura L so aceita o centro num miolo de L - 0.6, porque o
    jogador tem 0.3 de raio para cada lado.
    """
    meia = LARGURA_JOGADOR / 2
    validos = []
    for inicio, fim in vaos_livres(blocos_do_z, x_min, x_max, y_pe):
        if fim - inicio >= LARGURA_JOGADOR:
            validos.append((inicio + meia, fim - meia))
    return validos


def _unir(intervalos):
    """Junta intervalos que se tocam, para nao contar apoio duas vezes."""
    if not intervalos:
        return []
    saida = []
    for inicio, fim in sorted(intervalos):
        if saida and inicio <= saida[-1][1]:
            saida[-1] = (saida[-1][0], max(saida[-1][1], fim))
        else:
            saida.append((inicio, fim))
    return saida


def _interseccao(primeiros, segundos):
    """Intervalos que estao nas duas listas."""
    saida = []
    for inicio_a, fim_a in primeiros:
        for inicio_b, fim_b in segundos:
            inicio, fim = max(inicio_a, inicio_b), min(fim_a, fim_b)
            if fim > inicio:
                saida.append((inicio, fim))
    return _unir(saida)


def _subtrair(intervalos, buracos):
    """Tira dos intervalos as partes cobertas pelos buracos."""
    saida = list(intervalos)
    for buraco_inicio, buraco_fim in buracos:
        restante = []
        for inicio, fim in saida:
            if buraco_fim <= inicio or buraco_inicio >= fim:
                restante.append((inicio, fim))
                continue
            if inicio < buraco_inicio:
                restante.append((inicio, buraco_inicio))
            if buraco_fim < fim:
                restante.append((buraco_fim, fim))
        saida = restante
    return saida


def _cobertos_por_bloco_baixo(blocos_do_z, y_topo, folga=1e-6):
    """Faixas de x onde algo baixo se apoia em y_topo, impedindo ficar ali.

    `vaos_livres` perdoa obstaculos cujo topo cabe na altura do degrau, porque
    quem anda sobe neles sem pular. Mas quem quer **ficar de pe** em y_topo nao
    pode: o apoio de verdade passa a ser o topo da laje, que aparece sozinho na
    lista de candidatos. As faixas devolvidas aqui saem do nivel de baixo.

    Devolve a faixa ja alargada pelo meio-corpo do jogador: o centro dele nao
    pode chegar a menos de 0.3 da laje, senao o corpo encosta.
    """
    meia = LARGURA_JOGADOR / 2
    faixas = []
    for x, y, altura, largura in blocos_do_z:
        if largura <= 0.0 or altura <= 0.0:
            continue
        topo = y + altura
        if topo <= y_topo + folga or topo > y_topo + ALTURA_DEGRAU:
            continue
        meio = x + 0.5
        faixas.append((meio - largura / 2 - meia, meio + largura / 2 + meia))
    return _unir(faixas)


def apoios(blocos_do_z, y_topo, largura_minima=0.5, tolerancia=1e-6):
    """Intervalos de x que tem chao exatamente no nivel y_topo.

    `largura_minima` descarta haste de bambu e afins: com 0.19 de largura elas
    tecnicamente sustentam o jogador, mas tratar um bambuzal como plataforma
    faria a analise de rota inventar caminhos que ninguem percorre.
    """
    intervalos = []
    for x, y, altura, largura in blocos_do_z:
        if largura < largura_minima or altura <= 0.0:
            continue
        if abs((y + altura) - y_topo) > tolerancia:
            continue
        meio = x + 0.5
        intervalos.append((meio - largura / 2, meio + largura / 2))
    return _unir(intervalos)


def superficies(blocos_do_z, x_min, x_max, largura_minima=0.5):
    """Todas as alturas onde da para ficar de pe num dado z, e em que x.

    Devolve [(y_topo, [(x_inicio, x_fim), ...])], ordenado por altura. E a
    primitiva que faltava para o mapa de verdade: `vaos_livres` responde "da
    para passar nesta altura?", e esta responde "que alturas existem?". Sem
    ela, toda a analise ficava presa ao piso do estagio, e os pedacos do
    percurso que exigem subir simplesmente nao existiam para o agente.
    """
    topos = sorted({round(y + altura, 4)
                    for x, y, altura, largura in blocos_do_z
                    if largura >= largura_minima and altura > 0.0})
    saida = []
    for y_topo in topos:
        suporte = apoios(blocos_do_z, y_topo, largura_minima)
        if not suporte:
            continue
        # Onde ha apoio e, ao mesmo tempo, espaco para o corpo do jogador.
        cabe = posicoes_validas(blocos_do_z, x_min, x_max, y_topo)
        onde = _interseccao(suporte, cabe)
        # Onde uma laje ou tapete se apoia neste nivel, o apoio de verdade e o
        # topo dela - que entra na lista como candidato proprio. Subtrair so a
        # faixa coberta, e nao descartar o intervalo inteiro: a primeira versao
        # deste filtro era tudo-ou-nada e derrubou apoios legitimos, deixando o
        # estagio Pale Garden sem solucao.
        onde = _subtrair(onde, _cobertos_por_bloco_baixo(blocos_do_z, y_topo))
        onde = [(inicio, fim) for inicio, fim in onde if fim > inicio]
        if onde:
            saida.append((y_topo, onde))
    return saida


def faixas_altas_demais(blocos_do_z, y_referencia, altura_livre):
    """Onde o **centro** do jogador nao passa, saltando de y_referencia.

    Um bloco atrapalha o salto quando o topo dele fica acima do apogeu e a base
    ainda esta na altura do corpo. Devolve as faixas ja alargadas pelo
    meio-corpo, porque o centro nao pode chegar a menos de 0.3 do obstaculo.

    Serve para perguntar "existe um x por onde saltar?" em vez de "a faixa
    inteira esta limpa?". A diferenca decide o mapa: qualquer haste de bambu na
    celula do meio reprova a faixa toda, e mesmo assim o jogador passa ao lado
    dela.
    """
    meia = LARGURA_JOGADOR / 2
    apogeu = y_referencia + altura_livre
    faixas = []
    for x, y, altura, largura in blocos_do_z:
        if largura <= 0.0 or altura <= 0.0:
            continue
        if y + altura <= apogeu:
            continue                      # passa por cima
        if y >= apogeu + ALTURA_JOGADOR:
            continue                      # passa por baixo
        meio = x + 0.5
        faixas.append((meio - largura / 2 - meia, meio + largura / 2 + meia))
    return _unir(faixas)


def altura_do_obstaculo(blocos_do_z, y_pe, x_inicio, x_fim):
    """Quanto o obstaculo mais alto sobe acima de y_pe, dentro de uma faixa.

    Devolve 0.0 quando nada atrapalha. E o numero que o estado precisa para
    distinguir um degrau de uma parede: ate ALTURA_DEGRAU o jogador sobe
    andando, ate ~1.25 ele vence pulando, acima disso e parede.
    """
    maior = 0.0
    for x, y, altura, largura in blocos_do_z:
        if largura <= 0.0 or altura <= 0.0:
            continue
        topo = y + altura
        if topo <= y_pe:
            continue
        meio = x + 0.5
        if meio + largura / 2 <= x_inicio or meio - largura / 2 >= x_fim:
            continue
        maior = max(maior, topo - y_pe)
    return maior


def intervalos_se_cruzam(primeiros, segundos):
    """Diz se existe um x que serve nas duas listas de intervalos.

    E o teste de que da para **passar de um z para o outro**. O corpo do
    jogador tem 0.6 de profundidade, entao na fronteira entre duas celulas ele
    ocupa as duas ao mesmo tempo e precisa caber nas duas. Sem esta checagem,
    um trecho onde cada z tem passagem, mas as passagens ficam em lados
    opostos, pareceria andavel e nao e.
    """
    for inicio_a, fim_a in primeiros:
        for inicio_b, fim_b in segundos:
            if max(inicio_a, inicio_b) <= min(fim_a, fim_b):
                return True
    return False
