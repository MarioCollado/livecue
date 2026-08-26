"""Gestión de configuraciones persistentes del usuario."""

import json
from pathlib import Path
from core.config import APP_DATA_DIR
from core.logger import log_error, log_info, log_debug

SETTINGS_FILE = APP_DATA_DIR / "settings.json"

def load_settings() -> dict:
    """Carga configuraciones guardadas en settings.json."""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                log_debug(f"Configuraciones cargadas desde {SETTINGS_FILE}: {data}", module="Main")
                return data
    except Exception as e:
        log_error(f"Error al cargar settings.json: {e}", module="Main", exc=e)
    return {}

def save_settings(settings: dict):
    """Guarda o actualiza configuraciones en settings.json."""
    try:
        data = load_settings()
        data.update(settings)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log_debug(f"Configuraciones guardadas en {SETTINGS_FILE}: {settings}", module="Main")
    except Exception as e:
        log_error(f"Error al guardar settings.json: {e}", module="Main", exc=e)
