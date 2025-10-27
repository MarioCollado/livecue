# osc/server.py
import threading
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from core.constants import CLIENT_LISTEN_PORT
import osc.handlers as handlers

def create_server():
    dispatcher = Dispatcher()

    # Mapear mensajes OSC
    dispatcher.map("/live/song/get/cue_points", handlers.cue_handler)
    dispatcher.map("/live/song/get/metronome", handlers.metronome_state_handler)
    dispatcher.map("/live/song/get/beat", handlers.beat_handler)
    
    # IMPORTANTE: Los listeners envían datos sin el "get"
    dispatcher.map("/live/song/get/current_song_time", handlers.song_time_handler)
    dispatcher.map("/live/song/current_song_time", handlers.song_time_handler)  # Listener
    
    dispatcher.map("/live/song/get/tempo", handlers.tempo_handler)
    dispatcher.map("/live/song/get/time_signature", handlers.time_signature_handler)
    
    dispatcher.map("/live/song/get/is_playing", handlers.is_playing_handler)
    dispatcher.map("/live/song/is_playing", handlers.is_playing_handler)  # Listener
    
    dispatcher.set_default_handler(handlers.catch_all_handler)
    dispatcher.map("/live/track/get/arrangement_clips/name", handlers.handle_track_arrangement_clips_name)
    dispatcher.map("/live/track/get/arrangement_clips/start_time", handlers.handle_track_arrangement_clips_start_time)

    server = ThreadingOSCUDPServer(("0.0.0.0", CLIENT_LISTEN_PORT), dispatcher)
    print(f"[OSC SERVER] ✓ Escuchando en puerto {CLIENT_LISTEN_PORT}")
    return server