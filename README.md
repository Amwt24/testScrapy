# Ig_ScrapingV4 📸

Un scraper de Instagram moderno, modular y robusto desarrollado en Python utilizando **Playwright**. Diseñado para extraer listas de seguidores (Followers) y seguidos (Following) simulando comportamiento humano para minimizar riesgos de bloqueo.

## 🚀 Características

*   **Tecnología Playwright:** Más rápido y fiable que Selenium.
*   **Persistencia de Sesión:** Guarda las cookies y el estado de la sesión (`logs/session_cookies.json`) para evitar iniciar sesión manualmente en cada ejecución.
*   **Comportamiento Humano:** 
    *   Usa delays aleatorios.
    *   Simula el scroll usando la rueda del ratón (no scripts invasivos).
    *   Escribe texto caracter por caracter.
*   **Arquitectura Modular:** Código limpio y fácil de mantener (`src/`).
*   **Doble Extracción:** Configurable para extraer Followers, Following o ambos.

## 📋 Requisitos

*   Python 3.8+
*   Cuenta de Instagram (preferiblemente una cuenta secundaria para evitar riesgos).

## 🛠️ Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/Ig_ScrapingV4.git
    cd Ig_ScrapingV4
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Instalar navegadores de Playwright:**
    ```bash
    playwright install chromium
    ```

4.  **Configurar variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto (basado en el ejemplo):
    ```ini
    IG_USERNAME=tu_usuario
    IG_PASSWORD=tu_contraseña
    TARGET_ACCOUNT=cuenta_objetivo
    
    # Configuración de Scrapeo
    EXTRACT_FOLLOWERS=true
    EXTRACT_FOLLOWING=true
    
    # Límites de seguridad
    MAX_FOLLOWERS=1000
    MAX_FOLLOWING=1000
    ```

## ▶️ Uso

Simplemente ejecuta el archivo principal:

```bash
python main.py
```

### Funcionamiento:
1.  **Primera vez:** Se abrirá el navegador y verás como el bot inicia sesión. Si aparece algún captcha o verificación de dos pasos, puedes intervenir manualmente en la ventana del navegador.
2.  **Siguientes veces:** El bot detectará el archivo de sesión y entrará directamente al perfil objetivo.
3.  **Resultados:** Los archivos CSV se guardarán automáticamente en la carpeta `data/`.

## 📁 Estructura del Proyecto

```text
Ig_ScrapingV4/
├── data/             # Archivos CSV generados
├── logs/             # Logs de ejecución y cookies de sesión (ignorado en git)
├── src/              # Código fuente modular
│   ├── auth.py       # Lógica de login y sesión
│   ├── scraper.py    # Lógica de extracción (scroll, parsing)
│   ├── config.py     # Configuración centralizada
│   └── utils.py      # Utilidades (logger, delays)
├── main.py           # Punto de entrada
└── requirements.txt  # Dependencias
```

## ⚠️ Disclaimer

Este software es únicamente para **fines educativos y de investigación**. El uso de bots automatizados puede violar los Términos de Servicio de Instagram. Úsalo bajo tu propia responsabilidad. Se recomienda usar cuentas de prueba y establecer límites moderados de extracción (`MAX_FOLLOWERS`).
