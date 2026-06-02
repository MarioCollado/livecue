"""Configuración centralizada de LiveCue."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()


def get_app_data_dir() -> Path:
    """Obtiene el directorio base de la aplicación según el entorno."""

    force_dev = os.environ.get("LIVECUE_DEV_MODE", "").lower() == "true"

    if getattr(sys, "frozen", False) and not force_dev:
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            base = Path(appdata) / "LiveCue"
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / "LiveCue"
        else:
            base = Path.home() / ".local" / "share" / "LiveCue"
    else:
        base = Path(__file__).parent.parent

    base.mkdir(parents=True, exist_ok=True)
    return base


APP_DATA_DIR = get_app_data_dir()

_custom_setlists_dir = os.getenv("SETLISTS_DIR")
if _custom_setlists_dir:
    SETLISTS_DIR = Path(_custom_setlists_dir)
else:
    SETLISTS_DIR = APP_DATA_DIR / "setlist" / "data"
SETLISTS_DIR.mkdir(parents=True, exist_ok=True)

LIVE_IP = os.getenv("LIVE_IP", "127.0.0.1")
LIVE_SEND_PORT = int(os.getenv("LIVE_SEND_PORT", "11000"))
OSC_SEND_PORT = LIVE_SEND_PORT
CLIENT_LISTEN_PORT = int(os.getenv("CLIENT_LISTEN_PORT", "11001"))
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
DEFAULT_WINDOW_WIDTH = int(os.getenv("DEFAULT_WINDOW_WIDTH", "1280"))
DEFAULT_WINDOW_HEIGHT = int(os.getenv("DEFAULT_WINDOW_HEIGHT", "800"))
OSC_TIMEOUT = float(os.getenv("OSC_TIMEOUT", "2.0"))
SCAN_DELAY = float(os.getenv("SCAN_DELAY", "0.1"))

__all__ = [
    "APP_DATA_DIR",
    "CLIENT_LISTEN_PORT",
    "DEFAULT_WINDOW_HEIGHT",
    "DEFAULT_WINDOW_WIDTH",
    "FLASK_PORT",
    "LIVE_IP",
    "LIVE_SEND_PORT",
    "OSC_SEND_PORT",
    "OSC_TIMEOUT",
    "SCAN_DELAY",
    "SETLISTS_DIR",
    "get_app_data_dir",
]
