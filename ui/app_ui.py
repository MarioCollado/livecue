# Copyright (c) 2025 Mario Collado Rodríguez - MIT License

# ui/app_ui.py
import flet as ft
import time
import threading
import asyncio
from core.state import state
from core.playback import playback
from setlist.manager import manager
from ui.themes import ThemeManager
from ui.components import BeatIndicator, TempoDisplay, StatusBar, MetronomeButton 
from ui.header_component import create_header, SetTimer
from version_info import APP_VERSION

DEBOUNCE_NAV_MS = 300

# ============================================
# SAFE UI UPDATE - SYNC VERSION
# ============================================
def safe_ui_update_sync(page_ref):
    """Versión SÍNCRONA segura con retry"""
    if not page_ref:
        return False

    max_retries = 3
    for attempt in range(max_retries):
        try:
            if not hasattr(page_ref, 'update'):
                return False

            if hasattr(page_ref, 'window') and page_ref.window is None:
                return False

            page_ref.update()
            return True

        except AssertionError as e:
            # Este es el error específico que estás teniendo
            print(f"[SAFE_UI_UPDATE] AssertionError en intento {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(0.05)  # Pequeña pausa antes de reintentar
                continue
            return False
            
        except Exception as e:
            error_msg = str(e)
            if "__uid" not in error_msg and "update_async" not in error_msg:
                print(f"[SAFE_UI_UPDATE ERROR] {error_msg}")
            return False
    
    return False
    
# ============================================
# TRACK LIST VIEW - CORREGIDO
# ============================================
class TrackListView:
    instance = None
    
    def __init__(self, theme: ThemeManager, page: ft.Page):
        self.theme = theme
        self.page = page
        self.drag_state = {"dragging_index": None}
        self.column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self._update_lock = threading.Lock()
    
    async def update(self):
        """Update async con protección contra controles corruptos"""
        if not self._update_lock.acquire(blocking=False):
            print("[UI] Update ya en progreso, ignorando...")
            return
        
        try:
            # Validaciones básicas
            if not self.page:
                print("[UI] Page es None")
                return

            if hasattr(self.page, 'window') and self.page.window is None:
                print("[UI] Ventana cerrada")
                return

            if not hasattr(self.page, 'controls') or not self.page.controls:
                print("[UI] Page sin controles inicializados")
                return

            # NUEVO: Obtener tracks ANTES de limpiar
            tracks = state.tracks
            
            if not tracks:
                print("[UI] No hay tracks para mostrar")
                # Limpiar solo si hay algo que limpiar
                if len(self.column.controls) > 0:
                    self.column.controls.clear()
                    try:
                        self.page.update()
                    except:
                        pass
                return

            # NUEVO: Crear TODOS los items primero (sin modificar column)
            new_items = []
            for idx, track in enumerate(tracks):
                try:
                    item = self._create_track_item(idx, track)
                    new_items.append(item)
                except Exception as e:
                    print(f"[UI] Error creando item {idx}: {e}")
                    continue

            # Si no se crearon items, abortar
            if not new_items:
                print("[UI] No se pudieron crear items")
                return

            # CRÍTICO: Limpiar y asignar en una sola operación
            try:
                self.column.controls = new_items  # REEMPLAZAR en lugar de clear + append
                self.page.update()
                print(f"[UI] ✓ Lista actualizada: {len(tracks)} tracks")
            except AssertionError as e:
                print(f"[UI] AssertionError en update: {e}")
                # FALLBACK: Intentar reconstruir desde cero
                await self._rebuild_from_scratch(tracks)
            except Exception as e:
                print(f"[UI] Error en page.update: {e}")

        except Exception as e:
            print(f"[ERROR] TrackListView.update: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._update_lock.release()

    async def _rebuild_from_scratch(self, tracks):
        """Reconstruye la lista desde cero en caso de corrupción"""
        try:
            print("[UI] Reconstruyendo lista desde cero...")
            
            # Crear nueva columna
            new_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
            
            # Crear items
            for idx, track in enumerate(tracks):
                try:
                    new_column.controls.append(self._create_track_item(idx, track))
                except Exception as e:
                    print(f"[UI] Error recreando item {idx}: {e}")
                    continue
            
            # Reemplazar columna completa
            if hasattr(self, 'column') and self.column:
                # Obtener el contenedor padre (listbox_container)
                parent = None
                for control in self.page.controls:
                    if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                        for row in control.content.controls:
                            if hasattr(row, 'controls'):
                                for col in row.controls:
                                    if hasattr(col, 'content') and col.content == self.column:
                                        parent = col
                                        break
                
                if parent:
                    parent.content = new_column
                    self.column = new_column
                    self.page.update()
                    print("[UI] ✓ Lista reconstruida correctamente")
                else:
                    print("[UI] ✗ No se encontró contenedor padre")
            
        except Exception as e:
            print(f"[ERROR] _rebuild_from_scratch: {e}")
            import traceback
            traceback.print_exc()

    def _create_track_item(self, track_index: int, track):
        """Crea un item de track con validación"""
        try:
            is_selected = track_index == state.current_index
            has_sections = len(track.sections) > 0
            is_expanded = track.expanded
            
            header = self._create_track_header(track_index, track, is_selected, has_sections, is_expanded)
            sections = self._create_sections(track_index, track) if is_expanded and has_sections else None
            
            track_column = ft.Column(spacing=0, controls=[header] + ([sections] if sections else []))
            
            # Validar que header se creó correctamente
            if not header:
                raise ValueError(f"Header nulo para track {track_index}")
            
            drag_target = ft.DragTarget(
                group="tracks",
                content=track_column,
                on_will_accept=self._on_will_accept_drag,
                on_accept=self._create_drag_accept_handler(track_index),
                on_leave=self._on_drag_leave
            )
            
            draggable = ft.Draggable(
                group="tracks",
                content=drag_target,
                content_feedback=self._create_drag_feedback(track_index, track),
                on_drag_start=self._create_drag_start_handler(track_index)
            )
            
            return draggable
            
        except Exception as e:
            print(f"[ERROR] _create_track_item({track_index}): {e}")
            # Devolver un container de placeholder en caso de error
            return ft.Container(
                content=ft.Text(f"Error: Track {track_index + 1}", color=ft.Colors.RED),
                padding=10
            )
        
    def _create_track_header(self, track_index, track, is_selected, has_sections, is_expanded):
        return ft.Container(
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    f"{track_index + 1:02d}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE if is_selected else self.theme.get("text_primary"),
                                ),
                                width=36,
                                height=36,
                                border_radius=18,
                                bgcolor=self.theme.get("accent") if is_selected else self.theme.get("bg_secondary"),
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(width=12),
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        track.title,
                                        size=15,
                                        weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500,
                                        color=self.theme.get("text_primary")
                                    ),
                                    ft.Text(
                                        f"{len(track.sections)} sections",
                                        size=11,
                                        color=self.theme.get("text_secondary"),
                                        visible=has_sections
                                    )
                                ]
                            ),
                            ft.IconButton(
                                icon=ft.Icons.KEYBOARD_ARROW_DOWN if not is_expanded else ft.Icons.KEYBOARD_ARROW_UP,
                                icon_size=18,
                                on_click=self._create_toggle_expand_handler(track_index),  # CORREGIDO
                                visible=has_sections,
                                icon_color=self.theme.get("accent"),
                            ),
                            ft.Icon(ft.Icons.DRAG_HANDLE, size=18, color=self.theme.get("text_secondary"), opacity=0.3)
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        width=None,
                        height=2,
                        bgcolor=self.theme.get("accent"),
                        margin=ft.margin.only(top=6),
                        visible=is_selected
                    )
                ]
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            border_radius=12,
            bgcolor=self.theme.get("bg_card") if is_selected else self.theme.get("bg_card"),
            on_click=self._create_track_click_handler(track_index),  # CORREGIDO
        )

    def _create_sections(self, track_index, track):
        section_items = []
        for sec_idx, section in enumerate(track.sections):
            section_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(width=48),
                            ft.Container(width=2, height=28, bgcolor=self.theme.get("accent"), opacity=0.4),
                            ft.Container(width=10),
                            ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, size=16, color=self.theme.get("accent"), opacity=0.7),
                            ft.Container(width=8),
                            ft.Text(section.name, size=13, weight=ft.FontWeight.W_500, expand=True, color=self.theme.get("text_primary"))
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    border_radius=8,
                    bgcolor=self.theme.get("bg_secondary"),
                    on_click=self._create_section_click_handler(track_index, sec_idx),  # CORREGIDO
                    ink=True,
                )
            )
        return ft.Container(content=ft.Column(spacing=4, controls=section_items), padding=ft.padding.only(top=8))

    def _create_drag_feedback(self, track_index, track):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"{track_index + 1}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Container(width=10),
                    ft.Text(track.title, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
                ],
                spacing=0
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            width=320,
            border_radius=10,
            bgcolor=self.theme.get("accent"),
            opacity=0.95
        )

    # ============================================
    # HANDLERS CORREGIDOS - Sin lambdas problemáticas
    # ============================================
    def _create_track_click_handler(self, track_index):
        """Crea handler para click en track"""
        def handler(e):
            self.page.run_task(self._on_track_click, track_index)
        return handler

    def _create_toggle_expand_handler(self, track_index):
        """Crea handler para toggle expand"""
        def handler(e):
            self.page.run_task(self._toggle_expand, track_index)
        return handler

    def _create_section_click_handler(self, track_index, section_index):
        """Crea handler para click en sección"""
        def handler(e):
            self.page.run_task(self._on_section_click, track_index, section_index)
        return handler

    def _create_drag_start_handler(self, track_index):
        """Crea handler para drag start"""
        def handler(e):
            self._on_drag_start(track_index)
        return handler

    def _create_drag_accept_handler(self, target_index):
        """Crea handler para drag accept"""
        def handler(e):
            self.page.run_task(self._on_drag_accept, target_index)
        return handler

    # ============================================
    # DRAG & DROP CALLBACKS
    # ============================================
