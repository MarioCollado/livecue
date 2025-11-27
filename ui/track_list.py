# ui/track_list.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
import threading
import time
from core.state import state
from ui.themes import ThemeManager
from ui.components import StatusBar
from core.playback import playback

# ============================================
# TRACK LIST VIEW
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

            # Obtener tracks ANTES de limpiar
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

            # Crear TODOS los items primero (sin modificar column)
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
                                on_click=self._create_toggle_expand_handler(track_index),  
                                visible=has_sections,
                                icon_color=self.theme.get("accent"),
                            ),
                            ft.Icon(ft.Icons.DRAG_HANDLE, size=18, color=self.theme.get("text_secondary"), opacity=0.3)
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ]
            ),
        padding=ft.padding.symmetric(horizontal=20, vertical=16),
        border_radius=12,
        bgcolor=self.theme.get("bg_card"),
        border=ft.border.all(2, self.theme.get("accent")) if is_selected else None,
        on_click=self._create_track_click_handler(track_index),  
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
                    on_click=self._create_section_click_handler(track_index, sec_idx),  
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
            
            # CRÍTICO: Restaurar opacidad de TODOS los controles antes de actualizar
            for control in self.column.controls:
                try:
                    if hasattr(control, 'content') and hasattr(control.content, 'content'):
                        control.content.content.opacity = 1.0
                except:
                    pass
            
            StatusBar.instance.text.value = f"● ✓ Reordenado: {moved_track.title}"
            StatusBar.instance.text.color = self.theme.get("button_play")
            
            # Forzar recreación completa de la lista
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
        """Click en track - ASYNC con auto-expand y toggle"""
        if 0 <= track_index < len(state.tracks):
            tracks_list = state.tracks
            previous_index = state.current_index
            
            #  Si haces click en el mismo track que ya está seleccionado
            if previous_index == track_index:
                # Toggle: colapsar/expandir el actual
                tracks_list[track_index].expanded = not tracks_list[track_index].expanded
                state.tracks = tracks_list
                
                StatusBar.instance.text.value = f"● {state.tracks[track_index].title}"
                StatusBar.instance.text.color = self.theme.get("accent")
                await self.update()
                return
            
            # Colapsar el track anterior si es diferente
            if 0 <= previous_index < len(tracks_list):
                tracks_list[previous_index].expanded = False
            
            #  Expandir el track actual (si tiene secciones)
            if len(tracks_list[track_index].sections) > 0:
                tracks_list[track_index].expanded = True
            
            # Actualizar índice actual
            state.current_index = track_index
            state.tracks = tracks_list  # Forzar setter

            StatusBar.instance.text.value = f"● Seleccionado: {state.tracks[track_index].title}"
            StatusBar.instance.text.color = self.theme.get("accent")
            await self.update()

    async def _toggle_expand(self, track_index):
        """Toggle expand de secciones - ASYNC (manual con flecha)"""
        if 0 <= track_index < len(state.tracks):
            tracks_list = state.tracks
            
            # Toggle manual: simplemente invierte el estado actual
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
