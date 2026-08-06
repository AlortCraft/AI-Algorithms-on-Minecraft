# AI Algorithms on Minecraft

Projeto acadêmico de Introdução à Inteligência Artificial que utiliza um bot no
Minecraft Java Edition. A comunicação com o jogo é feita com Mineflayer, por
meio de Python, e o servidor utiliza PaperMC.

O repositório contém dois ambientes:

- `world_labirinto`: mapa usado nos experimentos com BFS, DFS e A*.
- `world_parkour`: mapa que será usado no agente de parkour com Aprendizado por
  Reforço ou Redes Neurais.

O mapa selecionado por padrão é o de parkour.

## Estrutura principal

```text
.
|-- Servidor-BOT/
|   |-- paper-1.21.11-132.jar
|   |-- server.properties
|   |-- world_labirinto/
|   |-- world_labirinto_nether/
|   |-- world_labirinto_the_end/
|   |-- world_parkour/
|   |-- world_parkour_nether/
|   `-- world_parkour_the_end/
|-- src/
|   `-- labirinto/
|       |-- main.py
|       |-- problema.py
|       |-- buscas_cegas.py
|       `-- buscas_informadas.py
`-- requirements.txt
```

## Requisitos

- Minecraft Java Edition 1.21.11.
- Java 21 ou mais recente para executar o PaperMC.
- Python 3.11 ou mais recente.
- Git.
- Pelo menos 2 GB de memória disponíveis para o servidor.

O pacote Python `javascript` instala e utiliza a ponte necessária para acessar
os módulos JavaScript `mineflayer` e `vec3`. Na primeira execução, essa etapa
pode demorar um pouco e pode precisar de acesso à internet.

## 1. Clonar o projeto

```bash
git clone https://github.com/AlortCraft/AI-Algorithms-on-Minecraft.git
cd AI-Algorithms-on-Minecraft
```

## 2. Preparar o Python

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se o Windows disponibilizar o Python pelo comando `py`, ele pode ser usado no
lugar de `python`.

### Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 3. Escolher o mapa

Com o servidor completamente desligado, abra
`Servidor-BOT/server.properties` e altere somente `level-name`.

Para utilizar o parkour:

```properties
level-name=world_parkour
```

Para utilizar o labirinto:

```properties
level-name=world_labirinto
```

Não é necessário mover, renomear ou excluir nenhuma pasta. O PaperMC associa
automaticamente as dimensões auxiliares pelos nomes
`<level-name>_nether` e `<level-name>_the_end`.

Nunca troque `level-name` enquanto o servidor estiver em execução.

## 4. Iniciar o servidor PaperMC

Entre na pasta do servidor:

```bash
cd Servidor-BOT
```

No Linux, pode-se usar o script incluído:

```bash
chmod +x INICIAR_SERVIDOR.sh
./INICIAR_SERVIDOR.sh
```

O script entra automaticamente na pasta `Servidor-BOT`, portanto também pode
ser chamado diretamente da raiz do repositório:

```bash
chmod +x Servidor-BOT/INICIAR_SERVIDOR.sh
./Servidor-BOT/INICIAR_SERVIDOR.sh
```

No Windows 11, execute no PowerShell do VS Code:

```powershell
.\INICIAR_SERVIDOR.bat
```

Também é possível iniciar diretamente pela tarefa configurada no VS Code:

1. Abra a pasta raiz do projeto no VS Code.
2. Pressione `Ctrl+Shift+P`.
3. Procure por `Tasks: Run Task` ou `Tarefas: Executar Tarefa`.
4. Selecione `Iniciar servidor PaperMC`.

O terminal dessa tarefa funciona como o console do Minecraft. Não o feche
enquanto o servidor estiver em uso; para encerrar, digite `stop` e pressione
Enter.

Em qualquer sistema com Java disponível:

```bash
java -Xmx2G -Xms2G -jar paper-1.21.11-132.jar nogui
```

Espere a mensagem `Done` aparecer no console. Para encerrar corretamente,
digite `stop` no console do servidor. Fechar o terminal à força pode corromper
o mundo.

Configurações importantes que já estão habilitadas:

- `allow-flight=true`, para evitar expulsões durante os saltos.
- `enable-command-block=true`, para permitir checkpoints do mapa.
- `level-name=world_parkour`, que seleciona o mapa padrão.

### Primeiro acesso: conceder permissão de administrador

Na primeira vez que cada pessoa entrar no servidor, ela deve ser adicionada
como administradora pelo terminal do PaperMC. Espere o servidor mostrar `Done`,
entre no Minecraft e digite no terminal do servidor, sem a barra `/`:

```text
op NOME_DO_JOGADOR
```

O mesmo deve ser feito para o bot. Use exatamente o nome definido em
`username` no código. Com a configuração de exemplo deste projeto:

```text
op Cleitinho
```

O jogador e o bot precisam aparecer como operadores para que comandos como
`/tp` e `/setblock` funcionem. Esse procedimento normalmente é necessário
somente no primeiro acesso de cada nome; o PaperMC registra os operadores em
`Servidor-BOT/ops.json`.

