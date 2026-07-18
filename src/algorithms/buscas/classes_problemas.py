from javascript import require, On

vec3 = require('vec3')


class Problem:
    def __init__(self, bot, inistate, goal, y_fixo, actions):
        self.bot = bot
        self.inistate = inistate
        self.goal = goal
        self.y_fixo = y_fixo
        self.actions = actions

    def getinitialState(self):
        return self.inistate

    def GoalState(self, state):
        return state == self.goal
    
    def heuristic(self, state):
        # pela distancia de manhattan
        x, z = state

        x_alvo, z_alvo = self.goal

        distancia = abs(x - x_alvo) + abs(z - z_alvo)
        print(distancia)

        return distancia

    def getSucessors(self, state):
        sucessors = []
        x, z = state

        
        for acao, (dx, dz) in self.actions.items():
            nx = x + dx
            nz = z + dz

            # Instanciando nas 3 alturas do bloco vizinho
            pos_pes = vec3(nx, self.y_fixo, nz)
            pos_cabeca = vec3(nx, self.y_fixo + 1, nz)
            pos_chao = vec3(nx, self.y_fixo - 1, nz)

            # Disparando os sensores do Mineflayer
            bloco_pes = self.bot.blockAt(pos_pes)
            bloco_cabeca = self.bot.blockAt(pos_cabeca)
            bloco_chao = self.bot.blockAt(pos_chao)

            # Verifica se os blocos existem antes de checar
            if bloco_pes and bloco_cabeca and bloco_chao:
                pes_livre = (bloco_pes.name == 'air')
                cabeca_livre = (bloco_cabeca.name == 'air')
                chao_firme = (bloco_chao.name != 'air') 

                # Se o caminho for passável, ele se torna válido
                if pes_livre and cabeca_livre and chao_firme:
                    tupla_sucessor = ((nx, nz), acao, 1)
                    sucessors.append(tupla_sucessor)

        return sucessors