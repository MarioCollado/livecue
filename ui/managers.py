"""Managers de UI extraídos de app_ui para reducir acoplamiento."""

from __future__ import annotations

import asyncio
import threading
import time

import flet as ft

from core.i18n import i18n
from core.constants import FLASK_PORT
from core.playback import playback
from core.state import state
from ui.components import StatusBar
from ui.control_panel import ControlPanel
from ui.header_component import SetTimer, create_header
from ui.track_list import TrackListView
from ui.themes import ThemeManager


class SafeUIUpdater:
    """Maneja actualizaciones seguras de la UI con retry."""

    @staticmethod
    def update_sync(page_ref, max_retries: int = 3) -> bool:
        if not page_ref:
            return False

        for attempt in range(max_retries):
            try:
                if not hasattr(page_ref, "update"):
                    return False

                if hasattr(page_ref, "window") and page_ref.window is None:
                    return False

                page_ref.update()
                return True
            except AssertionError:
                print(f"[SAFE_UI_UPDATE] AssertionError en intento {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(0.05)
                    continue
                return False
            except Exception as e:
                error_msg = str(e)
                if "__uid" not in error_msg and "update_async" not in error_msg:
                    print(f"[SAFE_UI_UPDATE ERROR] {error_msg}")
                return False

        return False


class OSCCallbackManager:
    """Gestiona los callbacks de OSC de forma thread-safe."""

    def __init__(self, page: ft.Page, control_panel: ControlPanel, track_list: TrackListView):
        self.page = page
        self.control_panel = control_panel
        self.track_list = track_list

    def setup_callbacks(self):
        self.page.trigger_pulse = self._trigger_pulse_wrapper
        self.page.update_tempo_display = self._update_tempo_display_wrapper
        self.page.update_listbox = self._update_listbox_wrapper
        self.page.update_metronome_ui = self._update_metronome_ui_wrapper

    def _trigger_pulse_wrapper(self, beat: int):
        try:
            self.control_panel.beat_indicator.pulse(
                beat,
                state.time_signature_num,
                lambda: SafeUIUpdater.update_sync(self.page),
            )
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] trigger_pulse: {e}")

    def _update_tempo_display_wrapper(self):
        try:
            self.control_panel.tempo_display.update(
                state.current_tempo,
                state.time_signature_num,
                lambda: SafeUIUpdater.update_sync(self.page),
            )
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_tempo_display: {e}")

    def _update_listbox_wrapper(self):
        try:
            if hasattr(self.page, "run_task"):
                self.track_list.debouncer.request_update(
                    lambda: self.page.run_task(self.track_list.update)
                )
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_listbox: {e}")

    def _update_metronome_ui_wrapper(self):
        try:
            self.control_panel.metronome_btn.set_state(state.metronome_on)
            SafeUIUpdater.update_sync(self.page)
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_metronome_ui: {e}")