## 5. Configurar a conexão do bot

Abra `src/labirinto/main.py` e localize a criação do bot:

```python
bot = mineflayer.createBot({
    'host': '100.110.191.127',
    'port': 25565,
    'username': 'Cleitinho',
    'hideErrors': False
})
```

Altere:

- `host`: use `localhost` quando bot e servidor estiverem no mesmo computador;
  caso contrário, use o IP privado do computador do servidor.
- `port`: deve ser igual a `server-port` em `server.properties`.
- `username`: nome que aparecerá para o bot no servidor.

O endereço salvo no código pertence ao ambiente original do projeto e pode não
funcionar nos computadores dos demais integrantes.

## 6. Executar o bot

Volte para a raiz do projeto, mantenha o ambiente virtual ativado e execute:

```bash
python -m src.labirinto.main
```

No Linux ou macOS, use `python3` caso o comando `python` não esteja disponível.

Quando a conexão funcionar, o console exibirá que o bot está pronto e o bot
enviará uma mensagem no chat do Minecraft.

## Comandos disponíveis no mapa de labirinto

Com `world_labirinto` selecionado, envie uma destas mensagens no chat:

| Mensagem | Comportamento |
| --- | --- |
| `teste andar` | Testa o deslocamento até uma coordenada fixa. |
| `labirinto BFS` | Executa a busca em largura. |
| `labirinto DFS` | Executa a busca em profundidade. |
| `labirinto A*` | Executa a busca A*. |
| `labirinto DJ` | Aciona a opção reservada para Dijkstra. |
| `teleporte` | Teleporta o bot até o jogador configurado no código. |

Os algoritmos pintam de vermelho os blocos explorados e de verde o caminho
final. Por isso, o usuário do bot precisa ter permissão para executar
`/setblock` e `/tp`. Caso o nome do jogador ou do bot tenha sido alterado,
conceda novamente a permissão pelo console do servidor:

```text
op NOME_DO_JOGADOR
op NOME_DO_BOT
```

## Estado atual e limitações conhecidas

- BFS, DFS e A* pertencem ao experimento anterior do labirinto.
- A opção `labirinto DJ` ainda direciona a execução para DFS em `main.py`; a
  implementação de Dijkstra também precisa ser corrigida antes de ser usada.
- O código do labirinto assume altura fixa e movimento nos eixos X e Z. Ele não
  controla saltos de parkour.
- O agente de parkour com Aprendizado por Reforço ainda será implementado.
- As coordenadas do labirinto e alguns nomes de jogador estão fixos no código.

## Fluxo recomendado para o grupo

1. Atualize o repositório antes de começar: `git pull`.
2. Crie uma branch para sua tarefa.
3. Não execute dois servidores usando a porta `25565` ao mesmo tempo.
4. Encerre o PaperMC com `stop` antes de trocar de mapa ou copiar mundos.
5. Não envie `.venv`, `__pycache__` nem a pasta local `Servidor-BOT/backups`.
6. Registre nos experimentos o mapa, algoritmo, recompensa, hiperparâmetros e
   número de episódios utilizados.

## Solução de problemas

### O bot não conecta

- Confirme que o PaperMC chegou à mensagem `Done`.
- Verifique `host` e `port` em `src/labirinto/main.py`.
- Confira se firewall ou rede privada estão bloqueando a porta `25565`.
- Se o servidor estiver em outro computador, `localhost` não funcionará.

### O mapa errado foi carregado

- Pare o servidor com `stop`.
- Confira `level-name` em `Servidor-BOT/server.properties`.
- Confirme que não foi criada acidentalmente uma pasta como
  `world_parkour/world_parkour/level.dat`.

### Os checkpoints não funcionam

- Confirme `enable-command-block=true` em `server.properties`.
- Verifique se o mapa foi iniciado sem erros no console.
- Confira se algum comando exige permissões adicionais.

### Windows mostra `Failed to extract jar files` ou `AccessDeniedException`

Esse erro normalmente indica que o Java ou o OneDrive bloqueou temporariamente
um arquivo gerado pelo PaperMC.

1. Confirme que não existe outro servidor Java aberto.
2. Feche o terminal antigo do servidor.
3. Pause temporariamente a sincronização do OneDrive.
4. Exclua apenas `Servidor-BOT/cache/mojang_1.21.11.jar`.
5. Execute novamente `INICIAR_SERVIDOR.bat` com acesso à internet; o PaperMC
   baixará novamente esse arquivo de cache.

Não exclua nenhuma pasta cujo nome comece com `world_`. Se o bloqueio persistir,
clone o projeto em uma pasta local que não seja sincronizada pelo OneDrive,
como `C:\Projetos\AI-Algorithms-on-Minecraft`.

### Aviso sobre `online-mode=false`

O servidor está configurado em modo offline para o ambiente privado original.
Não exponha a porta do servidor à internet dessa forma: qualquer pessoa pode
escolher nomes de usuários sem autenticação. Use uma rede privada controlada ou
ative `online-mode=true` quando todos tiverem contas autenticadas.
