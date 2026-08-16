"""Pequeno verificador compartilhado pelos testes do parkour."""


class Verificador:
    def __init__(self, titulo):
        self.titulo = titulo
        self.passaram = 0
        self.falharam = []
        self.secao_atual = ''
        print(f'\n=== testes de {titulo} ===')

    def secao(self, nome):
        self.secao_atual = nome
        print(f'\n  {nome}')

    def verdadeiro(self, condicao, descricao):
        if condicao:
            self.passaram += 1
            print(f'    ok    {descricao}')
        else:
            self.falharam.append(f'{self.secao_atual}: {descricao}')
            print(f'    FALHA {descricao}')

    def perto(self, obtido, esperado, tolerancia, descricao):
        texto = (f'{descricao}: {obtido:.4f} '
                 f'(esperado {esperado:.4f} +- {tolerancia})')
        self.verdadeiro(abs(obtido - esperado) <= tolerancia, texto)

    def encerrar(self):
        total = self.passaram + len(self.falharam)
        print(f'\n=== {self.titulo}: {self.passaram}/{total} passaram ===')
        for falha in self.falharam:
            print(f'    FALHOU: {falha}')
        return 1 if self.falharam else 0
