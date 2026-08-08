"""Grava a trajetoria de um jogador humano percorrendo o mapa.

Serve para responder o que a analise offline nao consegue: **por onde passa a
rota de verdade**. A geometria diz quais apoios existem, mas nao qual deles o
mapa espera que voce use, nem que truque vence uma subida que parece alta
demais.

Foi escrito porque travamos exatamente nisso: o portico de z=1067 exige subir
2 blocos a partir do chao, e nem a analise de alcance nem a fisica acham
sequencia que faca isso. Um humano faz. Gravar o humano e mais barato do que
adivinhar.

    python -m src.parkour.gravar_rota --jogador Yosef --segundos 120

Gera resultados/metricas/rota_<jogador>.json com uma amostra por tick, e um
resumo dos apoios usados: para cada z, a altura em que o jogador estava.
"""

import argparse
import json
import os
import time

from javascript import On, require

from . import config as configuracao_modulo


def resumir(amostras):
    """Para cada z inteiro, a menor e a maior altura em que o jogador esteve.

    O interessante e a menor: e o apoio de onde ele saiu, e portanto o que a
    analise de rota deveria ter encontrado.
    """
    por_z = {}
    for a in amostras:
        z = int(a['z'])
        baixo, alto = por_z.get(z, (a['y'], a['y']))
        por_z[z] = (min(baixo, a['y']), max(alto, a['y']))
    return {z: por_z[z] for z in sorted(por_z)}


def main():
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument('--jogador', required=True)
    analisador.add_argument('--segundos', type=int, default=120)
    argumentos = analisador.parse_args()

    dados = configuracao_modulo.carregar_bot()
    mineflayer = require('mineflayer')
    bot = mineflayer.createBot({
        'host': dados['host'],
        'port': dados['porta'],
        'username': 'Observador',
        'hideErrors': dados.get('esconder_erros', False),
    })

    estado = {'pronto': False, 'amostras': []}

    @On(bot, 'spawn')
    def ao_nascer(este):
        if estado['pronto']:
            return
        estado['pronto'] = True
        print(f"observando {argumentos.jogador} por {argumentos.segundos}s...")
        print("percorra o trecho normalmente; nao precisa avisar quando comecar")

        limite = time.time() + argumentos.segundos
        ausente = 0
        tick = 0
        while time.time() < limite:
            bot.waitForTicks(1)
            tick += 1
            # O servidor so manda entidades dentro do alcance de visao. Sem
            # colar no jogador, a gravacao morre depois de uns 60 blocos - e o
            # percurso tem 400.
            if tick % 20 == 0:
                bot.chat(f"/tp Observador {argumentos.jogador}")
            try:
                jogador = bot.players[argumentos.jogador]
                posicao = jogador.entity.position
            except Exception:
                ausente += 1
                if ausente % 100 == 1:
                    print(f"  nao estou vendo {argumentos.jogador}; "
                          f"chegue mais perto do bot")
                continue
            ausente = 0
            estado['amostras'].append({
                'x': round(float(posicao.x), 3),
                'y': round(float(posicao.y), 3),
                'z': round(float(posicao.z), 3),
            })

        resumo = resumir(estado['amostras'])
        destino = os.path.join(configuracao_modulo.RAIZ, 'resultados', 'metricas',
                               f"rota_{argumentos.jogador}.json")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, 'w', encoding='utf-8') as arquivo:
            json.dump({'jogador': argumentos.jogador,
                       'amostras': estado['amostras'],
                       'apoios_por_z': {str(z): resumo[z] for z in resumo}},
                      arquivo, indent=2)

        print(f"\n{len(estado['amostras'])} amostras gravadas")
        print("altura mais baixa em que voce esteve, por z:")
        for z in sorted(resumo):
            baixo, alto = resumo[z]
            print(f"   z={z}  y de {baixo:.2f} a {alto:.2f}")
        print(f"\ndetalhe: {os.path.relpath(destino, configuracao_modulo.RAIZ)}")
        bot.quit()


if __name__ == '__main__':
    main()
