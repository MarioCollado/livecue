# ui/about_dialog.py
# Copyright (c) 2025 Mario Mario Collado Rodríguez - CC BY-NC-SA 4.0

"""Diálogo 'Acerca de' con información de copyright y licencia"""

import flet as ft
from version_info import APP_VERSION

def show_about_dialog(page: ft.Page, theme_get_color):
    """Muestra el diálogo 'Acerca de' con copyright e info de licencia"""
    
    def close_dialog(e):
        dialog.open = False
        page.update()
    
    dialog_content = ft.Column(
        width=500,
        tight=True,
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            # Logo y título
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.AUDIOTRACK_ROUNDED, 
                            size=40, 
                            color=ft.Colors.WHITE
                        ),
                        width=60, 
                        height=60, 
                        border_radius=30,
                        bgcolor=theme_get_color("accent"),
                    ),
                ]
            ),
            
            ft.Text(
                "LiveCue",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=theme_get_color("text_primary"),
                text_align=ft.TextAlign.CENTER,
            ),
            
            ft.Text(
                "Ableton Setlist Controller",
                size=14,
                color=theme_get_color("text_secondary"),
                text_align=ft.TextAlign.CENTER,
            ),
            
            ft.Text(
                f"Versión {APP_VERSION}",
                size=12,
                weight=ft.FontWeight.W_500,
                color=theme_get_color("accent"),
                text_align=ft.TextAlign.CENTER,
            ),
            
            ft.Divider(thickness=1, color=theme_get_color("accent") + "40"),
            
            # Copyright
            ft.Container(
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(
                            "© 2025 Mario Collado Rodríguez",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=theme_get_color("text_primary"),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Todos los derechos reservados",
                            size=11,
                            color=theme_get_color("text_secondary"),
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ]
                ),
                padding=ft.padding.symmetric(vertical=8),
                border_radius=8,
                bgcolor=theme_get_color("bg_card") + "40",
            ),
            
            # Licencia
            ft.Container(
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(
                                    ft.Icons.GAVEL_ROUNDED,
                                    size=18,
                                    color=theme_get_color("accent")
                                ),
                                ft.Text(
                                    "Licencia CC BY-NC-SA 4.0",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme_get_color("text_primary"),
                                ),
                            ]
                        ),
                        
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color="#4CAF50"),
                                        ft.Text(
                                            "Uso personal y educativo",
                                            size=11,
                                            color=theme_get_color("text_secondary"),
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color="#4CAF50"),
                                        ft.Text(
                                            "Modificaciones permitidas",
                                            size=11,
                                            color=theme_get_color("text_secondary"),
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.CANCEL, size=14, color="#F44336"),
                                        ft.Text(
                                            "Uso comercial PROHIBIDO sin permiso",
                                            size=11,
                                            color=theme_get_color("text_secondary"),
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                padding=ft.padding.all(12),
                border_radius=8,
                bgcolor=theme_get_color("bg_card"),
                border=ft.border.all(1, theme_get_color("accent") + "30"),
            ),
            
            # Contacto
            ft.Container(
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            "📧 Contacto",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=theme_get_color("text_primary"),
                        ),
                        ft.Text(
                            "Email: mcolladorguez@gmail.com",
                            size=11,
                            color=theme_get_color("text_secondary"),
                            selectable=True,
                        ),
                        ft.Text(
                            "GitHub: github.com/MarioCollado/LiveCue",
                            size=11,
                            color=theme_get_color("text_secondary"),
                            selectable=True,
                        ),
                        ft.Text(
                            "Licencias comerciales: mcolladorguez@gmail.com",
                            size=10,
                            italic=True,
                            color=theme_get_color("accent"),
                            selectable=True,
                        ),
                    ]
                ),
                padding=ft.padding.all(10),
                border_radius=8,
                bgcolor=theme_get_color("bg_secondary"),
            ),
            
            # Aviso legal
            ft.Container(
                content=ft.Text(
                    "Este software se proporciona 'TAL CUAL', sin garantías de ningún tipo. "
                    "El autor no es responsable de daños derivados del uso del software.",
                    size=9,
                    color=theme_get_color("text_secondary"),
                    text_align=ft.TextAlign.CENTER,
                    italic=True,
                ),
                padding=ft.padding.all(8),
            ),
        ]
    )
    
    dialog = ft.AlertDialog(
        modal=True,
        title=None,
        bgcolor=theme_get_color("bg_secondary"),
        content=dialog_content,
        actions=[
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.TextButton(
                        "Ver Licencia Completa",
                        on_click=lambda e: page.launch_url(
                            "https://creativecommons.org/licenses/by-nc-sa/4.0/"
                        ),
                        style=ft.ButtonStyle(
                            color=theme_get_color("accent"),
                        ),
                    ),
                    ft.FilledButton(
                        "Cerrar",
                        on_click=close_dialog,
                        style=ft.ButtonStyle(
                            bgcolor=theme_get_color("accent"),
                        ),
                    ),
                ]
            )
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    page.open(dialog)


# ============================================================================
# INTEGRACIÓN EN app_ui.py
# ============================================================================

# En app_ui.py, importa:
# from ui.about_dialog import show_about_dialog

# Y agrega un botón en el header o menú:
"""
about_btn = ft.IconButton(
    icon=ft.Icons.INFO_OUTLINE_ROUNDED,
    icon_size=18,
    icon_color=get_color("text_secondary"),
    tooltip="Acerca de LiveCue",
    on_click=lambda e: show_about_dialog(page, theme.get),
    style=ft.ButtonStyle(
        shape=ft.CircleBorder(),
        padding=ft.padding.all(8),
    ),
)
"""