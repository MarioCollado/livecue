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
    dispatcher.map("/live/song/set/metronome", handlers.metronome_state_handler)
    dispatcher.map("/live/song/get/beat", handlers.beat_handler)
    dispatcher.map("/live/song/get/current_song_time", handlers.song_time_handler)
    dispatcher.map("/live/song/get/playing_status", handlers.playing_status_handler)
    dispatcher.map("/live/song/get/tempo", handlers.tempo_handler)
    dispatcher.map("/live/song/get/time_signature", handlers.time_signature_handler)
    dispatcher.set_default_handler(handlers.catch_all_handler)

    server = ThreadingOSCUDPServer(("0.0.0.0", CLIENT_LISTEN_PORT), dispatcher)
    return server
