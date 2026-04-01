# ============================================================================
# LiveCue - Ableton Setlist Controller
# Copyright (c) 2026 Mario Collado Rodríguez. Todos los derechos reservados.
# 
# Este software está licenciado bajo CC BY-NC-SA 4.0
# NO se permite uso comercial sin autorización explícita por escrito.
# 
# Licencia: https://creativecommons.org/licenses/by-nc-sa/4.0/
# Repositorio: https://github.com/MarioCollado/LiveCue
# Contacto para licencias comerciales: mcolladorguez@gmail.com
# ============================================================================

# ui/app_ui.py
import flet as ft
import time
import threading
import asyncio
from core.state import state
from core.playback import playback
from setlist.manager import manager
from ui.themes import ThemeManager
from ui.components import StatusBar
from ui.header_component import create_header, SetTimer
from ui.welcome_dialog import show_welcome_dialog
from ui.dialogs import DialogManager
from ui.track_list import TrackListView
from ui.control_panel import ControlPanel
from core.i18n import i18n


# ============================================
# SAFE UI UPDATE UTILITY
# ============================================
class SafeUIUpdater:
    """Maneja actualizaciones seguras de la UI con retry"""
    
    @staticmethod
    def update_sync(page_ref, max_retries: int = 3) -> bool:
        """Versión SÍNCRONA segura con retry"""
        if not page_ref:
            return False

        for attempt in range(max_retries):
            try:
                if not hasattr(page_ref, 'update'):
                    return False

                if hasattr(page_ref, 'window') and page_ref.window is None:
                    return False

                page_ref.update()
                return True

            except AssertionError as e:
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


# ============================================
# OSC CALLBACK MANAGER
# ============================================
class OSCCallbackManager:
    """Gestiona los callbacks de OSC de forma thread-safe"""
    
    def __init__(self, page: ft.Page, control_panel: ControlPanel, track_list: TrackListView):
        self.page = page
        self.control_panel = control_panel
        self.track_list = track_list
    
    def setup_callbacks(self):
        """Configura todos los callbacks de OSC"""
        self.page.trigger_pulse = self._trigger_pulse_wrapper
        self.page.update_tempo_display = self._update_tempo_display_wrapper
        self.page.update_listbox = self._update_listbox_wrapper
        self.page.update_metronome_ui = self._update_metronome_ui_wrapper
    
    def _trigger_pulse_wrapper(self, beat: int):
        """Wrapper thread-safe para trigger_pulse desde OSC"""
        try:
            self.control_panel.beat_indicator.pulse(
                beat, 
                state.time_signature_num, 
                lambda: SafeUIUpdater.update_sync(self.page)
            )
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] trigger_pulse: {e}")

    def _update_tempo_display_wrapper(self):
        """Wrapper thread-safe para update_tempo_display desde OSC"""
        try:
            self.control_panel.tempo_display.update(
                state.current_tempo, 
                state.time_signature_num, 
                lambda: SafeUIUpdater.update_sync(self.page)
            )
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_tempo_display: {e}")

    def _update_listbox_wrapper(self):
        """Wrapper thread-safe para update_listbox desde OSC con debounce interno"""
        try:
            if hasattr(self.page, 'run_task'):
                # El debouncer ahora es interno de TrackListView
                self.track_list.debouncer.request_update(
                    lambda: self.page.run_task(self.track_list.update)
                )
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_listbox: {e}")
                
    def _update_metronome_ui_wrapper(self):
        """Wrapper thread-safe para update_metronome_ui desde OSC"""
        try:
            self.control_panel.metronome_btn.set_state(state.metronome_on)
            SafeUIUpdater.update_sync(self.page)
        except Exception as e:
            if "__uid" not in str(e):
                print(f"[ERROR] update_metronome_ui: {e}")


