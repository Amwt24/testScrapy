import logging
import os
import random
import time
from datetime import datetime
from . import config

# Definir nivel SUCCESS
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)

logging.Logger.success = success

def setup_logger(name="IgScraper"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger

    # Formato
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S')

    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(config.LOGS_DIR, f"run_{timestamp}.log")
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def human_delay(min_sec=1.0, max_sec=3.0):
    """Espera un tiempo aleatorio para simular comportamiento humano."""
    time.sleep(random.uniform(min_sec, max_sec))

def type_like_human(page, selector, text):
    """Escribe texto caracter por caracter con delay variable."""
    page.focus(selector)
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.05, 0.15))
