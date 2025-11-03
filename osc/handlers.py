# osc/handlers.py
from core.state import state, Locator, Track, Section
from osc.client import send_message
import threading
from typing import Dict, List, Optional

class OSCHandlers:
    """Manejadores OSC con sincronización thread-safe"""
    
    def __init__(self):
        self._clip_data: Dict[int, Dict] = {}
        self._lock = threading.RLock()  # Lock para sincronización
        self._processing_cue_points = False
        self._processing_clips = False
    
    def handle_cue_points(self, address, *args):
        """Procesa cue points - Thread-safe"""
        with self._lock:
            if self._processing_cue_points:
                print("[WARN] Ya procesando cue points, ignorando...")
                return
            
            self._processing_cue_points = True
        
        try:
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
                    print(f"[ERROR] Procesando locator {i//2}: {e}")
                    continue
            
            if not raw_locators:
                print("[WARN] No se procesaron locators válidos")
                return
            
            # Ordenar y reasignar IDs
            raw_locators.sort(key=lambda x: x.beat)
            for i, loc in enumerate(raw_locators):
                loc.id = i
            
            with self._lock:
                state.locators = raw_locators
                self._build_track_structure(raw_locators)
            
            # Actualizar UI de forma segura
            self._safe_ui_update('update_listbox')
            
        except Exception as e:
            print(f"[ERROR] handle_cue_points: {e}")
            import traceback
            traceback.print_exc()
        finally:
            with self._lock:
                self._processing_cue_points = False
    
    def _build_track_structure(self, locators: List[Locator]):
        """Construye estructura de tracks - Debe llamarse con lock"""
        new_tracks = []
        current_track = None
        track_number = 0
        
        for loc in locators:
            name_upper = loc.name.upper()
            
            if name_upper.startswith("START TRACK"):
                # Cerrar track anterior
                if current_track:
                    print(f"[WARN] Track '{current_track.title}' sin END TRACK")
                    current_track.end = loc.beat
                    new_tracks.append(current_track)
                
                # Extraer título
                title = "Untitled"
                if '"' in loc.name:
                    parts = loc.name.split('"')
                    if len(parts) >= 2:
                        title = parts[1].strip()
                
                track_number += 1
                current_track = Track(
                    title=title,
                    start=loc.beat,
                    end=0,
                    track_number=track_number,
                    start_locator_id=loc.original_id
                )
                print(f"[PARSE] Track #{track_number}: '{title}' @ beat {loc.beat}")
            
            elif name_upper.startswith("END TRACK"):
                if current_track:
                    current_track.end = loc.beat
                    new_tracks.append(current_track)
                    print(f"[PARSE] ✓ Track completado: '{current_track.title}'")
                    current_track = None
            
            elif current_track and not loc.is_click_toggle:
                # Agregar como sección
                section = Section(name=loc.name.title(), beat=loc.beat)
                current_track.add_section(section)
        
        # Cerrar último track
        if current_track:
            last_beat = locators[-1].beat if locators else 0
            current_track.end = last_beat
            new_tracks.append(current_track)
        
        # Actualizar state de forma atómica
        state.tracks = new_tracks
        print(f"[OSC] ✓ Tracks detectados: {len(new_tracks)}")
        
        # Ajustar current_index si es necesario
        if state.current_index >= len(new_tracks):
            state.current_index = len(new_tracks) - 1 if new_tracks else -1
    
    def handle_metronome(self, address, *args):
        """Maneja estado del metrónomo"""
        if args:
            with self._lock:
                state.metronome_on = bool(int(args[0]))
            print(f"[OSC] Metrónomo: {'ON' if state.metronome_on else 'OFF'}")
            self._safe_ui_update('update_metronome_ui')
    
    def handle_song_time(self, address, *args):
        """Maneja el tiempo de canción - Optimizado"""
        if not args:
            return
        
        current_beat = int(args[0])
        
        with self._lock:
            # Evitar disparos duplicados
            if state.last_triggered_beat == current_beat:
                return
            state.last_triggered_beat = current_beat
            state.current_song_time = args[0]
        
        # Actualizar UI (trigger_pulse y progress son thread-safe)
        self._safe_ui_update('trigger_pulse', current_beat)
    
    def handle_playing_status(self, address, *args):
        """Maneja el estado de reproducción"""
        if args:
            with self._lock:
                state.is_playing = bool(int(args[0]))
            print(f"[OSC] is_playing: {state.is_playing}")
    
    def handle_tempo(self, address, *args):
        """Maneja cambios de tempo"""
        if args:
            with self._lock:
                state.current_tempo = float(args[0])
            print(f"[OSC] Tempo: {state.current_tempo} BPM")
            self._safe_ui_update('update_tempo_display')
    
    def handle_time_signature(self, address, *args):
        """Maneja cambios de time signature"""
        if args:
            with self._lock:
                state.time_signature_num = int(args[0])
            print(f"[OSC] Time signature: {state.time_signature_num}/4")
            self._safe_ui_update('update_tempo_display')
    
    def handle_beat(self, address, *args):
        """Maneja el beat actual (método alternativo)"""
        if args:
            current_beat = int(args[0])
            with self._lock:
                state.current_beat = current_beat
            self._safe_ui_update('trigger_pulse', current_beat)
    
    def handle_clip_names(self, address, *args):
        """Maneja nombres de clips"""
        if len(args) < 2:
            return
        
        track_index = args[0]
        clip_names = [n for n in args[1:] if n and str(n).lower() != "none"]
        
        with self._lock:
            self._clip_data.setdefault(track_index, {})["names"] = clip_names
            print(f"[CLIPS] Recibidos {len(clip_names)} nombres para track {track_index}")
        
        self._try_assign_clips(track_index)
    
    def handle_clip_times(self, address, *args):
        """Maneja tiempos de clips"""
        if len(args) < 2:
            return
        
        track_index = args[0]
        clip_times = [float(t) for t in args[1:]]
        
        with self._lock:
            self._clip_data.setdefault(track_index, {})["times"] = clip_times
            print(f"[CLIPS] Recibidos {len(clip_times)} tiempos para track {track_index}")
        
        self._try_assign_clips(track_index)
    
    def _try_assign_clips(self, track_index: int):
        """Intenta asignar clips si hay datos completos - Thread-safe"""
        with self._lock:
            if self._processing_clips:
                print("[WARN] Ya procesando clips, ignorando...")
                return
            
            data = self._clip_data.get(track_index, {})
            names = data.get("names")
            times = data.get("times")
            
            if not names or not times:
                print(f"[CLIPS] Datos incompletos para track {track_index}")
                return
            
            if len(names) != len(times):
                print(f"[WARN] Desajuste: {len(names)} nombres vs {len(times)} tiempos")
                return
            
            self._processing_clips = True
        
        try:
            self._assign_clips_to_tracks(names, times, track_index)
        except Exception as e:
            print(f"[ERROR] Asignando clips: {e}")
            import traceback
            traceback.print_exc()
        finally:
            with self._lock:
                self._processing_clips = False
                # Limpiar datos solo después de procesar exitosamente
                if track_index in self._clip_data:
                    self._clip_data[track_index] = {}
    
    def _assign_clips_to_tracks(self, names: List[str], times: List[float], source_track_index: int):
        """Asigna clips a tracks - NO limpia secciones existentes"""
        with self._lock:
            if not state.tracks:
                print("[WARN] No hay tracks disponibles")
                return
            
            print(f"[CLIPS] Asignando {len(names)} clips del track {source_track_index}")
            
            assigned_count = 0
            skipped_count = 0
            
            for name, time in zip(names, times):
                track = state.find_track_by_beat(float(time))
                if track:
                    # Verificar si la sección ya existe
                    exists = any(s.beat == float(time) for s in track.sections)
                    if not exists:
                        section = Section(name=name, beat=float(time), time=float(time))
                        track.add_section(section)
                        assigned_count += 1
                        print(f"[CLIPS] ✓ '{name}' → {track.title}")
                    else:
                        print(f"[CLIPS] ⊘ '{name}' ya existe en {track.title}")
                else:
                    skipped_count += 1
                    print(f"[CLIPS] ✗ '{name}' @ {time} fuera de rango")
            
            print(f"[CLIPS] Asignados: {assigned_count}, Omitidos: {skipped_count}")
        
        # Actualizar UI
        self._safe_ui_update('update_listbox')
    
    def _safe_ui_update(self, method_name: str, *args):
        """Actualiza UI de forma thread-safe con validación"""
        if not state.page_ref:
            return
        
        try:
            # Validar que page_ref esté viva
            if not hasattr(state.page_ref, 'update'):
                return
            
            method = getattr(state.page_ref, method_name, None)
            if method and callable(method):
                method(*args)
        except AttributeError:
            # El objeto fue destruido, ignorar
            pass
        except Exception as e:
            error_msg = str(e)
            # Ignorar errores de objetos eliminados o async
            if "__uid" not in error_msg and "update_async" not in error_msg:
                print(f"[UI UPDATE ERROR] {method_name}: {e}")
                    
    def handle_error(self, address, *args):
        """Maneja errores relevantes"""
        if "/error" in address.lower():
            # Filtrar errores conocidos/esperados
            msg = str(args)
            if "get/beat" not in msg and "playing_status" not in msg:
                print(f"[OSC ERROR] {address}: {args}")

# Instancia global
handlers = OSCHandlers()