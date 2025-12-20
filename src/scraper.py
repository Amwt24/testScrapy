import time
import random
from playwright.sync_api import Page
from . import config, utils

logger = utils.setup_logger()

def scrape_list(page: Page, list_type: str, target_account: str, max_count: int):
    """
    Extrae usuarios de 'followers' o 'following'.
    list_type debe ser 'followers' o 'following'.
    """
    users_collected = []
    seen_users = set()
    
    logger.info(f"📋 Iniciando extracción de {list_type} para @{target_account} (Meta: {max_count})")
    
    try:
        # 1. Ir al perfil
        page.goto(f"https://www.instagram.com/{target_account}/")
        time.sleep(3)
        
        # 2. Abrir modal
        # Usamos href parcial para encontrar el enlace correcto
        link_selector = f"a[href*='/{list_type}']"
        try:
            page.wait_for_selector(link_selector, timeout=5000)
            page.locator(link_selector).click()
        except Exception:
            logger.error(f"❌ No se encontró el enlace de {list_type}. ¿La cuenta es privada o está mal el nombre?")
            return []
            
        # 3. Esperar al modal
        logger.info("🖱️ Modal abierto. Preparando scroll...")
        try:
            modal_selector = "div[role='dialog']"
            page.wait_for_selector(modal_selector, timeout=5000)
            # Encontrar el div scrolleable dentro del modal. 
            # Generalmente es el hijo directo o cercano con overflow-y: auto o similar.
            # Una estrategia robusta es buscar el div que contiene la lista de items.
            scrollable_div_selector = f"{modal_selector} div._aano" # Selector común en IG actual (clase ofuscada, puede cambiar)
            
            # Fallback si _aano no existe: buscar por estructura
            if not page.locator(scrollable_div_selector).is_visible():
                 # Buscar cualquier div dentro del dialogo con scroll vertical
                 scrollable_div_selector = f"{modal_selector} > div > div > div:nth-child(2)" 

            logger.debug(f"Objetivo de scroll identificado: {scrollable_div_selector}")
            
        except Exception as e:
            logger.error(f"❌ Error detectando modal: {e}")
            return []

        time.sleep(2)

        # 4. Loop de Scroll y Extracción
        consecutive_no_new = 0
        max_no_new_strikes = 10 # Si falla 10 veces seguidas, asumimos fin
        
        while len(users_collected) < max_count:
            # Extraer nombres visibles actuales
            # Los usuarios suelen estar en <span> o <a> con href="/username/"
            # Buscamos enlaces que parezcan usuarios dentro del modal
            elements = page.locator(f"{modal_selector} a").all()
            
            new_in_batch = 0
            for el in elements:
                href = el.get_attribute("href")
                if href and href.count('/') == 2: # /username/ tiene 2 slashes si es relativo, o mas si es absoluto
                    username = href.strip('/').split('/')[-1]
                    
                    if (username not in seen_users 
                        and username != target_account 
                        and username not in ['explore', 'reels', 'stories']):
                        
                        seen_users.add(username)
                        users_collected.append(username)
                        new_in_batch += 1
            
            # Logging de progreso
            if new_in_batch > 0:
                consecutive_no_new = 0
                if len(users_collected) % 20 == 0:
                    logger.info(f"  ✓ Progreso: {len(users_collected)} / {max_count}")
            else:
                consecutive_no_new += 1
                logger.debug(f"  ⏳ Scroll sin nuevos usuarios ({consecutive_no_new}/{max_no_new_strikes})")
            
            if len(users_collected) >= max_count:
                break
                
            if consecutive_no_new >= max_no_new_strikes:
                logger.warning("⚠️ No se cargan nuevos usuarios. Posible fin de lista o límite de IG.")
                break
                
            # Scroll Action
            try:
                # ESTRATEGIA ROBUSTA: Usar rueda del mouse en lugar de buscar el div exacto
                # Ponemos el mouse sobre el modal
                page.locator(modal_selector).hover()
                # Scrolleamos hacia abajo
                page.mouse.wheel(0, 1500)
                
                time.sleep(random.uniform(1.5, 2.5)) # Delay humano
            except Exception as e:
                logger.error(f"Error scrolleando: {e}")
                break

        logger.success(f"✅ Extracción de {list_type} finalizada. Total: {len(users_collected)}")
        return users_collected

    except Exception as e:
        logger.error(f"❌ Error crítico en scrape_list: {e}")
        return users_collected
