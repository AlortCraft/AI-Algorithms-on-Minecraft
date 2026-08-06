@echo off
setlocal
cd /d "%~dp0"

where java >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Java nao foi encontrado no PATH do Windows.
    echo Instale o Java 21 ou mais recente e abra novamente o VS Code.
    pause
    exit /b 1
)

echo [INFO] Iniciando o servidor PaperMC...
echo [INFO] Para encerrar com seguranca, digite stop e pressione Enter.
echo.

java -Xms2G -Xmx2G -jar "paper-1.21.11-132.jar" nogui
set "SERVER_EXIT=%ERRORLEVEL%"

if not "%SERVER_EXIT%"=="0" (
    echo.
    echo [ERRO] O servidor terminou com o codigo %SERVER_EXIT%.
    echo Consulte logs\latest.log para ver os detalhes.
)

echo.
pause
exit /b %SERVER_EXIT%
