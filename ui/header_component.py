# ui/header_component.py
import flet as ft
from version_info import APP_VERSION
import socket
import subprocess
import re


def get_local_ip():
    """Obtiene la IP local de la máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_tailscale_ip():
    """Obtiene la IP de Tailscale si está disponible"""
    try:
        # Método 1: Intentar con el comando tailscale
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            # Validar que sea una IP de Tailscale (100.x.x.x)
            if ip.startswith("100."):
                return ip
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    
    try:
        # Método 2: Buscar en las interfaces de red
        import platform
        
        if platform.system() == "Windows":
            # En Windows, buscar interfaces Tailscale
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Buscar sección de Tailscale y extraer IPv4
                lines = result.stdout.split('\n')
                in_tailscale = False
                for line in lines:
                    if "Tailscale" in line or "tailscale" in line:
                        in_tailscale = True
                    elif in_tailscale and "IPv4" in line:
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if match:
                            ip = match.group(1)
                            if ip.startswith("100."):
                                return ip
                    elif in_tailscale and line.strip() == "":
                        in_tailscale = False
        else:
            # Linux/Mac: Buscar interfaz tailscale0
            result = subprocess.run(
                ["ip", "-4", "addr", "show", "tailscale0"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
    except Exception:
        pass
    
    return None


def create_header(page: ft.Page, palette_dropdown: ft.Dropdown, save_counter: ft.Text,
                  save_btn: ft.IconButton, load_btn: ft.IconButton, get_color, 
                  web_port: int = 5000) -> ft.Container:
    """
    Crea el header con información de red (Local + Tailscale).
    
    Args:
        page: Referencia a la página de Flet
        palette_dropdown: Dropdown para selección de paleta
        save_counter: Texto que muestra el contador de setlists
        save_btn: Botón de guardar
        load_btn: Botón de cargar
        get_color: Función para obtener colores del tema actual
        web_port: Puerto del servidor web (default 5000)
        
    Returns:
        Container con el header completo
    """
    
    local_ip = get_local_ip()
    tailscale_ip = get_tailscale_ip()
    
    # Determinar qué mostrar en el header principal
    if tailscale_ip:
        primary_ip = tailscale_ip
        primary_icon = ft.Icons.VPN_LOCK
        primary_color = get_color("button_play")
    else:
        primary_ip = local_ip
        primary_icon = ft.Icons.WIFI
        primary_color = get_color("accent")
    
    # Crear tooltip text
    tooltip_lines = [f"Local WiFi: {local_ip}:{web_port}"]
    if tailscale_ip:
        tooltip_lines.append(f"Tailscale: {tailscale_ip}:{web_port}")
    tooltip_lines.append(f"OSC: {local_ip}:11001")
    tooltip_text = "\n".join(tooltip_lines)
    
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
                
                # Centro: Selector de paleta + Network Info
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        # Selector de paleta
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
                        
                        # Network Info con Tooltip
                        ft.Container(
                            content=ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(
                                        primary_icon,
                                        size=18,
                                        color=primary_color,
                                    ),
                                    ft.Column(
                                        spacing=1,
                                        controls=[
                                            ft.Text(
                                                primary_ip,
                                                size=13,
                                                weight=ft.FontWeight.W_700,
                                                color=get_color("text_primary"),
                                            ),
                                            ft.Text(
                                                f"Web:{web_port} | OSC:11001",
                                                size=9,
                                                weight=ft.FontWeight.W_500,
                                                color=get_color("text_secondary"),
                                            ),
                                        ],
                                    ),
                                    # Indicador de Tailscale activo
                                    ft.Container(
                                        content=ft.Icon(
                                            ft.Icons.CHECK_CIRCLE,
                                            size=12,
                                            color=get_color("button_play"),
                                        ),
                                        visible=tailscale_ip is not None,
                                    ),
                                ],
                            ),
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            border_radius=12,
                            bgcolor=get_color("bg_card") + "80",
                            border=ft.border.all(1, primary_color + "30"),
                            tooltip=tooltip_text,  # CORREGIDO: tooltip como propiedad del Container
                        ),
                    ],
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
                                        tooltip="Guardar Setlist",
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
                                        tooltip="Cargar Setlist",
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