class InitialScanManager:
    """Gestiona el escaneo inicial de tracks con feedback visual."""

    def __init__(self, page: ft.Page, control_panel: ControlPanel, track_list: TrackListView, theme: ThemeManager):
        self.page = page
        self.control_panel = control_panel
        self.track_list = track_list
        self.theme = theme

    async def run(self):
        try:
            print("[INIT] ⏳ UI renderizada, esperando estabilización...")
            await asyncio.sleep(1.2)

            print("[INIT] ⟳ Ejecutando scan inicial con feedback visual...")

            state.is_scanning = True
            await self._update_progress("Iniciando escaneo inicial...", 0)
            await self._update_progress("Conectando con Ableton Live...", 15)
            await self._update_progress("Detectando locators...", 35)
            await self._update_progress("Procesando tracks...", 50)

            scan_success = await self._execute_scan()

            if scan_success:
                await self._update_progress("Identificando secciones...", 75)
                await self._update_progress("Finalizando...", 90)
                await self._update_ui_with_results()
            else:
                await self._show_no_tracks_warning()

        except Exception as e:
            print(f"[ERROR] run_initial_scan: {e}")
            import traceback

            traceback.print_exc()
            await self._show_error(str(e))
        finally:
            await self._cleanup()

    async def _update_progress(self, message: str, progress: int):
        self.control_panel._update_scan_ui(message, progress, scanning=True)
        await asyncio.sleep(0.3)

    async def _execute_scan(self) -> bool:
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

        await asyncio.get_event_loop().run_in_executor(None, lambda: scan_complete.wait(timeout=10.0))
        return scan_success[0]

    async def _update_ui_with_results(self):
        print("[INIT] Actualizando UI con tracks...")
        self.control_panel._update_scan_ui("Actualizando interfaz...", 95, scanning=True)
        await asyncio.sleep(0.2)

        if TrackListView.instance:
            print("[INIT] Forzando recreación de items tras scan...")
            await TrackListView.instance.update()
            await asyncio.sleep(0.15)
            await TrackListView.instance.update()

            print("[INIT] ✓ UI actualizada correctamente")
            track_count = state.get_track_count()
            self.control_panel._update_scan_ui(f"✓ {track_count} tracks encontrados", 100, scanning=True)

            StatusBar.instance.text.value = f"● ✓ Scan inicial completo: {track_count} tracks"
            StatusBar.instance.text.color = self.theme.get("button_play")
            self.page.update()

            await asyncio.sleep(2)
        else:
            print("[INIT] ✗ TrackListView.instance no disponible")
            self.control_panel._update_scan_ui("✗ Error en UI", 0, scanning=True)
            await asyncio.sleep(2)

    async def _show_no_tracks_warning(self):
        print("[INIT] ⚠ No hay tracks para mostrar en UI")
        self.control_panel._update_scan_ui("⚠ No se detectaron tracks", 0, scanning=True)
        StatusBar.instance.text.value = "● ⚠ Sin tracks detectados"
        StatusBar.instance.text.color = self.theme.get("text_secondary")
        self.page.update()
        await asyncio.sleep(2)

    async def _show_error(self, error_msg: str):
        try:
            self.control_panel._update_scan_ui(f"✗ Error: {error_msg[:30]}", 0, scanning=True)
            StatusBar.instance.text.value = "● ✗ Error en scan inicial"
            StatusBar.instance.text.color = self.theme.get("button_stop")
            self.page.update()
            await asyncio.sleep(2)
        except Exception:
            pass

    async def _cleanup(self):
        state.is_scanning = False
        self.control_panel._update_scan_ui("", 0, scanning=False)
        await asyncio.sleep(1)
        try:
            self.control_panel.scan_status_text.visible = False
            self.page.update()
        except Exception:
            pass


class ThemeChangeHandler:
    """Maneja los cambios de tema."""

    def __init__(
        self,
        page: ft.Page,
        theme: ThemeManager,
        control_panel: ControlPanel,
        track_list: TrackListView,
        palette_dropdown: ft.Dropdown,
        listbox_container: ft.Container,
        save_counter: ft.Text,
        save_btn: ft.IconButton,
        load_btn: ft.IconButton,
        set_timer,
    ):
        self.page = page
        self.theme = theme
        self.control_panel = control_panel
        self.track_list = track_list
        self.palette_dropdown = palette_dropdown
        self.listbox_container = listbox_container
        self.save_counter = save_counter
        self.save_btn = save_btn
        self.load_btn = load_btn
        self.set_timer = set_timer

    def handle_change(self, e):
        try:
            self.theme.set_theme(self.palette_dropdown.value)
            self._update_base_colors()
            self._recreate_header()
            self._update_control_panel_colors()
            self._update_other_components()

            StatusBar.instance.text.value = i18n.get("status_palette", self.theme.current_name)
            StatusBar.instance.text.color = self.theme.get("accent")

            self.page.run_task(self.track_list.update)
            self.page.update()
        except Exception as ex:
            print(f"[ERROR] on_theme_change: {ex}")

    def _update_base_colors(self):
        self.page.bgcolor = self.theme.get("bg_main")
        self.listbox_container.bgcolor = self.theme.get("bg_card") + "40"

    def _recreate_header(self):
        new_header = create_header(
            self.page,
            self.palette_dropdown,
            self.save_counter,
            self.save_btn,
            self.load_btn,
            self.theme.get,
            web_port=FLASK_PORT,
            set_timer=self.set_timer,
        )
        self.page.controls[0].content.controls[0] = new_header

    def _update_control_panel_colors(self):
        self.control_panel.play_btn.bgcolor = self.theme.get("button_play")
        self.control_panel.stop_btn.bgcolor = self.theme.get("button_stop")
        self.control_panel.prev_btn.bgcolor = self.theme.get("button_nav")
        self.control_panel.next_btn.bgcolor = self.theme.get("button_nav")
        self.control_panel.scan_btn.bgcolor = self.theme.get("button_scan")
        self.control_panel.beat_indicator.container.bgcolor = self.theme.get("bg_card")

    def _update_other_components(self):
        self.control_panel.tempo_display.text.color = self.theme.get("text_primary")
        self.control_panel.scan_status_text.color = self.theme.get("accent")


__all__ = [
    "InitialScanManager",
    "OSCCallbackManager",
    "SafeUIUpdater",
    "ThemeChangeHandler",
]
