# ui/header_components.py
import flet as ft
from version_info import APP_VERSION


def create_header(page: ft.Page, palette_dropdown: ft.Dropdown, save_counter: ft.Text,
                  save_btn: ft.IconButton, load_btn: ft.IconButton, get_color) -> ft.Container:
    """
    Crea el header simplificado y moderno.
    
    Args:
        page: Referencia a la página de Flet
        palette_dropdown: Dropdown para selección de paleta
        save_counter: Texto que muestra el contador de setlists
        save_btn: Botón de guardar
        load_btn: Botón de cargar
        get_color: Función para obtener colores del tema actual
        
    Returns:
        Container con el header completo
    """
    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Logo + Título
                ft.Row(
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        # Logo simple
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.AUDIOTRACK_ROUNDED,
                                color=ft.Colors.WHITE,
                                size=24,
                            ),
                            width=46,
                            height=46,
                            border_radius=23,
                            bgcolor=get_color("accent"),
                        ),
                        # Título
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Ableton Setlist",
                                    size=20,
                                    weight=ft.FontWeight.W_700,
                                    color=get_color("text_primary"),
                                ),
                                ft.Text(
                                    "Live Performance Controller",
                                    size=11,
                                    weight=ft.FontWeight.W_500,
                                    color=get_color("text_secondary"),
                                    opacity=0.7,
                                ),
                            ],
                        ),
                    ],
                ),
                
                # Centro: Selector de paleta
                ft.Container(
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.PALETTE_ROUNDED,
                                size=18,
                                color=get_color("accent"),
                                opacity=0.8,
                            ),
                            ft.Container(
                                content=palette_dropdown,
                                width=180,
                            ),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                    border_radius=12,
                    bgcolor=get_color("bg_card") + "60",
                ),
                
                # Derecha: Controles
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        # Contador
                        ft.Container(
                            content=ft.Row(
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.FOLDER_SPECIAL_ROUNDED,
                                        size=16,
                                        color=get_color("accent")
                                    ),
                                    ft.Text(
                                        save_counter.value,
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                        color=get_color("text_primary"),
                                    ),
                                ],
                            ),
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=10,
                            bgcolor=get_color("bg_card") + "60",
                        ),
                        
                        # Botones
                        ft.Container(
                            content=ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(
                                            ft.Icons.SAVE_ROUNDED,
                                            size=18,
                                            color=ft.Colors.WHITE,
                                        ),
                                        width=38,
                                        height=38,
                                        border_radius=19,
                                        bgcolor=get_color("accent"),
                                        on_click=save_btn.on_click,
                                        ink=True,
                                    ),
                                    ft.Container(
                                        content=ft.Icon(
                                            ft.Icons.FOLDER_OPEN_ROUNDED,
                                            size=18,
                                            color=ft.Colors.WHITE,
                                        ),
                                        width=38,
                                        height=38,
                                        border_radius=19,
                                        bgcolor=get_color("accent"),
                                        on_click=load_btn.on_click,
                                        ink=True,
                                    ),
                                ],
                            ),
                            padding=4,
                            border_radius=12,
                            bgcolor=get_color("bg_card") + "40",
                        ),
                        
                        # Versión
                        ft.Container(
                            content=ft.Text(
                                f"v{APP_VERSION}",
                                size=10,
                                weight=ft.FontWeight.W_600,
                                color=get_color("text_secondary"),
                            ),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=10,
                            bgcolor=get_color("accent") + "20",
                        ),
                    ],
                ),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=12),
        height=75,
        bgcolor=get_color("bg_secondary"),
    )