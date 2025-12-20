import os
import time
from playwright.sync_api import BrowserContext, Page, expect
from . import config, utils

logger = utils.setup_logger()

def login(context: BrowserContext) -> Page:
    """
    Maneja el inicio de sesión. 
    Intenta cargar cookies existentes. Si fallan o no existen, realiza login manual y guarda sesión.
    """
    page = context.new_page()
    
    # 1. Intentar cargar sesión
    if os.path.exists(config.SESSION_FILE):
        logger.info("🍪 Cargando sesión existente...")
        # Nota: En Playwright, el context se crea CON el storage_state. 
        # Si estamos aquí, asumimos que 'context' ya se inicializó con storage_state si existía archivo.
        # Solo verificamos si funcionó.
        try:
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            time.sleep(3)
            # Verificar si estamos logueados buscando si aparece el input de usuario
            # Si aparece el input de username, es que NO estamos logueados.
            if page.locator("input[name='username']").is_visible():
                logger.warning("⚠️ La sesión guardada expiró o es inválida.")
            else:
                logger.success("✅ Sesión válida recuperada.")
                return page
        except Exception as e:
            logger.error(f"Error verificando sesión: {e}")

    # 2. Login Manual si es necesario
    logger.info("🔐 Iniciando login manual...")
    page.goto("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    
    # Aceptar cookies si aparecen
    try:
        page.get_by_role("button", name="Allow all cookies").click(timeout=2000)
    except:
        pass

    # Llenar formulario
    try:
        logger.info("⌨️ Escribiendo credenciales...")
        page.wait_for_selector("input[name='username']")
        utils.type_like_human(page, "input[name='username']", config.USERNAME)
        utils.type_like_human(page, "input[name='password']", config.PASSWORD)
        
        # Usar selector más específico para evitar ambigüedad con "Log in with Facebook"
        page.locator("button[type='submit']").click()
        
        # Esperar a que cargue la siguiente página (puede ser el feed o "Save Info")
        page.wait_for_load_state("domcontentloaded")
        
        logger.info("🚀 Login enviado. Verificando estado...")
        
        # Si nos manda a /accounts/onetap/, es que ya entramos pero quiere confirmar "Guardar Info"
        if "onetap" in page.url:
            logger.info("ℹ️ Detectada pantalla 'One Tap' (Guardar Info). Gestionando...")
            handle_post_login_dialogs(page)
        
        # Esperar a ver algún elemento del Feed para confirmar éxito
        # Buscamos el icono de "Home" o "Inicio"
        try:
            page.wait_for_selector("svg[aria-label='Home'], svg[aria-label='Inicio']", timeout=10000)
        except:
            logger.warning("⚠️ No se detectó el icono Home. Puede que haya otros diálogos pendientes.")
            handle_post_login_dialogs(page)

        # Guardar sesión
        logger.info("💾 Guardando nueva sesión...")
        context.storage_state(path=config.SESSION_FILE)
        logger.success("✅ Login exitoso y sesión guardada.")
        
    except Exception as e:
        logger.error(f"❌ Falló el login: {e}")
        # Opcional: Tomar screenshot
        page.screenshot(path=os.path.join(config.LOGS_DIR, "login_error.png"))
        raise e

    return page

def handle_post_login_dialogs(page: Page):
    """Cierra los modales molestos de 'Guardar info' y 'Notificaciones'."""
    dialog_keywords = ["Save Info", "Not Now", "Ahora no", "Guardar información"]
    
    # Intentar varias veces porque pueden aparecer en secuencia
    for _ in range(3):
        try:
            # Buscar botones comunes de rechazo
            for text in ["Not Now", "Ahora no"]:
                btn = page.get_by_role("button", name=text)
                if btn.is_visible():
                    btn.click()
                    time.sleep(1)
        except:
            pass
        time.sleep(1)