# ============================================
# INITIAL SCAN MANAGER
# ============================================
class InitialScanManager:
    """Gestiona el escaneo inicial de tracks con feedback visual"""
    
    def __init__(self, page: ft.Page, control_panel: ControlPanel, 
                 track_list: TrackListView, theme: ThemeManager):
        self.page = page
        self.control_panel = control_panel
        self.track_list = track_list
        self.theme = theme
    
    async def run(self):
        """Ejecuta el scan después de que la UI esté completamente renderizada"""
        try:
            print("[INIT] ⏳ UI renderizada, esperando estabilización...")
            await asyncio.sleep(1.2)
            
            print("[INIT] ⟳ Ejecutando scan inicial con feedback visual...")
            
            state.is_scanning = True
            
            # PASO 1: Iniciar
            await self._update_progress("Iniciando escaneo inicial...", 0)
            
            # PASO 2: Conectar
            await self._update_progress("Conectando con Ableton Live...", 15)
            
            # PASO 3: Detectar locators
            await self._update_progress("Detectando locators...", 35)
            
            # PASO 4: Procesar tracks
            await self._update_progress("Procesando tracks...", 50)
            
            # Ejecutar scan en thread separado
            scan_success = await self._execute_scan()
            
            if scan_success:
                # PASO 5: Identificar secciones
                await self._update_progress("Identificando secciones...", 75)
                
                # PASO 6: Finalizar
                await self._update_progress("Finalizando...", 90)
                
                # PASO 7: Actualizar UI
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
        """Actualiza el progreso del scan"""
        self.control_panel._update_scan_ui(message, progress, scanning=True)
        await asyncio.sleep(0.3)
    
    async def _execute_scan(self) -> bool:
        """Ejecuta el scan real en un thread separado"""
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
        
        return scan_success[0]
    
    async def _update_ui_with_results(self):
        """Actualiza la UI con los resultados del scan"""
        print("[INIT] Actualizando UI con tracks...")
        
        self.control_panel._update_scan_ui("Actualizando interfaz...", 95, scanning=True)
        await asyncio.sleep(0.2)
        
        if TrackListView.instance:
            # Forzar recreación completa para actualizar callbacks
            print("[INIT] Forzando recreación de items tras scan...")
            await TrackListView.instance.update()
            
            # Segundo update para asegurar que callbacks están actualizados
            await asyncio.sleep(0.15)
            await TrackListView.instance.update()
            
            print("[INIT] ✓ UI actualizada correctamente")
            
            track_count = state.get_track_count()
            self.control_panel._update_scan_ui(
                f"✓ {track_count} tracks encontrados", 
                100, 
                scanning=True
            )
            
            StatusBar.instance.text.value = f"● ✓ Scan inicial completo: {track_count} tracks"
            StatusBar.instance.text.color = self.theme.get("button_play")
            self.page.update()
            
            await asyncio.sleep(2)
        else:
            print("[INIT] ✗ TrackListView.instance no disponible")
            self.control_panel._update_scan_ui("✗ Error en UI", 0, scanning=True)
            await asyncio.sleep(2)
    
    async def _show_no_tracks_warning(self):
        """Muestra advertencia cuando no hay tracks"""
        print("[INIT] ⚠ No hay tracks para mostrar en UI")
        self.control_panel._update_scan_ui("⚠ No se detectaron tracks", 0, scanning=True)
        
        StatusBar.instance.text.value = "● ⚠ Sin tracks detectados"
        StatusBar.instance.text.color = self.theme.get("text_secondary")
        self.page.update()
        
        await asyncio.sleep(2)
    
    async def _show_error(self, error_msg: str):
        """Muestra error en la UI"""
        try:
            self.control_panel._update_scan_ui(
                f"✗ Error: {error_msg[:30]}", 
                0, 
                scanning=True
            )
            StatusBar.instance.text.value = "● ✗ Error en scan inicial"
            StatusBar.instance.text.color = self.theme.get("button_stop")
            self.page.update()
            await asyncio.sleep(2)
        except:
            pass
    
    async def _cleanup(self):
        """Limpia el estado después del scan"""
        state.is_scanning = False
        self.control_panel._update_scan_ui("", 0, scanning=False)
        
        await asyncio.sleep(1)
        try:
            self.control_panel.scan_status_text.visible = False
            self.page.update()
        except:
            pass


