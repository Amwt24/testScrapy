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

def main():
    logger = utils.setup_logger()
    logger.info("🚀 Iniciando Ig_ScrapingV4 con Playwright")
    
    # Validaciones previas
    if not config.USERNAME or not config.PASSWORD:
        logger.error("❌ Faltan credenciales en .env")
        return

    with sync_playwright() as p:
        # Configurar navegador
        browser = p.chromium.launch(
            headless=False, # Ver el navegador (importante para 'visual')
            args=["--start-maximized"] # Maximizar para mejor renderizado
        )
        
        # Contexto persistente (Carga session.json si existe)
        if os.path.exists(config.SESSION_FILE):
            context = browser.new_context(
                storage_state=config.SESSION_FILE,
                no_viewport=True # Usar tamaño de ventana real
            )
        else:
            context = browser.new_context(no_viewport=True)

        try:
            # 1. Autenticación
            page = auth.login(context)
            
            # 2. Extracción de FOLLOWING
            if config.EXTRACT_FOLLOWING:
                following = scraper.scrape_list(
                    page, 
                    "following", 
                    config.TARGET_ACCOUNT, 
                    config.MAX_FOLLOWING
                )
                save_csv(following, f"{config.TARGET_ACCOUNT}_following.csv")
            
            # 3. Extracción de FOLLOWERS
            if config.EXTRACT_FOLLOWERS:
                followers = scraper.scrape_list(
                    page, 
                    "followers", 
                    config.TARGET_ACCOUNT, 
                    config.MAX_FOLLOWERS
                )
                save_csv(followers, f"{config.TARGET_ACCOUNT}_followers.csv")
                
        except Exception as e:
            logger.error(f"❌ Error en ejecución principal: {e}")
        finally:
            context.close()
            browser.close()
            logger.info("👋 Proceso terminado.")

if __name__ == "__main__":
    main()
