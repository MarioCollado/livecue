# core/state.py - VERSIÓN MEJORADA
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import threading

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

            
    # ===== PROPERTIES CON GETTERS/SETTERS THREAD-SAFE =====
    
    @property
    def locators(self) -> List[Locator]:
        with self._lock:
            return self._locators.copy()
    
    @locators.setter
    def locators(self, value: List[Locator]):
        with self._lock:
            self._locators = value
    
    @property
    def tracks(self) -> List[Track]:
        with self._lock:
            # CAMBIO: Devolver copia para evitar modificaciones externas
            return self._tracks.copy()

    @tracks.setter
    def tracks(self, value: List[Track]):
        with self._lock:
            self._tracks = value.copy() if value else []
            # Ajustar current_index si es necesario
            if self._current_index >= len(self._tracks):
                self._current_index = len(self._tracks) - 1 if self._tracks else -1    
    
    @property
    def current_index(self) -> int:
        with self._lock:
            return self._current_index
    
    @current_index.setter
    def current_index(self, value: int):
        with self._lock:
            self._current_index = value
    
    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing
    
    @is_playing.setter
    def is_playing(self, value: bool):
        with self._lock:
            self._is_playing = value
    
    @property
    def metronome_on(self) -> bool:
        with self._lock:
            return self._metronome_on
    
    @metronome_on.setter
    def metronome_on(self, value: bool):
        with self._lock:
            self._metronome_on = value
    
    @property
    def current_beat(self) -> int:
        with self._lock:
            return self._current_beat
    
    @current_beat.setter
    def current_beat(self, value: int):
        with self._lock:
            self._current_beat = value
    
    @property
    def current_tempo(self) -> float:
        with self._lock:
            return self._current_tempo
    
    @current_tempo.setter
    def current_tempo(self, value: float):
        with self._lock:
            self._current_tempo = value
    
    @property
    def time_signature_num(self) -> int:
        with self._lock:
            return self._time_signature_num
    
    @time_signature_num.setter
    def time_signature_num(self, value: int):
        with self._lock:
            self._time_signature_num = value
    
    @property
    def current_song_time(self) -> float:
        with self._lock:
            return self._current_song_time
    
    @current_song_time.setter
    def current_song_time(self, value: float):
        with self._lock:
            self._current_song_time = value
    
    @property
    def last_triggered_beat(self) -> Optional[int]:
        with self._lock:
            return self._last_triggered_beat
    
    @last_triggered_beat.setter
    def last_triggered_beat(self, value: Optional[int]):
        with self._lock:
            self._last_triggered_beat = value
    
    # ===== MÉTODOS THREAD-SAFE =====
    
    def get_current_track(self) -> Optional[Track]:
        """Retorna el track actualmente seleccionado"""
        with self._lock:
            if 0 <= self._current_index < len(self._tracks):
                return self._tracks[self._current_index]
        return None
    
    def find_track_by_beat(self, beat: float) -> Optional[Track]:
        """Encuentra el track que contiene un beat específico"""
        with self._lock:
            for track in self._tracks:
                if track.contains_beat(beat):
                    return track
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
            self._locators.clear()
            self._tracks.clear()
            self._current_index = -1
            self._last_triggered_beat = None
            self._is_playing = False
            print("[STATE] ✓ Estado reiniciado")

    # ===== CONTROL DE REFRESCO UI =====

    @property
    def needs_ui_refresh(self) -> bool:
        with self._lock:
            return self._needs_ui_refresh

    @needs_ui_refresh.setter
    def needs_ui_refresh(self, value: bool):
        with self._lock:
            self._needs_ui_refresh = value


# Instancia global
state = AppState()