# REEMPLAZAR estos 3 métodos en TrackListView

    def _on_will_accept_drag(self, e):
        """Valida si se puede aceptar el drop"""
        e.control.content.opacity = 0.5
        try:
            e.control.update()
        except:
            pass

    def _on_drag_leave(self, e):
        """Restaura opacidad cuando sale del drop zone"""
        e.control.content.opacity = 1.0
        try:
            e.control.update()
        except:
            pass

    def _on_drag_start(self, track_index):
        """Inicio de drag - SÍNCRONO"""
        self.drag_state["dragging_index"] = track_index
        print(f"[DRAG] Iniciando drag de track {track_index}")

    async def _on_drag_accept(self, target_index):
        """Acepta el drop y reordena - ASYNC con protección"""
        start_idx = self.drag_state.get("dragging_index")
        
        if start_idx is None:
            print("[DRAG] Error: No hay índice de inicio")
            return
        
        if start_idx == target_index:
            print(f"[DRAG] Mismo índice, ignorando")
            self.drag_state["dragging_index"] = None
            return
        
        try:
            print(f"[DRAG] Reordenando: {start_idx} -> {target_index}")
            
            # Validar índices
            tracks_list = state.tracks
            
            if not (0 <= start_idx < len(tracks_list)):
                print(f"[DRAG] Error: start_idx {start_idx} fuera de rango")
                return
            
            if not (0 <= target_index < len(tracks_list)):
                print(f"[DRAG] Error: target_index {target_index} fuera de rango")
                return
            
            # Reordenar
            moved_track = tracks_list.pop(start_idx)
            tracks_list.insert(target_index, moved_track)
            state.tracks = tracks_list
            
            # Ajustar current_index
            if state.current_index == start_idx:
                state.current_index = target_index
            elif start_idx < state.current_index <= target_index:
                state.current_index -= 1
            elif target_index <= state.current_index < start_idx:
                state.current_index += 1
            
            # ✅ CRÍTICO: Restaurar opacidad de TODOS los controles antes de actualizar
            for control in self.column.controls:
                try:
                    if hasattr(control, 'content') and hasattr(control.content, 'content'):
                        control.content.content.opacity = 1.0
                except:
                    pass
            
            StatusBar.instance.text.value = f"● ✓ Reordenado: {moved_track.title}"
            StatusBar.instance.text.color = self.theme.get("button_play")
            
            # ✅ Forzar recreación completa de la lista
            print("[DRAG] Recreando lista completa...")
            await self.update()
            
            print(f"[DRAG] ✓ Reordenamiento completado")
                
        except Exception as e:
            print(f"[DRAG] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.drag_state["dragging_index"] = None
            
    # ============================================
    # ASYNC CALLBACKS
    # ============================================
    async def _on_track_click(self, track_index):
        """Click en track - ASYNC"""
        if 0 <= track_index < len(state.tracks):
            state.current_index = track_index
            StatusBar.instance.text.value = f"● Seleccionado: {state.tracks[track_index].title}"
            StatusBar.instance.text.color = self.theme.get("accent")
            await self.update()

    async def _toggle_expand(self, track_index):
        """Toggle expand de secciones - ASYNC"""
        if 0 <= track_index < len(state.tracks):
            tracks_list = state.tracks
            tracks_list[track_index].expanded = not tracks_list[track_index].expanded
            state.tracks = tracks_list  # Forzar setter
            await self.update()

    async def _on_section_click(self, track_index, section_index):
        """Click en sección - ASYNC"""
        try:
            if playback.jump_to_section(track_index, section_index):
                section = state.tracks[track_index].sections[section_index]
                StatusBar.instance.text.value = f"● ▶ {section.name}"
                StatusBar.instance.text.color = self.theme.get("accent")
                self.page.update()
        except Exception as e:
            print(f"[ERROR] _on_section_click: {e}")

# ============================================
# UPDATE DEBOUNCER
# ============================================
class UpdateDebouncer:
    """Evita updates demasiado frecuentes"""
    def __init__(self, min_interval=0.1):
        self.min_interval = min_interval
        self.last_update = 0
        self.pending_update = None
        self.lock = threading.Lock()
    
    def request_update(self, callback):
        """Solicita un update con debounce"""
        with self.lock:
            current_time = time.time()
            
            # Si pasó suficiente tiempo, ejecutar inmediatamente
            if current_time - self.last_update >= self.min_interval:
                self.last_update = current_time
                callback()
            else:
                # Guardar para ejecutar después
                self.pending_update = callback
                
                # Programar ejecución diferida
                def execute_pending():
                    time.sleep(self.min_interval)
                    with self.lock:
                        if self.pending_update:
                            self.pending_update()
                            self.pending_update = None
                            self.last_update = time.time()
                
                threading.Thread(target=execute_pending, daemon=True).start()

# Crear instancia global
update_debouncer = UpdateDebouncer(min_interval=0.15)

# ============================================
# CONTROL PANEL - SIN CAMBIOS SIGNIFICATIVOS
# ============================================
class ControlPanel:
    def __init__(self, theme: ThemeManager, page: ft.Page):
        self.theme = theme
        self.page = page
        self.last_nav_time = 0

        self.metronome_btn = MetronomeButton(theme.get, lambda e: page.run_task(self._on_metronome_click, e))
        self.tempo_display = TempoDisplay(theme.get, state.current_tempo, state.time_signature_num)
        self.beat_indicator = BeatIndicator(theme.get)
        
        self.play_btn = self._create_button("PLAY", ft.Icons.PLAY_ARROW_ROUNDED, self._on_play, "button_play")
        self.stop_btn = self._create_button("STOP", ft.Icons.STOP_ROUNDED, self._on_stop, "button_stop")
        self.prev_btn = self._create_nav_btn(ft.Icons.SKIP_PREVIOUS_ROUNDED, self._on_prev)
        self.next_btn = self._create_nav_btn(ft.Icons.SKIP_NEXT_ROUNDED, self._on_next)
        self.scan_btn = self._create_button("SCAN", ft.Icons.SEARCH_ROUNDED, self._on_scan, "button_scan")

        self.container = ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            self.metronome_btn.button,
                            self.tempo_display.text,
                            self.beat_indicator.container,
                            StatusBar.instance.text if hasattr(StatusBar, 'instance') else ft.Text("")
                        ]
                    ),
                    border_radius=12,
                    padding=ft.padding.all(18)
                ),
                ft.Divider(thickness=1, color=self.theme.get("accent"), height=8),
                ft.Container(
                    content=ft.Column(
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.play_btn,
                            self.stop_btn,
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[self.prev_btn, self.next_btn]),
                            self.scan_btn
                        ]
                    ),
                    border_radius=12,
                    padding=ft.padding.all(18),
                    expand=True
                )
            ]
        )

    def _create_button(self, text, icon, on_click, color_key):
        return ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(icon, size=24, color=ft.Colors.WHITE),
                    ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ]
            ),
            width=220,
            height=90,
            border_radius=10,
            bgcolor=self.theme.get(color_key),
            on_click=lambda e: self.page.run_task(on_click, e),
            ink=True,
        )
    
    def _create_nav_btn(self, icon, on_click):
        return ft.Container(
            content=ft.Icon(icon, size=28, color=ft.Colors.WHITE),
            width=92,
            height=72,
            border_radius=12,
            bgcolor=self.theme.get("button_nav"),
            on_click=lambda e: self.page.run_task(on_click, e),
            ink=True,
            alignment=ft.alignment.center,
        )

    async def _on_metronome_click(self, e):
        try:
            is_on = playback.toggle_metronome()
            self.metronome_btn.set_state(is_on)
            
            StatusBar.instance.text.value = f"● Metrónomo: {'ON' if is_on else 'OFF'}"
            StatusBar.instance.text.color = self.theme.get("button_metro_on") if is_on else self.theme.get("text_secondary")
            self.page.update()
        except Exception as ex:
            print(f"[ERROR] _on_metronome_click: {ex}")

    async def _on_play(self, e):
        try:
            current_idx = state.current_index
            track_count = state.get_track_count()
            
            if current_idx < 0 or current_idx >= track_count:
                StatusBar.instance.text.value = "● Sin track seleccionado"
                StatusBar.instance.text.color = self.theme.get("button_stop")
                self.page.update()
                return
            
            if state.is_playing:
                playback.stop()
                await asyncio.sleep(0.1)
            
            if playback.play_track(current_idx):
                track = state.tracks[current_idx]
                StatusBar.instance.text.value = f"● ▶ Play: {track.title}"
                StatusBar.instance.text.color = self.theme.get("button_play")
                self.page.update()
                await TrackListView.instance.update()
            else:
                StatusBar.instance.text.value = "● Error al reproducir"
                StatusBar.instance.text.color = self.theme.get("button_stop")
                self.page.update()
        except Exception as ex:
            print(f"[ERROR] _on_play: {ex}")

    async def _on_stop(self, e):
        try:
            playback.stop()
            StatusBar.instance.text.value = "● ▪ Stop"
            StatusBar.instance.text.color = self.theme.get("button_stop")
            self.page.update()
        except Exception as ex:
            print(f"[ERROR] _on_stop: {ex}")

    async def _on_next(self, e):
        try:
            if not self._check_nav_debounce():
                return
            
            if playback.next_track():
                await asyncio.sleep(0.12)
                await TrackListView.instance.update()
                
                track = state.get_current_track()
                if track:
                    StatusBar.instance.text.value = f"● ▶ Next: {track.title}"
                    StatusBar.instance.text.color = self.theme.get("button_play")
                    self.page.update()
            else:
                StatusBar.instance.text.value = "● ⊘ Último track"
                StatusBar.instance.text.color = self.theme.get("text_secondary")
                self.page.update()
        except Exception as ex:
            print(f"[ERROR] _on_next: {ex}")

    async def _on_prev(self, e):
        try:
            if not self._check_nav_debounce():
                return
            
            if playback.prev_track():
                await asyncio.sleep(0.12)
                await TrackListView.instance.update()
                
                track = state.get_current_track()
                if track:
                    StatusBar.instance.text.value = f"● ▶ Prev: {track.title}"
                    StatusBar.instance.text.color = self.theme.get("button_play")
                    self.page.update()
            else:
                StatusBar.instance.text.value = "● ⊘ Primer track"
                StatusBar.instance.text.color = self.theme.get("text_secondary")
                self.page.update()
        except Exception as ex:
            print(f"[ERROR] _on_prev: {ex}")

    async def _on_scan(self, e):
        try:
            StatusBar.instance.text.value = "● ⟳ Escaneando Ableton..."
            StatusBar.instance.text.color = self.theme.get("button_scan")
            self.page.update()

            if playback.scan_all():
                await asyncio.sleep(0.6)
                
                state.current_index = 0 if state.get_track_count() > 0 else -1
                await TrackListView.instance.update()
                
                StatusBar.instance.text.value = f"● ✓ Scan completo: {state.get_track_count()} tracks"
                StatusBar.instance.text.color = self.theme.get("button_play")
                self.page.update()
            else:
                StatusBar.instance.text.value = "● ✗ Error en scan"
                StatusBar.instance.text.color = self.theme.get("button_stop")
                self.page.update()
        except Exception as ex:
            print(f"[ERROR] _on_scan: {ex}")

    def _check_nav_debounce(self) -> bool:
        now = time.time()
        if now - self.last_nav_time < DEBOUNCE_NAV_MS / 1000:
            return False
        self.last_nav_time = now
        return True


