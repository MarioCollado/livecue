# core/state.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

from __future__ import annotations

import threading
from typing import List, Optional

from core.logger import log_debug, log_error, log_info, log_warning
from domain.models import ClickEvent, Locator, Section, Track


class AppState:
    """Estado global thread-safe de la aplicación."""

    def __init__(self):
        self._lock = threading.RLock()

        self._locators: List[Locator] = []
        self._tracks: List[Track] = []
        self._click_events: List[ClickEvent] = []

        self._current_index: int = -1
        self._is_playing: bool = False
        self._metronome_on: bool = False

        self._current_beat: int = 1
        self._current_tempo: float = 120.0
        self._time_signature_num: int = 4
        self._current_song_time: float = 0.0

        self.page_ref = None

        self._last_triggered_beat: Optional[int] = None
        self._needs_ui_refresh = False

        self.is_scanning = False
        self.scan_progress = 0
        self.scan_status = ""
        self.scan_error = None
        self.setlist_loaded = False

        log_debug("AppState inicializado", module="Main")

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

            if self._current_index >= len(self._tracks):
                old_index = self._current_index
                self._current_index = len(self._tracks) - 1 if self._tracks else -1
                log_debug(
                    f"current_index ajustado automáticamente: {old_index} → {self._current_index}",
                    module="Main",
                )

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
            self._current_beat = value

    @property
    def current_tempo(self) -> float:
        with self._lock:
            return self._current_tempo

    @current_tempo.setter
    def current_tempo(self, value: float):
        with self._lock:
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
            self._current_song_time = value

    @property
    def last_triggered_beat(self) -> Optional[int]:
        with self._lock:
            return self._last_triggered_beat

    @last_triggered_beat.setter
    def last_triggered_beat(self, value: Optional[int]):
        with self._lock:
            self._last_triggered_beat = value

    @property
    def click_events(self) -> list:
        with self._lock:
            return list(self._click_events)

    @click_events.setter
    def click_events(self, value: list):
        with self._lock:
            self._click_events = sorted(value, key=lambda e: e.beat)
            log_debug(f"click_events actualizados: {len(self._click_events)} eventos", module="Main")

    def get_current_track(self) -> Optional[Track]:
        with self._lock:
            if 0 <= self._current_index < len(self._tracks):
                track = self._tracks[self._current_index]
                log_debug(f"get_current_track: '{track.title}' (index {self._current_index})", module="Main")
                return track
        log_debug(f"get_current_track: None (index {self._current_index})", module="Main")
        return None

    def find_track_by_beat(self, beat: float) -> Optional[Track]:
        with self._lock:
            for track in self._tracks:
                if track.contains_beat(beat):
                    log_debug(f"find_track_by_beat({beat}): '{track.title}'", module="Main")
                    return track
        log_debug(f"find_track_by_beat({beat}): No encontrado", module="Main")
        return None

    def get_track_count(self) -> int:
        with self._lock:
            return len(self._tracks)

    def get_locator_count(self) -> int:
        with self._lock:
            return len(self._locators)

    def reset(self):
        with self._lock:
            old_locators = len(self._locators)
            old_tracks = len(self._tracks)

            self._locators.clear()
            self._tracks.clear()
            self._click_events.clear()
            self._current_index = -1
            self._last_triggered_beat = None
            self._is_playing = False

            log_info(
                f"🔄 Estado reiniciado (limpiados {old_locators} locators, {old_tracks} tracks)",
                module="Main",
            )

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

    def get_state_summary(self) -> str:
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


state = AppState()

__all__ = ["state", "AppState", "Locator", "Track", "Section", "ClickEvent"]

log_info("✓ Instancia global de AppState creada", module="Main")
