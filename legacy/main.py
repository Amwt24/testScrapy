"""
Instagram Profile Data Extractor - MODIFICADO PARA LISTAS LARGAS
Extrae: Lista completa de FOLLOWING (Seguidos)
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import datetime
import random
import csv
import json
import re
from time import sleep
from dotenv import load_dotenv, find_dotenv

# ====================== CONFIGURACIÓN ======================
dotenv_path = find_dotenv()
if not dotenv_path:
    print("❌ ERROR: No se encontró archivo .env")
    exit(1)

load_dotenv(dotenv_path)

yourusername = os.getenv("IG_USERNAME", "").strip()
yourpassword = os.getenv("IG_PASSWORD", "").strip()
target_account = os.getenv("TARGET_ACCOUNT", "").strip()

# Opciones de extracción
extract_followers = os.getenv("EXTRACT_FOLLOWERS", "false").lower() == "true"
extract_following = os.getenv("EXTRACT_FOLLOWING", "true").lower() == "true" # Por defecto true

try:
    max_followers = int(os.getenv("MAX_FOLLOWERS", "100"))
    max_following = int(os.getenv("MAX_FOLLOWING", "50000")) # Por defecto alto
except:
    max_followers = 100
    max_following = 50000

if not yourusername or not yourpassword or not target_account:
    print("❌ ERROR: Variables faltantes en .env")
    exit(1)

# ====================== LOGGER ======================
class Logger:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.logs_dir = "logs"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        
        self.log_file = os.path.join(self.logs_dir, f"profile_log_{self.timestamp}.txt")
        self.csv_file = f"{target_account}_complete_{self.timestamp}.csv"
        self.followers_csv = f"{target_account}_followers_{self.timestamp}.csv"
        self.following_csv = f"{target_account}_following_{self.timestamp}.csv"
        
    def log(self, message, level="INFO"):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        formatted = f"[{timestamp}] [{level}] {message}"
        print(formatted)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(formatted + "\n")
    
    def error(self, msg):
        self.log(msg, "ERROR")
    
    def success(self, msg):
        self.log(msg, "SUCCESS")
    
    def warning(self, msg):
        self.log(msg, "WARNING")
    
    def debug(self, msg):
        self.log(msg, "DEBUG")

logger = Logger()

# ====================== UTILIDADES ======================
def human_delay(min_sec=1.0, max_sec=2.5):
    sleep(random.uniform(min_sec, max_sec))

def type_like_human(element, text):
    for char in text:
        element.send_keys(char)
        sleep(random.uniform(0.05, 0.15))

def parse_number(text):
    if not text: return None
    text = text.lower().strip().replace(',', '')
    match = re.search(r'([\d\.]+)\s*([km])?', text)
    if match:
        num_str, unit = match.groups()
        try:
            num = float(num_str)
            if unit == 'k': return int(num * 1000)
            elif unit == 'm': return int(num * 1_000_000)
            else: return int(num)
        except: pass
    try: return int(float(text))
    except: return None

# ====================== SELENIUM SETUP ======================
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def handle_cookies(driver):
    selectors = [
        (By.XPATH, "//button[contains(text(),'Allow')]"),
        (By.XPATH, "//button[contains(text(),'Accept')]"),
        (By.XPATH, "//button[contains(text(),'Permitir')]"),
        (By.XPATH, "//button[contains(text(),'Aceptar')]"),
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            human_delay(1, 2)
            return
        except: continue

def login_instagram(driver):
    try:
        logger.log("🔐 Iniciando login...")
        driver.get('https://www.instagram.com/')
        sleep(3)
        handle_cookies(driver)
        
        username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        password_input = driver.find_element(By.NAME, "password")
        
        username_input.clear()
        password_input.clear()
        type_like_human(username_input, yourusername)
        type_like_human(password_input, yourpassword)
        
        password_input.send_keys(Keys.ENTER)
        logger.log("🚀 Credenciales enviadas...")
        sleep(random.uniform(5, 7))
        
        # Cerrar diálogos post-login
        dialogs = [
            "//button[contains(text(),'Not Now')]",
            "//button[contains(text(),'Ahora no')]",
            "//div[@role='button'][contains(text(),'Ahora no')]"
        ]
        for xpath in dialogs:
            try:
                btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                btn.click()
                sleep(1.5)
            except: pass
        
        logger.success("✓ Login completado")
        return True
    except Exception as e:
        logger.error(f"❌ Error en login: {str(e)}")
        return False

# ====================== SCROLL INTELIGENTE ======================
def scroll_modal_smart(driver):
    try:
        scroll_script = """
        const dialog = document.querySelector('div[role="dialog"]');
        if (!dialog) return false;
        const divs = dialog.querySelectorAll('div');
        for (let div of divs) {
            if (div.scrollHeight > div.clientHeight * 1.2) {
                div.scrollTop = div.scrollHeight;
                return true;
            }
        }
        return false;
        """
        result = driver.execute_script(scroll_script)
        if result:
            sleep(random.uniform(1.2, 2.0)) # Un poco más rápido para listas largas
            return True
        else:
            return False
    except: return False

# ====================== EXTRACCIÓN DE LISTAS ======================
def extract_list_selenium(driver, account_name, page_type, target_count):
    try:
        logger.log(f"\n{'='*60}")
        logger.log(f"📋 Extrayendo {page_type} de @{account_name} (Meta: {target_count})")
        
        # Navegar al perfil
        driver.get(f'https://www.instagram.com/{account_name}/')
        sleep(3)
        
        # Abrir modal
        logger.log(f"🖱️ Abriendo lista de {page_type}...")
        try:
            link_xpath = f'//a[contains(@href, "/{page_type}")]'
            followers_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, link_xpath)))
            driver.execute_script("arguments[0].click();", followers_link)
        except TimeoutException:
            logger.error(f"❌ No se pudo abrir {page_type}. ¿La cuenta es privada?")
            return []
        
        # Esperar modal
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
        except:
            logger.error("❌ Modal no cargó")
            return []
        
        human_delay(1.5, 2.5)
        
        users_list = []
        scraped = set()
        consecutive_no_progress = 0
        max_no_progress = 12
        scroll_attempts = 0
        
        # MODIFICACIÓN CRÍTICA: AUMENTADO PARA LISTAS LARGAS
        max_scroll_attempts = 15000 
        
        logger.log("🔄 Iniciando extracción masiva...")
        
        while len(users_list) < target_count and consecutive_no_progress < max_no_progress and scroll_attempts < max_scroll_attempts:
            # Captura de elementos
            user_links = driver.find_elements(By.XPATH, "//div[@role='dialog']//a[contains(@href, '/')]")
            new_users = 0
            
            for link in user_links:
                try:
                    href = link.get_attribute('href')
                    if href and 'instagram.com/' in href:
                        username = href.split('instagram.com/')[-1].strip('/').split('/')[0]
                        if (username and username not in scraped and username != account_name and
                            not username.startswith(('explore', 'p/', 'direct', 'stories'))):
                            
                            scraped.add(username)
                            users_list.append(username)
                            new_users += 1
                except: continue
            
            # Lógica de progreso
            if new_users > 0:
                consecutive_no_progress = 0
                if len(users_list) % 50 == 0: # Log menos frecuente para no saturar consola
                    logger.log(f"  ✓ Progreso: {len(users_list)}/{target_count}")
            else:
                consecutive_no_progress += 1
                logger.debug(f"  ⏳ Cargando... ({consecutive_no_progress})")
            
            if len(users_list) >= target_count:
                break
            
            scroll_attempts += 1
            if not scroll_modal_smart(driver):
                 # Si el script falla, intentamos scroll con teclas como fallback
                 try:
                     dialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
                     dialog.click()
                     driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
                     sleep(1)
                 except: pass

        logger.success(f"✅ FINALIZADO: {len(users_list)} usuarios extraídos")
        return users_list
        
    except Exception as e:
        logger.error(f"❌ Error crítico: {str(e)}")
        return users_list

# ====================== MAIN ======================
def main():
    driver = None
    try:
        logger.log("="*70)
        logger.log(f"🎯 EXTRAER 'FOLLOWING' DE @{target_account}")
        logger.log("="*70)
        
        driver = setup_driver()
        if not login_instagram(driver): return
        
        # Extraer Following
        following_list = []
        if extract_following:
            logger.log("\n➕ INICIANDO EXTRACCIÓN DE FOLLOWING")
            following_list = extract_list_selenium(driver, target_account, 'following', max_following)
            
            # Guardar resultados
            if following_list:
                with open(logger.following_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Target Account', 'Following Username'])
                    for user in following_list:
                        writer.writerow([target_account, user])
                logger.success(f"💾 Archivo guardado: {logger.following_csv}")
        
        logger.success("🎉 PROCESO TERMINADO")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Detenido manualmente por el usuario")
    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()