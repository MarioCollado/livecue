# ui/header_component.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
from version_info import APP_VERSION
from ui.themes import ThemeManager
from ui.about_dialog import show_about_dialog
import socket
import subprocess
import re
import time
import threading
import asyncio
from core.state import state
from core.playback import playback
from core.logger import log_info, log_error
from core.i18n import i18n
from core.utils import icon


def get_local_ip():
    """Obtiene la IP local de la máquina (funciona sin Internet)"""
    
    def is_valid_ip(ip):
        """Filtra IPs inválidas"""
        if not ip or ip.startswith("127."):  # localhost
            return False
        if ip.startswith("169.254."):  # link-local (APIPA)
            return False
        if ip.startswith("172.17.") or ip.startswith("172.18."):  # Docker común
            return False
        return True
    
    def is_virtual_adapter(adapter_name):
        """Detecta si es un adaptador virtual"""
        if not adapter_name:
            return False
        adapter_lower = adapter_name.lower()
        virtual_keywords = [
            'virtualbox', 'vmware', 'vbox', 'vethernet',
            'hyper-v', 'docker', 'wsl', 'loopback'
        ]
        return any(keyword in adapter_lower for keyword in virtual_keywords)
    
    def prioritize_ip(ip):
        """Asigna prioridad a las IPs (menor = mejor)"""
        if ip.startswith("100."):  # Tailscale
            return 0
        if ip.startswith("192.168.") or ip.startswith("10."):  # Redes privadas comunes
            # Evitar rangos de VirtualBox (192.168.56.x, 192.168.99.x)
            parts = ip.split(".")
            if len(parts) >= 3:
                third_octet = int(parts[2])
                if third_octet in [56, 99]:  # VirtualBox común
                    return 10  # Baja prioridad
            return 1
        if ip.startswith("172."):  # Rango 172.16-31 (privado)
            parts = ip.split(".")
            if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
                return 1
        return 2  # Otras IPs públicas/válidas
    
    # Método 1: Intentar con netifaces (más confiable)
    try:
        import netifaces
        all_ips = []
        for interface in netifaces.interfaces():
            # Filtrar interfaces virtuales por nombre
            if is_virtual_adapter(interface):
                continue
            
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get('addr')
                    if is_valid_ip(ip):
                        all_ips.append(ip)
        
        if all_ips:
            # Ordenar por prioridad y retornar la mejor
            all_ips.sort(key=prioritize_ip)
            return all_ips[0]
    except ImportError:
        pass
    except Exception:
        pass
    
    # Método 2: Parsear comandos del sistema
    try:
        import platform
        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                all_ips = []
                current_adapter = None
                
                for line in result.stdout.split('\n'):
                    # Detectar nombre del adaptador
                    if "adaptador" in line.lower() or "adapter" in line.lower():
                        current_adapter = line.strip()
                    
                    # Buscar IPv4
                    elif "IPv4" in line or "Dirección IPv4" in line:
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if match:
                            ip = match.group(1)
                            # Filtrar si el adaptador es virtual
                            if current_adapter and is_virtual_adapter(current_adapter):
                                continue
                            if is_valid_ip(ip):
                                all_ips.append(ip)
                
                if all_ips:
                    all_ips.sort(key=prioritize_ip)
                    return all_ips[0]
        else:
            # Linux/Mac
            for cmd in [["ip", "-4", "addr"], ["ifconfig"]]:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        all_ips = []
                        for match in re.finditer(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout):
                            ip = match.group(1)
                            if is_valid_ip(ip):
                                all_ips.append(ip)
                        
                        if all_ips:
                            all_ips.sort(key=prioritize_ip)
                            return all_ips[0]
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
    except Exception:
        pass
    
    # Método 3: Fallback al método antiguo (requiere Internet)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if is_valid_ip(ip):
            return ip
    except Exception:
        pass
    
    # Fallback final
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
            ),
            ft.Container(
                content=ft.Row(
                    spacing=5,
                    controls=[
                        icon("network", size=15, color=primary_color),
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
            about_btn,
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