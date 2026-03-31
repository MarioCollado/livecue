# ui/track_list.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
import threading
import time
import asyncio
from dataclasses import dataclass
from typing import Optional, Callable
from core.state import state
from ui.themes import ThemeManager
from ui.components import StatusBar
from core.playback import playback
from core.i18n import i18n


# ============================================
# DRAG STATE MANAGER
# ============================================
@dataclass
class DragState:
    """Gestiona el estado del drag & drop"""
    dragging_index: Optional[int] = None
    
    def start_drag(self, index: int):
        self.dragging_index = index
        
    def end_drag(self):
        self.dragging_index = None
        
    def is_dragging(self) -> bool:
        return self.dragging_index is not None


# ============================================
# UPDATE DEBOUNCER
# ============================================
class UpdateDebouncer:
    """Evita updates demasiado frecuentes con debouncing"""
    
    def __init__(self, min_interval: float = 0.1):
        self.min_interval = min_interval
        self.last_update = 0
        self.pending_update: Optional[Callable] = None
        self.lock = threading.Lock()
    
    def request_update(self, callback: Callable):
        """Solicita un update con debounce"""
        with self.lock:
            current_time = time.time()
            
            if current_time - self.last_update >= self.min_interval:
                self.last_update = current_time
                callback()
            else:
                self.pending_update = callback
                threading.Thread(target=self._execute_pending, daemon=True).start()
    
    def _execute_pending(self):
        """Ejecuta update pendiente tras el intervalo"""
        time.sleep(self.min_interval)
        with self.lock:
            if self.pending_update:
                self.pending_update()
                self.pending_update = None
                self.last_update = time.time()


