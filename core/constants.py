# core/constants.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
"""Constantes globales de LiveCue"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

def get_app_data_dir() -> Path:
    """Obtiene el directorio base de la aplicación según el entorno"""
    
    # Modo forzado por variable de entorno
    force_dev = os.environ.get('LIVECUE_DEV_MODE', '').lower() == 'true'
    
    # Si es ejecutable Y NO está en modo dev forzado, usar AppData
    if getattr(sys, 'frozen', False) and not force_dev:
        if sys.platform == 'win32':
            # Windows: %APPDATA%\LiveCue
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            base = Path(appdata) / 'LiveCue'
        elif sys.platform == 'darwin':
            # macOS: ~/Library/Application Support/LiveCue
            base = Path.home() / 'Library' / 'Application Support' / 'LiveCue'
        else:
            # Linux: ~/.local/share/LiveCue
            base = Path.home() / '.local' / 'share' / 'LiveCue'
    else:
        # Modo desarrollo: carpeta local del proyecto
        base = Path(__file__).parent.parent  # Sube dos niveles desde core/constants.py
    
    # Crear directorio si no existe
    base.mkdir(parents=True, exist_ok=True)
    return base

# Directorio base de la aplicación
APP_DATA_DIR = get_app_data_dir()

# Directorio de setlists - permite override desde .env
_custom_setlists_dir = os.getenv('SETLISTS_DIR')
if _custom_setlists_dir:
    SETLISTS_DIR = Path(_custom_setlists_dir)
else:
    SETLISTS_DIR = APP_DATA_DIR / "setlist" / "data"
SETLISTS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de red - lee desde .env con valores por defecto
LIVE_IP = os.getenv('LIVE_IP', '127.0.0.1')
LIVE_SEND_PORT = int(os.getenv('LIVE_SEND_PORT', '11000'))

# Puertos OSC
OSC_SEND_PORT = LIVE_SEND_PORT  # Alias de LIVE_SEND_PORT
CLIENT_LISTEN_PORT = int(os.getenv('CLIENT_LISTEN_PORT', '11001'))

# Puerto Flask para control remoto
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# Configuración de UI
DEFAULT_WINDOW_WIDTH = int(os.getenv('DEFAULT_WINDOW_WIDTH', '1280'))
DEFAULT_WINDOW_HEIGHT = int(os.getenv('DEFAULT_WINDOW_HEIGHT', '800'))

# Timeouts y delays
OSC_TIMEOUT = float(os.getenv('OSC_TIMEOUT', '2.0'))
SCAN_DELAY = float(os.getenv('SCAN_DELAY', '0.1'))