from javascript import require, On
import time
import math
import threading

import sys
from pathlib import Path

pasta_src = str(Path(__file__).resolve().parent.parent)
if pasta_src not in sys.path:
    sys.path.append(pasta_src)

from algorithms.classes_problemas import Problem
from algorithms.buscas_cegas import BFS, DFS
from algorithms.buscas_informadas import dijkstra, A_star



mineflayer = require('mineflayer')

print("🤖 Inicializando o Bot...")


vec3 = require('vec3')

bot = mineflayer.createBot({
    'host': '100.110.191.127',       
    'port': 25565,
    'username': 'Cleitinho',  
    'hideErrors': False        
})


def andar_para(x, z):
    centro_x = x + .5
    centro_z = z + .5
    pos_y = bot.entity.position.y

    alvo = vec3(centro_x, pos_y, centro_z)

    bot.lookAt(alvo)

    bot.setControlState("forward", True)

    movendo = True
    while movendo:
        distancia = bot.entity.position.distanceTo(alvo)

        if distancia <= .5:
            bot.setControlState("forward", False)
            movendo = False

        # impedindo sobrecarga
        time.sleep(0.05)


def resolver_labirinto(inicio, fim, y_sempre, algoritmo):
    actions = {
        "lado1": (1, 0),
        "lado2": (-1, 0),
        "lado3": (0, 1),
        "lado4": (0, -1)
    }

    labirinto = Problem(bot, inicio, fim, y_sempre, actions)

    if algoritmo == "BFS":
        caminho = BFS(labirinto)
    elif algoritmo == "DFS":
        caminho = DFS(labirinto)
    elif algoritmo == "dijkstra":
        caminho = DFS(labirinto)
    elif algoritmo == "A*":
        caminho = A_star(labirinto)


    x_alvo, z_alvo = inicio
    for direcao in caminho:
        if direcao == "lado1":
            x_alvo += 1
        elif direcao == "lado2":
            x_alvo -= 1
        elif direcao == "lado3":
            z_alvo += 1
        elif direcao == "lado4":
            z_alvo -= 1

        andar_para(x_alvo, z_alvo)
        bot.chat(f"/setblock {x_alvo} {y_sempre-1} {z_alvo} minecraft:green_concrete")
        #print(direcao)

    if x_alvo == fim[0] and z_alvo == fim[1]:
        bot.chat("Terminei o labirinto!")
    



@On(bot, 'spawn')
def handle_spawn():
    print(f"[{bot.username}] Conectado e pronto para o experimento!")
    bot.chat("Olá mundo! Pronto para os testes.")


@On(bot, 'messagestr')
def handle_message(message, position, jsonMsg, sender, verification=None):
    """O 'verification=None' torna o parâmetro opcional, evitando o crash."""
    print(f"📡 Chat lido: {message}")
    
    if "teleporte" in message:
        bot.chat(f"/tp {bot.username} TrainedDrop")

    if "teste andar" in message:
        threading.Thread(target=andar_para, args=(-23, 13)).start()

    if "labirinto BFS" in message:
        # Teleportar para posicao inicial
        bot.chat(f"/tp -7 94 25")

        threading.Thread(target=resolver_labirinto, args=((-7, 25), (-6, 67), 94, "BFS")).start()

    if "labirinto DFS" in message:
        # Teleportar para posicao inicial
        bot.chat(f"/tp -7 94 25")

        threading.Thread(target=resolver_labirinto, args=((-7, 25), (-6, 67), 94, "DFS")).start()

    if "labirinto DJ" in message:
        # Teleportar para posicao inicial
        bot.chat(f"/tp -7 94 25")

        threading.Thread(target=resolver_labirinto, args=((-7, 25), (-6, 67), 94, "dijkstra")).start()

    if "labirinto A*" in message:
        # Teleportar para posicao inicial
        bot.chat(f"/tp -7 94 25")

        threading.Thread(target=resolver_labirinto, args=((-7, 25), (-6, 67), 94, "A*")).start()


        