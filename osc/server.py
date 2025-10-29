# osc/server.py
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from core.constants import CLIENT_LISTEN_PORT
from osc.handlers import handlers

def create_server():
    """Crea y configura el servidor OSC"""
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
    
    # Registrar rutas
    for route, handler in routes.items():
        dispatcher.map(route, handler)
    
    # Handler por defecto para errores
    dispatcher.set_default_handler(handlers.handle_error)
    
    server = ThreadingOSCUDPServer(("0.0.0.0", CLIENT_LISTEN_PORT), dispatcher)
    print(f"[OSC SERVER] ✓ Escuchando en puerto {CLIENT_LISTEN_PORT}")
    return server