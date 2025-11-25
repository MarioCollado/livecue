# ui/about_dialog.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0

import flet as ft
from version_info import APP_VERSION
from core.i18n import i18n

def show_about_dialog(page: ft.Page, theme_get_color):
    
    def close_dialog(e):
        dialog.open = False
        page.update()
        
    # --- Componentes Reutilizables ---
    
    def _section_card(title, content_controls):
        return ft.Container(
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(title, size=11, weight=ft.FontWeight.BOLD, color=theme_get_color("accent")),
                    ft.Column(spacing=4, controls=content_controls)
                ]
            ),
            padding=12,
            border_radius=8,
            bgcolor=theme_get_color("bg_card"),
            border=ft.border.all(1, theme_get_color("border"))
        )
        
    def _info_row(label, value, is_link=False, url=None):
        content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(label, size=12, color=theme_get_color("text_secondary")),
                ft.Text(
                    value, 
                    size=12, 
                    color=theme_get_color("text_primary") if not is_link else theme_get_color("accent"),
                    weight=ft.FontWeight.W_500 if not is_link else ft.FontWeight.BOLD,
                    selectable=True
                )
            ]
        )
        
        if is_link and url:
            return ft.Container(
                content=content,
                on_click=lambda e: page.launch_url(url),
                ink=True,
                border_radius=4,
                padding=ft.padding.symmetric(horizontal=4, vertical=2)
            )
        return content

    # --- Contenido ---

    header = ft.Container(
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.AUDIOTRACK_ROUNDED, size=40, color=ft.Colors.WHITE),
                    width=64, height=64, border_radius=32,
                    bgcolor=theme_get_color("accent"),
                    shadow=ft.BoxShadow(blur_radius=10, color=theme_get_color("accent") + "40"),
                    alignment=ft.alignment.center
                ),
                ft.Text(
                    i18n.get("app_name"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=theme_get_color("text_primary"),
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    i18n.get("about_subtitle"),
                    size=13,
                    color=theme_get_color("text_secondary"),
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(
                    content=ft.Text(
                        f"v{APP_VERSION}",
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=theme_get_color("button_text"),
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    margin=ft.margin.only(top=4),
                    alignment=ft.alignment.center
                )
            ]
        ),
        padding=ft.padding.only(bottom=16)
    )

    dev_section = _section_card(
        i18n.get("about_dev_title"),
        [
            _info_row(i18n.get("about_author"), "Mario Collado Rodríguez"),
            _info_row(i18n.get("about_copyright"), "© 2025"),
            _info_row("GitHub", "github.com/MarioCollado/LiveCue", True, "https://github.com/MarioCollado/LiveCue"),
            _info_row("Email", "mcolladorguez@gmail.com", True, "mailto:mcolladorguez@gmail.com")
        ]
    )

    license_section = _section_card(
        i18n.get("about_license_title"),
        [
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.GAVEL_ROUNDED, size=14, color=theme_get_color("text_secondary")),
                    ft.Text("CC BY-NC-SA 4.0", size=12, weight=ft.FontWeight.BOLD, color=theme_get_color("text_primary"))
                ]
            ),
            ft.Divider(height=12, color=theme_get_color("border")),
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=14, color=ft.Colors.GREEN_400),
                    ft.Text(i18n.get("about_license_personal"), size=11, color=theme_get_color("text_secondary"))
                ]
            ),
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.CANCEL_ROUNDED, size=14, color=ft.Colors.RED_400),
                    ft.Text(i18n.get("about_license_commercial"), size=11, color=theme_get_color("text_secondary"))
                ]
            )
        ]
    )

    disclaimer = ft.Container(
        content=ft.Text(
            i18n.get("about_disclaimer"),
            size=10,
            color=theme_get_color("text_secondary"),
            text_align=ft.TextAlign.CENTER,
            italic=True
        ),
        padding=ft.padding.symmetric(vertical=8)
    )

    # --- Diálogo ---
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Container(width=0, height=0),
        title_padding=0,
        content_padding=24,
        bgcolor=theme_get_color("bg_secondary"),
        shape=ft.RoundedRectangleBorder(radius=16),
        content=ft.Container(
            width=360,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.START, 
                tight=True,
                spacing=16,
                controls=[
                    header,
                    dev_section,
                    license_section,
                    disclaimer
                ]
            )
        ),
        actions=[
            ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        ft.TextButton(
                             i18n.get("about_view_license"),
                            style=ft.ButtonStyle(color=theme_get_color("text_secondary")),
                            on_click=lambda e: page.launch_url("https://creativecommons.org/licenses/by-nc-sa/4.0/")
                        ),
                        ft.FilledButton(
                            i18n.get("close"),
                            style=ft.ButtonStyle(
                                bgcolor=theme_get_color("accent"),
                                color=theme_get_color("button_text"),
                                shape=ft.RoundedRectangleBorder(radius=8)
                            ),
                            on_click=close_dialog
                        )
                    ]
                ),
                padding=ft.padding.only(bottom=8)
            )
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER
    )
    
    page.open(dialog)