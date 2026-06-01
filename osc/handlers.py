# osc/handlers.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

from core.state import state, Locator, Track, Section, ClickEvent
from osc.client import send_message
from core.logger import log_info, log_error, log_warning, log_debug
import threading
import time
from typing import Dict, List, Optional

class OSCHandlers:
    """Manejadores OSC con sincronización thread-safe"""
    
    def __init__(self):
        self._clip_data: Dict[int, Dict] = {}
        self._lock = threading.RLock()  # Lock para sincronización
        self._processing_cue_points = False
        self._processing_clips = False
        self._clip_timestamps: Dict[str, float] = {}  # Timestamps para clips
        self._clip_timeout = 1.0  # Timeout de 1 segundo
        self._last_end_processed_idx = -1  # Para evitar loops infinitos al finalizar track
        self._triggered_click_beats: set = set()  # Beats de click ya disparados en esta sesión
        log_debug("OSCHandlers inicializado", module="OSC")
    
    def handle_cue_points(self, address, *args):
        """Procesa cue points - Thread-safe"""
        with self._lock:
            if self._processing_cue_points:
                log_warning("Ya procesando cue points, ignorando duplicado", module="OSC")
                return
            
            self._processing_cue_points = True
        
        try:
            log_info(f"📥 Cue points recibidos: {len(args)//2} locators", module="OSC")
            
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
                    log_error(f"Error procesando locator {i//2}", module="OSC", exc=e)
                    continue
            
            if not raw_locators:
                log_warning("No se procesaron locators válidos", module="OSC")
                return
            
            # Ordenar y reasignar IDs
            raw_locators.sort(key=lambda x: x.beat)
            for i, loc in enumerate(raw_locators):
                loc.id = i
            
            log_debug(f"Locators ordenados y reasignados: {len(raw_locators)}", module="OSC")
            
            with self._lock:
                state.locators = raw_locators
                self._build_track_structure(raw_locators)
                # Limpiar caché de datos antiguos al cargar nuevo track
                self._clip_data.clear()
                self._clip_timestamps.clear()
                self._triggered_click_beats.clear()
                self._last_end_processed_idx = -1

            log_debug("Limpiados datos de caché al cargar track nuevo", module="OSC")

            # Actualizar UI de forma segura
            self._safe_ui_update('update_listbox')
            
        except Exception as e:
            log_error("Error en handle_cue_points", module="OSC", exc=e)
        finally:
            with self._lock:
                self._processing_cue_points = False
    
    def _build_track_structure(self, locators: List[Locator]):
        """Construye estructura de tracks y eventos de click automation en un solo paso"""
        log_debug("Construyendo estructura de tracks...", module="OSC")

        # Si hay un setlist cargado manualmente, NO sobreescribir los tracks.
        # El scan OSC ordena por beat de Ableton y destruiría el orden personalizado.
        # Solo actualizamos locators (necesarios para los comandos OSC de play/jump).
        if state.setlist_loaded:
            log_info(
                "⚠️ Setlist cargado presente — el scan OSC NO sobreescribe tracks. "
                "Solo se actualizan locators de referencia.",
                module="OSC"
            )
            # Actualizar locators en estado para que play/jump funcionen vía OSC
            # pero NO reconstruir state.tracks (preservar orden del usuario)
            return

        new_tracks = []
        click_events = []
        current_track = None
        track_number = 0

        for loc in locators:
            # Normalizar: mayúsculas + sustituir guión bajo por espacio
            # Así "CLICK_OFF" y "CLICK OFF" son equivalentes
            name_norm = loc.name.upper().replace("_", " ").strip()

            if name_norm.startswith("START TRACK"):
                # Cerrar track anterior si quedó abierto
                if current_track:
                    log_warning(f"Track '{current_track.title}' sin END TRACK", module="OSC")
                    current_track.end = loc.beat
                    new_tracks.append(current_track)

                # Extraer título entre comillas
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
                    # bpm se detectará después en _scan_track_tempos()
                )
                log_debug(f"Track #{track_number}: '{title}' @ beat {loc.beat}", module="OSC")

            elif name_norm.startswith("END TRACK"):
                if current_track:
                    current_track.end = loc.beat
                    new_tracks.append(current_track)
                    log_debug(
                        f"✓ Track completado: '{current_track.title}' "
                        f"({current_track.end - current_track.start} beats)",
                        module="OSC"
                    )
                    current_track = None

            elif name_norm in ("CLICK ON", "CLICK OFF"):
                # Evento de automatización del metrónomo — funciona dentro O fuera de tracks
                enable = (name_norm == "CLICK ON")
                click_events.append(ClickEvent(beat=loc.beat, enable=enable))
                log_debug(
                    f"🎵 Click automation: {'ON' if enable else 'OFF'} @ beat {loc.beat}",
                    module="OSC"
                )

            elif current_track:
                # Cualquier otro locator dentro de un track = sección
                section = Section(name=loc.name.title(), beat=loc.beat)
                current_track.add_section(section)
                log_debug(f"Sección: '{section.name}' → '{current_track.title}'", module="OSC")

        # Cerrar último track si quedó sin END TRACK
        if current_track:
            last_beat = locators[-1].beat if locators else 0
            current_track.end = last_beat
            new_tracks.append(current_track)
            log_warning(
                f"Track '{current_track.title}' cerrado automáticamente (sin END TRACK)",
                module="OSC"
            )

        # Guardar resultados en el estado global
        state.tracks = new_tracks
        state.click_events = click_events

        log_info(
            f"✓ Estructura: {len(new_tracks)} tracks | "
            f"{len(click_events)} eventos de click automation",
            module="OSC"
        )
        for evt in click_events:
            log_info(f"   🎵 CLICK {'ON' if evt.enable else 'OFF'} @ beat {evt.beat}", module="OSC")

        # Ajustar current_index si es necesario
        if state.current_index >= len(new_tracks):
            old_index = state.current_index
            state.current_index = len(new_tracks) - 1 if new_tracks else -1
            log_debug(f"current_index ajustado: {old_index} → {state.current_index}", module="OSC")
    
    def handle_metronome(self, address, *args):
        """Maneja estado del metrónomo"""
        if args:
            with self._lock:
                state.metronome_on = bool(int(args[0]))
            log_info(f"🎵 Metrónomo: {'ON' if state.metronome_on else 'OFF'}", module="OSC")
            self._safe_ui_update('update_metronome_ui')
    
    def handle_song_time(self, address, *args):
        """Maneja el tiempo de canción - Optimizado"""
        if not args:
            return
        
        current_beat = int(args[0])
        current_exact_beat = float(args[0])
        
        # Rastrear si el beat ENTERO cambió — solo entonces pulsamos el beat indicator
        beat_changed = False
        
        with self._lock:
            # Evitar disparos duplicados del pulso visual
            if state.last_triggered_beat != current_beat:
                state.last_triggered_beat = current_beat
                beat_changed = True
            
            state.current_song_time = current_exact_beat
            
            # Lógica de fin de track (Auto-continue / Loop)
            if state.is_playing:
                current_track = state.get_current_track()
                if current_track and current_track.end > 0:
                    # Detectar con un pequeño margen si pasamos el final
                    if current_exact_beat >= current_track.end and current_exact_beat < current_track.end + 1.0:
                        # Asegurarnos de no dispararlo en repetición para el mismo play
                        if self._last_end_processed_idx != state.current_index:
                            self._last_end_processed_idx = state.current_index
                            
                            from core.playback import playback
                            
                            if getattr(current_track, 'loop_track', False):
                                # LOOP DE EMERGENCIA: salta atrás un compás completo
                                # (en lugar de reiniciar el track entero)
                                beats_per_bar = state.time_signature_num  # e.g. 4 en un 4/4
                                loop_start = max(current_track.start, current_exact_beat - beats_per_bar)
                                log_info(
                                    f"🚨 LOOP EMERGENCIA '{current_track.title}': "
                                    f"saltando a beat {loop_start:.1f} (compás de {beats_per_bar} beats)",
                                    module="OSC"
                                )
                                def do_loop(beat):
                                    from osc.client import send_message as _send
                                    import time as _time
                                    _send("/live/song/set/current_song_time", [beat])
                                    _time.sleep(0.05)
                                    _send("/live/song/continue_playing", [])
                                threading.Thread(target=do_loop, args=(loop_start,), daemon=True).start()
                                # Resetear para que detecte el próximo fin de compás
                                self._last_end_processed_idx = -1
                            elif getattr(current_track, 'auto_continue', False):
                                log_info(f"⏭ Auto-continue: pasando a la siguiente canción.", module="OSC")
                                threading.Thread(target=playback.next_track, daemon=True).start()
                            else:
                                log_info(f"⏹ Fin de track '{current_track.title}'. Deteniendo.", module="OSC")
                                threading.Thread(target=playback.stop, daemon=True).start()
            # ---- AUTOMATIZACIÓN CLICK ON/OFF ----
            # Comprobar si el beat actual activa algún evento de click
            if state.is_playing:
                # Calcular ventana de tolerancia dinámicamente basada en tempo
                if state.current_tempo > 0:
                    beat_duration_seconds = 60 / state.current_tempo
                    tolerance_seconds = 0.1  # 100ms ventana independiente del tempo
                    tolerance_beats = tolerance_seconds / beat_duration_seconds
                else:
                    tolerance_beats = 0.3  # Default si tempo no disponible

                for evt in state.click_events:
                    # Ventana dinámica para evitar capturar eventos no deseados a BPM altos
                    if abs(current_exact_beat - evt.beat) <= tolerance_beats and evt.beat not in self._triggered_click_beats:
                        self._triggered_click_beats.add(evt.beat)
                        target_value = 1 if evt.enable else 0
                        label = "ON" if evt.enable else "OFF"
                        log_info(f"🎵 Click automation: CLICK {label} @ beat {evt.beat:.1f} (ventana: ±{tolerance_beats:.2f})", module="OSC")

                        def _fire_click(val):
                            try:
                                send_message("/live/song/set/metronome", [val])
                                with state._lock:
                                    state.metronome_on = bool(val)
                            except Exception as e:
                                log_error(f"Click automation failed: {e}", module="OSC", exc=e)

                        threading.Thread(target=_fire_click, args=(target_value,), daemon=True).start()
                        self._safe_ui_update('update_metronome_ui')

        if beat_changed and current_beat % 4 == 0:
            log_debug(f"Beat: {current_beat}", module="OSC")
        
        # Solo actualizar el pulso visual cuando el beat ENTERO cambia
        # Ableton envía song_time decenas de veces por beat (posiciones decimales)
        # disparar en cada mensaje causaba el comportamiento glitchy
        if beat_changed:
            self._safe_ui_update('trigger_pulse', current_beat)
    
    def handle_playing_status(self, address, *args):
        """Maneja el estado de reproducción"""
        if args:
            new_status = bool(int(args[0]))
            with self._lock:
                old_status = state.is_playing
                state.is_playing = new_status
                
                # Resetear marca de procesamiento de final si detenemos o empezamos de nuevo
                if not new_status or old_status != new_status:
                    self._last_end_processed_idx = -1
                    self._triggered_click_beats.clear()  # Permitir re-disparar en el próximo play
            
            # Log solo si cambió
            if old_status != new_status:
                log_info(f"🎮 Estado: {'▶ Playing' if new_status else '■ Stopped'}", module="OSC")
    
    def handle_tempo(self, address, *args):
        """Maneja cambios de tempo"""
        if args:
            new_tempo = float(args[0])
            with self._lock:
                old_tempo = state.current_tempo
                state.current_tempo = new_tempo
            
            # Log solo si cambió significativamente
            if abs(new_tempo - old_tempo) > 0.1:
                log_info(f"🎼 Tempo: {new_tempo:.1f} BPM", module="OSC")
            
            self._safe_ui_update('update_tempo_display')
    
    def handle_time_signature(self, address, *args):
        """Maneja cambios de time signature"""
        if args:
            new_sig = int(args[0])
            with self._lock:
                old_sig = state.time_signature_num
                state.time_signature_num = new_sig
            
            # Log solo si cambió
            if new_sig != old_sig:
                log_info(f"🎵 Time signature: {new_sig}/4", module="OSC")
            
            self._safe_ui_update('update_tempo_display')
    
    def handle_beat(self, address, *args):
        """Maneja el beat actual (método alternativo)"""
        if args:
            current_beat = int(args[0])
            with self._lock:
                state.current_beat = current_beat
            
            # Log reducido para evitar spam
            if current_beat % 8 == 0:
                log_debug(f"Beat actualizado: {current_beat}", module="OSC")
            
            self._safe_ui_update('trigger_pulse', current_beat)
    
    def handle_clip_names(self, address, *args):
        """Maneja nombres de clips"""
        if len(args) < 2:
            log_warning("handle_clip_names: datos insuficientes", module="OSC")
            return
        
        track_index = args[0]
        clip_names = [n for n in args[1:] if n and str(n).lower() != "none"]
        
        # DEBUG: Ver datos crudos
        log_debug(f"📋 RAW nombres ({len(args[1:])}): {args[1:][:5]}...", module="OSC")
        
        with self._lock:
            self._clip_data.setdefault(track_index, {})["names"] = clip_names
            self._clip_timestamps[f"names_{track_index}"] = time.time()
            log_info(f"📋 Clips recibidos: {len(clip_names)} nombres para track {track_index}", module="OSC")
        
        self._try_assign_clips(track_index)
    
    def handle_clip_times(self, address, *args):
        """Maneja tiempos de clips"""
        if len(args) < 2:
            log_warning("handle_clip_times: datos insuficientes", module="OSC")
            return
        
        track_index = args[0]
        clip_times = [float(t) for t in args[1:]]
        
        # DEBUG: Ver datos crudos
        log_debug(f"⏱️  RAW tiempos ({len(clip_times)}): {clip_times[:5]}...", module="OSC")
        
        with self._lock:
            self._clip_data.setdefault(track_index, {})["times"] = clip_times
            self._clip_timestamps[f"times_{track_index}"] = time.time()
            log_info(f"⏱️  Clips recibidos: {len(clip_times)} tiempos para track {track_index}", module="OSC")
        
        self._try_assign_clips(track_index)
    
    def _try_assign_clips(self, track_index: int):
        """Intenta asignar clips si hay datos completos - Thread-safe"""
        with self._lock:
            if self._processing_clips:
                log_warning("Ya procesando clips, ignorando duplicado", module="OSC")
                return
            
            data = self._clip_data.get(track_index, {})
            names = data.get("names")
            times = data.get("times")
            
            if not names or not times:
                log_debug(f"Datos incompletos para track {track_index} (esperando más datos)", module="OSC")
                return
            
            # Verificar que ambos datos sean recientes
            names_time = self._clip_timestamps.get(f"names_{track_index}", 0)
            times_time = self._clip_timestamps.get(f"times_{track_index}", 0)
            current_time = time.time()
            
            # Si alguno es muy viejo, descartarlo
            if (current_time - names_time) > self._clip_timeout or \
               (current_time - times_time) > self._clip_timeout:
                log_warning(
                    f"⏰ Datos de clips obsoletos para track {track_index}, descartando",
                    module="OSC"
                )
                self._clip_data[track_index] = {}
                return
            
            # EMPAREJAMIENTO INTELIGENTE: No hacer return si hay desajuste
            if len(names) != len(times):
                min_length = min(len(names), len(times))
                log_warning(
                    f"⚠️  Desajuste de clips: {len(names)} nombres vs {len(times)} tiempos "
                    f"- emparejando los primeros {min_length}",
                    module="OSC"
                )
                # Recortar al tamaño mínimo
                names = names[:min_length]
                times = times[:min_length]
            
            self._processing_clips = True
        
        try:
            self._assign_clips_to_tracks(names, times, track_index)
        except Exception as e:
            log_error("Error asignando clips a tracks", module="OSC", exc=e)
        finally:
            with self._lock:
                self._processing_clips = False
                # Limpiar datos después de procesar
                if track_index in self._clip_data:
                    self._clip_data[track_index] = {}
                # Limpiar timestamps
                self._clip_timestamps.pop(f"names_{track_index}", None)
                self._clip_timestamps.pop(f"times_{track_index}", None)
    
    def _assign_clips_to_tracks(self, names: List[str], times: List[float], source_track_index: int):
        """Asigna clips a tracks - NO limpia secciones existentes"""
        with self._lock:
            if not state.tracks:
                log_warning("No hay tracks disponibles para asignar clips", module="OSC")
                return
            
            log_info(f"🔗 Asignando {len(names)} clips del track {source_track_index}", module="OSC")
            
            assigned_count = 0
            skipped_count = 0
            
            for name, time_val in zip(names, times):
                track = state.find_track_by_beat(float(time_val))
                if track:
                    # Verificar si la sección ya existe
                    exists = any(s.beat == float(time_val) for s in track.sections)
                    if not exists:
                        section = Section(name=name, beat=float(time_val), time=float(time_val))
                        track.add_section(section)
                        assigned_count += 1
                        log_debug(f"✓ '{name}' → {track.title}", module="OSC")
                    else:
                        log_debug(f"⊘ '{name}' ya existe en {track.title}", module="OSC")
                else:
                    skipped_count += 1
                    log_warning(f"✗ '{name}' @ beat {time_val} fuera de rango de tracks", module="OSC")
            
            log_info(f"✓ Clips asignados: {assigned_count}, Omitidos: {skipped_count}", module="OSC")
        
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
                log_warning(f"UI update falló para {method_name}: {error_msg}", module="OSC")
                    
    def handle_error(self, address, *args):
        """Maneja errores relevantes"""
        if "/error" in address.lower():
            # Filtrar errores conocidos/esperados
            msg = str(args)
            if "get/beat" not in msg and "playing_status" not in msg:
                log_error(f"OSC Error en {address}: {args}", module="OSC")

# Instancia global
handlers = OSCHandlers()
log_info("✓ Instancia global de OSCHandlers creada", module="OSC")