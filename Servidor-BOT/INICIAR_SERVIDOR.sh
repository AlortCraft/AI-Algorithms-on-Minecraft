#!/usr/bin/env bash

set -euo pipefail

# Usa a pasta do proprio script, mesmo quando ele e chamado da raiz do projeto.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v java >/dev/null 2>&1; then
    echo "[ERRO] Java nao foi encontrado no PATH."
    echo "Instale o Java 21 ou mais recente e tente novamente."
    exit 1
fi

PAPER_JAR="paper-1.21.11-132.jar"

if [[ ! -f "$PAPER_JAR" ]]; then
    echo "[ERRO] O arquivo $PAPER_JAR nao foi encontrado em:"
    echo "$SCRIPT_DIR"
    exit 1
fi

echo "[INFO] Iniciando o servidor PaperMC em $SCRIPT_DIR"
echo "[INFO] Para encerrar com seguranca, digite stop e pressione Enter."

exec java -Xmx2G -Xms2G -jar "$PAPER_JAR" nogui
