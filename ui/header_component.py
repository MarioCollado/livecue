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
        
    def set_text_ref(self, text_ref):
        """Asigna la referencia al Text widget"""
        self._timer_text = text_ref
        
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
    web_port: int = FLASK_PORT, set_timer: SetTimer = None
) -> ft.Container:
    """
    Header con logo y selector a la izquierda, metrónomo centrado y controles a la derecha.
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
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=10,
            bgcolor=get_color("bg_card") + "20",
            border=ft.border.all(1, get_color(color_key) + "30"),
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
                        padding=ft.padding.all(4),
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
                        padding=ft.padding.all(4),
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
                        padding=ft.padding.all(4),
                        bgcolor=get_color("bg_card") + "AA",
                    ),
                ),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=12,
        bgcolor="#0E0E0E",
    )

    # Selector de paleta pequeño y elegante - usando SVG
    palette_selector = ft.PopupMenuButton(
        content=icon("color_palette2", size=20, color=get_color("accent")),
        tooltip=i18n.get("header_theme_tooltip", palette_dropdown.value),
        items=[
            ft.PopupMenuItem(
                text=name,
                on_click=lambda e, n=name: on_palette_change(n)
            )
            for name in ThemeManager.list_themes()
        ],
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=ft.padding.all(8),
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
            padding=ft.padding.all(8),
            bgcolor=get_color("bg_card") + "AA",
            overlay_color={
                ft.ControlState.HOVERED: get_color("accent") + "20",
            },
        ),
    )

    # Grupo izquierdo: logo + paleta - usando SVG para el logo
    left_group = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=icon("logo", size=24, color=ft.Colors.WHITE),
                width=38, height=38, border_radius=19,
                bgcolor=get_color("accent"),
                shadow=ft.BoxShadow(blur_radius=6, color=get_color("accent") + "40"),
            ),
            palette_selector,
        ]
    )

    # Controles de la derecha (guardar, red, versión) - usando SVG para folder
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
                padding=ft.padding.symmetric(horizontal=7, vertical=3),
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
        padding=ft.padding.symmetric(horizontal=18, vertical=8),
        height=72,
        bgcolor=get_color("bg_secondary"),
    )
