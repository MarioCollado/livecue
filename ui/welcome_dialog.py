# ui/welcome_dialog.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
from version_info import APP_VERSION

def show_welcome_dialog(page: ft.Page, get_color, on_accept_callback=None):
    """
    Muestra un diálogo de bienvenida indicando que es una versión BETA/Prueba
    
    Args:
        page: Referencia a la página de Flet
        get_color: Función para obtener colores del tema
        on_accept_callback: Callback opcional a ejecutar cuando se acepta
    """
    
    async def close_dialog(e=None):
        dlg.open = False
        page.update()
        
        # Ejecutar callback si existe
        if on_accept_callback and callable(on_accept_callback):
            if hasattr(page, 'run_task'):
                page.run_task(on_accept_callback)
            else:
                on_accept_callback()
    
    # Contenido del diálogo
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Icon(
                    ft.Icons.SCIENCE_ROUNDED, 
                    size=32, 
                    color=get_color("accent")
                ),
                ft.Text(
                    "LiveCue - Versión BETA",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=get_color("text_primary")
                )
            ]
        ),
        bgcolor=get_color("bg_secondary"),
        content=ft.Container(
            width=500,
            content=ft.Column(
                spacing=16,
                tight=True,
                controls=[
                    # Banner de advertencia
                    ft.Container(
                        content=ft.Row(
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(
                                    ft.Icons.WARNING_AMBER_ROUNDED,
                                    size=24,
                                    color=ft.Colors.ORANGE_400
                                ),
                                ft.Text(
                                    "VERSIÓN DE PRUEBA",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ORANGE_400
                                )
                            ]
                        ),
                        padding=ft.padding.all(12),
                        border_radius=8,
                        bgcolor=ft.Colors.ORANGE_400 + "20",
                        border=ft.border.all(2, ft.Colors.ORANGE_400 + "40")
                    ),
                    
                    # Información de la versión
                    ft.Container(
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text(
                                    f"Versión: {APP_VERSION}",
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=get_color("text_primary")
                                ),
                                ft.Divider(height=1, color=get_color("accent") + "30"),
                            ]
                        )
                    ),
                    
                    # Mensaje principal
                    ft.Text(
                        "Estás utilizando una versión BETA de LiveCue. "
                        "Esta versión está en desarrollo activo y puede contener errores.",
                        size=13,
                        color=get_color("text_primary"),
                        text_align=ft.TextAlign.JUSTIFY
                    ),
                    
                    # Características BETA
                    ft.Container(
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text(
                                    "⚠️ Consideraciones:",
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=get_color("accent")
                                ),
                                ft.Text(
                                    "• Pueden aparecer errores inesperados",
                                    size=12,
                                    color=get_color("text_secondary")
                                ),
                                ft.Text(
                                    "• Algunas funciones están en desarrollo",
                                    size=12,
                                    color=get_color("text_secondary")
                                ),
                                ft.Text(
                                    "• Guarda tu trabajo frecuentemente",
                                    size=12,
                                    color=get_color("text_secondary")
                                ),
                                ft.Text(
                                    "• Reporta bugs en GitHub para mejorar la app",
                                    size=12,
                                    color=get_color("text_secondary")
                                ),
                            ]
                        ),
                        padding=ft.padding.all(12),
                        border_radius=8,
                        bgcolor=get_color("bg_card") + "60",
                    ),
                    
                    # Nota de licencia
                    ft.Container(
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text(
                                    "📜 Licencia: CC BY-NC-SA 4.0",
                                    size=11,
                                    weight=ft.FontWeight.W_500,
                                    color=get_color("text_secondary"),
                                    italic=True
                                ),
                                ft.Text(
                                    "NO se permite uso comercial sin autorización",
                                    size=10,
                                    color=get_color("text_secondary"),
                                    italic=True
                                ),
                            ]
                        ),
                        padding=ft.padding.symmetric(vertical=8),
                        border=ft.border.only(
                            top=ft.BorderSide(1, get_color("accent") + "20")
                        )
                    ),
                    
                    # Contacto
                    ft.Row(
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.EMAIL_OUTLINED,
                                size=14,
                                color=get_color("accent")
                            ),
                            ft.Text(
                                "mcolladorguez@gmail.com",
                                size=11,
                                color=get_color("accent"),
                                weight=ft.FontWeight.W_500
                            )
                        ]
                    )
                ]
            )
        ),
        actions=[
            ft.Container(
                content=ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.TextButton(
                            "Entendido",
                            on_click=lambda e: page.run_task(close_dialog, e),
                            style=ft.ButtonStyle(
                                color=get_color("text_secondary"),
                            )
                        ),
                        ft.FilledButton(
                            "✓ Aceptar y Continuar",
                            on_click=lambda e: page.run_task(close_dialog, e),
                            style=ft.ButtonStyle(
                                bgcolor=get_color("accent"),
                                color=ft.Colors.WHITE
                            )
                        )
                    ]
                ),
                padding=ft.padding.only(right=8, bottom=8)
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.open(dlg)