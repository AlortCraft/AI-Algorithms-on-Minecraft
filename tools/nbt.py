"""Leitor de NBT e de arquivos de regiao (.mca) do Minecraft.

Usa somente a biblioteca padrao do Python. Serve para ler o mapa direto dos
arquivos do servidor, sem precisar do Minecraft rodando.

O formato NBT e uma arvore de tags binarias. Cada tag comeca com um byte que
diz o tipo, seguido do nome e do conteudo. A tabela TIPOS abaixo lista todos.
"""

import gzip
import io
import os
import struct
import zlib

# Identificadores de tipo do formato NBT.
TAG_FIM = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LISTA = 9
TAG_COMPOSTO = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


def _ler_conteudo(fluxo, tipo):
    """Le o conteudo de uma tag ja sabendo o tipo dela."""
    if tipo == TAG_BYTE:
        return struct.unpack('>b', fluxo.read(1))[0]
    if tipo == TAG_SHORT:
        return struct.unpack('>h', fluxo.read(2))[0]
    if tipo == TAG_INT:
        return struct.unpack('>i', fluxo.read(4))[0]
    if tipo == TAG_LONG:
        return struct.unpack('>q', fluxo.read(8))[0]
    if tipo == TAG_FLOAT:
        return struct.unpack('>f', fluxo.read(4))[0]
    if tipo == TAG_DOUBLE:
        return struct.unpack('>d', fluxo.read(8))[0]
    if tipo == TAG_BYTE_ARRAY:
        tamanho = struct.unpack('>i', fluxo.read(4))[0]
        return list(fluxo.read(tamanho))
    if tipo == TAG_STRING:
        tamanho = struct.unpack('>H', fluxo.read(2))[0]
        return fluxo.read(tamanho).decode('utf-8', 'replace')
    if tipo == TAG_LISTA:
        tipo_itens = fluxo.read(1)[0]
        quantidade = struct.unpack('>i', fluxo.read(4))[0]
        return [_ler_conteudo(fluxo, tipo_itens) for _ in range(quantidade)]
    if tipo == TAG_COMPOSTO:
        composto = {}
        while True:
            tipo_filho = fluxo.read(1)[0]
            if tipo_filho == TAG_FIM:
                return composto
            tamanho = struct.unpack('>H', fluxo.read(2))[0]
            nome = fluxo.read(tamanho).decode('utf-8', 'replace')
            composto[nome] = _ler_conteudo(fluxo, tipo_filho)
    if tipo == TAG_INT_ARRAY:
        quantidade = struct.unpack('>i', fluxo.read(4))[0]
        return list(struct.unpack(f'>{quantidade}i', fluxo.read(4 * quantidade)))
    if tipo == TAG_LONG_ARRAY:
        quantidade = struct.unpack('>i', fluxo.read(4))[0]
        return list(struct.unpack(f'>{quantidade}q', fluxo.read(8 * quantidade)))
    raise ValueError(f"tipo de tag NBT desconhecido: {tipo}")


def ler_nbt(dados):
    """Le uma estrutura NBT completa a partir de bytes."""
    fluxo = io.BytesIO(dados)
    tipo = fluxo.read(1)[0]
    if tipo == TAG_FIM:
        return {}
    # A tag raiz tem um nome que nao interessa para nos; so precisamos pular.
    tamanho = struct.unpack('>H', fluxo.read(2))[0]
    fluxo.read(tamanho)
    return _ler_conteudo(fluxo, tipo)


def ler_nbt_arquivo(caminho):
    """Le um arquivo NBT comprimido com gzip, como level.dat ou playerdata."""
    with gzip.open(caminho, 'rb') as arquivo:
        return ler_nbt(arquivo.read())


