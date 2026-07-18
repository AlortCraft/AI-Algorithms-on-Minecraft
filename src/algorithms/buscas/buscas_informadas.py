from .classes_problemas import Problem
import heapq
import time

def dijkstra(problem: Problem):
    estado_inicial = problem.inistate

    if problem.GoalState(estado_inicial): 
        return []
    

    frontier = []

    heapq.heappush(frontier, estado_inicial)

    explorados = set()

    while len(frontier) > 0:
        custo_atual, estado_atual, caminho = heapq.heappop(frontier)

        if estado_atual in explorados:
            continue

        explorados.add(estado_atual)

        problem.bot.chat(f"/setblock {estado_atual[0]} {problem.y_fixo-1} {estado_atual[1]} minecraft:red_concrete")
        time.sleep(0.05)

        for prox_estado, acao, cost in problem.getSucessors(estado_atual):
            if prox_estado not in explorados:
                novo_caminho = caminho + [acao]
                novo_custo_acumulado = custo_atual + cost
                
                if problem.GoalState(prox_estado):
                    problem.bot.chat(f"/setblock {prox_estado[0]} {problem.y_fixo-1} {prox_estado[1]} minecraft:red_concrete")
                    return novo_caminho
                    
                heapq.heapush(frontier, (novo_custo_acumulado, prox_estado, novo_caminho))
                
    return None


def A_star(problem: Problem):
    estado_inicial = problem.inistate

    if problem.GoalState(estado_inicial): 
        return []
    

    frontier = []

    g_inicial = 0
    h_inicial = problem.heuristic(estado_inicial)
    f_inicial = g_inicial + h_inicial

    heapq.heappush(frontier, (f_inicial, g_inicial, estado_inicial, []))

    explorados = set()

    while len(frontier) > 0:
        f_atual, g_atual, estado_atual, caminho = heapq.heappop(frontier)

        if estado_atual in explorados:
            continue

        explorados.add(estado_atual)

        problem.bot.chat(f"/setblock {estado_atual[0]} {problem.y_fixo-1} {estado_atual[1]} minecraft:red_concrete")
        time.sleep(0.05)

        for prox_estado, acao, cost in problem.getSucessors(estado_atual):
            if prox_estado not in explorados:
                novo_caminho = caminho + [acao]

                novo_g = g_atual + cost

                novo_f = novo_g + problem.heuristic(prox_estado)
                
                if problem.GoalState(prox_estado):
                    problem.bot.chat(f"/setblock {prox_estado[0]} {problem.y_fixo-1} {prox_estado[1]} minecraft:red_concrete")
                    return novo_caminho
                    
                heapq.heappush(frontier, (novo_f, novo_g, prox_estado, novo_caminho))
                
    return None