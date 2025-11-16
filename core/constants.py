# core/constants.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

from pathlib import Path
import sys

LIVE_IP = "127.0.0.1"
LIVE_SEND_PORT = 11000
CLIENT_LISTEN_PORT = 11001


def get_base_dir() -> Path:
    """Devuelve la carpeta base real del programa.
    
    - Si está compilado (Nuitka), usa la carpeta del ejecutable.
    - Si está en modo desarrollo, usa la carpeta del proyecto.
    """
    if getattr(sys, "frozen", False):
        # Ejecutable Nuitka
        return Path(sys.argv[0]).parent
    else:
        # Ejecución normal con Python
        return Path(__file__).parent.parent


# Carpeta donde guardar setlists (universal)
BASE_DIR = get_base_dir()
SETLISTS_DIR = BASE_DIR / "setlist" / "data"

SETLISTS_DIR.mkdir(parents=True, exist_ok=True)

