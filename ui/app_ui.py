# ============================================================================
# LiveCue - Ableton Setlist Controller
# Copyright (c) 2025 Mario Collado Rodríguez. Todos los derechos reservados.
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
from ui.components import BeatIndicator, TempoDisplay, StatusBar, MetronomeButton 
from ui.header_component import create_header, SetTimer
from ui.welcome_dialog import show_welcome_dialog
from core.logger import log_info, log_error, log_warning, log_debug
from ui.dialogs import DialogManager
from ui.track_list import TrackListView, update_debouncer
from ui.control_panel import ControlPanel

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
# FUNCIÓN PRINCIPAL
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
            "DS-Digital": "fonts/DS-DIGI.TTF"
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
            
            # Actualizar colores del panel
            control_panel.play_btn.bgcolor = theme.get("button_play")
            control_panel.stop_btn.bgcolor = theme.get("button_stop")
            control_panel.prev_btn.bgcolor = theme.get("button_nav")
            control_panel.next_btn.bgcolor = theme.get("button_nav")
            control_panel.scan_btn.bgcolor = theme.get("button_scan")

            # Otros elementos dependientes del tema
            control_panel.beat_indicator.container.bgcolor = theme.get("bg_card")
            control_panel.tempo_display.text.color = theme.get("text_primary")
            control_panel.scan_status_text.color = theme.get("accent")
            
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
        bgcolor=theme.get("bg_card"),
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
    # SCAN INICIAL - VERSIÓN ROBUSTA CON FEEDBACK VISUAL
    # ============================================
    async def run_initial_scan():
        """Ejecuta el scan después de que la UI esté completamente renderizada"""
        try:
            print("[INIT] ⏳ UI renderizada, esperando estabilización...")
            await asyncio.sleep(1.2)
            
            print("[INIT] ⟳ Ejecutando scan inicial con feedback visual...")
            
            # PASO 1: Activar modo scanning
            state.is_scanning = True
            control_panel._update_scan_ui("Iniciando escaneo inicial...", 0, scanning=True)
            await asyncio.sleep(0.3)
            
            # PASO 2: Conectando
            control_panel._update_scan_ui("Conectando con Ableton Live...", 15, scanning=True)
            await asyncio.sleep(0.3)
            
            # PASO 3: Detectando locators
            control_panel._update_scan_ui("Detectando locators...", 35, scanning=True)
            await asyncio.sleep(0.2)
            
            # PASO 4: Procesando (inicio del scan real)
            control_panel._update_scan_ui("Procesando tracks...", 50, scanning=True)
            
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
            
            # PASO 5: Identificando secciones
            if scan_success[0]:
                control_panel._update_scan_ui("Identificando secciones...", 75, scanning=True)
                await asyncio.sleep(0.3)
            
            # PASO 6: Finalizando
            control_panel._update_scan_ui("Finalizando...", 90, scanning=True)
            await asyncio.sleep(0.2)
            
            # Actualizar UI si hay tracks
            if scan_success[0] and state.get_track_count() > 0:
                print("[INIT] Actualizando UI con tracks...")
                
                control_panel._update_scan_ui("Actualizando interfaz...", 95, scanning=True)
                await asyncio.sleep(0.2)
                
                if TrackListView.instance:
                    await TrackListView.instance.update()
                    print("[INIT] ✓ UI actualizada correctamente")
                    
                    # PASO 7: Éxito
                    track_count = state.get_track_count()
                    control_panel._update_scan_ui(f"✓ {track_count} tracks encontrados", 100, scanning=True)
                    
                    StatusBar.instance.text.value = f"● ✓ Scan inicial completo: {track_count} tracks"
                    StatusBar.instance.text.color = theme.get("button_play")
                    page.update()
                    
                    # Mostrar mensaje de éxito 2 segundos
                    await asyncio.sleep(2)
                else:
                    print("[INIT] ✗ TrackListView.instance no disponible")
                    control_panel._update_scan_ui("✗ Error en UI", 0, scanning=True)
                    await asyncio.sleep(2)
            else:
                print("[INIT] ⚠ No hay tracks para mostrar en UI")
                control_panel._update_scan_ui("⚠ No se detectaron tracks", 0, scanning=True)
                
                StatusBar.instance.text.value = "● ⚠ Sin tracks detectados"
                StatusBar.instance.text.color = theme.get("text_secondary")
                page.update()
                
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"[ERROR] run_initial_scan: {e}")
            import traceback
            traceback.print_exc()
            
            # Mostrar error en UI
            try:
                control_panel._update_scan_ui(f"✗ Error: {str(e)[:30]}", 0, scanning=True)
                StatusBar.instance.text.value = "● ✗ Error en scan inicial"
                StatusBar.instance.text.color = theme.get("button_stop")
                page.update()
                await asyncio.sleep(2)
            except:
                pass
        
        finally:
            # SIEMPRE restaurar UI
            state.is_scanning = False
            control_panel._update_scan_ui("", 0, scanning=False)
            
            # Ocultar status text después de 1 segundo
            await asyncio.sleep(1)
            try:
                control_panel.scan_status_text.visible = False
                page.update()
            except:
                pass
                            
    print("[INIT] Programando scan inicial...")
    page.run_task(run_initial_scan)

    # ============================================
    # MOSTRAR DIÁLOGO DE BIENVENIDA
    # ============================================
    # Mostrar después de que la UI esté lista
    async def show_welcome():
        await asyncio.sleep(0.5)  # Esperar a que la UI se renderice
        show_welcome_dialog(page, theme.get, on_accept_callback=None)

    page.run_task(show_welcome)

    print("[INIT] ✓ App lista - scan programado...\n")