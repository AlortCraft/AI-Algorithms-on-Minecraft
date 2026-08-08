"""O percurso carregado em memoria.

Guarda a geometria de um trecho do mapa e responde as duas perguntas que o
resto do codigo precisa fazer o tempo todo:

- colisao: quais caixas existem perto de uma posicao (para a fisica);
- leitura do ambiente: onde esta o proximo obstaculo (para o estado).

Tudo fica em memoria local. E esse o motivo de existir tools/mapear_mundo.py:
consultar o mundo pelo bot custaria uma ida-e-volta entre processos por bloco,
o que inviabilizaria o treino.
"""

import collections
import json
import math

from . import geometria
from .coordenadas import TransformacaoPercurso


class Percurso:
    def __init__(self, mapa, z_inicio, z_meta, y_pe=None, nome='?',
                 transformacao=None, mundo=None):
        self.nome = nome
        self.mundo = mundo or mapa.get('meta', {}).get('mundo')
        self.transformacao = transformacao or TransformacaoPercurso.identidade_padrao()
        self.pistas = mapa['pistas']
        self.z_inicio = z_inicio
        self.z_meta = z_meta
        self.y_pe = y_pe if y_pe is not None else mapa['y_pe']

        # Limites laterais da ponte. Passar deles significa cair.
        self.x_min = float(min(self.pistas))
        self.x_max = float(max(self.pistas) + 1)
        # x_partida e ajustado no fim do __init__, quando a geometria ja
        # estiver carregada: o meio do corredor nem sempre esta livre.
        self.x_partida = (self.x_min + self.x_max) / 2

        # Mapas novos guardam tambem o nome do bloco. A fisica usa somente a
        # caixa de colisao; o nome serve para conferir o JSON contra o mundo
        # real com bot.blockAt() antes de executar uma politica.
        self.nomes_blocos = {}
        for chave, nome_bloco in mapa.get('nomes', {}).items():
            x, y, z = (int(valor) for valor in chave.split(','))
            self.nomes_blocos[(x, y, z)] = nome_bloco

        # Indice por coluna (x, z), que e como a fisica consulta.
        self.colunas = collections.defaultdict(list)
        # Indice por z, que e como o estado consulta.
        self.por_z = {}
        for z_texto, blocos in mapa['solidos'].items():
            z = int(z_texto)
            self.por_z[z] = blocos
            for x, y, altura, largura in blocos:
                self.colunas[(x, z)].append((y, altura, largura))
        for chave in self.colunas:
            self.colunas[chave].sort()

        # Pre-calcula os vaos livres de cada z: nao muda durante o episodio e
        # e consultado a cada passo.
        self.vaos = {}
        for z in range(self.z_inicio - 2, self.z_meta + 3):
            self.vaos[z] = geometria.vaos_livres(
                self.por_z.get(z, []), self.x_min, self.x_max, self.y_pe)

        self.z_obstaculos = sorted(
            z for z in range(self.z_inicio, self.z_meta + 1)
            if self._tem_obstaculo(z))

        self.validas = {
            z: geometria.posicoes_validas(self.por_z.get(z, []),
                                          self.x_min, self.x_max, self.y_pe)
            for z in range(self.z_inicio, self.z_meta + 2)
        }
        self._superficies = {}
        self._validas_na_altura = {}
        self.viaveis = self._calcular_viaveis()
        self.x_partida = self._posicao_de_partida()

    # Alcance de um salto correndo no Minecraft: cerca de 4 blocos de vao com
    # impulso, e 1.25 bloco de subida. Sao os limites que separam "vao que da
    # para saltar" de "vao que mata".
    SALTO_ALCANCE = 4
    SALTO_SUBIDA = 1.25

    def superficies_em(self, z):
        """Alturas onde da para ficar de pe em z, com as faixas de x."""
        if z not in self._superficies:
            self._superficies[z] = geometria.superficies(
                self.por_z.get(z, []), self.x_min, self.x_max)
        return self._superficies[z]

    def _calcular_viaveis(self):
        """De quais posicoes, em cada z, ainda da para chegar ao fim.

        Retropropaga a partir da meta, sobre estados (z, altura, faixa de x) -
        e nao mais so (z, faixa). Um estado e viavel se alguma transicao leva a
        um estado viavel adiante, onde transicao e andar para o z seguinte,
        subir um degrau, ou saltar ate SALTO_ALCANCE blocos a frente subindo no
        maximo SALTO_SUBIDA.

        A versao anterior olhava so o piso do estagio. Nele, 8 dos 67 z do
        Bamboo simplesmente nao tem passagem, e o mesmo vale para todos os
        outros estagios: a analise plana declarava o mapa insoluvel e a
        ferramenta entao recortava apenas os pedacos planos. Era dai que vinham
        os `trechos` do config - o subconjunto do mapa que evita a escalada.
        """
        viaveis = {}
        for altura, faixas in self.superficies_em(self.z_meta):
            viaveis.setdefault(self.z_meta, []).extend(
                (altura, faixa) for faixa in faixas)

        for z in range(self.z_meta - 1, self.z_inicio - 1, -1):
            todos = [(a, f) for a, fs in self.superficies_em(z) for f in fs]
            alcancaveis = [estado for estado in todos
                           if self._leva_adiante(z, estado[0], estado[1], viaveis)]
            viaveis[z] = self._fechar_no_mesmo_z(todos, alcancaveis)
        return viaveis

    def _fechar_no_mesmo_z(self, todos, alcancaveis):
        """Inclui quem chega, andando de lado dentro do mesmo z, a quem ja sai.

        Sem isto o mapa de verdade fica insoluvel. O percurso e cheio de
        lugares onde o caminho e "suba no bloco ao lado, depois siga" - sao os
        pilares que marcam onde pular. Olhando so para frente, o estado de
        onde se sobe parecia um beco sem saida, e a analise condenava o
        estagio inteiro.

        Andar de lado dentro de um mesmo z e livre; o que limita e a altura,
        que segue a mesma regra do salto.
        """
        dentro = list(alcancaveis)
        mudou = True
        while mudou:
            mudou = False
            for altura, faixa in todos:
                if (altura, faixa) in dentro:
                    continue
                for altura_vizinha, faixa_vizinha in dentro:
                    if altura_vizinha - altura > self.SALTO_SUBIDA:
                        continue
                    if geometria.intervalos_se_cruzam([faixa], [faixa_vizinha]):
                        dentro.append((altura, faixa))
                        mudou = True
                        break
        return dentro

    def _leva_adiante(self, z, altura, faixa, viaveis):
        """Diz se de (z, altura, faixa) sai alguma transicao para um estado viavel."""
        for adiante in range(z + 1, min(z + self.SALTO_ALCANCE, self.z_meta) + 1):
            for altura_destino, faixa_destino in viaveis.get(adiante, []):
                subida = altura_destino - altura
                if subida > self.SALTO_SUBIDA:
                    continue
                # Passo simples exige encostar; salto longo nao, mas ainda
                # precisa de alinhamento lateral para o corpo caber na chegada.
                if not geometria.intervalos_se_cruzam([faixa], [faixa_destino]):
                    continue
                if adiante > z + 1 and subida > geometria.ALTURA_DEGRAU:
                    continue        # saltar longe E alto ao mesmo tempo, nao
                # So o salto longo precisa de corredor: o passo para a celula
                # vizinha nao passa por cima de nada.
                if adiante > z + 1 and not self.corredor_do_salto(
                        z, adiante, altura, faixa, faixa_destino):
                    continue
                return True
        return False

    def corredor_do_salto(self, z, adiante, altura, faixa, faixa_destino):
        """Por onde da para saltar de z ate `adiante`, sem bater no meio.

        Devolve as posicoes de centro que servem na decolagem, na aterrissagem
        e em todas as celulas intermediarias. Vazio significa que o salto nao
        existe.

        A pergunta e "existe um x?", e nao "a faixa toda esta limpa?". A
        segunda versao reprovava qualquer salto que passasse perto de um bambu
        e derrubava os 7 estagios; sem checagem nenhuma, a analise mandava
        pular por cima de um muro de 2 blocos em pale_garden2.
        """
        # Interseccao tolerante: duas faixas que so se encostam ainda deixam
        # passar, e e assim que `intervalos_se_cruzam` ja as trata. Usar a
        # interseccao estrita aqui rejeitava metade das transicoes do mapa.
        inicio = max(faixa[0], faixa_destino[0])
        fim = min(faixa[1], faixa_destino[1])
        if fim < inicio:
            return []
        corredor = [(inicio, fim)]
        for meio in range(z + 1, adiante):
            if not corredor:
                return []
            corredor = geometria._subtrair(
                corredor,
                geometria.faixas_altas_demais(self.por_z.get(meio, []),
                                              altura, self.SALTO_SUBIDA))
        return [(inicio, fim) for inicio, fim in corredor if fim > inicio]

    def posicoes_validas_na_altura(self, z, altura):
        """Onde o centro do jogador cabe em z, para quem esta na altura dada.

        A versao de altura fixa (`posicoes_validas_em`) responde sempre pelo
        piso do estagio. Quem esta em cima de um bloco enxerga outra coisa: o
        que era parede vira degrau, e o que era passagem pode ter sumido.
        """
        chave = (z, round(altura * 2) / 2)   # meio bloco basta, e limita o cache
        if chave not in self._validas_na_altura:
            self._validas_na_altura[chave] = geometria.posicoes_validas(
                self.por_z.get(z, []), self.x_min, self.x_max, chave[1])
        return self._validas_na_altura[chave]

    def altura_do_obstaculo_em(self, z, altura, x_inicio, x_fim):
        """Quanto o obstaculo de z sobe acima de `altura`, na faixa dada."""
        return geometria.altura_do_obstaculo(self.por_z.get(z, []), altura,
                                             x_inicio, x_fim)

    def obstaculo_a_frente_na_altura(self, z_corpo, altura, x_inicio, x_fim,
                                     alcance=6):
        """Primeiro z adiante com algo mais alto que um degrau, para quem esta
        em `altura` e ocupa a faixa lateral dada."""
        inicio = int(z_corpo + geometria.LARGURA_JOGADOR / 2) + 1
        for z in range(inicio, min(inicio + alcance, self.z_meta + 1)):
            if self.altura_do_obstaculo_em(z, altura, x_inicio, x_fim) > \
                    geometria.ALTURA_DEGRAU:
                return z
        return None

    def posicoes_validas_em(self, z):
        """Onde o centro do jogador cabe num dado z, sem olhar o que vem depois."""
        if z not in self.validas:
            self.validas[z] = geometria.posicoes_validas(
                self.por_z.get(z, []), self.x_min, self.x_max, self.y_pe)
        return self.validas[z]

    def estados_viaveis(self, z):
        """[(altura, (x_inicio, x_fim))] de onde ainda da para terminar."""
        if z in self.viaveis:
            return self.viaveis[z]
        return [(self.y_pe, faixa) for faixa in self.posicoes_validas_em(z)]

    def nivel_de_partida(self):
        """Altura do apoio viavel mais baixo no inicio do trecho.

        Num percurso 3D o comeco nem sempre e o chao do estagio: em
        pale_garden2 os apoios que levam ao fim estao em y=102 e y=103, e o
        piso em 101 e um beco. Nascer em y_pe punha o bot no beco, ele nao
        tinha acao capaz de sair, e o trecho parecia insoluvel.
        """
        alturas = [altura for altura, _ in self.estados_viaveis(self.z_inicio)]
        return min(alturas) if alturas else float(self.y_pe)

    def posicoes_no_nivel(self, z, altura, tolerancia=geometria.ALTURA_DEGRAU):
        """Faixas viaveis cujo apoio esta no nivel do chao indicado.

        Para nascer nao serve o filtro de alcance de `posicoes_viaveis`: ele
        aceita apoios ate um salto acima, e um x que so e apoio um bloco mais
        alto colocaria o bot dentro da parede.

        A tolerancia e a altura do degrau, e nao zero, porque "o chao" inclui o
        que estiver apoiado nele: com um tapete de 0.0625 em cima do piso, o
        apoio real fica em y_pe+0.0625 e uma comparacao exata nao acha nenhuma
        posicao de nascimento - o trecho inteiro ficava sem partida valida.
        """
        faixas = [faixa for nivel, faixa in self.estados_viaveis(z)
                  if -1e-6 <= nivel - altura <= tolerancia]
        return geometria._unir(faixas)

    def posicoes_viaveis(self, z, altura=None):
        """Faixas de x viaveis em z, opcionalmente so as alcancaveis de `altura`.

        Sem `altura` junta todos os niveis, o que serve para perguntas do tipo
        "este z tem alguma saida?". Com `altura`, filtra pelo que o corpo
        alcanca dali - subir no maximo um salto, descer a vontade.

        O filtro importa: juntar os niveis fazia o agente guloso mirar uma
        passagem que so existe tres blocos acima da cabeca dele, e ele ficava
        empurrando a parede ate o episodio truncar.
        """
        if z not in self.viaveis:
            return self.posicoes_validas_em(z)
        faixas = [faixa for nivel, faixa in self.viaveis[z]
                  if altura is None or nivel - altura <= self.SALTO_SUBIDA]
        return geometria._unir(faixas)

    def tem_solucao(self):
        """Diz se existe caminho andando do inicio ate a meta."""
        return bool(self.posicoes_viaveis(self.z_inicio))

    def _posicao_de_partida(self):
        """Onde o bot nasce: a posicao viavel mais perto do meio do corredor.

        Nem todo trecho comeca com o meio desimpedido, e nem toda posicao
        livre serve. Nascer no beco sem saida de Sand fazia o episodio comecar
        perdido, sem nenhuma acao capaz de consertar.
        """
        centro = (self.x_min + self.x_max) / 2
        # Mesma razao do sorteio em ambiente_sim: nascer no piso, e nao numa
        # faixa que so existe em cima de um bloco.
        opcoes = (self.posicoes_no_nivel(self.z_inicio, self.nivel_de_partida())
                  or self.validas.get(self.z_inicio, []))

        melhor, distancia_melhor = centro, float('inf')
        for inicio, fim in opcoes:
            alvo = min(max(centro, inicio), fim)
            distancia = abs(alvo - centro)
            if distancia < distancia_melhor:
                melhor, distancia_melhor = alvo, distancia
        return melhor

    @classmethod
    def carregar(cls, caminho_mapa, definicao_trecho):
        with open(caminho_mapa, encoding='utf-8') as arquivo:
            mapa = json.load(arquivo)

        if 'inicio' in definicao_trecho or 'fim' in definicao_trecho:
            transformacao = TransformacaoPercurso(
                definicao_trecho.get('inicio'), definicao_trecho.get('fim'))
            metadados = mapa.get('meta', {})
            sistema = metadados.get('coordenadas')
            if sistema != 'locais':
                raise ValueError(
                    f"o trecho '{definicao_trecho.get('nome', '?')}' usa inicio/fim, "
                    f"mas o mapa {caminho_mapa!r} nao foi exportado em "
                    "coordenadas locais. Use tools.mapear_percurso.")
            if (metadados.get('inicio_mundo') != definicao_trecho.get('inicio')
                    or metadados.get('fim_mundo') != definicao_trecho.get('fim')):
                raise ValueError(
                    f"o JSON de '{definicao_trecho.get('nome', '?')}' foi "
                    "exportado com inicio/fim diferentes do cenario. "
                    "Exporte o mapa novamente com tools.mapear_percurso.")
            mundo_esperado = definicao_trecho.get('mundo')
            if mundo_esperado and metadados.get('mundo') != mundo_esperado:
                raise ValueError(
                    f"o trecho espera '{mundo_esperado}', mas o JSON veio de "
                    f"'{metadados.get('mundo')}'")
            z_inicio = 0
            z_meta = int(round(transformacao.comprimento))
            y_pe = definicao_trecho.get(
                'y_pe', definicao_trecho['inicio'].get('y', mapa.get('y_pe')))
            return cls(mapa, z_inicio, z_meta, y_pe,
                       definicao_trecho.get('nome', '?'), transformacao,
                       definicao_trecho.get('mundo') or mapa.get('meta', {}).get('mundo'))

        return cls(mapa,
                   definicao_trecho['z_inicio'],
                   definicao_trecho['z_meta'],
                   definicao_trecho.get('y_pe'),
                   definicao_trecho.get('nome', '?'),
                   mundo=definicao_trecho.get('mundo') or mapa.get('meta', {}).get('mundo'))

    def _tem_obstaculo(self, z):
        """Diz se algum bloco atrapalha na altura do corpo, neste z."""
        for _, y, altura, largura in self.por_z.get(z, []):
            if largura <= 0.0 or altura <= 0.0:
                continue
            if y + altura > self.y_pe + geometria.ALTURA_DEGRAU and \
               y < self.y_pe + 2:
                return True
        return False

    def blocos_na_coluna(self, x_celula, z_celula):
        """Caixas de colisao de uma coluna, de baixo para cima."""
        return self.colunas.get((x_celula, z_celula), ())

    def proximo_obstaculo(self, z):
        """Devolve o primeiro obstaculo em z ou depois dele, ou None."""
        for z_obstaculo in self.z_obstaculos:
            if z_obstaculo >= z:
                return z_obstaculo
        return None

    def obstaculo_a_frente(self, z_corpo):
        """O proximo obstaculo que o corpo ainda vai encontrar.

        Precisa medir pela **frente** do corpo, e nao pela celula onde ele
        esta. Um bot no meio da celula 1177 ja passou pela parede de 1177: o
        que importa dali em diante e a de 1178. Usar a celula atual fazia o
        agente enxergar o obstaculo que ficou para tras e atravessar o slalom
        inteiro em linha reta, ate encostar numa parede.
        """
        frente = z_corpo + geometria.LARGURA_JOGADOR / 2
        return self.proximo_obstaculo(math.ceil(frente - 1e-9))

    def vaos_livres(self, z):
        """Intervalos de x livres num z, ja pre-calculados."""
        if z in self.vaos:
            return self.vaos[z]
        return geometria.vaos_livres(
            self.por_z.get(z, []), self.x_min, self.x_max, self.y_pe)

    def fora_da_ponte(self, x):
        return x < self.x_min or x > self.x_max

    def comprimento(self):
        return self.z_meta - self.z_inicio

    def resumo(self):
        eixo = (f"progresso {self.z_inicio}->{self.z_meta}, "
                f"mundo {self.transformacao.nome_direcao}"
                if not self.transformacao.identidade
                else f"z {self.z_inicio}->{self.z_meta}")
        return (f"trecho {self.nome}: {eixo} ({self.comprimento()} blocos), "
                f"lateral [{self.x_min}, {self.x_max}], y_pe={self.y_pe}, "
                f"{len(self.z_obstaculos)} obstaculos")
