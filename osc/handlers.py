# osc/handlers.py
from core import state
from core import utils
from setlist import manager as setlist_manager  # por si queremos extender
from osc.client import send_message
import time

def cue_handler(address, *args):
    print(f"\n[OSC] ✓ Cue points recibidos: {len(args)//2} locators")
    raw_locators = []
    for i in range(0, len(args), 2):
        try:
            name = args[i].strip()
            beat = args[i + 1]
            # Guardar el índice ORIGINAL que viene de Ableton
            raw_locators.append({"original_id": i // 2, "name": name, "beat": beat})
        except Exception as e:
            print(f"Error procesando locator: {e}")

    # ORDENAR por beat
    raw_locators.sort(key=lambda x: x["beat"])

    # Asignar IDs secuenciales DESPUÉS de ordenar
    for i, loc in enumerate(raw_locators):
        loc["id"] = i

    # Guardar en state.locators
    state.locators = raw_locators

    print(f"[DEBUG] Primeros 5 locators ordenados:")
    for loc in raw_locators[:5]:
        print(f"  [ID={loc['id']}, OrigID={loc['original_id']}] {loc['name']} @ beat {loc['beat']}")

    # --- PARSING AVANZADO ---
    state.tracks = []
    current_track = None
    track_number = 0

    for loc in raw_locators:
        name_upper = loc["name"].upper()

        if name_upper.startswith("START TRACK"):
            if current_track:
                print(f"[WARN] Track '{current_track['title']}' no tenía END TRACK")
                current_track["end"] = loc["beat"]
                state.tracks.append(current_track)

            title = "Untitled"
            if '"' in loc["name"]:
                parts = loc["name"].split('"')
                if len(parts) >= 2:
                    title = parts[1]

            track_number += 1
            current_track = {
                "title": title,
                "start": loc["beat"],
                "start_locator_id": loc["original_id"],  # ← USAR EL ID ORIGINAL DE ABLETON
                "track_number": track_number,
                "sections": []
            }
            print(f"[PARSE] Track #{track_number}: '{title}' @ beat {loc['beat']} → usando original_id={loc['original_id']}")

        elif name_upper.startswith("END TRACK"):
            if current_track:
                current_track["end"] = loc["beat"]
                state.tracks.append(current_track)
                print(f"[PARSE] ✓ Track completado: '{current_track['title']}' ({current_track['start']} → {current_track['end']})")
                current_track = None
            else:
                print(f"[WARN] END TRACK sin START TRACK @ beat {loc['beat']}")

        elif current_track:
            current_track["sections"].append({
                "name": loc["name"].title(),
                "beat": loc["beat"]
            })

    if current_track:
        print(f"[WARN] Último track sin END TRACK")
        current_track["end"] = raw_locators[-1]["beat"]
        state.tracks.append(current_track)

    print(f"\n[OSC] ✓ Tracks detectados: {len(state.tracks)}")
    for t in state.tracks:
        print(f"  #{t['track_number']}: {t['title']}")
        print(f"    Locator original_id: {t.get('start_locator_id', '?')}")
        print(f"    Rango: beats {t['start']:.0f} → {t['end']:.0f}")
        print(f"    Secciones: {len(t['sections'])}")

    if state.page_ref and hasattr(state.page_ref, 'update_listbox'):
        state.page_ref.update_listbox()

def metronome_state_handler(address, *args):
    if not args:
        return
    state.metronome_on = bool(int(args[0]))
    print(f"[OSC] Metrónomo: {'ON' if state.metronome_on else 'OFF'}")
    if state.page_ref and hasattr(state.page_ref, "update_metronome_ui"):
        state.page_ref.update_metronome_ui()

def beat_handler(address, *args):
    """Método 1: Beat directo de Ableton"""
    if args:
        state.current_beat = int(args[0])
        if state.page_ref and hasattr(state.page_ref, "trigger_pulse"):
            state.page_ref.trigger_pulse(state.current_beat)

def song_time_handler(address, *args):
    """Método 2: Calcular beat desde song_time"""
    if args:
        state.current_song_time = float(args[0])
        beat_in_measure = (state.current_song_time % state.time_signature_num) + 1
        calculated_beat = int(beat_in_measure)

        if calculated_beat != state.current_beat:
            state.current_beat = calculated_beat
            if state.page_ref and hasattr(state.page_ref, "trigger_pulse"):
                state.page_ref.trigger_pulse(state.current_beat)

def playing_status_handler(address, *args):
    """Detecta si está reproduciendo"""
    if args:
        state.is_playing = bool(int(args[0]))
        print(f"[OSC] Playing: {state.is_playing}")

def tempo_handler(address, *args):
    """Recibe el tempo actual"""
    if args:
        state.current_tempo = float(args[0])
        print(f"[OSC] Tempo: {state.current_tempo} BPM")
        if state.page_ref and hasattr(state.page_ref, "update_tempo_display"):
            state.page_ref.update_tempo_display()

def time_signature_handler(address, *args):
    """Recibe el time signature"""
    if args and len(args) >= 1:
        state.time_signature_num = int(args[0])
        print(f"[OSC] Time signature: {state.time_signature_num}/4")
        if state.page_ref and hasattr(state.page_ref, "update_tempo_display"):
            state.page_ref.update_tempo_display()

def catch_all_handler(address, *args):
    if "/beat" in address.lower() or "/time" in address.lower():
        print(f"[OSC DEBUG] {address}: {args}")

# ==============================
# HANDLERS DE CLIPS / OSC
# ==============================

# Estructura global para almacenar datos de clips temporalmente por track
track_clip_data = {}  # { track_index: { "names": [...], "times": [...] } }

def handle_track_arrangement_clips_name(path, *args):
    track_index = args[0]
    clip_names = [n for n in args[1:] if n and str(n).lower() != "none"]
    track_clip_data.setdefault(track_index, {})["names"] = clip_names
    maybe_assign_track_clips(track_index)

def handle_track_arrangement_clips_start_time(path, *args):
    track_index = args[0]
    clip_times = [float(t) for t in args[1:]]
    track_clip_data.setdefault(track_index, {})["times"] = clip_times
    maybe_assign_track_clips(track_index)

def maybe_assign_track_clips(track_index):
    """Asigna clips a tracks solo si ya tenemos nombres y tiempos listos."""
    data = track_clip_data.get(track_index, {})
    names = data.get("names")
    times = data.get("times")

    if not names or not times:
        return  # Esperar a que llegue el otro

    # Limpiar las secciones de todos los tracks antes de asignar
    for track in state.tracks:
        track["sections"] = []

    print(f"[OSC] ✓ Asignando {len(names)} clips del track OSC {track_index}")

    for name, time in zip(names, times):
        try:
            beat = float(time)
        except Exception:
            continue

        # Buscar el track correcto según beat
        assigned = False
        for track in state.tracks:
            if track["start"] <= beat < track["end"]:
                track["sections"].append({
                    "name": name,
                    "beat": beat,
                    "time": beat,
                    "relative_beat": beat - track["start"]
                })
                print(f"[STRUCTURE]   ✓ '{name}' (beat {beat:.1f}) → {track['title']}")
                assigned = True
                break

        if not assigned:
            print(f"[STRUCTURE]   ✗ '{name}' (beat {beat}) → fuera de rango de tracks")

    # Ordenar secciones
    for track in state.tracks:
        track["sections"].sort(key=lambda x: x["beat"])

    # Limpiar datos temporales
    track_clip_data[track_index] = {}

    # Actualizar UI
    if hasattr(state, 'page_ref') and state.page_ref:
        try:
            state.page_ref.update_listbox()
        except Exception:
            pass

def assign_clips_to_tracks_from_arrangement(clip_names, clip_times):
    """Asigna clips de arrangement a los tracks según su posición temporal"""
    print(f"\n[STRUCTURE] Asignando {len(clip_names)} clips a tracks...")

    # Limpiar secciones existentes
    for track in state.tracks:
        track["sections"] = []

    # Asignar cada clip al track correcto
    for clip_name, clip_time in zip(clip_names, clip_times):
        # Saltar clips sin nombre
        if not clip_name or str(clip_name).strip().lower() == "none":
            continue

        # Encontrar a qué track pertenece este clip
        assigned = False
        for track in state.tracks:
            # Usar "start" y "end" según tu estructura
            start = track.get("start", 0)
            end = track.get("end", float('inf'))

            try:
                ct = float(clip_time)
            except Exception:
                ct = clip_time  # si no convertible, dejar como está

            if isinstance(ct, (int, float)) and start <= ct < end:
                track["sections"].append({
                    "name": clip_name,
                    "beat": ct,
                    "time": ct,
                    "relative_beat": ct - start
                })
                print(f"[STRUCTURE]   ✓ '{clip_name}' (beat {ct:.1f}) → {track['title']}")
                assigned = True
                break

        if not assigned:
            print(f"[STRUCTURE]   ✗ '{clip_name}' (beat {clip_time}) → No asignado (fuera de rango de tracks)")
            # Debug: mostrar rangos de tracks
            for track in state.tracks:
                print(f"[STRUCTURE]     Track '{track['title']}': beats {track.get('start', 0)} - {track.get('end', '?')}")

    # Ordenar secciones por tiempo
    for track in state.tracks:
        track["sections"].sort(key=lambda x: x["beat"])
        if len(track["sections"]) > 0:
            print(f"[STRUCTURE] ✓ Track '{track['title']}': {len(track['sections'])} secciones")

    print(f"[STRUCTURE] ✓ Proceso completado\n")

    # Actualizar UI
    if hasattr(state, 'page_ref') and state.page_ref:
        try:
            state.page_ref.update_listbox()
        except Exception:
            pass
