@echo off
setlocal
cd /d "%~dp0"

set "JAVA_EXE="
for /d %%D in ("C:\Program Files\Eclipse Adoptium\jdk-21*") do (
    if exist "%%~fD\bin\java.exe" set "JAVA_EXE=%%~fD\bin\java.exe"
)

if not defined JAVA_EXE (
    echo [ERRO] Java 21 Temurin nao foi encontrado.
    echo Instale o JDK 21 antes de iniciar o Paper 1.21.11.
    pause
    exit /b 1
)

echo [INFO] Iniciando o servidor PaperMC...
echo [INFO] Java: %JAVA_EXE%
echo [INFO] Memoria do Paper: 6 GB
echo [INFO] Para encerrar com seguranca, digite stop e pressione Enter.
echo.

"%JAVA_EXE%" -Xms6G -Xmx6G -jar "paper-1.21.11-132.jar" nogui
set "SERVER_EXIT=%ERRORLEVEL%"

if not "%SERVER_EXIT%"=="0" (
    echo.
    echo [ERRO] O servidor terminou com o codigo %SERVER_EXIT%.
    echo Consulte logs\latest.log para ver os detalhes.
)

echo.
pause
exit /b %SERVER_EXIT%
