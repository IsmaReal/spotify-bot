@echo off
echo Verificando entorno...

:: Verificar si existe el entorno virtual
IF EXIST "venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
) ELSE (
    echo Creando entorno virtual...
    python -m venv venv
    call venv\Scripts\activate.bat
)

:: Instalar dependencias necesarias
echo Verificando e instalando dependencias...
pip install selenium webdriver_manager pandas >nul 2>&1

echo Iniciando bot de Spotify Charts para Uruguay...
python bot.py uy
pause 