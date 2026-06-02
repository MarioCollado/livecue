# core/playback.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

from __future__ import annotations

import threading
import time

from core.logger import log_debug
from core.state import state
from osc.client import send_message
from services.playback_service import (
    jump_to_section as _jump_to_section,
    next_track as _next_track,
    play_track as _play_track,
    prev_track as _prev_track,
    scan_all as _scan_all,
    stop as _stop,
    toggle_metronome as _toggle_metronome,
)


class PlaybackController:
    """Controlador de reproducción de Ableton con sincronización."""

    def __init__(self):
        self._scan_lock = threading.Lock()
        self._playback_lock = threading.Lock()
        self._last_scan_time = 0
        self._scan_cooldown = 1.0
        log_debug("PlaybackController inicializado", module="Playback")

    def scan_all(self) -> bool:
        return _scan_all(self, send_message, time.sleep, state)

    def _scan_track_tempos(self):
        from services.playback_service import _scan_track_tempos as _service_scan_track_tempos

        return _service_scan_track_tempos(self, send_message, time.sleep, state)

    def play_track(self, track_index: int) -> bool:
        return _play_track(self, track_index, send_message, time.sleep, state)

    def _force_stop_internal(self, send_message_fn=send_message, sleep_fn=time.sleep):
        try:
            for _ in range(2):
                send_message_fn("/live/song/stop_playing", [])
                sleep_fn(0.03)
            log_debug("Stop interno forzado", module="Playback")
        except Exception as e:
            from core.logger import log_error

            log_error("Error en stop interno", module="Playback", exc=e)

    def stop(self):
        return _stop(self, send_message, time.sleep, state)

    def jump_to_section(self, track_index: int, section_index: int) -> bool:
        return _jump_to_section(self, track_index, section_index, send_message, time.sleep, state)

    def toggle_metronome(self) -> bool:
        return _toggle_metronome(self, send_message, state)

    def next_track(self) -> bool:
        return _next_track(self, send_message, time.sleep, state)

    def prev_track(self) -> bool:
        return _prev_track(self, send_message, time.sleep, state)


playback = PlaybackController()

__all__ = ["PlaybackController", "playback"]

log_debug("✓ Instancia global de PlaybackController creada", module="Playback")
