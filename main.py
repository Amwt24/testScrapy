"""
Instagram Profile Data Extractor - With Smart Scroll
Extrae: Username, Seguidores, Seguidos, Biografía, Descripción
+ Lista completa de followers y following
Selenium con scroll inteligente automático
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
    print("\nCrea un archivo .env con:")
    print("IG_USERNAME=tu_usuario")
    print("IG_PASSWORD=tu_contraseña")
    print("TARGET_ACCOUNT=cuenta_objetivo")
    print("EXTRACT_FOLLOWERS=true")
    print("EXTRACT_FOLLOWING=true")
    print("MAX_FOLLOWERS=100")
    print("MAX_FOLLOWING=100")
    exit(1)

load_dotenv(dotenv_path)

yourusername = os.getenv("IG_USERNAME", "").strip()
yourpassword = os.getenv("IG_PASSWORD", "").strip()
target_account = os.getenv("TARGET_ACCOUNT", "").strip()

# Opciones de extracción
extract_followers = os.getenv("EXTRACT_FOLLOWERS", "false").lower() == "true"
extract_following = os.getenv("EXTRACT_FOLLOWING", "false").lower() == "true"

try:
    max_followers = int(os.getenv("MAX_FOLLOWERS", "100"))
    max_following = int(os.getenv("MAX_FOLLOWING", "100"))
except:
    max_followers = 100
    max_following = 100

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
def human_delay(min_sec=1.0, max_sec=3.0):
    sleep(random.uniform(min_sec, max_sec))

def type_like_human(element, text):
    for char in text:
        element.send_keys(char)
        sleep(random.uniform(0.05, 0.15))

def parse_number(text):
    """Convierte texto con K/M a número (ej: '1.5K' -> 1500)"""
    if not text:
        return None
    
    text = text.lower().strip().replace(',', '')
    
    # Buscar patrones con K o M
    match = re.search(r'([\d\.]+)\s*([km])?', text)
    if match:
        num_str, unit = match.groups()
        try:
            num = float(num_str)
            if unit == 'k':
                return int(num * 1000)
            elif unit == 'm':
                return int(num * 1_000_000)
            else:
                return int(num)
        except:
            pass
    
    # Intentar conversión directa
    try:
        return int(float(text))
    except:
        return None

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
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            human_delay(1, 2)
            return
        except:
            continue

def login_instagram(driver):
    try:
        logger.log("🔐 Iniciando login...")
        driver.get('https://www.instagram.com/')
        sleep(3)
        
        handle_cookies(driver)
        
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = driver.find_element(By.NAME, "password")
        
        username_input.clear()
        password_input.clear()
        
        type_like_human(username_input, yourusername)
        type_like_human(password_input, yourpassword)
        
        password_input.send_keys(Keys.ENTER)
        logger.log("🚀 Credenciales enviadas...")
        
        sleep(random.uniform(4, 6))
        
        # Cerrar diálogos
        dialogs = [
            "//button[contains(text(),'Not Now')]",
            "//button[contains(text(),'Ahora no')]"
        ]
        for xpath in dialogs:
            try:
                btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                btn.click()
                sleep(2)
            except:
                pass
        
        logger.success("✓ Login completado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en login: {str(e)}")
        return False

# ====================== SCROLL INTELIGENTE ======================
def scroll_modal_smart(driver):
    """Scroll inteligente que busca el div correcto automáticamente"""
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
            sleep(random.uniform(1.5, 2.5))
            return True
        else:
            logger.debug("  ⚠ No se encontró div scrolleable")
            return False
        
    except Exception as e:
        logger.debug(f"  ✗ Error en scroll: {str(e)}")
        return False

# ====================== EXTRACCIÓN DE LISTAS ======================
def extract_list_selenium(driver, account_name, page_type, target_count):
    """
    Extrae lista de seguidores o seguidos con Selenium y scroll automático
    page_type: 'followers' o 'following'
    """
    try:
        logger.log(f"\n{'='*60}")
        logger.log(f"📋 Extrayendo lista de {page_type} de @{account_name}")
        logger.log(f"🎯 Objetivo: {target_count} usuarios")
        logger.log(f"{'='*60}")
        
        human_delay(1.5, 2.2)
        
        # Verificar cuenta existe
        try:
            driver.find_element(By.XPATH, "//h2[contains(text(), 'Sorry')]")
            logger.error("❌ Cuenta no existe")
            return []
        except NoSuchElementException:
            logger.debug("✓ Cuenta accesible")
        
        # Abrir modal
        logger.log(f"🖱️ Abriendo modal de {page_type}...")
        try:
            followers_link = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, f'//a[contains(@href, "/{page_type}")]'))
            )
            driver.execute_script("arguments[0].click();", followers_link)
        except TimeoutException:
            logger.error(f"❌ No se encontró enlace de {page_type}")
            return []
        
        # Esperar modal
        try:
            modal = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
            )
            logger.success(f"✓ Modal de {page_type} abierto")
        except TimeoutException:
            logger.error("❌ Modal no detectado")
            return []
        
        human_delay(1.5, 2.5)
        
        # Extracción con scroll
        users_list = []
        scraped = set()
        consecutive_no_progress = 0
        max_no_progress = 10
        scroll_attempts = 0
        max_scroll_attempts = 200
        
        logger.log("🔄 Iniciando extracción con scroll inteligente...")
        
        while len(users_list) < target_count and consecutive_no_progress < max_no_progress and scroll_attempts < max_scroll_attempts:
            user_links = driver.find_elements(By.XPATH, "//div[@role='dialog']//a[contains(@href, '/')]")
            new_users = 0
            
            for link in user_links:
                try:
                    href = link.get_attribute('href')
                    if href and 'instagram.com/' in href:
                        username = href.split('instagram.com/')[-1].strip('/').split('/')[0]
                        if (username and username not in scraped and username != account_name and
                            not username.startswith(('explore', 'p/', 'direct'))):
                            scraped.add(username)
                            users_list.append(username)
                            new_users += 1
                            if len(users_list) >= target_count:
                                logger.success(f"🎯 Objetivo alcanzado: {len(users_list)}")
                                break
                except:
                    continue
            
            if new_users > 0:
                consecutive_no_progress = 0
                logger.log(f"  ✓ Progreso: {len(users_list)}/{target_count} (+{new_users})")
            else:
                consecutive_no_progress += 1
                if consecutive_no_progress <= 3:
                    logger.debug(f"  ⏳ Esperando carga ({consecutive_no_progress})")
                else:
                    logger.warning(f"  ⚠ Sin progreso ({consecutive_no_progress})")
            
            if len(users_list) >= target_count:
                break
            
            scroll_attempts += 1
            if scroll_attempts % 10 == 1:
                logger.debug(f"  📜 Scroll #{scroll_attempts}")
            
            scroll_modal_smart(driver)
            sleep(random.uniform(1.4, 2.2))
        
        logger.log("="*60)
        if len(users_list) >= target_count:
            logger.success(f"✅ ÉXITO: {len(users_list)} usuarios extraídos")
        elif users_list:
            logger.warning(f"⚠ PARCIAL: {len(users_list)}/{target_count} usuarios")
        else:
            logger.error("❌ No se extrajo ningún usuario")
        
        logger.log(f"   Total scrolls: {scroll_attempts}")
        logger.log("="*60)
        
        # Cerrar modal
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            sleep(2)
        except:
            pass
        
        return users_list
        
    except Exception as e:
        logger.error(f"❌ Error extrayendo lista: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        return []

# ====================== EXTRACCIÓN DE PERFIL ======================
def extract_profile_data(driver, account):
    """Extrae datos básicos del perfil"""
    
    logger.log(f"\n{'='*60}")
    logger.log(f"📊 EXTRAYENDO DATOS BÁSICOS DE: @{account}")
    logger.log(f"{'='*60}")
    
    profile_data = {
        'username': account,
        'followers': None,
        'following': None,
        'posts': None,
        'bio': None,
        'description': None,
        'website': None
    }
    
    try:
        url = f'https://www.instagram.com/{account}/'
        driver.get(url)
        sleep(3)
        
        # Verificar si existe
        try:
            error = driver.find_element(By.XPATH, "//h2[contains(text(), 'Sorry')]")
            logger.error("❌ Cuenta no existe o es privada")
            return profile_data
        except NoSuchElementException:
            pass
        
        logger.log("🔍 Extrayendo datos del perfil...")
        
        # SEGUIDORES
        try:
            followers_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, f'//a[contains(@href, "/{account}/followers/")]'))
            )
            text = followers_link.text
            profile_data['followers'] = parse_number(text)
            
            if not profile_data['followers']:
                title = followers_link.get_attribute('title')
                profile_data['followers'] = parse_number(title)
            
            if profile_data['followers']:
                logger.success(f"✓ Seguidores: {profile_data['followers']:,}")
        except Exception as e:
            logger.warning(f"⚠ No se pudieron obtener seguidores: {str(e)}")
        
        # SEGUIDOS
        try:
            following_link = driver.find_element(By.XPATH, f'//a[contains(@href, "/{account}/following/")]')
            text = following_link.text
            profile_data['following'] = parse_number(text)
            
            if not profile_data['following']:
                title = following_link.get_attribute('title')
                profile_data['following'] = parse_number(title)
            
            if profile_data['following']:
                logger.success(f"✓ Seguidos: {profile_data['following']:,}")
        except Exception as e:
            logger.warning(f"⚠ No se pudieron obtener seguidos: {str(e)}")
        
        # POSTS
        try:
            # Buscar el número de posts
            spans = driver.find_elements(By.TAG_NAME, 'span')
            for span in spans:
                text = span.text
                if 'post' in text.lower():
                    profile_data['posts'] = parse_number(text)
                    if profile_data['posts']:
                        logger.success(f"✓ Posts: {profile_data['posts']:,}")
                        break
        except Exception as e:
            logger.warning(f"⚠ No se pudieron obtener posts: {str(e)}")
        
        # BIOGRAFÍA Y DESCRIPCIÓN
        try:
            # Nombre completo (descripción)
            try:
                desc_elem = driver.find_element(By.XPATH, "//header//section//h1 | //header//section//span")
                profile_data['description'] = desc_elem.text.strip()
                if profile_data['description']:
                    logger.success(f"✓ Descripción: {profile_data['description'][:50]}...")
            except:
                pass
            
            # Bio
            try:
                # La bio suele estar en un span específico dentro del header
                bio_spans = driver.find_elements(By.XPATH, "//header//div//span")
                for span in bio_spans:
                    text = span.text.strip()
                    if text and len(text) > 5 and 'follower' not in text.lower() and 'following' not in text.lower():
                        if not profile_data['bio']:
                            profile_data['bio'] = text
                            logger.success(f"✓ Biografía: {profile_data['bio'][:50]}...")
                            break
            except:
                pass
            
            # Website
            try:
                website_link = driver.find_element(By.XPATH, "//header//a[starts-with(@href, 'http')]")
                profile_data['website'] = website_link.get_attribute('href')
                logger.success(f"✓ Website: {profile_data['website']}")
            except:
                pass
            
        except Exception as e:
            logger.warning(f"⚠ Error extrayendo bio: {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Error general: {str(e)}")
    
    return profile_data

# ====================== GUARDAR RESULTADOS ======================
def save_profile_data(profile_data):
    """Guarda datos básicos del perfil"""
    try:
        with open(logger.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Username', 'Followers', 'Following', 'Posts', 'Description', 'Bio', 'Website'])
            writer.writerow([
                profile_data['username'],
                profile_data['followers'] or 'N/A',
                profile_data['following'] or 'N/A',
                profile_data['posts'] or 'N/A',
                profile_data['description'] or 'N/A',
                profile_data['bio'] or 'N/A',
                profile_data['website'] or 'N/A'
            ])
        
        logger.success(f"✅ CSV perfil guardado: {logger.csv_file}")
        
    except Exception as e:
        logger.error(f"❌ Error guardando perfil: {str(e)}")

def save_followers_list(followers_list):
    """Guarda lista de seguidores"""
    try:
        with open(logger.followers_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Username', 'Follower'])
            for follower in followers_list:
                writer.writerow([target_account, follower])
        
        logger.success(f"✅ CSV followers guardado: {logger.followers_csv} ({len(followers_list)} usuarios)")
        
    except Exception as e:
        logger.error(f"❌ Error guardando followers: {str(e)}")

def save_following_list(following_list):
    """Guarda lista de seguidos"""
    try:
        with open(logger.following_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Username', 'Following'])
            for following in following_list:
                writer.writerow([target_account, following])
        
        logger.success(f"✅ CSV following guardado: {logger.following_csv} ({len(following_list)} usuarios)")
        
    except Exception as e:
        logger.error(f"❌ Error guardando following: {str(e)}")

def save_summary(profile_data, followers_list, following_list):
    """Guarda resumen en TXT"""
    txt_file = f"{target_account}_summary_{logger.timestamp}.txt"
    
    try:
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"{'='*70}\n")
            f.write(f"RESUMEN COMPLETO DEL PERFIL: @{target_account}\n")
            f.write(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n\n")
            
            f.write(f"📊 DATOS BÁSICOS:\n")
            f.write(f"{'─'*70}\n")
            f.write(f"👤 Username: {profile_data['username']}\n")
            f.write(f"👥 Seguidores: {profile_data['followers']:,}\n" if profile_data['followers'] else "👥 Seguidores: N/A\n")
            f.write(f"➕ Seguidos: {profile_data['following']:,}\n" if profile_data['following'] else "➕ Seguidos: N/A\n")
            f.write(f"📷 Posts: {profile_data['posts']:,}\n" if profile_data['posts'] else "📷 Posts: N/A\n")
            f.write(f"🌐 Website: {profile_data['website']}\n" if profile_data['website'] else "🌐 Website: N/A\n")
            f.write(f"📝 Descripción: {profile_data['description']}\n" if profile_data['description'] else "📝 Descripción: N/A\n")
            f.write(f"📄 Biografía:\n{profile_data['bio']}\n" if profile_data['bio'] else "📄 Biografía: N/A\n")
            
            if followers_list:
                f.write(f"\n{'='*70}\n")
                f.write(f"👥 SEGUIDORES EXTRAÍDOS: {len(followers_list)}\n")
                f.write(f"{'─'*70}\n")
                for i, follower in enumerate(followers_list[:20], 1):
                    f.write(f"{i:3d}. {follower}\n")
                if len(followers_list) > 20:
                    f.write(f"... y {len(followers_list) - 20} más\n")
            
            if following_list:
                f.write(f"\n{'='*70}\n")
                f.write(f"➕ SEGUIDOS EXTRAÍDOS: {len(following_list)}\n")
                f.write(f"{'─'*70}\n")
                for i, following in enumerate(following_list[:20], 1):
                    f.write(f"{i:3d}. {following}\n")
                if len(following_list) > 20:
                    f.write(f"... y {len(following_list) - 20} más\n")
        
        logger.success(f"✅ Resumen guardado: {txt_file}")
        
    except Exception as e:
        logger.error(f"❌ Error guardando resumen: {str(e)}")

# ====================== MAIN ======================
def main():
    driver = None
    
    try:
        logger.log("="*70)
        logger.log("🎯 INSTAGRAM COMPLETE PROFILE EXTRACTOR")
        logger.log("="*70)
        logger.log(f"📊 Cuenta objetivo: @{target_account}")
        logger.log(f"👥 Extraer followers: {'SÍ' if extract_followers else 'NO'} (max: {max_followers})")
        logger.log(f"➕ Extraer following: {'SÍ' if extract_following else 'NO'} (max: {max_following})")
        logger.log("="*70)
        
        # FASE 1: LOGIN
        logger.log("\n🔐 FASE 1: LOGIN")
        driver = setup_driver()
        
        if not login_instagram(driver):
            logger.error("❌ Login fallido")
            return
        
        # FASE 2: DATOS BÁSICOS
        logger.log("\n📊 FASE 2: DATOS BÁSICOS DEL PERFIL")
        profile_data = extract_profile_data(driver, target_account)
        save_profile_data(profile_data)
        
        # FASE 3: FOLLOWERS
        followers_list = []
        if extract_followers:
            logger.log("\n👥 FASE 3: EXTRACCIÓN DE FOLLOWERS")
            followers_list = extract_list_selenium(driver, target_account, 'followers', max_followers)
            if followers_list:
                save_followers_list(followers_list)
        else:
            logger.log("\n⏭️ FASE 3: Extracción de followers OMITIDA")
        
        # FASE 4: FOLLOWING
        following_list = []
        if extract_following:
            logger.log("\n➕ FASE 4: EXTRACCIÓN DE FOLLOWING")
            following_list = extract_list_selenium(driver, target_account, 'following', max_following)
            if following_list:
                save_following_list(following_list)
        else:
            logger.log("\n⏭️ FASE 4: Extracción de following OMITIDA")
        
        # FASE 5: RESUMEN
        logger.log("\n💾 FASE 5: GUARDANDO RESUMEN")
        save_summary(profile_data, followers_list, following_list)
        
        # RESUMEN FINAL
        logger.log("\n" + "="*70)
        logger.success("🎉 PROCESO COMPLETADO")
        logger.log("="*70)
        logger.log(f"📁 Archivos generados:")
        logger.log(f"   • Perfil: {logger.csv_file}")
        if followers_list:
            logger.log(f"   • Followers: {logger.followers_csv} ({len(followers_list)} usuarios)")
        if following_list:
            logger.log(f"   • Following: {logger.following_csv} ({len(following_list)} usuarios)")
        logger.log(f"   • Log: {logger.log_file}")
        logger.log("="*70)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interrumpido por usuario")
    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()