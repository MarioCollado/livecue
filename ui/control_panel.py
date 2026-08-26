# ui/control_panel.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
import time
import asyncio
from core.state import state
from ui.themes import ThemeManager
from core.playback import playback
from core.utils import icon
from ui.track_list import TrackListView
from ui.components import MetronomeButton, TempoDisplay, BeatIndicator, StatusBar
from core.i18n import i18n

DEBOUNCE_NAV_MS = 300

# ============================================
# CONTROL PANEL
# ============================================
class ControlPanel:
    def __init__(self, theme: ThemeManager, page: ft.Page):
        self.theme = theme
        self.page = page
        self.last_nav_time = 0

        self.metronome_btn = MetronomeButton(theme.get, lambda e: page.run_task(self._on_metronome_click, e))
        self.tempo_display = TempoDisplay(theme.get, state.current_tempo, state.time_signature_num)
        self.beat_indicator = BeatIndicator(theme.get)
        
        # PLAY y STOP solo con icono grande
        self.play_btn = self._create_icon_only_button(
            icon("play_txt", size=48, color=ft.Colors.WHITE),
            self._on_play,
            "button_play"
        )
        self.stop_btn = self._create_icon_only_button(
            icon("hand-stop", size=48, color=ft.Colors.WHITE),
            self._on_stop,
            "button_stop"
        )
        
        self.prev_btn = self._create_nav_btn(ft.Icons.SKIP_PREVIOUS_ROUNDED, self._on_prev)
        self.next_btn = self._create_nav_btn(ft.Icons.SKIP_NEXT_ROUNDED, self._on_next)

        # ===== SCAN con spinner =====
        self.scan_btn = self._create_scan_button()
        self.scan_progress_bar = ft.ProgressBar(
            width=220,
            height=4,
            visible=False,
            color=theme.get("accent"),
            bgcolor=theme.get("bg_secondary")
        )
        self.scan_status_text = ft.Text(
            "",
            size=11,
            color=theme.get("accent"),
            visible=False,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_500
        )
        
        scan_section = ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.scan_btn,
                self.scan_progress_bar,
                self.scan_status_text
            ]
        )

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
                    padding=ft.padding.Padding(left=18, right=18, top=18, bottom=18)
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
                            scan_section
                        ]
                    ),
                    border_radius=12,
                    padding=ft.padding.Padding(left=18, right=18, top=18, bottom=18),
                    expand=True
                )
            ]
        )

    def _set_status(self, message: str, color_key: str, refresh: bool = True):
        StatusBar.instance.text.value = message
        StatusBar.instance.text.color = self.theme.get(color_key)
        if hasattr(self, 'compact_status_text') and self.compact_status_text:
            self.compact_status_text.value = message
            self.compact_status_text.color = self.theme.get(color_key)
        if refresh:
            self.page.update()

    def _set_status_icon(self, message: str, color_key: str, refresh: bool = True):
        self._set_status(f"● {message}", color_key, refresh=refresh)

    def _create_icon_only_button(self, icon_widget, on_click, color_key):
        """Crea un botón con solo el icono (sin texto)"""
        return ft.Container(
            content=icon_widget,
            width=220,
            height=90,
            border_radius=10,
            bgcolor=self.theme.get(color_key),
            on_click=lambda e: self.page.run_task(on_click, e),
            ink=True,
            alignment=ft.Alignment.CENTER,
        )

    def _create_button(self, text, icon, on_click, color_key):
        # Si icon es un string, crear ft.Icon; si es un widget, usarlo directamente
        if isinstance(icon, str):
            icon_widget = ft.Icon(icon, size=24, color=ft.Colors.WHITE)
        else:
            # Es un widget (como el resultado de icon()), usarlo tal cual
            icon_widget = icon
        
        return ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    icon_widget,
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
            alignment=ft.Alignment.CENTER,
        )

    async def _on_metronome_click(self, e):
        try:
            is_on = playback.toggle_metronome()
            self.set_metronome_state(is_on)
            self._set_status(
                i18n.get("status_metronome", i18n.get("status_metronome_on") if is_on else i18n.get("status_metronome_off")),
                "button_metro_on" if is_on else "text_secondary",
            )
        except Exception as ex:
            print(f"[ERROR] _on_metronome_click: {ex}")

    async def _on_play(self, e):
        try:
            current_idx = state.current_index
            track_count = state.get_track_count()
            
            if current_idx < 0 or current_idx >= track_count:
                self._set_status(i18n.get("status_no_track_selected"), "button_stop")
                return
            
            if state.is_playing:
                playback.stop()
                await asyncio.sleep(0.1)
            
            if playback.play_track(current_idx):
                track = state.tracks[current_idx]
                
                # 🆕 ACTUALIZAR DISPLAY DE TEMPO si el track tiene BPM
                if track.bpm is not None and track.bpm > 0:
                    self.tempo_display.update(
                        tempo=track.bpm,
                        page_update_fn=self.page.update
                    )
                
                self._set_status(i18n.get("status_play", track.title), "button_play")
                # Solo actualizar el track actual, no toda la lista
                await TrackListView.instance.update_single_track(current_idx)
            else:
                self._set_status(i18n.get("status_play_error"), "button_stop")
        except Exception as ex:
            print(f"[ERROR] _on_play: {ex}")

    async def _on_stop(self, e):
        try:
            playback.stop()
            self._set_status(i18n.get("status_stop"), "button_stop")
        except Exception as ex:
            print(f"[ERROR] _on_stop: {ex}")

    async def _on_next(self, e):
        try:
            if not self._check_nav_debounce():
                return
            
            previous_idx = state.current_index
            if playback.next_track():
                await asyncio.sleep(0.12)
                # Actualizar solo los tracks afectados
                if previous_idx >= 0:
                    await TrackListView.instance.update_single_track(previous_idx)
                await TrackListView.instance.update_single_track(state.current_index)
                
                track = state.get_current_track()
                if track:
                    self._set_status(i18n.get("status_next", track.title), "button_play")
            else:
                self._set_status(i18n.get("status_last_track"), "text_secondary")
        except Exception as ex:
            print(f"[ERROR] _on_next: {ex}")

    async def _on_prev(self, e):
        try:
            if not self._check_nav_debounce():
                return
            
            previous_idx = state.current_index
            if playback.prev_track():
                await asyncio.sleep(0.12)
                # Actualizar solo los tracks afectados
                if previous_idx >= 0:
                    await TrackListView.instance.update_single_track(previous_idx)
                await TrackListView.instance.update_single_track(state.current_index)
                
                track = state.get_current_track()
                if track:
                    self._set_status(i18n.get("status_prev", track.title), "button_play")
            else:
                self._set_status(i18n.get("status_first_track"), "text_secondary")
        except Exception as ex:
            print(f"[ERROR] _on_prev: {ex}")

    def _check_nav_debounce(self) -> bool:
        now = time.time()
        if now - self.last_nav_time < DEBOUNCE_NAV_MS / 1000:
            return False
        self.last_nav_time = now
        return True

    def _create_scan_button(self):
        """Crea el botón SCAN con spinner"""
        # Spinner (oculto por defecto)
        self.scan_spinner = ft.ProgressRing(
            width=18,
            height=18,
            stroke_width=2.5,
            visible=False,
            color=ft.Colors.WHITE
        )
        
        # Icono (visible por defecto)
        self.scan_icon = icon("search2",size=24,color=ft.Colors.WHITE)
        
        # Texto
        self.scan_text = ft.Text(i18n.get("scan_btn"), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        
        return ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Stack(
                        width=24,
                        height=24,
                        controls=[
                            self.scan_icon,
                            self.scan_spinner
                        ]
                    ),
                    self.scan_text
                ]
            ),
            width=220,
            height=90,
            border_radius=10,
            bgcolor=self.theme.get("button_scan"),
            on_click=lambda e: self.page.run_task(self._on_scan, e),
            ink=True,
        )
    
    async def _on_scan(self, e):
        """Escanea tracks desde Ableton CON FEEDBACK VISUAL"""
        try:
            # El usuario pide un scan manual: quiere reconstruir desde Ableton.
            # Resetear el flag de setlist cargado para que _build_track_structure
            # reconstruya los tracks desde los cue_points de Ableton sin protección.
            state.setlist_loaded = False

            # PASO 1: Activar modo scanning
            state.is_scanning = True
            self._update_scan_ui(i18n.get("scan_starting"), 0, scanning=True)
            await asyncio.sleep(0.3)
            
            # PASO 2: Conectando con Ableton
            self._update_scan_ui(i18n.get("scan_connecting"), 15, scanning=True)
            await asyncio.sleep(0.3)
            
            # PASO 3: Detectando locators
            self._update_scan_ui(i18n.get("scan_detecting"), 35, scanning=True)
            await asyncio.sleep(0.2)
            
            # PASO 4: Ejecutar scan real
            self._update_scan_ui(i18n.get("scan_processing"), 60, scanning=True)
            
            # Ejecutar scan en thread separado para no bloquear UI
            scan_success = await asyncio.get_event_loop().run_in_executor(
                None,
                playback.scan_all
            )
            
            if scan_success:
                # PASO 5: Procesando secciones
                self._update_scan_ui(i18n.get("scan_sections"), 85, scanning=True)
                await asyncio.sleep(0.4)
                
                # PASO 6: Finalizando
                self._update_scan_ui(i18n.get("scan_finalizing"), 95, scanning=True)
                await asyncio.sleep(0.2)
                
                # Actualizar índice
                state.current_index = 0 if state.get_track_count() > 0 else -1
                
                # Actualizar lista
                await TrackListView.instance.update()
                
                # PASO 7: Completado
                track_count = state.get_track_count()
                self._update_scan_ui(i18n.get("scan_found", track_count), 100, scanning=True)
                self._set_status_icon(i18n.get("status_scan_complete", track_count), "button_play")
                
                # Mostrar mensaje de éxito 1.5 segundos
                await asyncio.sleep(1.5)
                
            else:
                # Error en scan
                self._update_scan_ui(i18n.get("scan_error"), 0, scanning=True)
                self._set_status_icon(i18n.get("status_scan_error"), "button_stop")
                await asyncio.sleep(2)
            
        except Exception as ex:
            print(f"[ERROR] _on_scan: {ex}")
            import traceback
            traceback.print_exc()
            
            self._update_scan_ui(i18n.get("scan_error_critical"), 0, scanning=True)
            self._set_status_icon(f"✗ Error: {str(ex)}", "button_stop")
            await asyncio.sleep(2)
            
        finally:
            # Siempre restaurar UI
            state.is_scanning = False
            self._update_scan_ui("", 0, scanning=False)
            
            # Ocultar status text después de 2 segundos
            await asyncio.sleep(2)
            self.scan_status_text.visible = False
            self.page.update()

    def _update_scan_ui(self, message: str, progress: int, scanning: bool = True):
        """Actualiza la UI del botón SCAN"""
        try:
            if scanning:
                # Modo scanning
                self.scan_icon.visible = False
                self.scan_spinner.visible = True
                self.scan_text.value = i18n.get("scan_scanning")
                self.scan_btn.disabled = True
                self.scan_progress_bar.visible = True
                self.scan_progress_bar.value = progress / 100
                self.scan_status_text.visible = True
                self.scan_status_text.value = message
                self.scan_status_text.color = self.theme.get("accent")
            else:
                # Modo normal
                self.scan_icon.visible = True
                self.scan_spinner.visible = False
                self.scan_text.value = i18n.get("scan_btn")
                self.scan_btn.disabled = False
                self.scan_progress_bar.visible = False
            
            self.page.update()
        except Exception as e:
            print(f"[ERROR] _update_scan_ui: {e}")

    def set_metronome_state(self, is_on: bool):
        """Establece el estado del metrónomo en todos los controles"""
        self.metronome_btn.set_state(is_on)
        if hasattr(self, 'compact_metronome_btn') and self.compact_metronome_btn:
            self.compact_metronome_btn.bgcolor = self.theme.get("button_metro_on" if is_on else "button_metro")

    def update_theme_colors(self):
        """Actualiza los colores de todos los botones según el tema actual"""
        self.play_btn.bgcolor = self.theme.get("button_play")
        self.stop_btn.bgcolor = self.theme.get("button_stop")
        self.prev_btn.bgcolor = self.theme.get("button_nav")
        self.next_btn.bgcolor = self.theme.get("button_nav")
        self.scan_btn.bgcolor = self.theme.get("button_scan")
        self.beat_indicator.container.bgcolor = self.theme.get("bg_card")
        
        # Actualizar componentes compactos si están inicializados
        if hasattr(self, 'compact_play_btn') and self.compact_play_btn:
            self.compact_play_btn.bgcolor = self.theme.get("button_play")
            self.compact_stop_btn.bgcolor = self.theme.get("button_stop")
            self.compact_prev_btn.bgcolor = self.theme.get("button_nav")
            self.compact_next_btn.bgcolor = self.theme.get("button_nav")
            self.compact_scan_btn.bgcolor = self.theme.get("button_scan")
            self.compact_metronome_btn.bgcolor = self.theme.get("button_metro_on" if state.metronome_on else "button_metro")
            self.compact_status_text.color = StatusBar.instance.text.color
            self.compact_container.bgcolor = self.theme.get("bg_secondary")
            self.compact_container.border = ft.border.Border.all(1, self.theme.get("border") + "40")

    def get_compact_container(self) -> ft.Container:
        """Devuelve el contenedor de controles compactos, creándolo si no existe"""
        if not hasattr(self, 'compact_container'):
            self._create_compact_components()
        return self.compact_container

    def _create_compact_components(self):
        """Crea los componentes compactos optimizados para modo lateral/compacto"""
        self.compact_play_btn = ft.Container(
            content=icon("play_txt", size=20, color=ft.Colors.WHITE),
            width=70,
            height=45,
            border_radius=8,
            bgcolor=self.theme.get("button_play"),
            on_click=self.play_btn.on_click,
            ink=True,
            alignment=ft.Alignment.CENTER,
        )
        self.compact_stop_btn = ft.Container(
            content=icon("hand-stop", size=20, color=ft.Colors.WHITE),
            width=70,
            height=45,
            border_radius=8,
            bgcolor=self.theme.get("button_stop"),
            on_click=self.stop_btn.on_click,
            ink=True,
            alignment=ft.Alignment.CENTER,
        )
        self.compact_prev_btn = ft.Container(
            content=ft.Icon(ft.Icons.SKIP_PREVIOUS_ROUNDED, size=20, color=ft.Colors.WHITE),
            width=50,
            height=45,
            border_radius=8,
            bgcolor=self.theme.get("button_nav"),
            on_click=self.prev_btn.on_click,
            ink=True,
            alignment=ft.Alignment.CENTER,
        )
        self.compact_next_btn = ft.Container(
            content=ft.Icon(ft.Icons.SKIP_NEXT_ROUNDED, size=20, color=ft.Colors.WHITE),
            width=50,
            height=45,
            border_radius=8,
            bgcolor=self.theme.get("button_nav"),
            on_click=self.next_btn.on_click,
            ink=True,
            alignment=ft.Alignment.CENTER,
        )
        self.compact_scan_btn = ft.Container(
            content=icon("search2", size=20, color=ft.Colors.WHITE),
            width=50,
            height=45,
            border_radius=8,
            bgcolor=self.theme.get("button_scan"),
            on_click=self.scan_btn.on_click,
            ink=True,
            alignment=ft.Alignment.CENTER,
        )
        self.compact_metronome_btn = ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    icon("metronome3", size=16, color=ft.Colors.WHITE),
                    ft.Text("CLICK", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ]
            ),
            width=80,
            height=45,
            border_radius=8,
            bgcolor=self.theme.get("button_metro_on" if state.metronome_on else "button_metro"),
            on_click=self.metronome_btn.button.on_click,
            ink=True,
            alignment=ft.Alignment.CENTER,
        )
        
        self.compact_status_text = ft.Text(
            StatusBar.instance.text.value if hasattr(StatusBar, 'instance') else "",
            size=11,
            color=self.theme.get("accent"),
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_500,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
            width=300,
        )
        
        self.compact_container = ft.Container(
            content=ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    # Row 1: Metrónomo + Tempo + Scan
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            self.compact_metronome_btn,
                            ft.Container(
                                content=self.tempo_display.text,
                                alignment=ft.Alignment.CENTER,
                                padding=ft.padding.Padding(left=10, right=10, top=0, bottom=0),
                            ),
                            self.compact_scan_btn,
                        ]
                    ),
                    # Row 2: Play/Stop/Nav
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            self.compact_prev_btn,
                            self.compact_play_btn,
                            self.compact_stop_btn,
                            self.compact_next_btn,
                        ]
                    ),
                    # Row 3: Status
                    self.compact_status_text,
                ]
            ),
            padding=ft.padding.Padding(left=12, right=12, top=12, bottom=12),
            bgcolor=self.theme.get("bg_secondary"),
            border_radius=12,
            border=ft.border.Border.all(1, self.theme.get("border") + "40"),
        )
