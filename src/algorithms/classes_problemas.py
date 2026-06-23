class Problem:
    def __init__(self, inistate, goal, actions, mapa):
        self.inistate = inistate
        self.actions = actions
        self.goal = goal

        self.mapa = mapa

    def getinitialState(self):
        return self.inistate

    def GoalState(self, state):
        return state == self.goal

    def getSucessors(self, state):
        sucessors = []

        if state in self.mapa:
            for next_state, action, cost in self.mapa[state]:
                tupla_sucessor = (next_state, action, cost)
                sucessors.append(tupla_sucessor)

        return sucessors

    def getCost(self, actions):
        totalCost = 0
        actualState = self.inistate

        for acao in actions:
            acao_valida = False

            for next_state, acao_possivel, step_cost in self.getSucessors(actualState):
                if acao == acao_possivel:
                    totalCost += step_cost
                    actualState = next_state
                    acao_valida = True
                    break

            if not acao_valida:
                raise Exception("Ação Invalida")
                
        return totalCost