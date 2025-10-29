# core/state.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional

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
        return max(0, min(1, (current_beat - self.start) / duration))

class AppState:
    """Estado global de la aplicación"""
    
    def __init__(self):
        # Datos de Ableton
        self.locators: List[Locator] = []
        self.tracks: List[Track] = []
        
        # Estado de reproducción
        self.current_index: int = -1
        self.is_playing: bool = False
        self.metronome_on: bool = False
        
        # Tiempo y tempo
        self.current_beat: int = 1
        self.current_tempo: float = 120.0
        self.time_signature_num: int = 4
        self.current_song_time: float = 0.0
        
        # Referencias UI
        self.page_ref = None
        self.track_progress_bars: Dict[int, any] = {}
        
        # Control de updates
        self.last_triggered_beat: Optional[int] = None
    
    def get_current_track(self) -> Optional[Track]:
        """Retorna el track actualmente seleccionado"""
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    
    def find_track_by_beat(self, beat: float) -> Optional[Track]:
        """Encuentra el track que contiene un beat específico"""
        for track in self.tracks:
            if track.contains_beat(beat):
                return track
        return None
    
    def reset(self):
        """Reinicia el estado"""
        self.locators.clear()
        self.tracks.clear()
        self.current_index = -1
        self.track_progress_bars.clear()
        self.last_triggered_beat = None

# Instancia global
state = AppState()