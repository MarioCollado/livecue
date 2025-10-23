# osc/handlers.py
from core import state
from core import utils
from setlist import manager as setlist_manager  # por si queremos extender
import time

def cue_handler(address, *args):
    # actualiza state.locators y dispara update_listbox si existe page_ref
    print(f"\n[OSC] ✓ Cue points recibidos: {len(args)//2} locators")
    state.locators = []
    for i in range(0, len(args), 2):
        try:
            name = args[i]
            beat = args[i+1]
            state.locators.append({"id": i//2, "name": name, "beat": beat})
            print(f"  - Locator {i//2}: {name} @ beat {beat}")
        except Exception as e:
            print(f"Error procesando locator: {e}")
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
