# Copyright (c) 2025 Mario Collado Rodríguez - MIT License

# core/playback.py
"""Lógica de reproducción thread-safe"""
import time
import threading
from osc.client import send_message
from core.state import state

class PlaybackController:
    """Controlador de reproducción de Ableton con sincronización"""
    
    def __init__(self):
        self._scan_lock = threading.Lock()
        self._playback_lock = threading.Lock()
        self._last_scan_time = 0
        self._scan_cooldown = 1.0  # Segundos entre scans
    
    def scan_all(self) -> bool:
        """Escanea datos de Ableton - Previene múltiples scans simultáneos"""
        current_time = time.time()
        
        # Prevenir scans muy frecuentes
        if current_time - self._last_scan_time < self._scan_cooldown:
            print(f"[PLAYBACK] ⊘ Scan en cooldown ({self._scan_cooldown}s)")
            return False
        
        with self._scan_lock:
            print("[PLAYBACK] ➤ Iniciando scan completo...")
            
            try:
                # 1. Obtener cue points (estructura principal)
                send_message("/live/song/get/cue_points", [])
                time.sleep(0.3)  # Esperar respuesta
                
                # 2. Obtener clips del arrangement (TRACK 0 solamente)
                # IMPORTANTE: Solo el track 0 existe en Ableton por defecto
                send_message("/live/track/get/arrangement_clips/name", [0])
                time.sleep(0.15)
                
                send_message("/live/track/get/arrangement_clips/start_time", [0])
                time.sleep(0.15)
                
                # 3. Obtener estado de reproducción (sin índices)
                send_message("/live/song/get/metronome", [])
                time.sleep(0.05)
                
                send_message("/live/song/get/tempo", [])
                time.sleep(0.05)
                
                send_message("/live/song/get/is_playing", [])
                time.sleep(0.05)
                
                # 4. Iniciar listeners (sin parámetros de track)
                send_message("/live/song/start_listen/current_song_time", [])
                time.sleep(0.05)
                
                send_message("/live/song/start_listen/is_playing", [])
                time.sleep(0.05)
                
                self._last_scan_time = current_time
                print("[PLAYBACK] ✓ Scan completado")
                return True
                
            except Exception as e:
                print(f"[PLAYBACK] ✗ Error en scan: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def play_track(self, track_index: int) -> bool:
        """Reproduce un track específico - Thread-safe"""
        with self._playback_lock:
            if not (0 <= track_index < len(state.tracks)):
                print(f"[PLAYBACK] ✗ Índice inválido: {track_index}")
                return False
            
            track = state.tracks[track_index]
            locator_id = track.start_locator_id
            
            if locator_id is None:
                print(f"[PLAYBACK] ✗ Track '{track.title}' sin locator ID")
                return False
            
            try:
                print(f"[PLAYBACK] ▶ Reproduciendo: {track.title}")
                
                # Secuencia de reproducción
                send_message("/live/song/stop_playing", [])
                time.sleep(0.08)
                
                send_message("/live/song/cue_point/jump", [locator_id])
                time.sleep(0.08)
                
                send_message("/live/song/start_playing", [])
                
                # Actualizar estado
                state.is_playing = True
                state.current_index = track_index
                                
                return True
                
            except Exception as e:
                print(f"[PLAYBACK] ✗ Error reproduciendo: {e}")
                return False
    
    def stop(self):
        """Detiene la reproducción - Thread-safe"""
        with self._playback_lock:
            try:
                send_message("/live/song/stop_playing", [])
                state.is_playing = False
                print("[PLAYBACK] ■ Stop")
                                            
            except Exception as e:
                print(f"[PLAYBACK] ✗ Error deteniendo: {e}")
    
    def jump_to_section(self, track_index: int, section_index: int) -> bool:
        """Salta a una sección específica - Thread-safe"""
        with self._playback_lock:
            if not (0 <= track_index < len(state.tracks)):
                return False
            
            track = state.tracks[track_index]
            if not (0 <= section_index < len(track.sections)):
                return False
            
            section = track.sections[section_index]
            
            try:
                print(f"[PLAYBACK] ⇒ Saltando a: {section.name}")
                
                send_message("/live/song/stop_playing", [])
                time.sleep(0.05)
                
                send_message("/live/song/set/current_song_time", [section.beat])
                time.sleep(0.05)
                
                send_message("/live/song/start_playing", [])
                
                state.is_playing = True
                state.current_index = track_index
                
                return True
                
            except Exception as e:
                print(f"[PLAYBACK] ✗ Error saltando: {e}")
                return False
    
    def toggle_metronome(self) -> bool:
        """Alterna el metrónomo - Thread-safe"""
        with self._playback_lock:
            try:
                state.metronome_on = not state.metronome_on
                send_message("/live/song/set/metronome", [1 if state.metronome_on else 0])
                print(f"[PLAYBACK] Metrónomo: {'ON' if state.metronome_on else 'OFF'}")
                return state.metronome_on
                
            except Exception as e:
                print(f"[PLAYBACK] ✗ Error toggling metrónomo: {e}")
                return state.metronome_on
    
    def next_track(self) -> bool:
        """Avanza al siguiente track"""
        if state.current_index < len(state.tracks) - 1:
            return self.play_track(state.current_index + 1)
        print("[PLAYBACK] ⊘ Ya en el último track")
        return False
    
    def prev_track(self) -> bool:
        """Retrocede al track anterior"""
        if state.current_index > 0:
            return self.play_track(state.current_index - 1)
        print("[PLAYBACK] ⊘ Ya en el primer track")
        return False
    
# Instancia global
playback = PlaybackController()