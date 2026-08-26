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
import asyncio
from core.state import state
from core.constants import FLASK_PORT
from setlist.manager import manager
from ui.themes import ThemeManager
from ui.components import StatusBar
from ui.header_component import create_header, SetTimer
from ui.welcome_dialog import show_welcome_dialog
from ui.dialogs import DialogManager
from ui.track_list import TrackListView
from ui.control_panel import ControlPanel
from ui.managers import InitialScanManager, OSCCallbackManager, ThemeChangeHandler


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
        self.page.app_builder = self
        
        self.page.title = "Ableton Setlist Controller"
        self.page.padding = 0
        self.page.spacing = 0
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.fonts = {"DS-Digital": "fonts/DS-DIGI.TTF"}
        self.page.on_close = self._on_window_close

        # Configurar estado inicial de la ventana según settings persistidos
        view_mode = getattr(state, 'view_mode', 'fullscreen')
        if view_mode == "fullscreen":
            self.page.window.width = 900
            self.page.window.height = 800
            self.page.window.resizable = True
            self.page.window.maximized = True
        elif view_mode == "side_panel":
            self.page.window.maximized = False
            self.page.window.width = 380
            self.page.window.height = 800
            self.page.window.resizable = True
        elif view_mode == "compact":
            self.page.window.maximized = False
            self.page.window.width = 420
            self.page.window.height = 360
            self.page.window.resizable = True
    
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
                content_padding=ft.padding.Padding(left=8, right=8, top=8, bottom=8),
        )
    
    def _setup_layout(self):
        """Configura el layout de la aplicación"""
        self.listbox_container = ft.Container(
            content=self.track_list.column,
            expand=True,
            border_radius=12,
            padding=ft.padding.Padding(left=10, right=10, top=10, bottom=10),
            bgcolor=self.theme.get("bg_card") + "40",
        )

        self.view_mode = getattr(state, 'view_mode', 'fullscreen')

        # Header inicial vacío
        self.header_container = ft.Container()

        # Contenedor principal para el layout dinámico
        self.main_layout_container = ft.Container(expand=True)

        # Estructura fija a la página
        self.page.add(
            ft.Container(
                expand=True,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        self.header_container,
                        self.main_layout_container
                    ]
                )
            )
        )

        # Aplicamos el modo de vista actual para renderizar el contenido
        self.apply_view_mode(self.view_mode, initial=True)
    
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

    def apply_view_mode(self, mode: str, initial=False):
        """Cambia el modo de visualización de la ventana y el layout"""
        self.view_mode = mode
        state.view_mode = mode
        
        # Guardar configuración
        try:
            from core.settings import save_settings
            save_settings({"view_mode": mode})
        except Exception as e:
            print(f"[SETTINGS] Error guardando vista: {e}")
            
        # Re-crear header adaptativo
        new_header = create_header(
            self.page,
            self.palette_dropdown,
            self.save_counter,
            self.save_btn,
            self.load_btn,
            self.theme.get,
            web_port=FLASK_PORT,
            set_timer=self.set_timer,
            on_mode_change=self.apply_view_mode,
            view_mode=mode
        )
        
        # Actualizar en el árbol de la página. Siempre reemplazamos el control
        # que actúa como header en la columna principal para asegurar que el
        # header inicial se muestre correctamente.
        try:
            self.page.controls[0].content.controls[0] = new_header
        except Exception:
            # Fallback: si por alguna razón la estructura no existe todavía,
            # asignamos al contenedor local para que ThemeChangeHandler pueda
            # acceder a él más tarde.
            self.header_container = new_header
        else:
            self.header_container = new_header
            
        # Ajustar dimensiones de ventana
        if mode == "fullscreen":
            self.page.window.maximized = True
            self.page.window.resizable = True
        elif mode == "side_panel":
            self.page.window.maximized = False
            self.page.window.width = 380
            self.page.window.height = 800
            self.page.window.resizable = True
        elif mode == "compact":
            self.page.window.maximized = False
            self.page.window.width = 420
            self.page.window.height = 360
            self.page.window.resizable = True

        # Reconstruir contenido principal
        if mode == "fullscreen":
            # Restaurar padding original para listbox_container
            self.listbox_container.padding = ft.padding.Padding(left=18, right=18, top=18, bottom=18)
            main_row = ft.Row(
                spacing=18,
                expand=True,
                controls=[
                    ft.Column(expand=True, spacing=0, controls=[self.listbox_container]),
                    ft.Container(width=250, content=self.control_panel.container)
                ]
            )
            self.main_layout_container.content = ft.Container(
                expand=True,
                padding=ft.padding.Padding(left=18, right=18, top=10, bottom=18),
                content=main_row
            )
        elif mode == "side_panel":
            # Reducir padding en listbox_container para pantallas estrechas
            self.listbox_container.padding = ft.padding.Padding(left=10, right=10, top=10, bottom=10)
            main_col = ft.Column(
                spacing=10,
                expand=True,
                controls=[
                    self.listbox_container,
                    self.control_panel.get_compact_container()
                ]
            )
            self.main_layout_container.content = ft.Container(
                expand=True,
                    padding=ft.padding.Padding(left=10, right=10, top=5, bottom=10),
                content=main_col
            )
        elif mode == "compact":
            self.main_layout_container.content = ft.Container(
                expand=True,
                padding=ft.padding.Padding(left=10, right=10, top=10, bottom=10),
                content=self._build_compact_view()
            )
            
        if not initial:
            self.page.update()

    def _build_compact_view(self) -> ft.Column:
        """Construye la vista compacta para monitores de escenario"""
        self.current_song_title = ft.Text(
            self._get_current_song_title(),
            size=20,
            weight=ft.FontWeight.BOLD,
            color=self.theme.get("accent"),
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
            text_align=ft.TextAlign.CENTER,
        )
        self.next_song_title = ft.Text(
            self._get_next_song_title(),
            size=13,
            weight=ft.FontWeight.W_500,
            color=self.theme.get("text_secondary"),
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
            text_align=ft.TextAlign.CENTER,
        )
        
        song_display = ft.Container(
            content=ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "PISTA ACTUAL", 
                        size=9, 
                        weight=ft.FontWeight.BOLD, 
                        color=self.theme.get("text_secondary")
                    ),
                    self.current_song_title,
                    ft.Container(height=2),
                    self.next_song_title,
                ],
            ),
            padding=ft.padding.Padding(left=12, right=12, top=10, bottom=10),
            bgcolor=self.theme.get("bg_card") + "40",
            border_radius=10,
            alignment=ft.Alignment.CENTER,
        )
        
        compact_main_column = ft.Column(
            spacing=8,
            controls=[
                song_display,
                self.control_panel.get_compact_container(),
            ]
        )
        
        return compact_main_column

    def _get_current_song_title(self) -> str:
        track = state.get_current_track()
        if track:
            return f"{state.current_index + 1:02d}. {track.title}"
        return "Sin pista seleccionada"
        
    def _get_next_song_title(self) -> str:
        next_idx = state.current_index + 1
        if 0 <= next_idx < len(state.tracks):
            return f"SIGUIENTE: {state.tracks[next_idx].title}"
        return "SIGUIENTE: Fin del setlist"

    def update_compact_view(self):
        """Actualiza los textos de pista actual/siguiente en tiempo real"""
        try:
            if hasattr(self, 'current_song_title') and self.current_song_title:
                self.current_song_title.value = self._get_current_song_title()
            if hasattr(self, 'next_song_title') and self.next_song_title:
                self.next_song_title.value = self._get_next_song_title()
            
            if hasattr(self.control_panel, 'compact_status_text') and self.control_panel.compact_status_text:
                self.control_panel.compact_status_text.value = StatusBar.instance.text.value
                self.control_panel.compact_status_text.color = StatusBar.instance.text.color
                
            self.page.update()
        except Exception:
            pass


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main(page: ft.Page):
    """Función principal - Thread-safe con async"""
    app = AppBuilder(page)
    app.build()
