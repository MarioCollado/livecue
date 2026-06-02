# osc/client.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

"""Cliente OSC para enviar mensajes a Ableton Live"""

from core.constants import LIVE_IP, LIVE_SEND_PORT
from core.logger import log_debug, log_error, log_info, log_warning

try:
    from pythonosc import udp_client
except ImportError:
    udp_client = None


if udp_client is not None:
    try:
        client = udp_client.SimpleUDPClient(LIVE_IP, LIVE_SEND_PORT)
        log_info(f"✓ Cliente OSC conectado a {LIVE_IP}:{LIVE_SEND_PORT}", module="OSC")
    except Exception as e:
        log_error("Error creando cliente OSC", module="OSC", exc=e)
        raise
else:
    class _FallbackOSCClient:
        def send_message(self, address, args):
            return None

    client = _FallbackOSCClient()
    log_warning("python-osc no está instalado; se usará un cliente OSC inactivo.", module="OSC")


def send_message(address, args=None):
    """Envía un mensaje OSC a Ableton Live."""

    if args is None:
        args = []

    try:
        client.send_message(address, args)

        if not any(x in address for x in ["current_song_time", "get/beat", "is_playing"]):
            if args:
                log_debug(f"→ {address} {args}", module="OSC")
            else:
                log_debug(f"→ {address}", module="OSC")

    except Exception as e:
        log_error(f"Error enviando OSC: {address}", module="OSC", exc=e)
