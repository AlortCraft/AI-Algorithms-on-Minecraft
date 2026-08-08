"""Roda todos os testes de uma vez:

    python -m testes

Nao precisa de Minecraft, nem de nenhuma biblioteca instalada.
"""

import sys

from testes import teste_ambiente, teste_fisica


def main():
    codigo = 0
    for modulo in (teste_fisica, teste_ambiente):
        codigo |= modulo.main()

    print()
    if codigo:
        print("HOUVE FALHAS. Veja acima qual verificacao quebrou.")
    else:
        print("Tudo passou.")
    return codigo


if __name__ == '__main__':
    sys.exit(main())
