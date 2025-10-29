# core/playback.py
"""Lógica de reproducción separada de la UI"""
import time
from osc.client import send_message
from core.state import state

class PlaybackController:
    """Controlador de reproducción de Ableton"""
    
    @staticmethod
    def scan_all():
        """Escanea todos los datos de Ableton"""
        send_message("/live/song/get/cue_points", [])
        time.sleep(0.2)
        send_message("/live/track/get/arrangement_clips/name", [0])
        send_message("/live/track/get/arrangement_clips/start_time", [0])
        time.sleep(0.1)
        send_message("/live/song/get/metronome", [])
        send_message("/live/song/get/tempo", [])
        send_message("/live/song/get/is_playing", [])
        send_message("/live/song/start_listen/current_song_time", [])
        send_message("/live/song/start_listen/is_playing", [])
    
    @staticmethod
    def play_track(track_index: int) -> bool:
        """Reproduce un track específico"""
        if not (0 <= track_index < len(state.tracks)):
            return False
        
        track = state.tracks[track_index]
        locator_id = track.start_locator_id
        
        if locator_id is None:
            print("[PLAYBACK] ✗ Track sin locator ID")
            return False
        
        # Secuencia de reproducción
        send_message("/live/song/stop_playing", [])
        time.sleep(0.1)
        send_message("/live/song/cue_point/jump", [locator_id])
        time.sleep(0.1)
        send_message("/live/song/start_playing", [])
        
        state.is_playing = True
        state.current_index = track_index
        return True
    
    @staticmethod
    def stop():
        """Detiene la reproducción"""
        send_message("/live/song/stop_playing", [])
        state.is_playing = False
        
        # Resetear progress bar del track actual
        if state.current_index in state.track_progress_bars:
            state.track_progress_bars[state.current_index].bar.width = 0
    
    @staticmethod
    def jump_to_section(track_index: int, section_index: int) -> bool:
        """Salta a una sección específica"""
        if not (0 <= track_index < len(state.tracks)):
            return False
        
        track = state.tracks[track_index]
        if not (0 <= section_index < len(track.sections)):
            return False
        
        section = track.sections[section_index]
        
        send_message("/live/song/stop_playing", [])
        time.sleep(0.05)
        send_message("/live/song/set/current_song_time", [section.beat])
        time.sleep(0.05)
        send_message("/live/song/start_playing", [])
        
        state.is_playing = True
        return True
    
    @staticmethod
    def toggle_metronome():
        """Alterna el metrónomo"""
        state.metronome_on = not state.metronome_on
        send_message("/live/song/set/metronome", [1 if state.metronome_on else 0])
        return state.metronome_on
    
    @staticmethod
    def next_track() -> bool:
        """Avanza al siguiente track"""
        if state.current_index < len(state.tracks) - 1:
            return PlaybackController.play_track(state.current_index + 1)
        return False
    
    @staticmethod
    def prev_track() -> bool:
        """Retrocede al track anterior"""
        if state.current_index > 0:
            return PlaybackController.play_track(state.current_index - 1)
        return False

# Instancia global
playback = PlaybackController()