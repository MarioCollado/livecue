# osc/handlers.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

from core.state import state, Locator, Track, Section
from osc.client import send_message
from core.logger import log_info, log_error, log_warning, log_debug
import threading
import time
from typing import Dict, List, Optional

class OSCHandlers:
    """Manejadores OSC con sincronización thread-safe"""
    
    def __init__(self):
        self._clip_data: Dict[int, Dict] = {}
        self._lock = threading.RLock()  # Lock para sincronización
        self._processing_cue_points = False
        self._processing_clips = False
        self._clip_timestamps: Dict[str, float] = {}  # Timestamps para clips
        self._clip_timeout = 1.0  # Timeout de 1 segundo
        log_debug("OSCHandlers inicializado", module="OSC")
    
    def handle_cue_points(self, address, *args):
        """Procesa cue points - Thread-safe"""
        with self._lock:
            if self._processing_cue_points:
                log_warning("Ya procesando cue points, ignorando duplicado", module="OSC")
                return
            
            self._processing_cue_points = True
        
        try:
            log_info(f"📥 Cue points recibidos: {len(args)//2} locators", module="OSC")
            
            # Parsear locators
            raw_locators = []
            for i in range(0, len(args), 2):
                try:
                    raw_locators.append(Locator(
                        id=i // 2,
                        original_id=i // 2,
                        name=args[i].strip(),
                        beat=args[i + 1]
                    ))
                except Exception as e:
                    log_error(f"Error procesando locator {i//2}", module="OSC", exc=e)
                    continue
            
            if not raw_locators:
                log_warning("No se procesaron locators válidos", module="OSC")
                return
            
            # Ordenar y reasignar IDs
            raw_locators.sort(key=lambda x: x.beat)
            for i, loc in enumerate(raw_locators):
                loc.id = i
            
            log_debug(f"Locators ordenados y reasignados: {len(raw_locators)}", module="OSC")
            
            with self._lock:
                state.locators = raw_locators
                self._build_track_structure(raw_locators)
            
            # Actualizar UI de forma segura
            self._safe_ui_update('update_listbox')
            
        except Exception as e:
            log_error("Error en handle_cue_points", module="OSC", exc=e)
        finally:
            with self._lock:
                self._processing_cue_points = False
    
    def _build_track_structure(self, locators: List[Locator]):
        """Construye estructura de tracks - Debe llamarse con lock"""
        log_debug("Construyendo estructura de tracks...", module="OSC")
        
        new_tracks = []
        current_track = None
        track_number = 0
        
        for loc in locators:
            name_upper = loc.name.upper()
            
            if name_upper.startswith("START TRACK"):
                # Cerrar track anterior
                if current_track:
                    log_warning(f"Track '{current_track.title}' sin END TRACK", module="OSC")
                    current_track.end = loc.beat
                    new_tracks.append(current_track)
                
                # Extraer título
                title = "Untitled"
                if '"' in loc.name:
                    parts = loc.name.split('"')
                    if len(parts) >= 2:
                        title = parts[1].strip()
                
                track_number += 1
                current_track = Track(
                    title=title,
                    start=loc.beat,
                    end=0,
                    track_number=track_number,
                    start_locator_id=loc.original_id
                    # bpm se detectará después en _scan_track_tempos()
                )
                log_debug(f"Track #{track_number}: '{title}' @ beat {loc.beat}", module="OSC")
            
            elif name_upper.startswith("END TRACK"):
                if current_track:
                    current_track.end = loc.beat
                    new_tracks.append(current_track)
                    log_debug(f"✓ Track completado: '{current_track.title}' ({current_track.end - current_track.start} beats)", module="OSC")
                    current_track = None
            
            elif current_track and not loc.is_click_toggle:
                # Agregar como sección
                section = Section(name=loc.name.title(), beat=loc.beat)
                current_track.add_section(section)
                log_debug(f"Sección agregada: '{section.name}' a '{current_track.title}'", module="OSC")
        
        # Cerrar último track
        if current_track:
            last_beat = locators[-1].beat if locators else 0
            current_track.end = last_beat
            new_tracks.append(current_track)
            log_warning(f"Track '{current_track.title}' cerrado automáticamente (sin END TRACK)", module="OSC")
        
        # Actualizar state de forma atómica
        state.tracks = new_tracks
        log_info(f"✓ Estructura construida: {len(new_tracks)} tracks detectados", module="OSC")
        
        # Ajustar current_index si es necesario
        if state.current_index >= len(new_tracks):
            old_index = state.current_index
            state.current_index = len(new_tracks) - 1 if new_tracks else -1
            log_debug(f"current_index ajustado: {old_index} → {state.current_index}", module="OSC")
    
    def handle_metronome(self, address, *args):
        """Maneja estado del metrónomo"""
        if args:
            with self._lock:
                state.metronome_on = bool(int(args[0]))
            log_info(f"🎵 Metrónomo: {'ON' if state.metronome_on else 'OFF'}", module="OSC")
            self._safe_ui_update('update_metronome_ui')
    
    def handle_song_time(self, address, *args):
        """Maneja el tiempo de canción - Optimizado"""
        if not args:
            return
        
        current_beat = int(args[0])
        
        with self._lock:
            # Evitar disparos duplicados
            if state.last_triggered_beat == current_beat:
                return
            state.last_triggered_beat = current_beat
            state.current_song_time = args[0]
        
        # Log solo cada 4 beats para no saturar
        if current_beat % 4 == 0:
            log_debug(f"Beat: {current_beat}", module="OSC")
        
        # Actualizar UI (trigger_pulse y progress son thread-safe)
        self._safe_ui_update('trigger_pulse', current_beat)
    
    def handle_playing_status(self, address, *args):
        """Maneja el estado de reproducción"""
        if args:
            new_status = bool(int(args[0]))
            with self._lock:
                old_status = state.is_playing
                state.is_playing = new_status
            
            # Log solo si cambió
            if old_status != new_status:
                log_info(f"🎮 Estado: {'▶ Playing' if new_status else '■ Stopped'}", module="OSC")
    
    def handle_tempo(self, address, *args):
        """Maneja cambios de tempo"""
        if args:
            new_tempo = float(args[0])
            with self._lock:
                old_tempo = state.current_tempo
                state.current_tempo = new_tempo
            
            # Log solo si cambió significativamente
            if abs(new_tempo - old_tempo) > 0.1:
                log_info(f"🎼 Tempo: {new_tempo:.1f} BPM", module="OSC")
            
            self._safe_ui_update('update_tempo_display')
    
    def handle_time_signature(self, address, *args):
        """Maneja cambios de time signature"""
        if args:
            new_sig = int(args[0])
            with self._lock:
                old_sig = state.time_signature_num
                state.time_signature_num = new_sig
            
            # Log solo si cambió
            if new_sig != old_sig:
                log_info(f"🎵 Time signature: {new_sig}/4", module="OSC")
            
            self._safe_ui_update('update_tempo_display')
    
    def handle_beat(self, address, *args):
        """Maneja el beat actual (método alternativo)"""
        if args:
            current_beat = int(args[0])
            with self._lock:
                state.current_beat = current_beat
            
            # Log reducido para evitar spam
            if current_beat % 8 == 0:
                log_debug(f"Beat actualizado: {current_beat}", module="OSC")
            
            self._safe_ui_update('trigger_pulse', current_beat)
    
    def handle_clip_names(self, address, *args):
        """Maneja nombres de clips"""
        if len(args) < 2:
            log_warning("handle_clip_names: datos insuficientes", module="OSC")
            return
        
        track_index = args[0]
        clip_names = [n for n in args[1:] if n and str(n).lower() != "none"]
        
        # DEBUG: Ver datos crudos
        log_debug(f"📋 RAW nombres ({len(args[1:])}): {args[1:][:5]}...", module="OSC")
        
        with self._lock:
            self._clip_data.setdefault(track_index, {})["names"] = clip_names
            self._clip_timestamps[f"names_{track_index}"] = time.time()
            log_info(f"📋 Clips recibidos: {len(clip_names)} nombres para track {track_index}", module="OSC")
        
        self._try_assign_clips(track_index)
    
    def handle_clip_times(self, address, *args):
        """Maneja tiempos de clips"""
        if len(args) < 2:
            log_warning("handle_clip_times: datos insuficientes", module="OSC")
            return
        
        track_index = args[0]
        clip_times = [float(t) for t in args[1:]]
        
        # DEBUG: Ver datos crudos
        log_debug(f"⏱️  RAW tiempos ({len(clip_times)}): {clip_times[:5]}...", module="OSC")
        
        with self._lock:
            self._clip_data.setdefault(track_index, {})["times"] = clip_times
            self._clip_timestamps[f"times_{track_index}"] = time.time()
            log_info(f"⏱️  Clips recibidos: {len(clip_times)} tiempos para track {track_index}", module="OSC")
        
        self._try_assign_clips(track_index)
    
    def _try_assign_clips(self, track_index: int):
        """Intenta asignar clips si hay datos completos - Thread-safe"""
        with self._lock:
            if self._processing_clips:
                log_warning("Ya procesando clips, ignorando duplicado", module="OSC")
                return
            
            data = self._clip_data.get(track_index, {})
            names = data.get("names")
            times = data.get("times")
            
            if not names or not times:
                log_debug(f"Datos incompletos para track {track_index} (esperando más datos)", module="OSC")
                return
            
            # Verificar que ambos datos sean recientes
            names_time = self._clip_timestamps.get(f"names_{track_index}", 0)
            times_time = self._clip_timestamps.get(f"times_{track_index}", 0)
            current_time = time.time()
            
            # Si alguno es muy viejo, descartarlo
            if (current_time - names_time) > self._clip_timeout or \
               (current_time - times_time) > self._clip_timeout:
                log_warning(
                    f"⏰ Datos de clips obsoletos para track {track_index}, descartando",
                    module="OSC"
                )
                self._clip_data[track_index] = {}
                return
            
            # EMPAREJAMIENTO INTELIGENTE: No hacer return si hay desajuste
            if len(names) != len(times):
                min_length = min(len(names), len(times))
                log_warning(
                    f"⚠️  Desajuste de clips: {len(names)} nombres vs {len(times)} tiempos "
                    f"- emparejando los primeros {min_length}",
                    module="OSC"
                )
                # Recortar al tamaño mínimo
                names = names[:min_length]
                times = times[:min_length]
            
            self._processing_clips = True
        
        try:
            self._assign_clips_to_tracks(names, times, track_index)
        except Exception as e:
            log_error("Error asignando clips a tracks", module="OSC", exc=e)
        finally:
            with self._lock:
                self._processing_clips = False
                # Limpiar datos después de procesar
                if track_index in self._clip_data:
                    self._clip_data[track_index] = {}
                # Limpiar timestamps
                self._clip_timestamps.pop(f"names_{track_index}", None)
                self._clip_timestamps.pop(f"times_{track_index}", None)
    
    def _assign_clips_to_tracks(self, names: List[str], times: List[float], source_track_index: int):
        """Asigna clips a tracks - NO limpia secciones existentes"""
        with self._lock:
            if not state.tracks:
                log_warning("No hay tracks disponibles para asignar clips", module="OSC")
                return
            
            log_info(f"🔗 Asignando {len(names)} clips del track {source_track_index}", module="OSC")
            
            assigned_count = 0
            skipped_count = 0
            
            for name, time_val in zip(names, times):
                track = state.find_track_by_beat(float(time_val))
                if track:
                    # Verificar si la sección ya existe
                    exists = any(s.beat == float(time_val) for s in track.sections)
                    if not exists:
                        section = Section(name=name, beat=float(time_val), time=float(time_val))
                        track.add_section(section)
                        assigned_count += 1
                        log_debug(f"✓ '{name}' → {track.title}", module="OSC")
                    else:
                        log_debug(f"⊘ '{name}' ya existe en {track.title}", module="OSC")
                else:
                    skipped_count += 1
                    log_warning(f"✗ '{name}' @ beat {time_val} fuera de rango de tracks", module="OSC")
            
            log_info(f"✓ Clips asignados: {assigned_count}, Omitidos: {skipped_count}", module="OSC")
        
        # Actualizar UI
        self._safe_ui_update('update_listbox')
    
    def _safe_ui_update(self, method_name: str, *args):
        """Actualiza UI de forma thread-safe con validación"""
        if not state.page_ref:
            return
        
        try:
            # Validar que page_ref esté viva
            if not hasattr(state.page_ref, 'update'):
                return
            
            method = getattr(state.page_ref, method_name, None)
            if method and callable(method):
                method(*args)
        except AttributeError:
            # El objeto fue destruido, ignorar
            pass
        except Exception as e:
            error_msg = str(e)
            # Ignorar errores de objetos eliminados o async
            if "__uid" not in error_msg and "update_async" not in error_msg:
                log_warning(f"UI update falló para {method_name}: {error_msg}", module="OSC")
                    
    def handle_error(self, address, *args):
        """Maneja errores relevantes"""
        if "/error" in address.lower():
            # Filtrar errores conocidos/esperados
            msg = str(args)
            if "get/beat" not in msg and "playing_status" not in msg:
                log_error(f"OSC Error en {address}: {args}", module="OSC")

# Instancia global
handlers = OSCHandlers()
log_info("✓ Instancia global de OSCHandlers creada", module="OSC")