class Mundo:
    """Acesso somente-leitura aos chunks de um mundo salvo em disco.

    Um mundo e dividido em regioes de 32x32 chunks, cada uma num arquivo .mca.
    Cada chunk tem 16x16 blocos na horizontal e e dividido verticalmente em
    secoes de 16 blocos de altura.
    """

    def __init__(self, pasta_mundo):
        self.pasta_mundo = pasta_mundo
        self.pasta_regioes = os.path.join(pasta_mundo, 'region')
        if not os.path.isdir(self.pasta_regioes):
            raise FileNotFoundError(f"pasta de regioes nao encontrada: {self.pasta_regioes}")
        self._regioes = {}
        self._chunks = {}

    def _regiao(self, rx, rz):
        if (rx, rz) not in self._regioes:
            caminho = os.path.join(self.pasta_regioes, f'r.{rx}.{rz}.mca')
            if os.path.exists(caminho):
                with open(caminho, 'rb') as arquivo:
                    self._regioes[(rx, rz)] = arquivo.read()
            else:
                self._regioes[(rx, rz)] = None
        return self._regioes[(rx, rz)]

    def chunk(self, cx, cz):
        """Devolve o NBT de um chunk, ou None se ele nunca foi gerado."""
        if (cx, cz) in self._chunks:
            return self._chunks[(cx, cz)]

        dados = self._regiao(cx >> 5, cz >> 5)
        chunk = None
        if dados is not None:
            # O cabecalho da regiao tem 1024 entradas de 4 bytes: 3 de
            # deslocamento (em setores de 4 KiB) e 1 de tamanho.
            indice = ((cx & 31) + (cz & 31) * 32) * 4
            deslocamento = int.from_bytes(dados[indice:indice + 3], 'big')
            if deslocamento != 0:
                setores = dados[indice + 3]
                bruto = dados[deslocamento * 4096: deslocamento * 4096 + setores * 4096]
                tamanho = int.from_bytes(bruto[0:4], 'big')
                compressao = bruto[4]
                conteudo = bruto[5:5 + tamanho - 1]
                if compressao == 1:
                    conteudo = gzip.decompress(conteudo)
                elif compressao == 2:
                    conteudo = zlib.decompress(conteudo)
                chunk = ler_nbt(conteudo)

        self._chunks[(cx, cz)] = chunk
        return chunk

    def blocos_do_chunk(self, cx, cz, y_min=None, y_max=None):
        """Devolve {(x, y, z): nome_do_bloco} de um chunk, ignorando o ar."""
        chunk = self.chunk(cx, cz)
        if chunk is None:
            return {}

        blocos = {}
        for secao in chunk.get('sections', []):
            base_y = secao['Y'] * 16
            if y_max is not None and base_y > y_max:
                continue
            if y_min is not None and base_y + 15 < y_min:
                continue

            estados = secao.get('block_states', {})
            paleta = [entrada['Name'] for entrada in estados.get('palette', [])]
            if not paleta:
                continue

            dados = estados.get('data')
            if dados is None:
                # Secao inteira feita de um unico bloco.
                if paleta[0] == 'minecraft:air':
                    continue
                for y in range(base_y, base_y + 16):
                    if y_min is not None and y < y_min:
                        continue
                    if y_max is not None and y > y_max:
                        continue
                    for z in range(16):
                        for x in range(16):
                            blocos[(cx * 16 + x, y, cz * 16 + z)] = paleta[0]
                continue

            # Os indices da paleta ficam empacotados dentro de inteiros de 64
            # bits. Desde a versao 1.16 um indice nunca cruza a fronteira entre
            # dois inteiros, entao os bits que sobram no fim de cada um sao lixo.
            bits = max(4, (len(paleta) - 1).bit_length())
            por_inteiro = 64 // bits
            mascara = (1 << bits) - 1
            indices = []
            for inteiro in dados:
                sem_sinal = inteiro & 0xFFFFFFFFFFFFFFFF
                for posicao in range(por_inteiro):
                    indices.append((sem_sinal >> (posicao * bits)) & mascara)

            for i, indice in enumerate(indices[:4096]):
                nome = paleta[indice]
                if nome == 'minecraft:air':
                    continue
                # A ordem dentro da secao e y, depois z, depois x.
                y = base_y + i // 256
                if y_min is not None and y < y_min:
                    continue
                if y_max is not None and y > y_max:
                    continue
                blocos[(cx * 16 + i % 16, y, cz * 16 + (i % 256) // 16)] = nome

        return blocos

    def blocos_na_caixa(self, x_min, x_max, y_min, y_max, z_min, z_max):
        """Devolve {(x, y, z): nome} de todos os blocos solidos numa caixa."""
        blocos = {}
        for cx in range(x_min // 16, x_max // 16 + 1):
            for cz in range(z_min // 16, z_max // 16 + 1):
                for posicao, nome in self.blocos_do_chunk(cx, cz, y_min, y_max).items():
                    x, y, z = posicao
                    if x_min <= x <= x_max and z_min <= z <= z_max:
                        blocos[posicao] = nome
        return blocos

    def entidades_de_bloco(self, x_min, x_max, z_min, z_max):
        """Devolve as entidades de bloco (placas, command blocks) numa area."""
        encontradas = []
        for cx in range(x_min // 16, x_max // 16 + 1):
            for cz in range(z_min // 16, z_max // 16 + 1):
                chunk = self.chunk(cx, cz)
                if chunk is None:
                    continue
                for entidade in chunk.get('block_entities', []):
                    if x_min <= entidade.get('x', 0) <= x_max and z_min <= entidade.get('z', 0) <= z_max:
                        encontradas.append(entidade)
        return encontradas
