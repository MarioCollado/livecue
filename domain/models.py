from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Locator:
    """Representa un locator de Ableton."""

    id: int
    original_id: int
    name: str
    beat: float

    @property
    def is_click_toggle(self) -> bool:
        n = self.name.upper().replace("_", " ")
        return n in ["CLICK ON", "CLICK OFF"]

    @property
    def is_click_on(self) -> bool:
        n = self.name.upper().replace("_", " ")
        return n == "CLICK ON"

    @property
    def is_click_off(self) -> bool:
        n = self.name.upper().replace("_", " ")
        return n == "CLICK OFF"


@dataclass
class ClickEvent:
    """Evento de automatización del click/metrónomo."""

    beat: float
    enable: bool


@dataclass
class Section:
    """Representa una sección dentro de un track."""

    name: str
    beat: float
    time: float = None
    relative_beat: float = 0

    def __post_init__(self):
        if self.time is None:
            self.time = self.beat


@dataclass
class Track:
    """Representa un track con sus secciones."""

    title: str
    start: float
    end: float
    track_number: int
    start_locator_id: Optional[int] = None
    bpm: Optional[float] = None
    sections: List[Section] = field(default_factory=list)
    expanded: bool = False
    auto_continue: bool = False
    loop_track: bool = False
    end_processed: bool = False

    def contains_beat(self, beat: float) -> bool:
        return self.start <= beat <= self.end

    def add_section(self, section: Section):
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.beat)
        section.relative_beat = section.beat - self.start

    def get_progress(self, current_beat: float) -> float:
        duration = self.end - self.start
        if duration <= 0:
            return 0
        progress = (current_beat - self.start) / duration
        return max(0, min(1, progress))


__all__ = ["Locator", "ClickEvent", "Section", "Track"]
