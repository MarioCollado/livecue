# osc/client.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

"""Cliente OSC para enviar mensajes a Ableton Live"""

from pythonosc import udp_client
from core.constants import LIVE_IP, LIVE_SEND_PORT
from core.logger import log_info, log_error, log_debug

# Crear cliente OSC
try:
    client = udp_client.SimpleUDPClient(LIVE_IP, LIVE_SEND_PORT)
    log_info(f"✓ Cliente OSC conectado a {LIVE_IP}:{LIVE_SEND_PORT}", module="OSC")
except Exception as e:
    log_error(f"Error creando cliente OSC", module="OSC", exc=e)
    raise

def send_message(address, args=None):
    """Envía un mensaje OSC a Ableton Live"""
    if args is None:
        args = []
    
    try:
        client.send_message(address, args)
        
        # Log solo mensajes importantes (no beats/time para evitar spam)
        if not any(x in address for x in ["current_song_time", "get/beat", "is_playing"]):
            if args:
                log_debug(f"→ {address} {args}", module="OSC")
            else:
                log_debug(f"→ {address}", module="OSC")
                
    except Exception as e:
        log_error(f"Error enviando OSC: {address}", module="OSC", exc=e)