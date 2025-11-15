# core/state.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import threading
from core.logger import log_info, log_error, log_warning, log_debug

@dataclass
class Locator:
    """Representa un locator de Ableton"""
    id: int
    original_id: int
    name: str
    beat: float
    
    @property
    def is_click_toggle(self) -> bool:
        return self.name.upper() in ["CLICK ON", "CLICK OFF"]

@dataclass
class Section:
    """Representa una sección dentro de un track"""
    name: str
    beat: float
    time: float = None
    relative_beat: float = 0
    
    def __post_init__(self):
        if self.time is None:
            self.time = self.beat

@dataclass
class Track:
    """Representa un track con sus secciones"""
    title: str
    start: float
    end: float
    track_number: int
    start_locator_id: Optional[int] = None
    sections: List[Section] = field(default_factory=list)
    expanded: bool = False
    
    def contains_beat(self, beat: float) -> bool:
        """Verifica si un beat está dentro del rango del track"""
        return self.start <= beat < self.end
    
    def add_section(self, section: Section):
        """Agrega una sección y mantiene el orden"""
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.beat)
        section.relative_beat = section.beat - self.start
    
    def get_progress(self, current_beat: float) -> float:
        """Calcula el progreso actual (0-1)"""
        duration = self.end - self.start
        if duration <= 0:
            return 0
        progress = (current_beat - self.start) / duration
        return max(0, min(1, progress))

