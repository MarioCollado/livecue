# Copyright (c) 2025 Mario Collado Rodríguez - MIT License

# core/constants.py
from pathlib import Path

LIVE_IP = "127.0.0.1"
LIVE_SEND_PORT = 11000
CLIENT_LISTEN_PORT = 11001

# Directorio para setlists
SETLISTS_DIR = Path(r"C:\Users\mario\Desktop\CUELIST_ABLETON_SETLIST\LIVECUE APP\setlist\data")
SETLISTS_DIR.mkdir(parents=True, exist_ok=True)
