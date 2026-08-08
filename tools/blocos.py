"""Caixas de colisao dos blocos do Minecraft.

Cada bloco ocupa uma caixa dentro da sua celula de 1x1x1. Modelamos essa caixa
com dois numeros:

    altura   quanto ocupa na vertical, a partir da base da celula
    largura  fracao ocupada na horizontal, centrada na celula

Exemplos:

    grama alta      altura 0.00                nao colide
    laje de baixo   altura 0.50  largura 1.00  meio bloco
    bloco cheio     altura 1.00  largura 1.00
    cerca           altura 1.50  largura 1.00  nao da para pular por cima
    bambu           altura 1.00  largura 0.19  uma haste fina no meio da celula

A largura importa mais do que parece. O jogador tem 0.6 de largura e o bambu
so ocupa 0.19 no centro da celula, entao **da para passar entre dois bambus de
celulas vizinhas**: a folga entre eles e 0.81. Sem modelar isso, trechos
inteiros do estagio Bamboo pareceriam intransponiveis, e nao sao.

A lista A_VALIDAR reune os blocos cuja caixa aqui e um palpite documentado e
precisa ser confirmada dentro do jogo. Ver docs/sim_para_real.md.
"""

LARGURA_CHEIA = 1.0

# Blocos que nao colidem de jeito nenhum.
ATRAVESSAVEL = {
    'air', 'cave_air', 'void_air', 'light', 'structure_void',
    'short_grass', 'tall_grass', 'short_dry_grass', 'tall_dry_grass',
    'fern', 'large_fern', 'dead_bush', 'seagrass', 'tall_seagrass', 'kelp',
    'vine', 'glow_lichen', 'hanging_roots', 'string', 'tripwire',
    'redstone_wire', 'rail', 'powered_rail', 'detector_rail', 'activator_rail',
    'torch', 'wall_torch', 'soul_torch', 'soul_wall_torch', 'redstone_torch',
    'water', 'flowing_water', 'lava', 'flowing_lava',
    'firefly_bush', 'closed_eyeblossom', 'open_eyeblossom', 'torchflower',
    'red_mushroom', 'brown_mushroom', 'sugar_cane', 'sweet_berry_bush',
    'nether_sprouts', 'crimson_roots', 'warped_roots', 'twisting_vines',
    'weeping_vines', 'nether_wart',
    'ladder',  # escalavel, mas sem colisao horizontal
}

# Sufixos que indicam familias inteiras sem colisao.
SUFIXOS_ATRAVESSAVEIS = (
    '_sign', '_pressure_plate', '_button', '_banner', '_sapling',
    '_petals', '_carpet', '_candle', '_rail', '_torch', '_vines',
)

# (altura, largura) para blocos individuais.
CAIXA_ESPECIAL = {
    'bamboo': (1.0, 0.1875),          # haste fina: da para passar ao lado
    'snow': (0.125, 1.0),
    'moss_carpet': (0.0625, 1.0),
    'pale_moss_carpet': (0.0625, 1.0),
    'lily_pad': (0.0625, 1.0),
    'big_dripleaf': (0.0625, 1.0),    # a folha inclina e derruba quem pisa
    'big_dripleaf_stem': (0.0, 0.0),
    'cactus': (1.0, 0.875),
    'lantern': (1.0, 0.375),
    'soul_lantern': (1.0, 0.375),
    'chain': (1.0, 0.1875),
    'end_rod': (1.0, 0.25),
    'cake': (0.5, 0.875),
    'conduit': (1.0, 0.5),
    'lightning_rod': (1.0, 0.25),
}

# Sufixos com caixa propria. A ordem importa: o primeiro que casar vence.
SUFIXOS_COM_CAIXA = (
    ('_slab', (0.5, 1.0)),
    ('_fence_gate', (1.5, 1.0)),
    ('_fence', (1.5, 1.0)),      # cercas se conectam e viram uma barreira
    ('_wall', (1.5, 1.0)),
    ('_trapdoor', (0.1875, 1.0)),  # fechado, deitado no chao
    ('_door', (1.0, 0.1875)),
    ('_bars', (1.0, 1.0)),       # barras se conectam e viram uma barreira
    ('_pane', (1.0, 1.0)),
    ('_stairs', (1.0, 1.0)),     # simplificacao: degrau tratado como bloco cheio
    ('_bed', (0.5625, 1.0)),
    ('_layer', (0.125, 1.0)),
    ('_pot', (0.375, 0.75)),
)

# Blocos cuja caixa acima e um palpite documentado, nao um fato verificado.
A_VALIDAR = {
    'bamboo': 'haste fina de 3/16; e o que torna o estagio Bamboo transponivel',
    'big_dripleaf': 'a folha inclina e derruba; o simulador nao modela isso',
    'big_dripleaf_stem': 'caule sem colisao, mas apoia quando a folha esta acima',
    'ladder': 'escalavel; o simulador nao modela escalada',
    'slime_block': 'quica; o simulador trata como bloco cheio comum',
    'cactus': 'causa dano ao encostar; o simulador so trata a colisao',
    'bamboo_trapdoor': 'alcapao aberto ou fechado muda a colisao',
    'honey_block': 'gruda e reduz a velocidade',
    'cobweb': 'reduz muito a velocidade',
    'powder_snow': 'afunda',
}


def _nome_curto(nome):
    return nome.split(':')[-1]


def caixa_colisao(nome):
    """Devolve (altura, largura) da caixa de colisao de um bloco."""
    curto = _nome_curto(nome)

    if curto in CAIXA_ESPECIAL:
        return CAIXA_ESPECIAL[curto]
    if curto in ATRAVESSAVEL:
        return (0.0, 0.0)
    if curto.endswith(SUFIXOS_ATRAVESSAVEIS):
        return (0.0, 0.0)
    for sufixo, caixa in SUFIXOS_COM_CAIXA:
        if curto.endswith(sufixo):
            return caixa
    return (1.0, LARGURA_CHEIA)


def altura_colisao(nome):
    return caixa_colisao(nome)[0]


def solido(nome):
    """Diz se o bloco atrapalha o movimento de alguma forma."""
    return caixa_colisao(nome)[0] > 0.0


def precisa_validar(nome):
    """Diz se a caixa deste bloco ainda e um palpite."""
    return _nome_curto(nome) in A_VALIDAR


def motivo_validacao(nome):
    return A_VALIDAR.get(_nome_curto(nome))
