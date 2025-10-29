# ui/components.py
"""Componentes UI reutilizables"""
import flet as ft
import time
import threading

class BeatIndicator:
    """Indicador visual de beat con pulso"""
    
    def __init__(self, get_color_fn):
        self.get_color = get_color_fn
        self.last_beat_time = 0
        
        self.circle_1 = ft.Container(
            width=30, height=30, border_radius=15,
            bgcolor=get_color_fn("text_secondary"), opacity=0.3
        )
        self.circle_2 = ft.Container(
            width=30, height=30, border_radius=15,
            bgcolor=get_color_fn("text_secondary"), opacity=0.3
        )
        
        self.container = ft.Container(
            width=100, height=60, border_radius=12,
            bgcolor=get_color_fn("bg_card"),
            alignment=ft.alignment.center,
            content=ft.Row(
                spacing=16,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[self.circle_1, self.circle_2]
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=12)
        )
    
    def pulse(self, beat: int, time_signature: int, page_update_fn):
        """Activa el pulso visual"""
        current_time = time.time()
        if current_time - self.last_beat_time < 0.05:
            return
        
        self.last_beat_time = current_time
        is_left = (beat % 2 == 1)
        
        active = self.circle_1 if is_left else self.circle_2
        inactive = self.circle_2 if is_left else self.circle_1
        
        active.bgcolor = self.get_color("progress_bar_bg")
        active.opacity = 1.0
        inactive.bgcolor = self.get_color("text_secondary")
        inactive.opacity = 0.3
        
        page_update_fn()
        
        # Fade out
        def fade():
            time.sleep(0.15)
            active.opacity = 0.3
            active.bgcolor = self.get_color("text_secondary")
            page_update_fn()
        
        threading.Thread(target=fade, daemon=True).start()


class TempoDisplay:
    """Display de tempo y time signature"""
    
    def __init__(self, get_color_fn, tempo=120.0, time_sig=4):
        self.get_color = get_color_fn
        self.tempo = tempo
        self.time_sig = time_sig
        
        self.text = ft.Text(
            self._format(),
            size=13,
            weight=ft.FontWeight.W_600,
            color=get_color_fn("text_primary")
        )
    
    def _format(self):
        return f"{self.tempo:.0f} BPM | {self.time_sig}/4"
    
    def update(self, tempo=None, time_sig=None, page_update_fn=None):
        """Actualiza los valores"""
        if tempo is not None:
            self.tempo = tempo
        if time_sig is not None:
            self.time_sig = time_sig
        
        self.text.value = self._format()
        if page_update_fn:
            page_update_fn()


class StatusBar:
    """Barra de estado"""
    
    def __init__(self, get_color_fn):
        self.get_color = get_color_fn
        self.text = ft.Text(
            "● Esperando...",
            size=12,
            weight=ft.FontWeight.W_500,
            color=get_color_fn("text_secondary")
        )
    
    def update(self, message: str, color=None, page_update_fn=None):
        """Actualiza el mensaje de estado"""
        self.text.value = f"● {message}"
        self.text.color = color or self.get_color("text_secondary")
        if page_update_fn:
            page_update_fn()


class ProgressBar:
    """Barra de progreso para tracks"""
    
    def __init__(self, get_color_fn, width=1220):
        self.max_width = width
        self.bar = ft.Container(
            width=0,
            height=6,
            bgcolor=get_color_fn("progress_bar_bg"),
            border_radius=3,
            animate=ft.Animation(100, ft.AnimationCurve.LINEAR)
        )
        
        self.container = ft.Container(
            content=ft.Container(
                width=width,
                height=6,
                border_radius=3,
                bgcolor=get_color_fn("bg_main"),
                content=ft.Stack(controls=[self.bar], width=width, height=6)
            ),
            visible=False,
            margin=ft.margin.only(top=6)
        )
    
    def update_progress(self, progress: float):
        """Actualiza el progreso (0-1)"""
        self.bar.width = int(progress * self.max_width)
        try:
            self.bar.update()
        except:
            pass
    
    def show(self):
        self.container.visible = True
    
    def hide(self):
        self.container.visible = False
        self.bar.width = 0


class MetronomeButton:
    """Botón de metrónomo con estado"""
    
    def __init__(self, get_color_fn, on_click_fn):
        self.get_color = get_color_fn
        self.is_on = False
        
        self.button = ft.ElevatedButton(
            icon=ft.Icons.MUSIC_OFF,
            text="CLICK OFF",
            on_click=on_click_fn,
            width=220,
            height=150
        )
        self._update_style()
    
    def toggle(self, page_update_fn=None):
        """Alterna el estado"""
        self.is_on = not self.is_on
        self._update_style()
        if page_update_fn:
            page_update_fn()
        return self.is_on
    
    def set_state(self, is_on: bool, page_update_fn=None):
        """Establece el estado"""
        self.is_on = is_on
        self._update_style()
        if page_update_fn:
            page_update_fn()
    
    def _update_style(self):
        self.button.icon = ft.Icons.MUSIC_NOTE if self.is_on else ft.Icons.MUSIC_OFF
        self.button.text = "CLICK ON" if self.is_on else "CLICK OFF"
        self.button.style = ft.ButtonStyle(
            color=self.get_color("button_text"),
            bgcolor=self.get_color("button_metro_on" if self.is_on else "button_metro")
        )