# ============================================
# DIALOG MANAGER - SIN CAMBIOS
# ============================================
class DialogManager:
    def __init__(self, page: ft.Page, theme: ThemeManager):
        self.page = page
        self.theme = theme

    async def show_save_setlist(self):
        if not state.locators:
            StatusBar.instance.text.value = "● ⚠️ Sin locators. Presiona SCAN primero"
            StatusBar.instance.text.color = self.theme.get("button_stop")
            self.page.update()
            return

        name_field = ft.TextField(
            label="Nombre del setlist",
            width=350,
            autofocus=True,
            hint_text="Ej: Concierto 2024",
            bgcolor=self.theme.get("bg_card"),
            color=self.theme.get("text_primary"),
            border_color=self.theme.get("accent"),
        )
        error_text = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

        async def close_dlg(e=None):
            dlg.open = False
            self.page.update()

        async def do_save(e=None):
            name = name_field.value.strip()
            if not name:
                error_text.value = "⚠️ Debes ingresar un nombre"
                error_text.visible = True
                self.page.update()
                return

            if manager.save(name, state.locators, state.tracks):
                sections_count = sum(len(t.sections) for t in state.tracks)
                StatusBar.instance.text.value = f"● ✓ '{name}' guardado ({len(state.locators)} locators, {len(state.tracks)} tracks, {sections_count} sections)"
                StatusBar.instance.text.color = self.theme.get("button_play")
                await close_dlg()
                await self._update_setlist_counter()
            else:
                error_text.value = "✖ Error al guardar"
                error_text.visible = True
                self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("💾 Guardar Setlist", color=self.theme.get("text_primary")),
            bgcolor=self.theme.get("bg_secondary"),
            content=ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    name_field,
                    ft.Text(
                        f"Se guardarán {len(state.locators)} locators y {len(state.tracks)} tracks",
                        size=12, 
                        italic=True, 
                        color=self.theme.get("text_secondary")
                    ),
                    error_text
                ]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.run_task(close_dlg, e)),
                ft.FilledButton("💾 Guardar", on_click=lambda e: self.page.run_task(do_save, e))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dlg)

    async def show_load_setlist(self):
        saved = manager.list_all()

        async def close_dlg(e=None):
            dlg.open = False
            self.page.update()

        async def do_load(e=None):
            if not dropdown.value:
                return

            try:
                data = manager.load(dropdown.value)
                if not data or "locators" not in data:
                    StatusBar.instance.text.value = "● ✖ Error al cargar"
                    StatusBar.instance.text.color = self.theme.get("button_stop")
                    self.page.update()
                    return

                if state.is_playing:
                    playback.stop()
                    await asyncio.sleep(0.2)

                state.locators = data["locators"]
                if "tracks" in data:
                    state.tracks = data["tracks"]

                state.current_index = 0 if state.tracks else -1

                await TrackListView.instance.update()

                total_sections = sum(len(t.sections) for t in state.tracks)
                StatusBar.instance.text.value = f"● ✓ '{data['name']}' cargado ({len(state.locators)} locators, {len(state.tracks)} tracks, {total_sections} sections)"
                StatusBar.instance.text.color = self.theme.get("button_play")
                self.page.update()
                await close_dlg()
            except Exception as ex:
                print(f"[ERROR] do_load: {ex}")
                import traceback
                traceback.print_exc()

        if saved:
            dropdown = ft.Dropdown(
                label="Setlists guardados",
                options=[ft.dropdown.Option(name) for name in saved],
                width=350,
                bgcolor=self.theme.get("bg_card"),
                border_color=self.theme.get("accent"),
            )
            content = ft.Column(
                width=400,
                tight=True,
                spacing=10,
                controls=[
                    dropdown,
                    ft.Text(
                        f"📁 {len(saved)} setlist(s) disponible(s)", 
                        size=12, 
                        italic=True,
                        color=self.theme.get("text_secondary")
                    )
                ]
            )
            actions = [
                ft.TextButton("Cancelar", on_click=lambda e: self.page.run_task(close_dlg, e)),
                ft.FilledButton("📂 Cargar", on_click=lambda e: self.page.run_task(do_load, e))
            ]
        else:
            content = ft.Column(
                width=400,
                tight=True,
                spacing=12,
                controls=[
                    ft.Text("No hay setlists guardados", size=14, color=self.theme.get("text_primary")),
                    ft.Text(
                        "💡 Usa el botón 💾 para guardar tu primer setlist", 
                        size=11, 
                        italic=True,
                        color=self.theme.get("text_secondary")
                    )
                ]
            )
            actions = [ft.TextButton("Cerrar", on_click=lambda e: self.page.run_task(close_dlg, e))]

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📂 Cargar Setlist", color=self.theme.get("text_primary")),
            bgcolor=self.theme.get("bg_secondary"),
            content=content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dlg)

    async def _update_setlist_counter(self):
            count = len(manager.list_all())
            if hasattr(self, 'save_counter'):
                self.save_counter.value = f"💾 {count}"
                self.page.update()


