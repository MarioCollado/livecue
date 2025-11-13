# osc/client.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

from pythonosc import udp_client
from core.constants import LIVE_IP, LIVE_SEND_PORT

client = udp_client.SimpleUDPClient(LIVE_IP, LIVE_SEND_PORT)
print(f"[INIT] ✓ Cliente OSC conectado a {LIVE_IP}:{LIVE_SEND_PORT}")

def send_message(address, args=None):
    if args is None:
        args = []
    try:
        client.send_message(address, args)
    except Exception as e:
        print(f"[OSC CLIENT ERROR] {e}")