# ============================================
# THEME CHANGE HANDLER
# ============================================
class ThemeChangeHandler:
    """Maneja los cambios de tema"""
    
    def __init__(self, page: ft.Page, theme: ThemeManager, control_panel: ControlPanel,
                 track_list: TrackListView, palette_dropdown: ft.Dropdown,
                 listbox_container: ft.Container, save_counter: ft.Text,
                 save_btn: ft.IconButton, load_btn: ft.IconButton, set_timer):
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
        """Callback para cambio de tema"""
        try:
            self.theme.set_theme(self.palette_dropdown.value)
            
            # Actualizar colores base
            self._update_base_colors()
            
            # Recrear header
            self._recreate_header()
            
            # Actualizar panel de control
            self._update_control_panel_colors()
            
            # Actualizar otros componentes
            self._update_other_components()
            
            # Actualizar status
            StatusBar.instance.text.value = i18n.get("status_palette", self.theme.current_name)
            StatusBar.instance.text.color = self.theme.get("accent")
            
            # Actualizar lista y página
            self.page.run_task(self.track_list.update)
            self.page.update()
            
        except Exception as ex:
            print(f"[ERROR] on_theme_change: {ex}")
    
    def _update_base_colors(self):
        """Actualiza colores base de la página"""
        self.page.bgcolor = self.theme.get("bg_main")
        self.listbox_container.bgcolor = self.theme.get("bg_card") + "40"
    
    def _recreate_header(self):
        """Recrea el header con el nuevo tema"""
        new_header = create_header(
            self.page, 
            self.palette_dropdown, 
            self.save_counter, 
            self.save_btn, 
            self.load_btn, 
            self.theme.get, 
            web_port=5000, 
            set_timer=self.set_timer
        )
        self.page.controls[0].content.controls[0] = new_header
    
    def _update_control_panel_colors(self):
        """Actualiza colores del panel de control"""
        self.control_panel.play_btn.bgcolor = self.theme.get("button_play")
        self.control_panel.stop_btn.bgcolor = self.theme.get("button_stop")
        self.control_panel.prev_btn.bgcolor = self.theme.get("button_nav")
        self.control_panel.next_btn.bgcolor = self.theme.get("button_nav")
        self.control_panel.scan_btn.bgcolor = self.theme.get("button_scan")
        self.control_panel.beat_indicator.container.bgcolor = self.theme.get("bg_card")
    
    def _update_other_components(self):
        """Actualiza otros componentes dependientes del tema"""
        self.control_panel.tempo_display.text.color = self.theme.get("text_primary")
        self.control_panel.scan_status_text.color = self.theme.get("accent")


