# ui/components.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
import time
import threading
import asyncio
from core.state import state
from ui.themes import ThemeManager
from core.playback import playback
from core.utils import icon
from ui.track_list import TrackListView
from setlist.manager import manager
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
                            scan_section
                        ]
                    ),
                    border_radius=12,
                    padding=ft.padding.all(18),
                    expand=True
                )
            ]
        )

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
            alignment=ft.alignment.center,
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
            alignment=ft.alignment.center,
        )

    async def _on_metronome_click(self, e):
        try:
            is_on = playback.toggle_metronome()
            self.metronome_btn.set_state(is_on)
            
            StatusBar.instance.text.value = i18n.get("status_metronome", i18n.get("status_metronome_on") if is_on else i18n.get("status_metronome_off"))
            StatusBar.instance.text.color = self.theme.get("button_metro_on") if is_on else self.theme.get("text_secondary")
            self.page.update()
        except Exception as ex:
            print(f"[ERROR] _on_metronome_click: {ex}")

    async def _on_play(self, e):
        try:
            current_idx = state.current_index
            track_count = state.get_track_count()
            
            if current_idx < 0 or current_idx >= track_count:
                StatusBar.instance.text.value = i18n.get("status_no_track_selected")
                StatusBar.instance.text.color = self.theme.get("button_stop")
                self.page.update()
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
                
                StatusBar.instance.text.value = i18n.get("status_play", track.title)
                StatusBar.instance.text.color = self.theme.get("button_play")
                self.page.update()
                # Solo actualizar el track actual, no toda la lista
                await TrackListView.instance.update_single_track(current_idx)
            else:
                StatusBar.instance.text.value = i18n.get("status_play_error")
                StatusBar.instance.text.color = self.theme.get("button_stop")
                self.page.update()
        except Exception as ex:
            print(f"[ERROR] _on_play: {ex}")

    async def _on_stop(self, e):
        try:
            playback.stop()
            StatusBar.instance.text.value = i18n.get("status_stop")
            StatusBar.instance.text.color = self.theme.get("button_stop")
            self.page.update()
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
                    StatusBar.instance.text.value = i18n.get("status_next", track.title)
                    StatusBar.instance.text.color = self.theme.get("button_play")
                    self.page.update()
            else:
                StatusBar.instance.text.value = i18n.get("status_last_track")
                StatusBar.instance.text.color = self.theme.get("text_secondary")
                self.page.update()
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
                    StatusBar.instance.text.value = i18n.get("status_prev", track.title)
                    StatusBar.instance.text.color = self.theme.get("button_play")
                    self.page.update()
            else:
                StatusBar.instance.text.value = i18n.get("status_first_track")
                StatusBar.instance.text.color = self.theme.get("text_secondary")
                self.page.update()
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
                
                StatusBar.instance.text.value = f"● {i18n.get('status_scan_complete', track_count)}"
                StatusBar.instance.text.color = self.theme.get("button_play")
                
                # Mostrar mensaje de éxito 1.5 segundos
                await asyncio.sleep(1.5)
                
            else:
                # Error en scan
                self._update_scan_ui(i18n.get("scan_error"), 0, scanning=True)
                StatusBar.instance.text.value = f"● {i18n.get('status_scan_error')}"
                StatusBar.instance.text.color = self.theme.get("button_stop")
                await asyncio.sleep(2)
            
        except Exception as ex:
            print(f"[ERROR] _on_scan: {ex}")
            import traceback
            traceback.print_exc()
            
            self._update_scan_ui(i18n.get("scan_error_critical"), 0, scanning=True)
            StatusBar.instance.text.value = f"● ✗ Error: {str(ex)}"
            StatusBar.instance.text.color = self.theme.get("button_stop")
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
