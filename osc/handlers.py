# osc/handlers.py
from core import state
from core import utils
from setlist import manager as setlist_manager
from osc.client import send_message
import time

def toggle_metronome(from_locator_name: str):
    """Activa o desactiva el metrónomo según el nombre del locator."""
    name = from_locator_name.strip().upper()
    if "CLICK ON" in name:
        state.metronome_on = True
        print("[LOCATOR] 🔊 CLICK ON — metrónomo activado")
        send_message("/live/metronome", 1)
    elif "CLICK OFF" in name:
        state.metronome_on = False
        print("[LOCATOR] 🔇 CLICK OFF — metrónomo desactivado")
        send_message("/live/metronome", 0)

    # Actualizar UI si existe
    if state.page_ref and hasattr(state.page_ref, "update_metronome_ui"):
        state.page_ref.update_metronome_ui()

def cue_handler(address, *args):
    print(f"\n[OSC] ✓ Cue points recibidos: {len(args)//2} locators")
    raw_locators = []
    for i in range(0, len(args), 2):
        try:
            name = args[i].strip()
            beat = args[i + 1]
            is_click_toggle = name.upper() in ["CLICK ON", "CLICK OFF"]
            raw_locators.append({
                "original_id": i // 2,
                "name": name,
                "beat": beat,
                "is_click_toggle": is_click_toggle
            })
        except Exception as e:
            print(f"Error procesando locator: {e}")

    # Ordenar por beat
    raw_locators.sort(key=lambda x: x["beat"])

    for i, loc in enumerate(raw_locators):
        loc["id"] = i

    state.locators = raw_locators

    print(f"[DEBUG] Primeros 5 locators ordenados:")
    for loc in raw_locators[:5]:
        print(f"  [ID={loc['id']}, OrigID={loc['original_id']}] {loc['name']} @ beat {loc['beat']}")

    # --- Parsing avanzado (tracks, secciones, etc) ---
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
                "start_locator_id": loc["original_id"],
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

def song_time_handler(addr, *args):
    """Usar el beat enviado por Ableton directamente para el pulso visual"""

    if not args:
        return

    current_beat = int(args[0])  # Ableton nos da el beat exacto
    state.current_song_time = args[0]

    # Evitar disparos duplicados
    if getattr(state, "last_triggered_beat", None) == current_beat:
        return

    state.last_triggered_beat = current_beat

    # Trigger del pulso visual
    try:
        if state.page_ref:
            state.page_ref.trigger_pulse(current_beat)
    except Exception as e:
        print(f"[OSC] Error en trigger_pulse: {e}")

    # Actualizar barra de progreso
    try:
        if state.page_ref:
            state.page_ref.update_track_progress(current_beat)
    except:
        pass

def is_playing_handler(address, *args):
    """Handler alternativo para is_playing"""
    if args:
        state.is_playing = bool(int(args[0]))
        print(f"[OSC] is_playing: {state.is_playing}")

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
    """Handler catch-all - solo errores importantes"""
    if "/error" in address.lower():
        # Solo mostrar errores que NO sean de comandos que sabemos que no existen
        if "get/beat" not in str(args) and "playing_status" not in str(args):
            print(f"[OSC ERROR] {address}: {args}")

# ==============================
# HANDLERS DE CLIPS / OSC
# ==============================

track_clip_data = {}

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
        return

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