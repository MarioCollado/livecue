# Copyright (c) 2025 Mario Collado Rodríguez - MIT License

# core/utils.py
import time
import json
import traceback

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
    traceback.print_exc()
    print(f"[{prefix}] excepción impresa arriba")
