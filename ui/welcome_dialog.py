# ui/welcome_dialog.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0

import flet as ft
from version_info import APP_VERSION
from core.i18n import i18n

def show_welcome_dialog(page: ft.Page, get_color, on_accept_callback=None):
    
    async def close_dialog(e=None):
        dlg.open = False
        page.update()
        if on_accept_callback and callable(on_accept_callback):
            if hasattr(page, 'run_task'):
                page.run_task(on_accept_callback)
            else:
                on_accept_callback()
    
    # --- Componentes Reutilizables ---
    
    def _info_card(icon, title, content_controls, color_key="accent"):
        return ft.Container(
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(icon, size=16, color=get_color(color_key)),
                            ft.Text(
                                title,
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=get_color("text_primary")
                            )
                        ]
                    ),
                    ft.Container(
                        content=ft.Column(spacing=4, controls=content_controls),
                        padding=ft.padding.only(left=24)
                    )
                ]
            ),
            padding=12,
            border_radius=8,
            bgcolor=get_color("bg_card"),
            border=ft.border.all(1, get_color("border"))
        )

    def _bullet_point(text):
        return ft.Row(
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=4, height=4, border_radius=2,
                    bgcolor=get_color("text_secondary"),
                    margin=ft.margin.only(top=7)
                ),
                ft.Text(
                    text,
                    size=12,
                    color=get_color("text_secondary"),
                    expand=True
                )
            ]
        )

    # --- Contenido ---

    header = ft.Container(
        content=ft.Column(
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(
                    ft.Icons.SCIENCE_ROUNDED,
                    size=48,
                    color=get_color("accent")
                ),
                ft.Text(
                    i18n.get("welcome_title"),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=get_color("text_primary"),
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(
                    content=ft.Text(
                        f"v{APP_VERSION}",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=get_color("button_text"),
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    alignment=ft.alignment.center
                )
            ]
        ),
        padding=ft.padding.only(bottom=10)
    )

    warning_card = ft.Container(
        content=ft.Row(
            spacing=12,
            controls=[
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.BLACK, size=24),
                ft.Column(
                    spacing=2,
                    expand=True,
                    controls=[
                        ft.Text(i18n.get("welcome_warning_title"), weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.BLACK),
                        ft.Text(
                            i18n.get("welcome_warning_text"),
                            size=11,
                            color=ft.Colors.BROWN_400
                        )
                    ]
                )
            ]
        ),
        padding=12,
        border_radius=8,
        bgcolor=ft.Colors.ORANGE_400 + "15",
        border=ft.border.all(1, ft.Colors.ORANGE_400 + "30")
    )

    features_list = [
        _bullet_point(i18n.get("welcome_feature_1")),
        _bullet_point(i18n.get("welcome_feature_2")),
        _bullet_point(i18n.get("welcome_feature_3")),
        _bullet_point(i18n.get("welcome_feature_4"))
    ]
    
    info_section = _info_card(
        ft.Icons.INFO_OUTLINE_ROUNDED,
        i18n.get("welcome_info_title"),
        features_list
    )

    license_section = ft.Container(
        alignment=ft.alignment.center,
        content=ft.Column(
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    i18n.get("welcome_license_title"),
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=get_color("text_secondary"),
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    i18n.get("welcome_license_text"),
                    size=10,
                    color=get_color("text_secondary"),
                    italic=True,
                    text_align=ft.TextAlign.CENTER
                )
            ]
        ),
        padding=ft.padding.only(top=10)
    )

    # --- Diálogo ---
    
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Container(width=0, height=0),
        title_padding=0,
        content_padding=24,
        bgcolor=get_color("bg_secondary"),
        shape=ft.RoundedRectangleBorder(radius=16),
        content=ft.Container(
            width=400,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,  # <--- FIX AQUÍ
                tight=True,
                spacing=16,
                controls=[
                    header,
                    warning_card,
                    info_section,
                    license_section
                ]
            )
        ),
        actions=[
            ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.FilledButton(
                            content=ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text(i18n.get("welcome_start_btn"), weight=ft.FontWeight.W_600),
                                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=16)
                                ]
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=get_color("accent"),
                                color=get_color("button_text"),
                                padding=ft.padding.symmetric(horizontal=32, vertical=18),
                                shape=ft.RoundedRectangleBorder(radius=12)
                            ),
                            on_click=lambda e: page.run_task(close_dialog, e)
                        )
                    ]
                ),
                padding=ft.padding.only(bottom=16)
            )
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER
    )
    
    page.open(dlg)
