import csv
import os
import sys
from playwright.sync_api import sync_playwright
from src import config, auth, scraper, utils

def save_csv(data, filename):
    """Guarda una lista de usuarios en CSV."""
    if not data:
        return
    
    filepath = os.path.join(config.DATA_DIR, filename)
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Target Account', 'Username'])
            for user in data:
                writer.writerow([config.TARGET_ACCOUNT, user])
        utils.setup_logger().success(f"💾 Archivo guardado: {filepath}")
    except Exception as e:
        utils.setup_logger().error(f"❌ Error guardando CSV: {e}")

def resolve_target_account(raw_target):
    """
    Intenta deducir el username real si se pasa un path de archivo o un string sucio.
    Soporta:
    - Username directo: "pepito"
    - Path de archivo resumen: "legacy/pepito_summary_2025.txt"
    - Path absoluto/relativo
    """
    logger = utils.setup_logger()
    cleaned = raw_target.strip()
    
    # 1. Si es un archivo existente, intentamos leer el contenido
    if os.path.isfile(cleaned):
        try:
            with open(cleaned, 'r', encoding='utf-8') as f:
                content = f.read()
                # Buscar patrón "Username: pepito"
                for line in content.splitlines():
                    if "Username:" in line:
                        found_user = line.split("Username:")[1].strip()
                        if found_user:
                            logger.info(f"📂 Username detectado dentro del archivo: {found_user}")
                            return found_user
        except Exception as e:
            logger.warning(f"⚠️ No se pudo leer el archivo target: {e}")

    # 2. Si parece un nombre de archivo (tiene extensión o path separators)
    base_name = os.path.basename(cleaned) # "pepito_summary_2025.txt"
    if "_summary_" in base_name:
        # Caso: nayeli.nxx_summary_20251217.txt
        candidate = base_name.split("_summary_")[0]
        logger.info(f"🔧 Username extraído del nombre de archivo: {candidate}")
        return candidate
    
    # 3. Limpieza básica de extensiones comunes si no macheó lo anterior
    if base_name.endswith(".txt") or base_name.endswith(".csv"):
        candidate = os.path.splitext(base_name)[0]
        logger.info(f"🔧 Extension removida, usando: {candidate}")
        return candidate

    return cleaned

def main():
    logger = utils.setup_logger()
    logger.info("🚀 Iniciando Ig_ScrapingV4 con Playwright")
    
    # Validaciones previas
    if not config.USERNAME or not config.PASSWORD:
        logger.error("❌ Faltan credenciales en .env")
        return

    # Saneamiento del Target Account
    config.TARGET_ACCOUNT = resolve_target_account(config.TARGET_ACCOUNT)
    logger.info(f"🎯 Cuenta objetivo fijada: {config.TARGET_ACCOUNT}")

    with sync_playwright() as p:
        # Configurar navegador
        browser = p.chromium.launch(
            headless=False, # Ver el navegador (importante para 'visual')
            args=[
                "--start-maximized",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ] 
        )
        
        # Contexto persistente (Carga session.json si existe)
        context = None
        if os.path.exists(config.SESSION_FILE):
            try:
                context = browser.new_context(
                    storage_state=config.SESSION_FILE,
                    no_viewport=True # Usar tamaño de ventana real
                )
                logger.info("✅ Sesión restaurada desde archivo.")
            except Exception as e:
                logger.warning(f"⚠️ Archivo de sesión corrupto o inválido. Creando nueva sesión. Error: {e}")
        
        if context is None:
            context = browser.new_context(no_viewport=True)

        try:
            # 1. Autenticación
            login_page = auth.login(context)
            login_page.close() # Cerramos la página de login/validación
            
            # 2. Extracción de FOLLOWING
            if config.EXTRACT_FOLLOWING:
                logger.info("🆕 Abriendo nueva página para Following...")
                page = context.new_page()
                following = scraper.scrape_list(
                    page, 
                    "following", 
                    config.TARGET_ACCOUNT, 
                    config.MAX_FOLLOWING
                )
                save_csv(following, f"{config.TARGET_ACCOUNT}_following.csv")
                page.close()
            
            # 3. Extracción de FOLLOWERS
            if config.EXTRACT_FOLLOWERS:
                logger.info("🆕 Abriendo nueva página para Followers...")
                page = context.new_page()
                followers = scraper.scrape_list(
                    page, 
                    "followers", 
                    config.TARGET_ACCOUNT, 
                    config.MAX_FOLLOWERS
                )
                save_csv(followers, f"{config.TARGET_ACCOUNT}_followers.csv")
                page.close()
                
        except Exception as e:
            logger.error(f"❌ Error en ejecución principal: {e}")
        finally:
            context.close()
            browser.close()
            logger.info("👋 Proceso terminado.")

if __name__ == "__main__":
    main()
