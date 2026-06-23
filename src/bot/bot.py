from javascript import require, On
import time

mineflayer = require('mineflayer')

print("🤖 Inicializando o Bot com rastreamento de vetor... Aguarde.")

bot = mineflayer.createBot({
    'host': '127.0.0.1',       
    'port': 62837,             # Certifique-se de usar a porta correta do seu mapa
    'username': 'Python_Bot',  
    'hideErrors': False        
})

# Variável global para armazenar a entidade (o corpo) do player que queremos seguir
player_alvo = None

@On(bot, 'spawn')
def handle_spawn(*args):
    print(f"✅ {bot.username} pronto para rastrear!")

# --- 1. ESCUTANDO O CHAT PARA ATIVAR O RASTREAMENTO ---
@On(bot, 'messagestr')
def handle_message(message, position, *args):
    global player_alvo
    texto_chat = str(message).lower()
    
    if bot.username.lower() in texto_chat:
        return

    if "venha" in texto_chat or "ande para mim" in texto_chat:
        bot.chat("Buscando sua assinatura de posicao...")
        
        # Varre todas as entidades (mobs, players, itens) que o bot consegue ver
        for entity_id in bot.entities:
            entity = bot.entities[entity_id]
            
            # Se for um jogador e nao for o próprio bot, encontramos o mestre!
            if entity.type == 'player' and entity.username != bot.username:
                player_alvo = entity
                bot.chat(f"Alvo encontrado: {entity.username}. Iniciando aproximacao!")
                return
        
        # Se saiu do loop e nao encontrou nada
        bot.chat("Nao consegui te avistar. Chegue mais perto de mim!")

    elif "pare" in texto_chat:
        bot.chat("Parando rastreamento.")
        player_alvo = None
        bot.setControlState('forward', False)


# --- 2. A MALHA DE CONTROLE (Executa 20 vezes por segundo) ---
@On(bot, 'physicsTick')
def handle_tick(*args):
    global player_alvo
    
    # Se nao tiver nenhum jogador como alvo, nao faz nada
    if player_alvo is None:
        return

    # Posição atual do bot e do jogador (Vetores 3D)
    pos_bot = bot.entity.position
    pos_alvo = player_alvo.position

    # Calcula a Distancia Euclidiana 3D entre o bot e você
    # O Mineflayer ja tem a funcao .distanceTo() nativa nos vetores
    distancia = pos_bot.distanceTo(pos_alvo)

    # Margem de seguranca: Se estiver a mais de 2 blocos de distancia, continue andando
    if distancia > 2.2:
        # 1. Faz o bot girar a "cabeca" e o corpo exatamente na direcao do jogador
        bot.lookAt(pos_alvo)
        
        # 2. Ativa o W para andar para frente
        bot.setControlState('forward', True)
    else:
        # Se chegou a menos de 2 blocos, para de andar para nao empurrar o player
        bot.setControlState('forward', False)
        bot.chat("Cheguei ao destino!")
        player_alvo = None # Desliga o rastreamento ate o proximo comando