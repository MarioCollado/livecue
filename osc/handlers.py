# osc/handlers.py
from core.state import state, Locator, Track, Section
from osc.client import send_message

class OSCHandlers:
    """Manejadores OSC consolidados"""
    
    def __init__(self):
        self._clip_data = {}  # Datos temporales de clips
    
    def handle_cue_points(self, address, *args):
        """Procesa cue points y construye estructura de tracks"""
        print(f"\n[OSC] ✓ Cue points recibidos: {len(args)//2} locators")
        
        # Parsear locators
        raw_locators = []
        for i in range(0, len(args), 2):
            try:
                raw_locators.append(Locator(
                    id=i // 2,
                    original_id=i // 2,
                    name=args[i].strip(),
                    beat=args[i + 1]
                ))
            except Exception as e:
                print(f"Error procesando locator: {e}")
        
        # Ordenar por beat y reasignar IDs
        raw_locators.sort(key=lambda x: x.beat)
        for i, loc in enumerate(raw_locators):
            loc.id = i
        
        state.locators = raw_locators
        self._build_track_structure(raw_locators)
        
        if state.page_ref and hasattr(state.page_ref, 'update_listbox'):
            state.page_ref.update_listbox()
    
    def _build_track_structure(self, locators: list):
        """Construye la estructura jerárquica de tracks"""
        state.tracks.clear()
        current_track = None
        track_number = 0
        
        for loc in locators:
            name_upper = loc.name.upper()
            
            if name_upper.startswith("START TRACK"):
                # Cerrar track anterior si existe
                if current_track:
                    print(f"[WARN] Track '{current_track.title}' sin END TRACK")
                    current_track.end = loc.beat
                    state.tracks.append(current_track)
                
                # Extraer título
                title = "Untitled"
                if '"' in loc.name:
                    parts = loc.name.split('"')
                    if len(parts) >= 2:
                        title = parts[1]
                
                track_number += 1
                current_track = Track(
                    title=title,
                    start=loc.beat,
                    end=0,  # Se asignará después
                    track_number=track_number,
                    start_locator_id=loc.original_id
                )
                print(f"[PARSE] Track #{track_number}: '{title}' @ beat {loc.beat}")
            
            elif name_upper.startswith("END TRACK"):
                if current_track:
                    current_track.end = loc.beat
                    state.tracks.append(current_track)
                    print(f"[PARSE] ✓ Track completado: '{current_track.title}'")
                    current_track = None
            
            elif current_track and not loc.is_click_toggle:
                # Agregar como sección
                section = Section(
                    name=loc.name.title(),
                    beat=loc.beat
                )
                current_track.add_section(section)
        
        # Cerrar último track si quedó abierto
        if current_track:
            current_track.end = locators[-1].beat if locators else 0
            state.tracks.append(current_track)
        
        print(f"[OSC] ✓ Tracks detectados: {len(state.tracks)}")
    
    def handle_metronome(self, address, *args):
        """Maneja estado del metrónomo"""
        if args:
            state.metronome_on = bool(int(args[0]))
            print(f"[OSC] Metrónomo: {'ON' if state.metronome_on else 'OFF'}")
            if state.page_ref:
                state.page_ref.update_metronome_ui()
    
    def handle_song_time(self, address, *args):
        """Maneja el tiempo de canción y dispara actualizaciones"""
        if not args:
            return
        
        current_beat = int(args[0])
        state.current_song_time = args[0]
        
        # Evitar disparos duplicados
        if state.last_triggered_beat == current_beat:
            return
        state.last_triggered_beat = current_beat
        
        # Actualizar UI
        if state.page_ref:
            state.page_ref.trigger_pulse(current_beat)
            state.page_ref.update_track_progress(current_beat)
    
    def handle_playing_status(self, address, *args):
        """Maneja el estado de reproducción"""
        if args:
            state.is_playing = bool(int(args[0]))
            print(f"[OSC] is_playing: {state.is_playing}")
    
    def handle_tempo(self, address, *args):
        """Maneja cambios de tempo"""
        if args:
            state.current_tempo = float(args[0])
            print(f"[OSC] Tempo: {state.current_tempo} BPM")
            if state.page_ref:
                state.page_ref.update_tempo_display()
    
    def handle_time_signature(self, address, *args):
        """Maneja cambios de time signature"""
        if args:
            state.time_signature_num = int(args[0])
            print(f"[OSC] Time signature: {state.time_signature_num}/4")
            if state.page_ref:
                state.page_ref.update_tempo_display()
    
    def handle_beat(self, address, *args):
        """Maneja el beat actual (método alternativo)"""
        if args:
            state.current_beat = int(args[0])
            if state.page_ref:
                state.page_ref.trigger_pulse(state.current_beat)
    
    def handle_clip_names(self, address, *args):
        """Maneja nombres de clips"""
        track_index = args[0]
        clip_names = [n for n in args[1:] if n and str(n).lower() != "none"]
        self._clip_data.setdefault(track_index, {})["names"] = clip_names
        self._assign_clips_if_ready(track_index)
    
    def handle_clip_times(self, address, *args):
        """Maneja tiempos de clips"""
        track_index = args[0]
        clip_times = [float(t) for t in args[1:]]
        self._clip_data.setdefault(track_index, {})["times"] = clip_times
        self._assign_clips_if_ready(track_index)
    
    def _assign_clips_if_ready(self, track_index: int):
        """Asigna clips a tracks cuando hay datos completos"""
        data = self._clip_data.get(track_index, {})
        names = data.get("names")
        times = data.get("times")
        
        if not names or not times:
            return
        
        # Limpiar secciones existentes
        for track in state.tracks:
            track.sections.clear()
        
        print(f"[OSC] ✓ Asignando {len(names)} clips del track {track_index}")
        
        # Asignar clips a tracks
        for name, time in zip(names, times):
            track = state.find_track_by_beat(float(time))
            if track:
                section = Section(name=name, beat=float(time), time=float(time))
                track.add_section(section)
                print(f"[CLIPS] ✓ '{name}' → {track.title}")
            else:
                print(f"[CLIPS] ✗ '{name}' fuera de rango")
        
        # Limpiar datos temporales
        self._clip_data[track_index] = {}
        
        # Actualizar UI
        if state.page_ref:
            state.page_ref.update_listbox()
    
    def handle_error(self, address, *args):
        """Maneja errores relevantes"""
        if "/error" in address.lower():
            if "get/beat" not in str(args) and "playing_status" not in str(args):
                print(f"[OSC ERROR] {address}: {args}")

# Instancia global
handlers = OSCHandlers()