# ============================================
# APP BUILDER
# ============================================
class AppBuilder:
    """Construye la aplicación completa"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.theme = None
        self.track_list = None
        self.control_panel = None
        self.dialog_manager = None
        self.set_timer = SetTimer()
    
    def build(self):
        """Construye y configura la aplicación completa"""
        try:
            print("[UI] Inicializando página...")
            self._setup_page()
            
            print("[UI] Creando componentes...")
            self._create_components()
            
            self._setup_header()
            self._setup_layout()
            self._setup_callbacks()
            
            # Managers
            osc_manager = OSCCallbackManager(self.page, self.control_panel, self.track_list)
            osc_manager.setup_callbacks()
            
            # Scan inicial
            scan_manager = InitialScanManager(
                self.page, 
                self.control_panel, 
                self.track_list, 
                self.theme
            )
            self.page.run_task(scan_manager.run)
            
            # Welcome dialog
            self.page.run_task(self._show_welcome)
            
            print("[INIT] ✓ App lista - scan programado...\n")
            
        except Exception as e:
            print(f"[ERROR] Inicialización fallida: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _setup_page(self):
        """Configura las propiedades básicas de la página"""
        state.page_ref = self.page
        
        self.page.title = "Ableton Setlist Controller"
        self.page.window.width = 900
        self.page.window.height = 800
        self.page.window.resizable = True
        self.page.window.maximized = True
        self.page.padding = 0
        self.page.spacing = 0
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.fonts = {"DS-Digital": "fonts/DS-DIGI.TTF"}
        
        self.page.on_close = self._on_window_close
    
    def _create_components(self):
        """Crea todos los componentes principales"""
        # Tema
        self.theme = ThemeManager("Deep Space")
        self.page.theme = ft.Theme(color_scheme_seed=self.theme.get("accent"))
        self.page.bgcolor = self.theme.get("bg_main")
        
        # Status bar
        status_bar = StatusBar(self.theme.get)
        StatusBar.instance = status_bar
        
        # Track list
        self.track_list = TrackListView(self.theme, self.page)
        TrackListView.instance = self.track_list
        
        # Control panel
        self.control_panel = ControlPanel(self.theme, self.page)
        
        # Dialog manager
        self.dialog_manager = DialogManager(self.page, self.theme)
    
    def _setup_header(self):
        """Configura el header y sus componentes"""
        # Save counter
        self.save_counter = ft.Text(
            f"💾 {len(manager.list_all())}", 
            size=12, 
            weight=ft.FontWeight.W_500, 
            color=self.theme.get("text_primary")
        )
        self.dialog_manager.save_counter = self.save_counter
        
        # Botones
        self.save_btn = ft.IconButton(
            icon=ft.Icons.SAVE,
            on_click=lambda e: self.page.run_task(self.dialog_manager.show_save_setlist),
            icon_size=22,
            tooltip="Guardar Setlist"
        )
        
        self.load_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda e: self.page.run_task(self.dialog_manager.show_load_setlist),
            icon_size=22,
            tooltip="Cargar Setlist"
        )
        
        # Palette dropdown
        self.palette_dropdown = ft.Dropdown(
            width=180,
            value=self.theme.current_name,
            options=[ft.dropdown.Option(name) for name in ThemeManager.list_themes()],
            text_size=13,
            bgcolor=self.theme.get("bg_card") + "00",
            border_color=self.theme.get("bg_main") + "00",
            focused_border_color=self.theme.get("accent") + "00",
            text_style=ft.TextStyle(
                weight=ft.FontWeight.W_600, 
                color=self.theme.get("text_primary")
            ),
            content_padding=ft.padding.symmetric(horizontal=8, vertical=8),
        )
    
    def _setup_layout(self):
        """Configura el layout de la aplicación"""
        self.listbox_container = ft.Container(
            content=self.track_list.column,
            expand=True,
            border_radius=12,
            padding=ft.padding.all(18),
            bgcolor=self.theme.get("bg_card") + "40",
        )
        
        # Header
        self.header_container = create_header(
            self.page,
            self.palette_dropdown,
            self.save_counter,
            self.save_btn,
            self.load_btn,
            self.theme.get,
            web_port=5000,
            set_timer=self.set_timer
        )
        
        # Main row
        main_row = ft.Row(
            spacing=18,
            expand=True,
            controls=[
                ft.Column(expand=True, spacing=0, controls=[self.listbox_container]),
                ft.Container(width=250, content=self.control_panel.container)
            ]
        )
        
        # Add to page
        self.page.add(
            ft.Container(
                expand=True,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        self.header_container,
                        ft.Container(
                            expand=True,
                            padding=ft.padding.only(left=18, right=18, bottom=18, top=10),
                            content=main_row
                        )
                    ]
                )
            )
        )
    
    def _setup_callbacks(self):
        """Configura los callbacks"""
        # Theme change handler
        theme_handler = ThemeChangeHandler(
            self.page,
            self.theme,
            self.control_panel,
            self.track_list,
            self.palette_dropdown,
            self.listbox_container,
            self.save_counter,
            self.save_btn,
            self.load_btn,
            self.set_timer
        )
        self.palette_dropdown.on_change = theme_handler.handle_change
    
    def _on_window_close(self, e):
        """Callback de cierre de ventana"""
        print("[UI] Cerrando aplicación...")
        state.page_ref = None
    
    async def _show_welcome(self):
        """Muestra el diálogo de bienvenida"""
        await asyncio.sleep(0.5)
        show_welcome_dialog(self.page, self.theme.get, on_accept_callback=None)


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main(page: ft.Page):
    """Función principal - Thread-safe con async"""
    app = AppBuilder(page)
    app.build()