class AppState:
    """Estado global thread-safe de la aplicación"""
    
    def __init__(self):
        # Lock para acceso thread-safe
        self._lock = threading.RLock()
        
        # Datos de Ableton
        self._locators: List[Locator] = []
        self._tracks: List[Track] = []
        
        # Estado de reproducción
        self._current_index: int = -1
        self._is_playing: bool = False
        self._metronome_on: bool = False
        
        # Tiempo y tempo
        self._current_beat: int = 1
        self._current_tempo: float = 120.0
        self._time_signature_num: int = 4
        self._current_song_time: float = 0.0
        
        # Referencias UI (no requieren lock)
        self.page_ref = None
        
        # Control de updates
        self._last_triggered_beat: Optional[int] = None

        # Señal para que la UI (Flet) sepa que debe refrescar
        self._needs_ui_refresh = False
        
        log_debug("AppState inicializado", module="Main")

            
    # ===== PROPERTIES CON GETTERS/SETTERS THREAD-SAFE =====
    
    @property
    def locators(self) -> List[Locator]:
        with self._lock:
            return self._locators.copy()
    
    @locators.setter
    def locators(self, value: List[Locator]):
        with self._lock:
            old_count = len(self._locators)
            self._locators = value
            new_count = len(self._locators)
            
            if new_count != old_count:
                log_debug(f"Locators actualizados: {old_count} → {new_count}", module="Main")
    
    @property
    def tracks(self) -> List[Track]:
        with self._lock:
            return self._tracks.copy()

    @tracks.setter
    def tracks(self, value: List[Track]):
        with self._lock:
            old_count = len(self._tracks)
            self._tracks = value.copy() if value else []
            new_count = len(self._tracks)
            
            # Ajustar current_index si es necesario
            if self._current_index >= len(self._tracks):
                old_index = self._current_index
                self._current_index = len(self._tracks) - 1 if self._tracks else -1
                log_debug(f"current_index ajustado automáticamente: {old_index} → {self._current_index}", module="Main")
            
            if new_count != old_count:
                log_debug(f"Tracks actualizados: {old_count} → {new_count}", module="Main")
    
    @property
    def current_index(self) -> int:
        with self._lock:
            return self._current_index
    
    @current_index.setter
    def current_index(self, value: int):
        with self._lock:
            if value != self._current_index:
                old_value = self._current_index
                self._current_index = value
                log_debug(f"current_index cambiado: {old_value} → {value}", module="Main")
    
    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing
    
    @is_playing.setter
    def is_playing(self, value: bool):
        with self._lock:
            if value != self._is_playing:
                self._is_playing = value
                log_debug(f"is_playing: {value}", module="Main")
    
    @property
    def metronome_on(self) -> bool:
        with self._lock:
            return self._metronome_on
    
    @metronome_on.setter
    def metronome_on(self, value: bool):
        with self._lock:
            if value != self._metronome_on:
                self._metronome_on = value
                log_debug(f"metronome_on: {value}", module="Main")
    
    @property
    def current_beat(self) -> int:
        with self._lock:
            return self._current_beat
    
    @current_beat.setter
    def current_beat(self, value: int):
        with self._lock:
            # No loguear cada beat (demasiado verbose)
            self._current_beat = value
    
    @property
    def current_tempo(self) -> float:
        with self._lock:
            return self._current_tempo
    
    @current_tempo.setter
    def current_tempo(self, value: float):
        with self._lock:
            # Log solo si cambió significativamente
            if abs(value - self._current_tempo) > 0.5:
                log_debug(f"current_tempo: {self._current_tempo:.1f} → {value:.1f}", module="Main")
            self._current_tempo = value
    
    @property
    def time_signature_num(self) -> int:
        with self._lock:
            return self._time_signature_num
    
    @time_signature_num.setter
    def time_signature_num(self, value: int):
        with self._lock:
            if value != self._time_signature_num:
                log_debug(f"time_signature: {self._time_signature_num}/4 → {value}/4", module="Main")
            self._time_signature_num = value
    
    @property
    def current_song_time(self) -> float:
        with self._lock:
            return self._current_song_time
    
    @current_song_time.setter
    def current_song_time(self, value: float):
        with self._lock:
            # No loguear (demasiado frecuente)
            self._current_song_time = value
    
    @property
    def last_triggered_beat(self) -> Optional[int]:
        with self._lock:
            return self._last_triggered_beat
    
    @last_triggered_beat.setter
    def last_triggered_beat(self, value: Optional[int]):
        with self._lock:
            # No loguear (demasiado frecuente)
            self._last_triggered_beat = value
    
    # ===== MÉTODOS THREAD-SAFE =====
    
    def get_current_track(self) -> Optional[Track]:
        """Retorna el track actualmente seleccionado"""
        with self._lock:
            if 0 <= self._current_index < len(self._tracks):
                track = self._tracks[self._current_index]
                log_debug(f"get_current_track: '{track.title}' (index {self._current_index})", module="Main")
                return track
        log_debug(f"get_current_track: None (index {self._current_index})", module="Main")
        return None
    
    def find_track_by_beat(self, beat: float) -> Optional[Track]:
        """Encuentra el track que contiene un beat específico"""
        with self._lock:
            for track in self._tracks:
                if track.contains_beat(beat):
                    log_debug(f"find_track_by_beat({beat}): '{track.title}'", module="Main")
                    return track
        log_debug(f"find_track_by_beat({beat}): No encontrado", module="Main")
        return None
    
    def get_track_count(self) -> int:
        """Retorna el número de tracks"""
        with self._lock:
            return len(self._tracks)
    
    def get_locator_count(self) -> int:
        """Retorna el número de locators"""
        with self._lock:
            return len(self._locators)
    
    def reset(self):
        """Reinicia el estado - Thread-safe"""
        with self._lock:
            old_locators = len(self._locators)
            old_tracks = len(self._tracks)
            
            self._locators.clear()
            self._tracks.clear()
            self._current_index = -1
            self._last_triggered_beat = None
            self._is_playing = False
            
            log_info(f"🔄 Estado reiniciado (limpiados {old_locators} locators, {old_tracks} tracks)", module="Main")

    # ===== CONTROL DE REFRESCO UI =====

    @property
    def needs_ui_refresh(self) -> bool:
        with self._lock:
            return self._needs_ui_refresh

    @needs_ui_refresh.setter
    def needs_ui_refresh(self, value: bool):
        with self._lock:
            if value != self._needs_ui_refresh:
                log_debug(f"needs_ui_refresh: {value}", module="Main")
            self._needs_ui_refresh = value
    
    # ===== MÉTODOS DE DIAGNÓSTICO =====
    
    def get_state_summary(self) -> str:
        """Retorna un resumen del estado actual (útil para debugging)"""
        with self._lock:
            summary = (
                f"Estado Global:\n"
                f"  Locators: {len(self._locators)}\n"
                f"  Tracks: {len(self._tracks)}\n"
                f"  Current Index: {self._current_index}\n"
                f"  Is Playing: {self._is_playing}\n"
                f"  Metronome: {self._metronome_on}\n"
                f"  Tempo: {self._current_tempo:.1f} BPM\n"
                f"  Time Signature: {self._time_signature_num}/4\n"
                f"  Current Beat: {self._current_beat}"
            )
            return summary
    
    def log_state_summary(self):
        """Loguea un resumen del estado actual"""
        log_info("=" * 60, module="Main")
        log_info("📊 RESUMEN DEL ESTADO", module="Main")
        log_info("=" * 60, module="Main")
        
        with self._lock:
            log_info(f"Locators: {len(self._locators)}", module="Main")
            log_info(f"Tracks: {len(self._tracks)}", module="Main")
            
            if self._tracks:
                for i, track in enumerate(self._tracks):
                    marker = "→" if i == self._current_index else " "
                    log_info(f"  {marker} Track {i+1}: '{track.title}' ({len(track.sections)} secciones)", module="Main")
            
            log_info(f"Reproducción: {'▶ Playing' if self._is_playing else '■ Stopped'}", module="Main")
            log_info(f"Metrónomo: {'ON' if self._metronome_on else 'OFF'}", module="Main")
            log_info(f"Tempo: {self._current_tempo:.1f} BPM @ {self._time_signature_num}/4", module="Main")
            log_info(f"Beat actual: {self._current_beat}", module="Main")
        
        log_info("=" * 60, module="Main")


# Instancia global
state = AppState()
log_info("✓ Instancia global de AppState creada", module="Main")