from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
import sys
from datetime import datetime, timedelta

def load_failed_dates(country_code):
    """Cargar fechas fallidas del archivo de registro"""
    log_file = f"failed_dates_{country_code}.json"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return set(json.load(f))
    return set()

def save_failed_date(country_code, date):
    """Guardar fecha fallida en el archivo de registro"""
    log_file = f"failed_dates_{country_code}.json"
    failed_dates = load_failed_dates(country_code)
    failed_dates.add(date)
    with open(log_file, 'w') as f:
        json.dump(list(failed_dates), f)

def setup_driver(download_dir):
    # Setup con optimizaciones de rendimiento
    options = Options()
    user_data_dir = os.path.join(os.getcwd(), "selenium")
    os.makedirs(user_data_dir, exist_ok=True)
    
    # Convertir el directorio de descargas a ruta absoluta
    download_dir_abs = os.path.abspath(download_dir)
    
    # Optimizaciones adicionales para velocidad
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-logging")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--remote-debugging-port=9222")  # Añadir puerto de debugging
    
    # Configuraciones experimentales para optimizar rendimiento
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir_abs,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 2,  # Deshabilitar imágenes
        "profile.default_content_setting_values.cookies": 1
    })
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(20)  # Aumentar timeout
        driver.implicitly_wait(2)  # Aumentar tiempo de espera implícito
        return driver
    except Exception as e:
        print(f"Error al iniciar Chrome: {str(e)}")
        # Intentar con configuración mínima si falla
        options = Options()
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("prefs", {
            "download.default_directory": download_dir_abs,
            "download.prompt_for_download": False
        })
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(2)
        return driver

def download_country_data(country_code, start_date, end_date, base_dir):
    # Crear directorio específico para el país
    download_dir = os.path.join(os.getcwd(), base_dir, country_code)
    os.makedirs(download_dir, exist_ok=True)
    
    # Cargar fechas fallidas conocidas
    failed_dates = load_failed_dates(country_code)
    
    # Configurar el driver para este país
    driver = setup_driver(download_dir)
    wait = WebDriverWait(driver, 5)  # Aumentar tiempo de espera explícito
    
    try:
        # Loguearse en Spotify Charts
        initial_url = f"https://charts.spotify.com/charts/view/regional-{country_code}-daily/{start_date.strftime('%Y-%m-%d')}"
        try:
            driver.get(initial_url)
        except:
            print("Timeout al cargar la página, intentando continuar...")
            driver.execute_script("window.stop();")
        
        # Pedir confirmación para cada país
        input(f"Presiona Enter para comenzar la descarga de {country_code.upper()}...")
        
        # Generar fechas
        dates = [(start_date + timedelta(days=x)).strftime("%Y-%m-%d") 
                for x in range((end_date - start_date).days + 1)]
        
        # Verificar archivos existentes
        existing_files = set(os.listdir(download_dir))
        print(f"\nArchivos existentes en {country_code.upper()}: {len(existing_files)}")
        
        # Filtrar fechas que ya están descargadas o han fallado previamente
        dates_to_download = [date for date in dates 
                        if f"regional-{country_code}-daily-{date}.csv" not in existing_files
                        and date not in failed_dates]
        
        print(f"Total de archivos a descargar para {country_code.upper()}: {len(dates_to_download)}")
        print(f"Fechas previamente fallidas: {len(failed_dates)}")
        
        if len(dates_to_download) == 0:
            print(f"¡Todos los archivos disponibles ya están descargados para {country_code.upper()}!")
            return
        
        for date in dates_to_download:
            print(f"\nProcesando {country_code.upper()} - fecha: {date}")
            url = f"https://charts.spotify.com/charts/view/regional-{country_code}-daily/{date}"
            try:
                driver.get(url)
            except:
                driver.execute_script("window.stop();")  # Detener carga si toma demasiado tiempo
            
            try:
                print("Buscando botón de descarga...")
                download_button = wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    'button[data-encore-id="buttonTertiary"][aria-labelledby="csv_download"]'
                )))
                print("Botón encontrado, haciendo clic...")
                driver.execute_script("arguments[0].click();", download_button)  # Click con JavaScript
                
                # Verificar si el archivo se descargó
                print(f"Descargando CSV para {date}...")
                time.sleep(0.5)  # Reducir pausa para verificar descarga
                downloaded_files = set(os.listdir(download_dir))
                new_files = downloaded_files - existing_files
                if new_files:
                    print(f"Archivo descargado: {new_files}")
                    existing_files = downloaded_files
                else:
                    print(f"¡Advertencia: No se detectó archivo para {date}!")
                    save_failed_date(country_code, date)
                
            except Exception as e:
                print(f"Fallo en {date}: {e}")
                save_failed_date(country_code, date)
                driver.save_screenshot(f"error_{country_code}_{date}.png")
                print(f"Se guardó un screenshot como error_{country_code}_{date}.png")
    
    finally:
        driver.quit()

def main():
    # Verificar argumentos
    valid_countries = ["ar", "cl", "uy", "mx", "es"]
    if len(sys.argv) != 2 or sys.argv[1] not in valid_countries:
        print("Uso: python bot.py [ar|cl|uy|mx|es]")
        print("ar: Argentina")
        print("cl: Chile")
        print("uy: Uruguay")
        print("mx: México")
        print("es: España")
        sys.exit(1)
        
    country = sys.argv[1]
    
    # Configuración base
    base_dir = "spotify_downloads"
    os.makedirs(base_dir, exist_ok=True)
    
    # Fechas para la descarga
    start_date = datetime(2020, 1, 1)
    end_date = datetime.now()
    
    print(f"\nIniciando descarga para {country.upper()}")
    download_country_data(country, start_date, end_date, base_dir)
    
    print("\n¡Descarga completada!")

if __name__ == "__main__":
    main()
