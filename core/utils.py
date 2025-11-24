# core/utils.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import time
import json
import traceback
from core.logger import log_error

def sanitize_filename(name: str) -> str:
    """Sanitiza un nombre para usar como filename (alfa-numérico, espacio, -, _)."""
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe_name:
        safe_name = "setlist"
    return safe_name

def pretty_json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)

def log_exc(prefix="ERROR"):
    import traceback
    # Capturar la excepción actual
    try:
        raise Exception("Capturing stack")
    except:
        # Esto es un hack si no se pasa la excepción, pero idealmente log_exc debería recibir la excepción.
        # Sin embargo, para mantener compatibilidad:
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_value:
            log_error(f"[{prefix}] {exc_value}", "UTILS", exc_value)
        else:
            log_error(f"[{prefix}] Unknown exception", "UTILS")
