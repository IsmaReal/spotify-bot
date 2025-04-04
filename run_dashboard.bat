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

:: Instalar todas las dependencias necesarias
echo Verificando e instalando dependencias...
pip install streamlit pandas plotly >nul 2>&1

echo Iniciando Spotify Charts Dashboard...
streamlit run dashboard.py
pause 