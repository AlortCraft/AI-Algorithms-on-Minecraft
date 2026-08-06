from javascript import require, On
import time
import threading



mineflayer = require('mineflayer')

print("🤖 Inicializando o Bot...")


vec3 = require('vec3')

bot = mineflayer.createBot({
    'host': '100.110.191.127',       
    'port': 25565,
    'username': 'LucidioBot',  
    'hideErrors': False        
})


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