# ============================================
# FUNCIÓN PRINCIPAL - CORREGIDA PARA FLET 0.28.3
# ============================================
def main(page: ft.Page):
    """Función principal - Thread-safe con async"""
    try:
        print("[UI] Inicializando página...")
        state.page_ref = page

        page.title = "Ableton Setlist Controller"
        page.window.width = 900
        page.window.height = 800
        page.window.resizable = True
        page.window.maximized = True
        page.padding = 0
        page.spacing = 0
        page.theme_mode = ft.ThemeMode.DARK

        page.fonts = {
            "DS-Digital": "fonts/DS-DIGI.TTF"  # Ruta relativa a assets/
        }
        
        set_timer = SetTimer()

        print("[UI] Creando componentes...")

    except Exception as e:
        print(f"[ERROR] Inicialización fallida: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Tema y componentes
    theme = ThemeManager("Deep Space")
    page.theme = ft.Theme(color_scheme_seed=theme.get("accent"))

    status_bar = StatusBar(theme.get)
    StatusBar.instance = status_bar

    track_list = TrackListView(theme, page)
    TrackListView.instance = track_list

    control_panel = ControlPanel(theme, page)
    dialog_manager = DialogManager(page, theme)

    # Header
    save_counter = ft.Text(
        f"💾 {len(manager.list_all())}", 
        size=12, 
        weight=ft.FontWeight.W_500, 
        color=theme.get("text_primary")
    )
    dialog_manager.save_counter = save_counter

    save_btn = ft.IconButton(
        icon=ft.Icons.SAVE,
        on_click=lambda e: page.run_task(dialog_manager.show_save_setlist),
        icon_size=22,
        tooltip="Guardar Setlist"
    )
    
    load_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda e: page.run_task(dialog_manager.show_load_setlist),
        icon_size=22,
        tooltip="Cargar Setlist"
    )

    # Palette dropdown
    palette_dropdown = ft.Dropdown(
        width=180,
        value=theme.current_name,
        options=[ft.dropdown.Option(name) for name in ThemeManager.list_themes()],
        text_size=13,
        bgcolor=theme.get("bg_card") + "00",
        border_color=theme.get("bg_main") + "00",
        focused_border_color=theme.get("accent") + "00",
        text_style=ft.TextStyle(weight=ft.FontWeight.W_600, color=theme.get("text_primary")),
        content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
    )

    def on_theme_change(e):
        """Callback síncrono para cambio de tema"""
        try:
            theme.set_theme(palette_dropdown.value)
            
            # Actualizar colores
            page.bgcolor = theme.get("bg_main")
            listbox_container.bgcolor = theme.get("bg_card") + "40"
            
            # Recrear header
            new_header = create_header(page, palette_dropdown, save_counter, save_btn, load_btn, theme.get, web_port=5000, set_timer=set_timer)
            page.controls[0].content.controls[0] = new_header
            
            control_panel.beat_indicator.container.bgcolor = theme.get("bg_card")
            control_panel.tempo_display.text.color = theme.get("text_primary")
            
            StatusBar.instance.text.value = f"● Paleta: {theme.current_name}"
            StatusBar.instance.text.color = theme.get("accent")
            
            # Actualizar lista y página
            page.run_task(track_list.update)
            page.update()
            
        except Exception as ex:
            print(f"[ERROR] on_theme_change: {ex}")

    palette_dropdown.on_change = on_theme_change

    header_container = create_header(
        page,
        palette_dropdown,
        save_counter,
        save_btn,
        load_btn,
        theme.get,
        web_port=5000,
        set_timer=set_timer
    )

    listbox_container = ft.Container(
        content=track_list.column,
        expand=True,
        border_radius=12,
        padding=ft.padding.all(18),
        bgcolor=theme.get("bg_card") + "00",
    )

    main_row = ft.Row(
        spacing=18,
        expand=True,
        controls=[
            ft.Column(expand=True, spacing=0, controls=[listbox_container]),
            ft.Container(width=250, content=control_panel.container)
        ]
    )

    page.add(
        ft.Container(
            expand=True,
            content=ft.Column(
                spacing=0,
                controls=[
                    header_container,
                    ft.Container(
                        expand=True,
                        padding=ft.padding.only(left=18, right=18, bottom=18, top=10),
                        content=main_row
                    )
                ]
            )
        )
    )

    # Callback de cierre
    def on_window_close(e):
        print("[UI] Cerrando aplicación...")
        state.page_ref = None
    
    page.on_close = on_window_close

    # ============================================
    # CALLBACKS OSC - Thread-safe
    # ============================================
    def trigger_pulse_wrapper(beat: int):
        """Wrapper thread-safe para trigger_pulse desde OSC"""
        try:
            control_panel.beat_indicator.pulse(beat, state.time_signature_num, lambda: safe_ui_update_sync(page))
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] trigger_pulse: {e}")

    def update_tempo_display_wrapper():
        """Wrapper thread-safe para update_tempo_display desde OSC"""
        try:
            control_panel.tempo_display.update(state.current_tempo, state.time_signature_num, lambda: safe_ui_update_sync(page))
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_tempo_display: {e}")

    def update_listbox_wrapper():
        """Wrapper thread-safe para update_listbox desde OSC CON DEBOUNCE"""
        try:
            if hasattr(page, 'run_task'):
                # NUEVO: Usar debouncer
                update_debouncer.request_update(
                    lambda: page.run_task(track_list.update)
                )
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_listbox: {e}")
                
    def update_metronome_ui_wrapper():
        """Wrapper thread-safe para update_metronome_ui desde OSC"""
        try:
            control_panel.metronome_btn.set_state(state.metronome_on)
            safe_ui_update_sync(page)
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_metronome_ui: {e}")

    # Asignar wrappers a page para que OSC los llame
    page.trigger_pulse = trigger_pulse_wrapper
    page.update_tempo_display = update_tempo_display_wrapper
    page.update_listbox = update_listbox_wrapper
    page.update_metronome_ui = update_metronome_ui_wrapper

    # ============================================
    # SCAN INICIAL - VERSIÓN ROBUSTA
    # ============================================
    async def run_initial_scan():
        """Ejecuta el scan después de que la UI esté completamente renderizada"""
        try:
            print("[INIT] ⏳ UI renderizada, esperando estabilización...")
            await asyncio.sleep(1.2)
            
            print("[INIT] ⟳ Ejecutando scan inicial...")

            # Ejecutar scan en thread separado
            scan_complete = threading.Event()
            scan_success = [False]

            def do_scan():
                try:
                    if playback.scan_all():
                        time.sleep(0.6)
                        if state.get_track_count() > 0:
                            state.current_index = 0
                            scan_success[0] = True
                            print(f"[INIT] ✓ {state.get_track_count()} tracks detectados")
                        else:
                            print("[INIT] ⚠ No se detectaron tracks")
                    else:
                        print("[INIT] ✗ Error en scan inicial")
                except Exception as e:
                    print(f"[ERROR] do_scan: {e}")
                finally:
                    scan_complete.set()

            scan_thread = threading.Thread(target=do_scan, daemon=True)
            scan_thread.start()

            # Esperar a que termine (timeout 10s)
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: scan_complete.wait(timeout=10.0)
            )

            # Actualizar UI si hay tracks
            if scan_success[0] and state.get_track_count() > 0:
                print("[INIT] Actualizando UI con tracks...")
                await asyncio.sleep(0.3)
                
                if TrackListView.instance:
                    await TrackListView.instance.update()
                    print("[INIT] ✓ UI actualizada correctamente")
                else:
                    print("[INIT] ✗ TrackListView.instance no disponible")
            else:
                print("[INIT] ⚠ No hay tracks para mostrar en UI")

        except Exception as e:
            print(f"[ERROR] run_initial_scan: {e}")
            import traceback
            traceback.print_exc()

    # Programar scan después del primer frame
    print("[INIT] Programando scan inicial...")
    page.run_task(run_initial_scan)

    print("[INIT] ✓ App lista - scan programado...\n")