# ============================================
# TRACK ITEM BUILDER
# ============================================
class TrackItemBuilder:
    """Construye componentes visuales de tracks"""
    
    def __init__(self, theme: ThemeManager):
        self.theme = theme
    
    def create_track_header(self, track_index: int, track, is_selected: bool, 
                           has_sections: bool, is_expanded: bool,
                           on_click: Callable, on_toggle: Callable,
                           on_toggle_auto_continue: Callable,
                           on_toggle_loop: Callable) -> ft.Container:
        """Crea el header de un track"""
        return ft.Container(
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Row(
                        controls=[
                            self._create_track_number(track_index, is_selected),
                            ft.Container(width=12),
                            self._create_track_info(track, is_selected, has_sections),
                            self._create_action_buttons(track, on_toggle_auto_continue, on_toggle_loop),
                            ft.Container(width=8),
                            self._create_expand_button(has_sections, is_expanded, on_toggle),
                            self._create_drag_handle()
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
            on_click=on_click,
        )
    
    def _create_track_number(self, track_index: int, is_selected: bool) -> ft.Container:
        """Crea el círculo con el número de track"""
        return ft.Container(
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
        )
    
    def _create_track_info(self, track, is_selected: bool, has_sections: bool) -> ft.Column:
        """Crea la columna con título y metadata"""
        return ft.Column(
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
                    i18n.get("track_sections_count", len(track.sections)),
                    size=11,
                    color=self.theme.get("text_secondary"),
                    visible=has_sections
                )
            ]
        )
    
    def _create_action_buttons(self, track, on_toggle_auto_continue: Callable, on_toggle_loop: Callable) -> ft.Row:
        auto_color = self.theme.get("button_play") if track.auto_continue else self.theme.get("text_secondary") + "60"
        loop_active = getattr(track, "loop_track", False)

        # Botón auto-continue: icono simple
        auto_btn = ft.IconButton(
            icon=ft.Icons.SKIP_NEXT_ROUNDED,
            icon_color=auto_color,
            icon_size=20,
            tooltip="Auto-continuar a la siguiente pista al terminar",
            on_click=on_toggle_auto_continue,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(6),
            )
        )

        # Botón LOOP
        EMERGENCY_RED = "#FF3B30"
        inactive_fg   = self.theme.get("text_secondary") + "70"
        inactive_border = self.theme.get("text_secondary") + "40"

        loop_btn = ft.Container(
            content=ft.Row(
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.WARNING_AMBER_ROUNDED if loop_active else ft.Icons.REPEAT_ONE_ROUNDED,
                        size=13,
                        color="#FFFFFF" if loop_active else inactive_fg,
                    ),
                    ft.Text(
                        "LOOP",
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color="#FFFFFF" if loop_active else inactive_fg,
                    ),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=20,
            bgcolor=EMERGENCY_RED if loop_active else self.theme.get("bg_secondary"),
            border=ft.border.all(1.5, EMERGENCY_RED if loop_active else inactive_border),
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=1,
                color=EMERGENCY_RED + "99",
            ) if loop_active else None,
            tooltip="🚨 EMERGENCIA: Loopear el compás actual hasta desactivar",
            on_click=on_toggle_loop,
            ink=True,
        )

        return ft.Row(
            spacing=6,
            controls=[loop_btn, auto_btn],
        )
    
    def _create_expand_button(self, has_sections: bool, is_expanded: bool, 
                             on_toggle: Callable) -> ft.IconButton:
        """Crea el botón de expand/collapse"""
        return ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_UP if is_expanded else ft.Icons.KEYBOARD_ARROW_DOWN,
            icon_size=18,
            on_click=on_toggle,
            visible=has_sections,
            icon_color=self.theme.get("accent"),
        )
    
    def _create_drag_handle(self) -> ft.Icon:
        """Crea el icono de drag"""
        return ft.Icon(
            ft.Icons.DRAG_HANDLE, 
            size=18, 
            color=self.theme.get("text_secondary"), 
            opacity=0.3
        )
    
    def create_sections_content(self, track_index: int, track, page: ft.Page, on_section_click: Callable) -> ft.Column:
        """Crea el contenido de las secciones con callbacks correctos"""
        section_items = []
        
        for sec_idx, section in enumerate(track.sections):
            # CRÍTICO: Crear closure para capturar valores correctos
            # Sin esto, todos los callbacks usarían el último sec_idx del loop
            def make_handler(ti, si):
                def handler(e):
                    print(f"[CALLBACK] Handler creado para track={ti}, section={si}")
                    page.run_task(on_section_click, ti, si)
                return handler
            
            # Pasar los valores ACTUALES de track_index y sec_idx
            handler = make_handler(track_index, sec_idx)
            
            section_items.append(
                self._create_section_item_sync(track_index, sec_idx, section, handler)
            )
        
        print(f"[SECTIONS] Creadas {len(section_items)} secciones para track {track_index}")
        return ft.Column(spacing=4, controls=section_items)
    
    def _create_section_item_sync(self, track_index: int, sec_idx: int, 
                            section, on_click: Callable) -> ft.Container:
        """Crea un item individual de sección con handler síncrono"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=48),
                    ft.Container(width=2, height=28, bgcolor=self.theme.get("accent"), opacity=0.4),
                    ft.Container(width=10),
                    ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, size=16, 
                           color=self.theme.get("accent"), opacity=0.7),
                    ft.Container(width=8),
                    ft.Text(section.name, size=13, weight=ft.FontWeight.W_500, 
                           expand=True, color=self.theme.get("text_primary"))
                ],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=8,
            bgcolor=self.theme.get("bg_secondary"),
            on_click=on_click,
            ink=True,
            animate_opacity=150,
        )
    
    def create_drag_feedback(self, track_index: int, track) -> ft.Container:
        """Crea el feedback visual durante el drag"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"{track_index + 1}", size=13, weight=ft.FontWeight.BOLD, 
                           color=ft.Colors.WHITE),
                    ft.Container(width=10),
                    ft.Text(track.title, size=14, weight=ft.FontWeight.W_600, 
                           color=ft.Colors.WHITE)
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
# DRAG DROP HANDLER
# ============================================
class DragDropHandler:
    """Maneja la lógica de drag & drop"""
    
    def __init__(self, drag_state: DragState, on_reorder: Callable):
        self.drag_state = drag_state
        self.on_reorder = on_reorder
    
    def on_drag_start(self, track_index: int):
        """Inicia el drag"""
        self.drag_state.start_drag(track_index)
        print(f"[DRAG] Iniciando drag de track {track_index}")
    
    def on_will_accept(self, e):
        """Valida si se puede aceptar el drop"""
        e.control.content.opacity = 0.5
        self._safe_update(e.control)
    
    def on_drag_leave(self, e):
        """Restaura opacidad cuando sale del drop zone"""
        e.control.content.opacity = 1.0
        self._safe_update(e.control)
    
    async def on_drag_accept(self, target_index: int):
        """Acepta el drop y ejecuta el reordenamiento"""
        start_idx = self.drag_state.dragging_index
        
        if start_idx is None or start_idx == target_index:
            self.drag_state.end_drag()
            return
        
        try:
            await self.on_reorder(start_idx, target_index)
        finally:
            self.drag_state.end_drag()
    
    @staticmethod
    def _safe_update(control):
        """Actualiza un control de forma segura"""
        try:
            control.update()
        except:
            pass


