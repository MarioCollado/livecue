# ui/header_component.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
from version_info import APP_VERSION
from ui.themes import ThemeManager
from ui.about_dialog import show_about_dialog
from ui.qr_dialog import show_qr_dialog
import time
import threading
from core.constants import FLASK_PORT
from core.i18n import i18n
from core.utils import icon
from core.network import get_local_ip, get_tailscale_ip

class SetTimer:
    """Temporizador para medir duración del directo"""
    
    def __init__(self):
        self.start_time = None
        self.elapsed = 0
        self.is_running = False
        self._timer_text = None
        self._update_thread = None
        self._stop_thread = False
        self._page = None
        
    def set_text_ref(self, text_ref):
        """Asigna la referencia al Text widget"""
        self._timer_text = text_ref
        # try to capture page reference if the Text control has it
        try:
            self._page = getattr(text_ref, 'page', None)
        except Exception:
            self._page = None
        
    def start(self):
        """Inicia el temporizador"""
        if not self.is_running:
            self.start_time = time.time() - self.elapsed
            self.is_running = True
            self._stop_thread = False
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()
            
    def pause(self):
        """Pausa el temporizador"""
        if self.is_running:
            self.elapsed = time.time() - self.start_time
            self.is_running = False
            self._stop_thread = True
            
    def reset(self):
        """Reinicia el temporizador"""
        self.pause()
        self.elapsed = 0
        if self._timer_text:
            self._timer_text.value = "00:00:00"
            try:
                if self._page:
                    self._page.update()
                else:
                    self._timer_text.update()
            except:
                pass
            
    def _update_loop(self):
        """Loop de actualización del display"""
        while not self._stop_thread and self.is_running:
            if self._timer_text:
                elapsed = time.time() - self.start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                self._timer_text.value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                try:
                    if self._page:
                        self._page.update()
                    else:
                        self._timer_text.update()
                except:
                    pass
            time.sleep(1)
            
    def get_elapsed_formatted(self):
        """Retorna el tiempo transcurrido formateado"""
        if self.is_running:
            elapsed = time.time() - self.start_time
        else:
            elapsed = self.elapsed
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def create_header(
    page: ft.Page, palette_dropdown: ft.Dropdown, save_counter: ft.Text,
    save_btn: ft.IconButton, load_btn: ft.IconButton, get_color,
    web_port: int = FLASK_PORT, set_timer: SetTimer = None,
    on_mode_change = None, view_mode: str = "fullscreen"
) -> ft.Container:
    """
    Header con logo y selector a la izquierda, metrónomo centrado y controles a la derecha.
    Soporta modo lateral y compacto adaptativo.
    """
    local_ip = get_local_ip()
    tailscale_ip = get_tailscale_ip()

    if set_timer is None:
        set_timer = SetTimer()

    def on_palette_change(palette_name):
        """Callback para cambiar paleta desde PopupMenu"""
        palette_dropdown.value = palette_name
        palette_dropdown.on_change(None)  # Trigger el cambio

    def _network_chip(label: str, value: str, color_key: str, tooltip: str, on_click):
        return ft.Container(
            content=ft.Row(
                spacing=4,
                controls=[
                    icon("network", size=14, color=get_color(color_key)),
                    ft.Text(f"{label}:", size=9, weight=ft.FontWeight.BOLD, color=get_color(color_key)),
                    ft.Text(f"{value}", size=11, weight=ft.FontWeight.W_600, color=get_color("text_primary")),
                    ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, size=14, color=get_color(color_key)),
                ],
            ),
            padding=ft.padding.Padding(left=8, right=8, top=3, bottom=3),
            border_radius=10,
            bgcolor=get_color("bg_card") + "20",
            border=ft.border.Border.all(1, get_color(color_key) + "30"),
            tooltip=tooltip,
            ink=True,
            on_click=on_click,
        )

    # Display y controles del temporizador
    timer_display = ft.Text(
        "00:00:00",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=get_color("accent"),
        font_family="DS-Digital",
        width=120,
        text_align=ft.TextAlign.CENTER,
    )
    set_timer.set_text_ref(timer_display)
    # Ensure SetTimer has access to the page for safe updates from threads
    try:
        set_timer._page = page
    except Exception:
        pass

    def on_timer_start(e): set_timer.start()
    def on_timer_pause(e): set_timer.pause()
    def on_timer_reset(e): set_timer.reset()

    # Bloque unificado del temporizador (display + botones)
    timer_widget = ft.Container(
        content=ft.Row(
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                timer_display,
                ft.IconButton(
                    icon=ft.Icons.PLAY_ARROW_ROUNDED,
                    icon_size=14,
                    icon_color=get_color("button_play"),
                    tooltip=i18n.get("start"),
                    on_click=on_timer_start,
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        padding=ft.padding.Padding(left=4, right=4, top=4, bottom=4),
                        bgcolor=get_color("bg_card") + "AA",
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.PAUSE_ROUNDED,
                    icon_size=14,
                    icon_color=get_color("button_stop"),
                    tooltip=i18n.get("pause"),
                    on_click=on_timer_pause,
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        padding=ft.padding.Padding(left=4, right=4, top=4, bottom=4),
                        bgcolor=get_color("bg_card") + "AA",
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.RESTART_ALT_ROUNDED,
                    icon_size=14,
                    icon_color=get_color("text_secondary"),
                    tooltip=i18n.get("reset"),
                    on_click=on_timer_reset,
                    style=ft.ButtonStyle(
                        shape=ft.CircleBorder(),
                        padding=ft.padding.Padding(left=4, right=4, top=4, bottom=4),
                        bgcolor=get_color("bg_card") + "AA",
                    ),
                ),
            ],
        ),
        padding=ft.padding.Padding(left=12, right=12, top=6, bottom=6),
        border_radius=12,
        bgcolor="#0E0E0E",
    )

    # Selector de paleta pequeño y elegante - usando SVG
    palette_selector = ft.PopupMenuButton(
        content=icon("color_palette2", size=20, color=get_color("accent")),
        tooltip=i18n.get("header_theme_tooltip", palette_dropdown.value),
        items=[
            ft.PopupMenuItem(
                content=ft.Text(name),
                on_click=lambda e, n=name: on_palette_change(n)
            )
            for name in ThemeManager.list_themes()
        ],
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=ft.padding.Padding(left=8, right=8, top=8, bottom=8),
            bgcolor=get_color("bg_card") + "AA",
            overlay_color={
                ft.ControlState.HOVERED: get_color("accent") + "20",
            },
        ),
    )
    
    # Selector de modo de visualización
    current_mode_icon = ft.Icons.GRID_VIEW_ROUNDED
    if view_mode == "fullscreen":
        current_mode_icon = ft.Icons.FULLSCREEN_ROUNDED
    elif view_mode == "side_panel":
        current_mode_icon = ft.Icons.VIEW_SIDEBAR_ROUNDED
    elif view_mode == "compact":
        current_mode_icon = ft.Icons.PICTURE_IN_PICTURE_ALT_ROUNDED

    mode_selector = ft.PopupMenuButton(
        content=ft.Icon(current_mode_icon, size=20, color=get_color("accent")),
        tooltip=f"Modo de vista: {view_mode.replace('_', ' ').title()}",
        items=[
            ft.PopupMenuItem(
                content=ft.Text("🖥️ Pantalla Completa"),
                on_click=lambda e: on_mode_change("fullscreen") if on_mode_change else None
            ),
            ft.PopupMenuItem(
                content=ft.Text("📱 Panel Lateral"),
                on_click=lambda e: on_mode_change("side_panel") if on_mode_change else None
            ),
            ft.PopupMenuItem(
                content=ft.Text("🎛️ Ventana Compacta"),
                on_click=lambda e: on_mode_change("compact") if on_mode_change else None
            ),
        ],
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=ft.padding.Padding(left=8, right=8, top=8, bottom=8),
            bgcolor=get_color("bg_card") + "AA",
            overlay_color={
                ft.ControlState.HOVERED: get_color("accent") + "20",
            },
        ),
    )
    
    # Botón "Acerca de"
    about_btn = ft.IconButton(
        icon=ft.Icons.INFO_OUTLINE_ROUNDED,
        icon_size=18,
        icon_color=get_color("text_secondary"),
        tooltip=i18n.get("header_about_tooltip"),
        on_click=lambda e: show_about_dialog(page, get_color),
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=ft.padding.Padding(left=8, right=8, top=8, bottom=8),
            bgcolor=get_color("bg_card") + "AA",
            overlay_color={
                ft.ControlState.HOVERED: get_color("accent") + "20",
            },
        ),
    )

    # Grupo izquierdo: logo + paleta + selector de modo
    left_group = ft.Row(
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=icon("logo", size=24, color=ft.Colors.WHITE),
                width=38, height=38, border_radius=19,
                bgcolor=get_color("accent"),
                shadow=ft.BoxShadow(blur_radius=6, color=get_color("accent") + "40"),
            ),
            palette_selector,
            mode_selector,
        ]
    )

    # Controles de la derecha (guardar, red, versión) - usando SVG para folder
    is_compact_mode = view_mode in ["side_panel", "compact"]
    
    if is_compact_mode:
        # Menú popup compacto para conservar espacio
        more_actions_btn = ft.PopupMenuButton(
            content=ft.Icon(ft.Icons.MORE_VERT_ROUNDED, size=20, color=get_color("text_secondary")),
            tooltip="Más opciones",
            items=[
                ft.PopupMenuItem(
                    content=ft.Text("💾 Guardar Setlist"),
                    on_click=lambda e: (print("[UI] Popup -> Guardar Setlist"), save_btn.on_click(e))
                ),
                ft.PopupMenuItem(
                    content=ft.Text("📂 Cargar Setlist"),
                    on_click=lambda e: (print("[UI] Popup -> Cargar Setlist"), load_btn.on_click(e))
                ),
                ft.PopupMenuItem(
                    content=ft.Text("🌐 Código QR / Red WLAN"),
                    on_click=lambda e: (print("[UI] Popup -> QR WLAN"), (hasattr(page, 'window') and getattr(page.window,'bring_to_front', lambda: None)()), show_qr_dialog(page, get_color, local_ip, web_port))
                ),
            ],
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.Padding(left=8, right=8, top=8, bottom=8),
                bgcolor=get_color("bg_card") + "AA",
            ),
        )
        
        if tailscale_ip and tailscale_ip != local_ip:
            more_actions_btn.items.append(
                ft.PopupMenuItem(
                    content=ft.Text("🔒 Código QR / Red VPN"),
                    on_click=lambda e: show_qr_dialog(page, get_color, tailscale_ip, web_port)
                )
            )
            
        more_actions_btn.items.append(
            ft.PopupMenuItem(
                content=ft.Text("ℹ️ Acerca de LiveCue"),
                on_click=lambda e: (print("[UI] Popup -> About"), (hasattr(page, 'window') and getattr(page.window,'bring_to_front', lambda: None)()), show_about_dialog(page, get_color))
            )
        )
        
        right_controls = ft.Row(
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[more_actions_btn]
        )
    else:
        right_controls = ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    content=ft.Row(
                        spacing=3,
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.SAVE_ROUNDED, size=16, color=ft.Colors.WHITE),
                                width=28, height=28, border_radius=14,
                                bgcolor=get_color("accent"),
                                on_click=save_btn.on_click, ink=True,
                                tooltip=i18n.get("header_save_tooltip"),
                            ),
                            ft.Container(
                                content=ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=16, color=ft.Colors.WHITE),
                                width=28, height=28, border_radius=14,
                                bgcolor=get_color("accent"),
                                on_click=load_btn.on_click, ink=True,
                                tooltip=i18n.get("header_load_tooltip"),
                            ),
                        ],
                    ),
                    padding=2,
                    border_radius=10,
                    bgcolor=get_color("bg_card") + "30",
                )
            ]
        )
        
        # Indicadores de red
        network_indicators = [
            _network_chip(
                "WLAN",
                local_ip,
                "accent",
                i18n.get("header_qr_tooltip") + f"\nOSC: {local_ip}:11001",
                lambda e: show_qr_dialog(page, get_color, local_ip, web_port),
            )
        ]
        
        if tailscale_ip and tailscale_ip != local_ip:
            network_indicators.append(
                _network_chip(
                    "VPN",
                    tailscale_ip,
                    "button_play",
                    i18n.get("header_qr_tooltip") + f"\nVPN: {tailscale_ip}:{web_port}",
                    lambda e: show_qr_dialog(page, get_color, tailscale_ip, web_port),
                )
            )

        right_controls.controls.extend(network_indicators)
        
        right_controls.controls.extend([
                ft.Container(
                    content=ft.Text(
                        f"v{APP_VERSION}",
                        size=9,
                        weight=ft.FontWeight.W_600,
                        color=get_color("text_secondary"),
                    ),
                    padding=ft.padding.Padding(left=7, right=7, top=3, bottom=3),
                    border_radius=8,
                    bgcolor=get_color("bg_main") + "16",
                ),
                about_btn,
            ])

    # Estructura principal
    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                left_group,
                timer_widget, 
                right_controls,
            ],
        ),
        padding=ft.padding.Padding(left=(10 if is_compact_mode else 18), right=(10 if is_compact_mode else 18), top=8, bottom=8),
        height=72,
        bgcolor=get_color("bg_secondary"),
    )
