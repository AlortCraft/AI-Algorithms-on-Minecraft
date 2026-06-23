from classes_problemas import Problem
from collections import deque




def BFS(problem: Problem):
    estado_inicial = problem.inistate

    if problem.GoalState(estado_inicial):
        return []

    frontier = deque()
    # fronteira recebe o estado inicial e as acoes tomadas para chegar no estado.
    frontier.append([estado_inicial, []])

    explorados = set()

    while len(frontier) > 0:
        estado_atual, caminho = frontier.popleft()

        explorados.add(estado_atual)

        for prox_estado, acao, custo in problem.getSucessors(estado_atual):
            estado_fronteira = any(estado == prox_estado for estado, _ in frontier)

            if prox_estado not in explorados and not estado_fronteira:
                novo_caminho = caminho + [acao]
                
                if problem.GoalState(prox_estado):
                    return novo_caminho
                    
                frontier.append((prox_estado, novo_caminho))
                
    return None


def DFS(problem: Problem):
    estado_inicial = problem.inistate

    if problem.GoalState(estado_inicial):
        return []

    frontier = deque()
    # fronteira recebe o estado inicial e as acoes tomadas para chegar no estado.
    frontier.append([estado_inicial, []])

    explorados = set()

    while len(frontier) > 0:
        estado_atual, caminho = frontier.pop()

        explorados.add(estado_atual)

        for prox_estado, acao, custo in problem.getSucessors(estado_atual):
            estado_fronteira = any(estado == prox_estado for estado, _ in frontier)

            if prox_estado not in explorados and not estado_fronteira:
                novo_caminho = caminho + [acao]
                
                if problem.GoalState(prox_estado):
                    return novo_caminho
                    
                frontier.append((prox_estado, novo_caminho))
                
    return None




def main():
    
    inistate = "João Pessoa"
    goal = "Maceió"
    actions = ["Viajar"]
    mapa = {
        "João Pessoa": [("Recife", "Pegar BR-101", 120), ("Campina Grande", "Pegar BR-230", 130)],
        "Recife": [("Maceió", "Pegar BR-101", 260)],
        "Campina Grande": [],
        "Maceió": []
    }


    problem = Problem(
        inistate=inistate,
        goal=goal,
        actions=actions,
        mapa=mapa
    )



    print(BFS(problem))
    print(DFS(problem))









if __name__ == "__main__":
    main()