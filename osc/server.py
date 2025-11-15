# osc/server.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

"""
Servidor OSC para comunicación con Ableton Live
Escucha mensajes OSC en CLIENT_LISTEN_PORT y los enruta a los handlers correspondientes
"""

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from core.constants import CLIENT_LISTEN_PORT
from osc.handlers import handlers
from core.logger import log_info, log_error, log_warning, log_debug

def create_server():
    """Crea y configura el servidor OSC"""
    log_debug("Creando dispatcher OSC...", module="OSC")
    dispatcher = Dispatcher()
    
    # Mapeo de rutas a handlers
    routes = {
        "/live/song/get/cue_points": handlers.handle_cue_points,
        "/live/song/get/metronome": handlers.handle_metronome,
        "/live/song/get/beat": handlers.handle_song_time,
        "/live/song/get/current_song_time": handlers.handle_song_time,
        "/live/song/current_song_time": handlers.handle_song_time,
        "/live/song/get/tempo": handlers.handle_tempo,
        "/live/song/get/time_signature": handlers.handle_time_signature,
        "/live/song/get/is_playing": handlers.handle_playing_status,
        "/live/song/is_playing": handlers.handle_playing_status,
        "/live/track/get/arrangement_clips/name": handlers.handle_clip_names,
        "/live/track/get/arrangement_clips/start_time": handlers.handle_clip_times,
    }
    
    log_debug(f"Registrando {len(routes)} rutas OSC...", module="OSC")
    
    # Registrar rutas
    for route, handler in routes.items():
        dispatcher.map(route, handler)
        log_debug(f"✓ Ruta mapeada: {route}", module="OSC")
    
    # Handler por defecto para errores y mensajes no mapeados
    dispatcher.set_default_handler(handlers.handle_error)
    log_debug("✓ Handler por defecto configurado", module="OSC")
    
    try:
        log_info(f"🌐 Creando servidor OSC en 0.0.0.0:{CLIENT_LISTEN_PORT}...", module="OSC")
        server = ThreadingOSCUDPServer(("0.0.0.0", CLIENT_LISTEN_PORT), dispatcher)
        log_info(f"✓ Servidor OSC escuchando en puerto {CLIENT_LISTEN_PORT}", module="OSC")
        return server
        
    except OSError as e:
        if e.errno == 10048 or "address already in use" in str(e).lower():
            log_error(f"Puerto {CLIENT_LISTEN_PORT} ya está en uso", module="OSC", exc=e)
            raise
        else:
            log_error(f"Error creando servidor OSC", module="OSC", exc=e)
            raise
    except Exception as e:
        log_error("Error inesperado creando servidor OSC", module="OSC", exc=e)
        raise