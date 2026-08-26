# ui/about_dialog.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0

import flet as ft
from version_info import APP_VERSION
from core.i18n import i18n

def show_about_dialog(page: ft.Page, theme_get_color):
    
    def close_dialog(e):
        page.pop_dialog()
        
    # --- Componentes Reutilizables ---

    def _section_card(title, content_controls):
        return ft.Container(
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=theme_get_color("accent")),
                    ft.Column(spacing=3, controls=content_controls)
                ]
            ),
            padding=12,
            border_radius=10,
            bgcolor=theme_get_color("bg_card"),
            border=ft.border.Border.all(1, theme_get_color("border"))
        )
        
    def _info_row(label, value, is_link=False, url=None):
        content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(label, size=12, color=theme_get_color("text_secondary")),
                ft.Text(
                    value,
                    size=12,
                    color=theme_get_color("accent") if is_link else theme_get_color("text_primary"),
                    weight=ft.FontWeight.BOLD if is_link else ft.FontWeight.W_500,
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
                padding=ft.padding.Padding(left=4, right=4, top=2, bottom=2)
            )
        return content

    # --- HEADER ---
    header = ft.Container(
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.AUDIOTRACK_ROUNDED, size=38, color=ft.Colors.WHITE),
                    width=60, height=60, border_radius=30,
                    bgcolor=theme_get_color("accent"),
                    shadow=ft.BoxShadow(blur_radius=10, color=theme_get_color("accent") + "40"),
                    alignment=ft.Alignment.CENTER
                ),
                ft.Text(
                    i18n.get("app_name"),
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=theme_get_color("text_primary"),
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    i18n.get("about_subtitle"),
                    size=12,
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
                    padding=ft.padding.Padding(left=8, right=8, top=1, bottom=1),
                    margin=ft.margin.Margin(top=2),
                    alignment=ft.Alignment.CENTER
                )
            ]
        ),
        padding=ft.padding.Padding(left=0, right=0, top=0, bottom=12)
    )

    # --- DONACIÓN ---
    donation_section = ft.Container(
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text("☕", size=30),
                ft.Text(
                    i18n.get("about_donation_title"),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.AMBER_300
                ),
                ft.Text(
                    i18n.get("about_donation_text"),
                    size=11,
                    color=theme_get_color("text_secondary"),
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.ElevatedButton(
                            content=ft.Row(
                                spacing=6,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("💳", size=15),
                                    ft.Text("PayPal", size=12, weight=ft.FontWeight.BOLD)
                                ]
                            ),
                            style=ft.ButtonStyle(
                                bgcolor="#0070ba",
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.padding.Padding(left=14, right=14, top=8, bottom=8)
                            ),
                            on_click=lambda e: page.launch_url("https://paypal.me/mariocollado1")
                        ),
                        ft.ElevatedButton(
                            content=ft.Row(
                                spacing=6,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("☕", size=15),
                                    ft.Text("BuyMeACoffee", size=12, weight=ft.FontWeight.BOLD)
                                ]
                            ),
                            style=ft.ButtonStyle(
                                bgcolor="#ff5e5b",
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.padding.Padding(left=14, right=14, top=8, bottom=8)
                            ),
                            on_click=lambda e: page.launch_url("https://buymeacoffee.com/mcollado")
                        )
                    ]
                )
            ]
        ),
        padding=14,
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.AMBER_700),
        border=ft.border.Border.all(2, ft.Colors.with_opacity(0.25, ft.Colors.AMBER_300)),
        margin=ft.margin.Margin(bottom=10)
    )

    # --- DEV INFO ---
    dev_section = _section_card(
        i18n.get("about_dev_title"),
        [
            _info_row(i18n.get("about_author"), "Mario Collado Rodríguez"),
            _info_row(i18n.get("about_copyright"), "© 2026"),
            _info_row("GitHub", "github.com/MarioCollado/LiveCue", True, "https://github.com/MarioCollado/LiveCue"),
            _info_row("Email", "mcolladorguez@gmail.com", True, "mailto:mcolladorguez@gmail.com")
        ]
    )

    # --- LICENSE ---
    license_section = _section_card(
        i18n.get("about_license_title"),
        [
            ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.GAVEL_ROUNDED, size=13, color=theme_get_color("text_secondary")),
                    ft.Text("CC BY-NC-SA 4.0", size=12, weight=ft.FontWeight.BOLD, color=theme_get_color("text_primary"))
                ]
            ),
            ft.Divider(height=10, color=theme_get_color("border")),
            ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=13, color=ft.Colors.GREEN_400),
                    ft.Text(i18n.get("about_license_personal"), size=11, color=theme_get_color("text_secondary"))
                ]
            ),
            ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.CANCEL_ROUNDED, size=13, color=ft.Colors.RED_400),
                    ft.Text(i18n.get("about_license_commercial"), size=11, color=theme_get_color("text_secondary"))
                ]
            )
        ]
    )

    # --- DISCLAIMER ---
    disclaimer = ft.Container(
        content=ft.Text(
            i18n.get("about_disclaimer"),
            size=10,
            color=theme_get_color("text_secondary"),
            text_align=ft.TextAlign.CENTER,
            italic=True
        ),
        padding=ft.padding.Padding(left=0, right=0, top=6, bottom=6)
    )

    # --- DIALOG ---
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Container(width=0, height=0),
        title_padding=0,
        content_padding=22,
        bgcolor=theme_get_color("bg_secondary"),
        shape=ft.RoundedRectangleBorder(radius=14),
        content=ft.Container(
            width=360,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.START, 
                tight=True,
                spacing=14,
                controls=[
                    header,
                    donation_section,
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
                    spacing=10,
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
                                shape=ft.RoundedRectangleBorder(radius=6)
                            ),
                            on_click=close_dialog
                        )
                    ]
                ),
                padding=ft.padding.Padding(left=0, right=0, top=0, bottom=6)
            )
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER
    )
    
    print("[UI] Opening about dialog")
    try:
        if hasattr(page, 'window'):
            wnd = page.window
            if hasattr(wnd, 'bring_to_front'):
                try:
                    wnd.bring_to_front()
                except Exception:
                    pass
            try:
                wnd.minimized = False
            except Exception:
                pass
    except Exception:
        pass
    page.show_dialog(dialog)
