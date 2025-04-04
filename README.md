# Spotify Charts Dashboard

Dashboard interactivo que muestra estadísticas de Spotify Charts para varios países de habla hispana.

## Estructura del Proyecto

- `dashboard.py`: Aplicación principal de Streamlit
- `bot.py`: Script para descargar datos de Spotify Charts
- `requirements.txt`: Dependencias del proyecto
- `spotify_downloads/`: Carpeta con los datos descargados por país

## Ejecución Local

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar el dashboard:
```bash
streamlit run dashboard.py
```

## Datos

Los datos se actualizan manualmente usando el bot. Cada país tiene su propia subcarpeta dentro de `spotify_downloads/`. 
