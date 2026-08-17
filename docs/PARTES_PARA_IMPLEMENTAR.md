# O que ainda falta validar ou implementar

## Para a primeira execução

1. Instalar Python, Node.js e as dependências do README.
2. Criar `config/bot.json` a partir do exemplo.
3. Selecionar o mundo correto e iniciar o servidor PaperMC.
4. Dar OP ao primeiro bot para permitir o teleporte de todos os atores.
5. Confirmar manualmente que `parkour reset` posiciona todos no início.
6. Treinar primeiro `labirinto_parkours/frente_1` e testar com `parkour rodar`.

O código Python está pronto para esse fluxo, mas a conexão completa não pode
ser comprovada sem o servidor aberto e o mundo carregado.

## Limitações técnicas atuais

### Percepção de blocos dinâmicos

A posição e a velocidade vêm ao vivo do Minecraft, porém `estado.py` consulta
um mapa de blocos exportado. Ele reconhece a geometria exportada de blocos,
cercas e plantas, mas não acompanha uma Big Dripleaf inclinando durante o
episódio. Para isso, o próximo passo é consultar `bot.blockAt(...)` perto do bot
e incluir o estado/propriedades atuais desses blocos na observação.

### Reset do cenário

O reset teleporta o bot, mas não restaura blocos alterados. Para treinos com
Big Dripleaf ou mecanismos, é necessário restaurar uma região com `/clone`,
usar um comando/plugin próprio ou esperar de forma confiável o bloco voltar ao
estado inicial antes do próximo episódio.

### Avaliação confiável

`parkour rodar` faz uma tentativa com exploração zero. Para uma medição
repetida, `parkour avaliar N` distribui N tentativas entre os bots conectados,
mantém a exploração em zero, não atualiza a tabela Q e registra cada episódio
no CSV com a fase `avaliacao`. O resumo final informa taxa de chegada e média
de passos. Para comparar parâmetros, use um arquivo de modelo diferente para
cada combinação e execute a mesma quantidade de avaliações.

### Velocidade e quantidade de bots

O código distribui episódios entre vários bots e informa episódios por minuto.
Comece com quatro e aumente enquanto o Paper mantiver 20 TPS e o ritmo total
continuar crescendo. Todos podem dividir uma pista estática porque entram numa
equipe sem colisão. Blocos dinâmicos ainda exigem pistas independentes.

O Q-Learning tabular usa pouca CPU e não se beneficia de GPU. Não aumente a
taxa de ticks para acelerar: isso pode mudar a dinâmica dos saltos e ensinar
uma política incompatível com 20 TPS.

### Segurança de compatibilidade

O modelo salvo verifica quantidade de estados e ações. Ele também aceita a
expansão controlada do conjunto permitido quando as colunas já existem no
catálogo: preserva um backup, mantém os valores anteriores e reativa a
exploração. Uma reordenação do catálogo não é migrada: ela incrementa
`VERSAO_CATALOGO` e usa um novo nome de modelo. Ainda não guarda uma assinatura
completa com cenário, trecho e parâmetros do estado. Use um arquivo de modelo
diferente para cada combinação e não reordene `acoes.CATALOGO` sem também
incrementar sua versão. Mudanças no significado do estado incrementam
`VERSAO_ESTADO` e também criam um caminho de modelo novo.

### Teste integrado

Os testes locais cobrem a equação de Bellman, salvamento, recompensa, laço de
episódio e CSV. Ainda falta um teste automatizado que abra o PaperMC e confirme
conexão, teleporte, controles, detecção dos blocos e recuperação após queda.
