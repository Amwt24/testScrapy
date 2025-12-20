import os
from dotenv import load_dotenv, find_dotenv

# Cargar variables de entorno
load_dotenv(find_dotenv())

# Credenciales
USERNAME = os.getenv("IG_USERNAME", "").strip()
PASSWORD = os.getenv("IG_PASSWORD", "").strip()

# Configuración del Objetivo
TARGET_ACCOUNT = os.getenv("TARGET_ACCOUNT", "").strip()

# Configuración de Extracción
EXTRACT_FOLLOWERS = os.getenv("EXTRACT_FOLLOWERS", "false").lower() == "true"
EXTRACT_FOLLOWING = os.getenv("EXTRACT_FOLLOWING", "true").lower() == "true"

try:
    MAX_FOLLOWERS = int(os.getenv("MAX_FOLLOWERS", "100"))
    MAX_FOLLOWING = int(os.getenv("MAX_FOLLOWING", "50000"))
except ValueError:
    MAX_FOLLOWERS = 100
    MAX_FOLLOWING = 50000

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SESSION_FILE = os.path.join(LOGS_DIR, "session_cookies.json")

# Asegurar directorios
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
