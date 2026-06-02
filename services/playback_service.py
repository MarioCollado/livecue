"""Servicios puros de reproducción y navegación."""

from __future__ import annotations

import time

from core.logger import log_debug, log_error, log_info, log_warning


def scan_all(controller, send_message_fn, sleep_fn, state) -> bool:
    """Escanea los datos de Ableton usando las dependencias inyectadas."""

    current_time = time.time()

    if current_time - controller._last_scan_time < controller._scan_cooldown:
        log_warning(f"⨂ Scan en cooldown ({controller._scan_cooldown}s)", module="Playback")
        return False

    with controller._scan_lock:
        log_info("⟳ Iniciando scan completo...", module="Playback")

        try:
            log_debug("Solicitando cue points", module="Playback")
            send_message_fn("/live/song/get/cue_points", [])
            sleep_fn(0.3)

            log_debug("Solicitando clips del track 0", module="Playback")
            send_message_fn("/live/track/get/arrangement_clips/name", [0])
            sleep_fn(0.15)

            send_message_fn("/live/track/get/arrangement_clips/start_time", [0])
            sleep_fn(0.15)

            log_debug("Solicitando estado de reproducción", module="Playback")
            send_message_fn("/live/song/get/metronome", [])
            sleep_fn(0.05)
            send_message_fn("/live/song/get/tempo", [])
            sleep_fn(0.05)
            send_message_fn("/live/song/get/is_playing", [])
            sleep_fn(0.05)

            log_debug("Iniciando listeners OSC", module="Playback")
            send_message_fn("/live/song/start_listen/current_song_time", [])
            sleep_fn(0.05)
            send_message_fn("/live/song/start_listen/is_playing", [])
            sleep_fn(0.05)

            controller._last_scan_time = current_time

            log_debug("Detectando tempo de cada track...", module="Playback")
            _scan_track_tempos(controller, send_message_fn, sleep_fn, state)

            log_info("✓ Scan completado correctamente", module="Playback")
            return True

        except Exception as e:
            log_error("Error en scan", module="Playback", exc=e)
            return False


def _scan_track_tempos(controller, send_message_fn, sleep_fn, state):
    from core.state import state as global_state

    current_state = state or global_state
    tracks = current_state.tracks
    if not tracks:
        return

    log_debug(f"Escaneando tempo de {len(tracks)} tracks...", module="Playback")

    for track in tracks:
        if track.start_locator_id is None:
            continue

        try:
            send_message_fn("/live/song/cue_point/jump", [track.start_locator_id])
            sleep_fn(0.2)
            send_message_fn("/live/song/get/tempo", [])
            sleep_fn(0.15)
            track.bpm = current_state.current_tempo
            log_debug(f"Track '{track.title}': {track.bpm:.1f} BPM", module="Playback")
        except Exception as e:
            log_error(f"Error detectando tempo de '{track.title}'", module="Playback", exc=e)


def play_track(controller, track_index: int, send_message_fn, sleep_fn, state) -> bool:
    """Reproduce un track específico."""

    with controller._playback_lock:
        tracks = state.tracks
        if not (0 <= track_index < len(tracks)):
            log_error(f"Índice inválido: {track_index}", module="Playback")
            return False

        track = tracks[track_index]
        locator_id = track.start_locator_id

        if locator_id is None:
            log_error(f"Track '{track.title}' sin locator ID", module="Playback")
            return False

        try:
            log_info(f"▶ Reproduciendo: {track.title}", module="Playback")
            log_debug(f"Track index: {track_index}, Locator ID: {locator_id}", module="Playback")

            controller._force_stop_internal(send_message_fn, sleep_fn)
            sleep_fn(0.12)

            send_message_fn("/live/song/cue_point/jump", [locator_id])
            sleep_fn(0.1)
            send_message_fn("/live/song/start_playing", [])

            state.is_playing = True
            state.current_index = track_index

            log_debug(
                f"Estado actualizado: is_playing=True, current_index={track_index}",
                module="Playback",
            )
            return True

        except Exception as e:
            log_error(f"Error reproduciendo track '{track.title}'", module="Playback", exc=e)
            return False


def stop(controller, send_message_fn, sleep_fn, state):
    """Detiene la reproducción."""

    with controller._playback_lock:
        try:
            log_info("■ Deteniendo reproducción...", module="Playback")

            for i in range(2):
                send_message_fn("/live/song/stop_playing", [])
                sleep_fn(0.05)
                log_debug(f"Stop enviado ({i+1}/2)", module="Playback")

            state.is_playing = False
            log_info("■ Reproducción detenida", module="Playback")

        except Exception as e:
            log_error("Error deteniendo reproducción", module="Playback", exc=e)


def jump_to_section(controller, track_index: int, section_index: int, send_message_fn, sleep_fn, state) -> bool:
    """Salta a una sección específica y reproduce desde ahí."""

    with controller._playback_lock:
        tracks = state.tracks
        if not (0 <= track_index < len(tracks)):
            log_error(f"Índice de track inválido: {track_index}", module="Playback")
            return False

        track = tracks[track_index]
        if not (0 <= section_index < len(track.sections)):
            log_error(f"Índice de sección inválido: {section_index}", module="Playback")
            return False

        section = track.sections[section_index]

        try:
            log_info(f"⇒ Saltando a: {section.name} (beat {section.beat})", module="Playback")
            log_debug(
                f"Track: {track.title}, Section: {section.name}, is_playing={state.is_playing}",
                module="Playback",
            )

            send_message_fn("/live/song/set/current_song_time", [section.beat])
            sleep_fn(0.15)

            if state.is_playing:
                log_debug("Estado: reproduciendo → usando continue_playing", module="Playback")
                send_message_fn("/live/song/continue_playing", [])
            else:
                log_debug("Estado: parado → usando start_playing", module="Playback")
                send_message_fn("/live/song/start_playing", [])

            sleep_fn(0.05)
            state.is_playing = True
            state.current_index = track_index

            log_debug(
                f"Salto completado: current_index={track_index}, beat={section.beat}",
                module="Playback",
            )
            return True

        except Exception as e:
            log_error(f"Error saltando a sección '{section.name}'", module="Playback", exc=e)
            return False


def toggle_metronome(controller, send_message_fn, state):
    """Alterna el metrónomo."""

    with controller._playback_lock:
        try:
            state.metronome_on = not state.metronome_on
            send_message_fn("/live/song/set/metronome", [1 if state.metronome_on else 0])
            log_info(f"🎵 Metrónomo: {'ON' if state.metronome_on else 'OFF'}", module="Playback")
            return state.metronome_on

        except Exception as e:
            log_error("Error toggling metrónomo", module="Playback", exc=e)
            return state.metronome_on


def next_track(controller, send_message_fn, sleep_fn, state) -> bool:
    """Avanza al siguiente track."""

    if state.current_index < len(state.tracks) - 1:
        log_debug(f"Next track: {state.current_index} → {state.current_index + 1}", module="Playback")
        return play_track(controller, state.current_index + 1, send_message_fn, sleep_fn, state)

    log_warning("⨂ Ya en el último track", module="Playback")
    return False


def prev_track(controller, send_message_fn, sleep_fn, state) -> bool:
    """Retrocede al track anterior."""

    if state.current_index > 0:
        log_debug(
            f"Previous track: {state.current_index} → {state.current_index - 1}",
            module="Playback",
        )
        return play_track(controller, state.current_index - 1, send_message_fn, sleep_fn, state)

    log_warning("⨂ Ya en el primer track", module="Playback")
    return False
