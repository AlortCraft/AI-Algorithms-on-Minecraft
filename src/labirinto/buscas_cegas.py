from .problema import Problem
from collections import deque
import time

def BFS(problem: Problem):
    estado_inicial = problem.inistate

    if problem.GoalState(estado_inicial):
        return []

    frontier = deque()  
    
    # fronteira recebe o estado inicial e as acoes tomadas para chegar no estado.
    frontier.append((estado_inicial, []))
    
    fronteira_set = {estado_inicial}


    explorados = set()

    while len(frontier) > 0:
        estado_atual, caminho = frontier.popleft()

        fronteira_set.remove(estado_atual)
        explorados.add(estado_atual)

        problem.bot.chat(f"/setblock {estado_atual[0]} {problem.y_fixo-1} {estado_atual[1]} minecraft:red_concrete")
        time.sleep(0.05)

        for prox_estado, acao, cost in problem.getSucessors(estado_atual):
            estado_fronteira = prox_estado in fronteira_set

            if prox_estado not in explorados and not estado_fronteira:
                novo_caminho = caminho + [acao]
                
                if problem.GoalState(prox_estado):
                    problem.bot.chat(f"/setblock {prox_estado[0]} {problem.y_fixo-1} {prox_estado[1]} minecraft:red_concrete")
                    return novo_caminho
                    
                frontier.append((prox_estado, novo_caminho))

                fronteira_set.add(prox_estado)
                
    return None


def DFS(problem: Problem):
    estado_inicial = problem.inistate

    if problem.GoalState(estado_inicial):
        return []

    frontier = deque()  
    # fronteira recebe o estado inicial e as acoes tomadas para chegar no estado.
    frontier.append((estado_inicial, []))
    
    fronteira_set = {estado_inicial}


    explorados = set()

    while len(frontier) > 0:
        estado_atual, caminho = frontier.pop()

        fronteira_set.remove(estado_atual)
        explorados.add(estado_atual)

        problem.bot.chat(f"/setblock {estado_atual[0]} {problem.y_fixo-1} {estado_atual[1]} minecraft:red_concrete")
        time.sleep(0.05)

        for prox_estado, acao, cost in problem.getSucessors(estado_atual):
            estado_fronteira = prox_estado in fronteira_set

            if prox_estado not in explorados and not estado_fronteira:
                novo_caminho = caminho + [acao]
                
                if problem.GoalState(prox_estado):
                    problem.bot.chat(f"/setblock {prox_estado[0]} {problem.y_fixo-1} {prox_estado[1]} minecraft:red_concrete")
                    return novo_caminho
                    
                frontier.append((prox_estado, novo_caminho))

                fronteira_set.add(prox_estado)
                
    return None




def main():
    pass









if __name__ == "__main__":
    main()
