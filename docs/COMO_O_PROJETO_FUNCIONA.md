# Como o parkour funciona agora

Existe um único fluxo de treinamento:

```text
Minecraft informa posição e velocidade
              ↓
estado.py transforma a situação em uma linha da tabela
              ↓
q_learning.py escolhe um controle
              ↓
ambiente_mc.py executa o controle no jogo
              ↓
recompensa.py pontua avanço, queda, travamento ou chegada
              ↓
q_learning.py atualiza a tabela e repete
```

`main.py` conecta os bots, recebe os comandos e executa as rodadas pedidas em
cada bot. Cada bot possui seu próprio ambiente físico, mas todos usam a mesma
tabela Q. A tabela possui um bloqueio interno para que escolhas, atualizações e
salvamentos simultâneos não se corrompam. `treinar.py` contém o laço de um
episódio; ele não pode treinar sem o Minecraft.

Em cada episódio um bot é teleportado ao início, recebe um estado, escolhe uma
ação com epsilon-greedy, mantém essa ação por alguns ticks e observa o efeito
real. Ao cair, chegar, ficar travado ou atingir o limite de passos, o episódio
termina e a tabela compartilhada é salva. A quantidade informada em
`parkour treinar N` representa N rodadas por bot. Assim, com 10 bots e N igual
a 5, são executados 50 episódios no total em cinco rodadas paralelas.

Nos corredores retos, o estado informa a presença de piso nas quatro células
seguintes e a altura relativa do apoio mais próximo. A meta exige pouso real.
O CSV separa progresso horizontal de progresso validado por contato com o chão
e registra a frequência das ações para permitir diagnosticar políticas ruins.

O estado ainda combina a posição e velocidade reais do bot com um mapa de
blocos exportado previamente. Portanto a física é real, mas a percepção da
forma dos blocos ainda é estática. Isso é especialmente importante para Big
Dripleaf e outros blocos que mudam de estado; veja `PARTES_PARA_IMPLEMENTAR.md`.

Ordem de leitura recomendada:

1. `q_learning.py`;
2. `treinar.py`;
3. `recompensa.py`;
4. `acoes.py`;
5. `ambiente_mc.py`;
6. `estado.py`.
