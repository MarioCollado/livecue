# ui/header_component.py
import flet as ft
from version_info import APP_VERSION
from ui.themes import ThemeManager
import socket
import subprocess
import re
import time
import threading


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
    web_port: int = 5000, set_timer: SetTimer = None
) -> ft.Container:
    """
    Header con logo y selector a la izquierda, metrónomo centrado y controles a la derecha.
    """
    local_ip = get_local_ip()
    tailscale_ip = get_tailscale_ip()
    primary_ip = tailscale_ip if tailscale_ip else local_ip
    primary_icon = ft.Icons.VPN_LOCK if tailscale_ip else ft.Icons.WIFI
    primary_color = get_color("button_play") if tailscale_ip else get_color("accent")

    tooltip_lines = [f"Local WiFi: {local_ip}:{web_port}"]
    if tailscale_ip: tooltip_lines.append(f"Tailscale: {tailscale_ip}:{web_port}")
    tooltip_lines.append(f"OSC: {local_ip}:11001")
    tooltip_text = "\n".join(tooltip_lines)

    if set_timer is None:
        set_timer = SetTimer()

    def on_palette_change(palette_name):
        """Callback para cambiar paleta desde PopupMenu"""
        palette_dropdown.value = palette_name
        palette_dropdown.on_change(None)  # Trigger el cambio

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
                    tooltip="Iniciar",
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
                    tooltip="Pausar",
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
                    tooltip="Reiniciar",
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
        # shadow=ft.BoxShadow(blur_radius=8, color=get_color("button_text") + "15"),
    )

    # Selector de paleta pequeño y elegante
    palette_selector= ft.PopupMenuButton(
        icon=ft.Icons.PALETTE_ROUNDED,
        icon_size=18,
        icon_color=get_color("accent"),
        tooltip=f"Tema: {palette_dropdown.value}",
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
    # Grupo izquierdo: logo + paleta
    left_group = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Icon(ft.Icons.AUDIOTRACK_ROUNDED, size=22, color=ft.Colors.WHITE),
                width=38, height=38, border_radius=19,
                bgcolor=get_color("accent"),
                shadow=ft.BoxShadow(blur_radius=6, color=get_color("accent") + "40"),
            ),
            palette_selector,
        ]
    )

    # Controles de la derecha (guardar, red, versión)
    right_controls = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Row(
                    spacing=4,
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_SPECIAL_ROUNDED, size=14, color=get_color("accent")),
                        ft.Text(
                            save_counter.value,
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=get_color("text_primary"),
                        ),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=8,
                bgcolor=get_color("bg_card") + "40",
            ),
            ft.Container(
                content=ft.Row(
                    spacing=3,
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.SAVE_ROUNDED, size=16, color=ft.Colors.WHITE),
                            width=28, height=28, border_radius=14,
                            bgcolor=get_color("accent"),
                            on_click=save_btn.on_click, ink=True,
                            tooltip="Guardar Setlist",
                        ),
                        ft.Container(
                            content=ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=16, color=ft.Colors.WHITE),
                            width=28, height=28, border_radius=14,
                            bgcolor=get_color("accent"),
                            on_click=load_btn.on_click, ink=True,
                            tooltip="Cargar Setlist",
                        ),
                    ],
                ),
                padding=2,
                border_radius=10,
                bgcolor=get_color("bg_card") + "30",
            ),
            ft.Container(
                content=ft.Row(
                    spacing=5,
                    controls=[
                        ft.Icon(primary_icon, size=15, color=primary_color),
                        ft.Text(
                            f"{primary_ip}",
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=get_color("text_primary"),
                        ),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=10,
                bgcolor=get_color("bg_card") + "20",
                border=ft.border.all(1, primary_color + "20"),
                tooltip=tooltip_text,
            ),
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
        ],
    )

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
