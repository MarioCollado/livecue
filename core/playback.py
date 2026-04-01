# core/playback.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import time
import threading
from osc.client import send_message
from core.state import state
from core.logger import log_info, log_error, log_warning, log_debug

"""Lógica de reproducción thread-safe"""
class PlaybackController:
    """Controlador de reproducción de Ableton con sincronización"""
    
    def __init__(self):
        self._scan_lock = threading.Lock()
        self._playback_lock = threading.Lock()
        self._last_scan_time = 0
        self._scan_cooldown = 1.0  # Segundos entre scans
        log_debug("PlaybackController inicializado", module="Playback")
    
    def scan_all(self) -> bool:
        """Escanea datos de Ableton - Previene múltiples scans simultáneos"""
        current_time = time.time()
        
        # Prevenir scans muy frecuentes
        if current_time - self._last_scan_time < self._scan_cooldown:
            log_warning(f"⊘ Scan en cooldown ({self._scan_cooldown}s)", module="Playback")
            return False
        
        with self._scan_lock:
            log_info("⟳ Iniciando scan completo...", module="Playback")
            
            try:
                # 1. Obtener cue points (estructura principal)
                log_debug("Solicitando cue points", module="Playback")
                send_message("/live/song/get/cue_points", [])
                time.sleep(0.3)  # Esperar respuesta
                
                # 2. Obtener clips del arrangement (TRACK 0 solamente)
                # IMPORTANTE: Solo el track 0 existe en Ableton por defecto
                log_debug("Solicitando clips del track 0", module="Playback")
                send_message("/live/track/get/arrangement_clips/name", [0])
                time.sleep(0.15)
                
                send_message("/live/track/get/arrangement_clips/start_time", [0])
                time.sleep(0.15)
                
                # 3. Obtener estado de reproducción (sin índices)
                log_debug("Solicitando estado de reproducción", module="Playback")
                send_message("/live/song/get/metronome", [])
                time.sleep(0.05)
                
                send_message("/live/song/get/tempo", [])
                time.sleep(0.05)
                
                send_message("/live/song/get/is_playing", [])
                time.sleep(0.05)
                
                # 4. Iniciar listeners (sin parámetros de track)
                log_debug("Iniciando listeners OSC", module="Playback")
                send_message("/live/song/start_listen/current_song_time", [])
                time.sleep(0.05)
                
                send_message("/live/song/start_listen/is_playing", [])
                time.sleep(0.05)
                
                self._last_scan_time = current_time
                
                # 5. 🆕 DETECTAR TEMPO DE CADA TRACK
                log_debug("Detectando tempo de cada track...", module="Playback")
                self._scan_track_tempos()
                
                log_info("✓ Scan completado correctamente", module="Playback")
                return True
                
            except Exception as e:
                log_error(f"Error en scan", module="Playback", exc=e)
                return False
    
    def _scan_track_tempos(self):
        """
        Detecta el tempo de cada track saltando a su locator inicial.
        IMPORTANTE: Solo funciona si Ableton tiene automation de tempo.
        """
        from core.state import state
        
        if not state.tracks:
            return
        
        log_debug(f"Escaneando tempo de {len(state.tracks)} tracks...", module="Playback")
        
        for track in state.tracks:
            if track.start_locator_id is None:
                continue
            
            try:
                # Saltar al locator del track
                send_message("/live/song/cue_point/jump", [track.start_locator_id])
                time.sleep(0.2)  # Esperar a que Ableton salte
                
                # Pedir el tempo en ese punto
                send_message("/live/song/get/tempo", [])
                time.sleep(0.15)  # Esperar respuesta
                
                # El tempo se actualizará en state.current_tempo vía OSC
                track.bpm = state.current_tempo
                log_debug(f"Track '{track.title}': {track.bpm:.1f} BPM", module="Playback")
                
            except Exception as e:
                log_error(f"Error detectando tempo de '{track.title}'", module="Playback", exc=e)
    
    def play_track(self, track_index: int) -> bool:
        """Reproduce un track específico - Thread-safe"""
        with self._playback_lock:
            if not (0 <= track_index < len(state.tracks)):
                log_error(f"Índice inválido: {track_index}", module="Playback")
                return False
            
            track = state.tracks[track_index]
            locator_id = track.start_locator_id
            
            if locator_id is None:
                log_error(f"Track '{track.title}' sin locator ID", module="Playback")
                return False
            
            try:
                log_info(f"▶ Reproduciendo: {track.title}", module="Playback")
                log_debug(f"Track index: {track_index}, Locator ID: {locator_id}", module="Playback")
                
                # 🆕 STOP AGRESIVO primero para limpiar cualquier reproducción
                self._force_stop_internal()
                time.sleep(0.12)  # Pausa más larga para asegurar stop completo
                
                # Secuencia de reproducción
                send_message("/live/song/cue_point/jump", [locator_id])
                time.sleep(0.1)
                
                send_message("/live/song/start_playing", [])
                
                # Actualizar estado
                state.is_playing = True
                state.current_index = track_index
                
                log_debug(f"Estado actualizado: is_playing=True, current_index={track_index}", module="Playback")
                return True
                
            except Exception as e:
                log_error(f"Error reproduciendo track '{track.title}'", module="Playback", exc=e)
                return False
    
    def _force_stop_internal(self):
        """Stop interno más agresivo - NO usa lock (llamado desde dentro de lock)"""
        try:
            # Enviar stop múltiples veces para asegurar
            for _ in range(2):
                send_message("/live/song/stop_playing", [])
                time.sleep(0.03)
            
            log_debug("Stop interno forzado", module="Playback")
        except Exception as e:
            log_error("Error en stop interno", module="Playback", exc=e)
    
    def stop(self):
        """Detiene la reproducción - Thread-safe con stop agresivo"""
        with self._playback_lock:
            try:
                log_info("■ Deteniendo reproducción...", module="Playback")
                
                # 🆕 STOP MÚLTIPLE para asegurar que mata todo
                for i in range(2):
                    send_message("/live/song/stop_playing", [])
                    time.sleep(0.05)
                    log_debug(f"Stop enviado ({i+1}/2)", module="Playback")
                
                # Actualizar estado
                state.is_playing = False
                
                log_info("■ Reproducción detenida", module="Playback")
                                            
            except Exception as e:
                log_error("Error deteniendo reproducción", module="Playback", exc=e)
    
    def jump_to_section(self, track_index: int, section_index: int) -> bool:
        """Salta a una sección específica y reproduce desde ahí - Thread-safe"""
        with self._playback_lock:
            if not (0 <= track_index < len(state.tracks)):
                log_error(f"Índice de track inválido: {track_index}", module="Playback")
                return False
            
            track = state.tracks[track_index]
            if not (0 <= section_index < len(track.sections)):
                log_error(f"Índice de sección inválido: {section_index}", module="Playback")
                return False
            
            section = track.sections[section_index]
            
            try:
                log_info(f"⇒ Saltando a: {section.name} (beat {section.beat})", module="Playback")
                log_debug(f"Track: {track.title}, Section: {section.name}, is_playing={state.is_playing}", module="Playback")
                
                # CRÍTICO: Primero posicionar el cursor
                send_message("/live/song/set/current_song_time", [section.beat])
                time.sleep(0.15)  # Delay aumentado para asegurar que Ableton procesa
                
                # SOLUCIÓN: Decidir según el estado actual
                if state.is_playing:
                    # Si está reproduciendo, usar continue para no interrumpir
                    log_debug("Estado: reproduciendo → usando continue_playing", module="Playback")
                    send_message("/live/song/continue_playing", [])
                else:
                    # Si está parado, DEBE usar start_playing
                    log_debug("Estado: parado → usando start_playing", module="Playback")
                    send_message("/live/song/start_playing", [])
                
                time.sleep(0.05)
                
                state.is_playing = True
                state.current_index = track_index
                
                log_debug(f"Salto completado: current_index={track_index}, beat={section.beat}", module="Playback")
                return True
                
            except Exception as e:
                log_error(f"Error saltando a sección '{section.name}'", module="Playback", exc=e)
                return False
                    
    def toggle_metronome(self) -> bool:
        """Alterna el metrónomo - Thread-safe"""
        with self._playback_lock:
            try:
                state.metronome_on = not state.metronome_on
                send_message("/live/song/set/metronome", [1 if state.metronome_on else 0])
                log_info(f"🎵 Metrónomo: {'ON' if state.metronome_on else 'OFF'}", module="Playback")
                return state.metronome_on
                
            except Exception as e:
                log_error("Error toggling metrónomo", module="Playback", exc=e)
                return state.metronome_on
    
    def next_track(self) -> bool:
        """Avanza al siguiente track"""
        if state.current_index < len(state.tracks) - 1:
            log_debug(f"Next track: {state.current_index} → {state.current_index + 1}", module="Playback")
            return self.play_track(state.current_index + 1)
        log_warning("⊘ Ya en el último track", module="Playback")
        return False
    
    def prev_track(self) -> bool:
        """Retrocede al track anterior"""
        if state.current_index > 0:
            log_debug(f"Previous track: {state.current_index} → {state.current_index - 1}", module="Playback")
            return self.play_track(state.current_index - 1)
        log_warning("⊘ Ya en el primer track", module="Playback")
        return False
    
# Instancia global
playback = PlaybackController()
log_info("✓ Instancia global de PlaybackController creada", module="Playback")