# ============================================
# TRACK LIST VIEW
# ============================================
class TrackListView:
    """Vista principal de la lista de tracks"""
    
    instance = None
    
    def __init__(self, theme: ThemeManager, page: ft.Page):
        self.theme = theme
        self.page = page
        self.column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Componentes
        self.drag_state = DragState()
        self.item_builder = TrackItemBuilder(theme)
        self.drag_handler = DragDropHandler(self.drag_state, self._handle_reorder)
        self.debouncer = UpdateDebouncer(min_interval=0.15)
        
        # Threading
        self._update_lock = threading.Lock()
        
        TrackListView.instance = self
    
    # ============================================
    # UPDATE METHODS
    # ============================================
    
    async def update(self, force_refresh: bool = False):
        """Actualiza la lista completa de tracks
        
        Args:
            force_refresh: Si True, fuerza actualización completa incluso si el número de tracks no cambió
        """
        if not self._can_update():
            return
        
        if not self._update_lock.acquire(blocking=False):
            print("[UI] Update ya en progreso, ignorando...")
            return
        
        try:
            tracks = state.tracks
            
            if not tracks:
                self._clear_list()
                return
            
            # Verificar si realmente necesitamos actualizar
            current_count = len(self.column.controls)
            new_count = len(tracks)
            
            # Si el número de tracks no cambió Y no es forzado, usar update_single_track
            if current_count == new_count and current_count > 0 and not force_refresh:
                print(f"[UI] Número de tracks sin cambios ({current_count}), usando update selectivo")
                # Solo actualizar el track actual si existe
                if 0 <= state.current_index < new_count:
                    await self.update_single_track(state.current_index)
                return
            
            if force_refresh:
                print(f"[UI] Forzando actualización completa de {new_count} tracks")
            
            new_items = self._build_all_items(tracks)
            
            if not new_items:
                print("[UI] No se pudieron crear items")
                return
            
            self._replace_items(new_items, len(tracks), force=force_refresh)
            
        except AssertionError as e:
            print(f"[UI] AssertionError en update: {e}")
            await self._rebuild_from_scratch(state.tracks)
        except Exception as e:
            print(f"[ERROR] TrackListView.update: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._update_lock.release()
    
    async def update_single_track(self, track_index: int):
        """Actualiza solo un track específico"""
        try:
            if not (0 <= track_index < len(self.column.controls)):
                return
            
            track = state.tracks[track_index]
            is_selected = track_index == state.current_index
            has_sections = len(track.sections) > 0
            is_expanded = track.expanded
            
            draggable = self.column.controls[track_index]
            track_column = draggable.content.content
            
            # Actualizar header y forzar render antes de la animacion
            track_column.controls[0] = self.item_builder.create_track_header(
                track_index, track, is_selected, has_sections, is_expanded,
                lambda e: self.page.run_task(self._on_track_click, track_index),
                lambda e: self.page.run_task(self._toggle_expand, track_index),
                lambda e, idx=track_index: self.page.run_task(self._toggle_auto_continue, idx),
                lambda e, idx=track_index: self.page.run_task(self._toggle_loop, idx)
            )
            # Refrescar solo el header sin esperar a la animacion de secciones
            try:
                self.page.update()
            except Exception:
                pass
            
            # Actualizar secciones con animación
            await self._animate_sections(track_column.controls[1], track_index, 
                                        track, is_expanded, has_sections)
            
        except Exception as e:
            print(f"[ERROR] update_single_track({track_index}): {e}")
            await self.update()
    
    # ============================================
    # PRIVATE UPDATE HELPERS
    # ============================================
    
    def _can_update(self) -> bool:
        """Verifica si es seguro actualizar"""
        if not self.page:
            print("[UI] Page es None")
            return False
        
        if hasattr(self.page, 'window') and self.page.window is None:
            print("[UI] Ventana cerrada")
            return False
        
        if not hasattr(self.page, 'controls') or not self.page.controls:
            print("[UI] Page sin controles inicializados")
            return False
        
        return True
    
    def _clear_list(self):
        """Limpia la lista de tracks"""
        if len(self.column.controls) > 0:
            self.column.controls.clear()
            try:
                self.page.update()
            except:
                pass
    
    def _build_all_items(self, tracks) -> list:
        """Construye todos los items de la lista"""
        items = []
        for idx, track in enumerate(tracks):
            try:
                item = self._create_track_item(idx, track)
                items.append(item)
            except Exception as e:
                print(f"[UI] Error creando item {idx}: {e}")
        return items
    
    def _replace_items(self, new_items: list, track_count: int, force: bool = False):
        """Reemplaza los items de la lista de forma segura
        
        Args:
            new_items: Nuevos items a mostrar
            track_count: Número de tracks
            force: Si True, permite reemplazar incluso si el número es el mismo
        """
        try:
            old_count = len(self.column.controls)
            
            # CRÍTICO: Verificar si realmente cambió algo
            if old_count == track_count and not force:
                print(f"[UI] ⚠ Advertencia: Intentando reemplazar {old_count} items con {track_count} items (mismo número)")
                # No hacer nada si es el mismo número - evita duplicaciones
                return
            
            # Limpiar completamente la lista ANTES de añadir nuevos items
            if old_count > 0:
                print(f"[UI] Limpiando {old_count} items existentes...")
                # Método 1: Limpiar la lista
                self.column.controls.clear()
                # Forzar actualización para que Flet procese la eliminación
                self.page.update()
            
            # Ahora asignar los nuevos items
            print(f"[UI] Añadiendo {track_count} nuevos items...")
            self.column.controls = new_items
            self.page.update()
            print(f"[UI] ✓ Lista actualizada: {track_count} tracks (anterior: {old_count})")
        except Exception as e:
            print(f"[UI] Error en _replace_items: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _rebuild_from_scratch(self, tracks):
        """Reconstruye la lista desde cero en caso de corrupción"""
        try:
            print("[UI] Reconstruyendo lista desde cero...")
            
            new_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
            
            for idx, track in enumerate(tracks):
                try:
                    new_column.controls.append(self._create_track_item(idx, track))
                except Exception as e:
                    print(f"[UI] Error recreando item {idx}: {e}")
            
            parent = self._find_parent_container()
            if parent:
                parent.content = new_column
                self.column = new_column
                self.page.update()
                print("[UI] ✓ Lista reconstruida correctamente")
            else:
                print("[UI] ✗ No se encontró contenedor padre")
                
        except Exception as e:
            print(f"[ERROR] _rebuild_from_scratch: {e}")
    
    def _find_parent_container(self):
        """Encuentra el contenedor padre de la columna"""
        for control in self.page.controls:
            if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                for row in control.content.controls:
                    if hasattr(row, 'controls'):
                        for col in row.controls:
                            if hasattr(col, 'content') and col.content == self.column:
                                return col
        return None
    
    async def _animate_sections(self, sections_container, track_index: int, 
                                track, is_expanded: bool, has_sections: bool):
        """Anima la expansión/colapso de secciones con efecto moderno y sutil"""
        if is_expanded and has_sections:
            # EXPANSIÓN: Primero crear contenido (invisible), luego animar
            sections_container.content = self.item_builder.create_sections_content(
                track_index, track, self.page, self._on_section_click
            )
            sections_container.opacity = 0.0  # Empezar invisible
            sections_container.padding = ft.padding.only(top=0)
            self.page.update()
            
            # Pequeño delay para suavizar el inicio
            await asyncio.sleep(0.05)
            
            # Animar expansión con curvas suaves
            sections_container.animate_size = ft.Animation(250, ft.AnimationCurve.EASE_OUT)
            sections_container.animate_opacity = ft.Animation(300, ft.AnimationCurve.EASE_IN)
            sections_container.opacity = 1.0
            sections_container.padding = ft.padding.only(top=12)
            self.page.update()
            
        else:
            # COLAPSO: Primero fade out, luego collapse
            sections_container.animate_opacity = ft.Animation(200, ft.AnimationCurve.EASE_OUT)
            sections_container.animate_size = ft.Animation(250, ft.AnimationCurve.EASE_IN)
            sections_container.opacity = 0.0
            sections_container.padding = ft.padding.only(top=0)
            self.page.update()
            
            # Esperar a que termine la animación antes de limpiar contenido
            await asyncio.sleep(0.25)
            sections_container.content = ft.Column(spacing=0, controls=[])
            self.page.update()
    
    # ============================================
    # ITEM CREATION
    # ============================================
    
    def _create_track_item(self, track_index: int, track) -> ft.Draggable:
        """Crea un item completo de track con drag & drop"""
        is_selected = track_index == state.current_index
        has_sections = len(track.sections) > 0
        is_expanded = track.expanded
        
        # Header
        header = self.item_builder.create_track_header(
            track_index, track, is_selected, has_sections, is_expanded,
            lambda e: self.page.run_task(self._on_track_click, track_index),
            lambda e: self.page.run_task(self._toggle_expand, track_index),
            lambda e, idx=track_index: self.page.run_task(self._toggle_auto_continue, idx),
            lambda e, idx=track_index: self.page.run_task(self._toggle_loop, idx)
        )
        
        # Secciones con animaciones modernas
        sections_container = ft.Container(
            content=self.item_builder.create_sections_content(track_index, track, self.page, self._on_section_click) 
                    if (is_expanded and has_sections) 
                    else ft.Column(spacing=0, controls=[]),
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            animate_size=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            opacity=1.0 if is_expanded else 0.0,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        
        # Columna principal
        track_column = ft.Column(spacing=0, controls=[header, sections_container])
        
        # Drag & Drop
        drag_target = ft.DragTarget(
            group="tracks",
            content=track_column,
            on_will_accept=self.drag_handler.on_will_accept,
            on_accept=lambda e: self.page.run_task(self.drag_handler.on_drag_accept, track_index),
            on_leave=self.drag_handler.on_drag_leave
        )
        
        draggable = ft.Draggable(
            group="tracks",
            content=drag_target,
            content_feedback=self.item_builder.create_drag_feedback(track_index, track),
            on_drag_start=lambda e: self.drag_handler.on_drag_start(track_index)
        )
        
        return draggable
    
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    async def _on_track_click(self, track_index: int):
        """Maneja el click en un track"""
        if not (0 <= track_index < len(state.tracks)):
            return
        
        tracks_list = state.tracks
        previous_index = state.current_index
        
        # Toggle si se hace click en el mismo track
        if previous_index == track_index:
            tracks_list[track_index].expanded = not tracks_list[track_index].expanded
            state.tracks = tracks_list
            await self.update_single_track(track_index)
            self._update_status(state.tracks[track_index].title, "accent")
            return
        
        # Cambio de track
        if previous_index >= 0:
            tracks_list[previous_index].expanded = False
        
        if len(tracks_list[track_index].sections) > 0:
            tracks_list[track_index].expanded = True
        
        state.current_index = track_index
        state.tracks = tracks_list
        
        self._update_status(i18n.get("status_selected", state.tracks[track_index].title), "accent")
        
        if previous_index >= 0 and previous_index != track_index:
            await self.update_single_track(previous_index)
        await self.update_single_track(track_index)
    
    async def _toggle_auto_continue(self, track_index: int):
        """Toggle auto-continuar"""
        tracks_list = state.tracks
        if not (0 <= track_index < len(tracks_list)): return
        tracks_list[track_index].auto_continue = not getattr(tracks_list[track_index], 'auto_continue', False)
        state.tracks = tracks_list
        await self.update_single_track(track_index)

    async def _toggle_loop(self, track_index: int):
        """Toggle loop"""
        tracks_list = state.tracks
        if not (0 <= track_index < len(tracks_list)): return
        tracks_list[track_index].loop_track = not getattr(tracks_list[track_index], 'loop_track', False)
        state.tracks = tracks_list
        await self.update_single_track(track_index)

    async def _toggle_expand(self, track_index: int):
        """Toggle de expansión/colapso de secciones con animación fluida"""
        if not (0 <= track_index < len(state.tracks)):
            return
        
        tracks_list = state.tracks
        track = tracks_list[track_index]
        currently_expanded = track.expanded
        
        # Seleccionar el track si no estaba seleccionado
        state.current_index = track_index
        
        if currently_expanded:
            # --- COLAPSAR ---
            track.expanded = False
            state.tracks = tracks_list
            await self.update_single_track(track_index)
        else:
            # --- EXPANDIR ---
            # Micro-delay para percepción de selección
            track.expanded = False  # Asegurar estado inicial para la animación
            state.tracks = tracks_list
            await self.update_single_track(track_index)
            
            await asyncio.sleep(0.01)  # 10ms - casi imperceptible pero suficiente
            
            tracks_list = state.tracks  # Refrescar referencia
            tracks_list[track_index].expanded = True
            state.tracks = tracks_list
            await self.update_single_track(track_index)
    
    async def _on_section_click(self, track_index: int, section_index: int):
        """Maneja el click en una sección"""
        try:
            print(f"[DEBUG] Click en sección: track={track_index}, section={section_index}")
            
            if playback.jump_to_section(track_index, section_index):
                section = state.tracks[track_index].sections[section_index]
                self._update_status(f"▶ {section.name}", "accent")
                self.page.update()
                print(f"[DEBUG] Salto exitoso a {section.name}")
            else:
                print(f"[ERROR] jump_to_section retornó False")
        except Exception as e:
            print(f"[ERROR] _on_section_click: {e}")
            import traceback
            traceback.print_exc()
    
    async def _handle_reorder(self, start_idx: int, target_idx: int):
        """Maneja el reordenamiento de tracks"""
        tracks_list = state.tracks
        
        if not (0 <= start_idx < len(tracks_list)) or not (0 <= target_idx < len(tracks_list)):
            print(f"[DRAG] Índices fuera de rango")
            return
        
        print(f"[DRAG] Reordenando: {start_idx} -> {target_idx}")
        
        # Reordenar
        moved_track = tracks_list.pop(start_idx)
        tracks_list.insert(target_idx, moved_track)
        state.tracks = tracks_list
        
        # Ajustar índice actual
        if state.current_index == start_idx:
            state.current_index = target_idx
        elif start_idx < state.current_index <= target_idx:
            state.current_index -= 1
        elif target_idx <= state.current_index < start_idx:
            state.current_index += 1
        
        # Restaurar opacidad
        self._restore_all_opacity()
        
        self._update_status(i18n.get("status_reordered", moved_track.title), "button_play")
        
        await self.update()
        print(f"[DRAG] ✓ Reordenamiento completado")
    
    def _restore_all_opacity(self):
        """Restaura la opacidad de todos los controles"""
        for control in self.column.controls:
            try:
                if hasattr(control, 'content') and hasattr(control.content, 'content'):
                    control.content.content.opacity = 1.0
            except:
                pass
    
    def _update_status(self, message: str, color_key: str):
        """Actualiza la barra de estado"""
        StatusBar.instance.text.value = f"● {message}"
        StatusBar.instance.text.color = self.theme.get(color_key)