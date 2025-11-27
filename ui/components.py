# ui/components.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import flet as ft
import time
import threading
from core.logger import log_error
from core.utils import icon

class BeatIndicator:
    def __init__(self, get_color_fn):
        self.get_color = get_color_fn
        self.last_beat_time = 0
        
        self.circle_1 = ft.Container(width=30, height=30, border_radius=15,
                                     bgcolor=get_color_fn("text_secondary"), opacity=0.3)
        self.circle_2 = ft.Container(width=30, height=30, border_radius=15,
                                     bgcolor=get_color_fn("text_secondary"), opacity=0.3)
        
        self.container = ft.Container(
            width=100, height=60, border_radius=12,
            bgcolor=get_color_fn("bg_card"),
            alignment=ft.alignment.center,
            content=ft.Row(
                spacing=16,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[self.circle_2, self.circle_1]
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=12)
        )
    
    def pulse(self, beat: int, time_signature: int, page_update_fn):
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

        # Actualizar UI de forma segura
        if page_update_fn and callable(page_update_fn):
            page_update_fn()
        
        def fade():
            time.sleep(0.15)
            try:
                active.opacity = 0.3
                active.bgcolor = self.get_color("text_secondary")
                if page_update_fn and callable(page_update_fn):
                    page_update_fn()
            except:
                pass
        
        threading.Thread(target=fade, daemon=True).start()


class TempoDisplay:
    def __init__(self, get_color_fn, tempo=120.0, time_sig=4):
        self.get_color = get_color_fn
        self.tempo = tempo
        self.time_sig = time_sig
        self.text = ft.Text(
            self._format(),
            size=13, weight=ft.FontWeight.W_600,
            color=get_color_fn("text_primary")
        )
    
    def _format(self):
        return f"{self.tempo:.0f} BPM"
        # return f"{self.tempo:.0f} BPM | {self.time_sig}/4"

    def update(self, tempo=None, time_sig=None, page_update_fn=None):
        try:
            if tempo is not None:
                self.tempo = tempo
            if time_sig is not None:
                self.time_sig = time_sig
            
            self.text.value = self._format()
            
            if page_update_fn and callable(page_update_fn):
                page_update_fn()
        except Exception as e:
            log_error(f"[ERROR] TempoDisplay.update: {e}", "UI", e)


class StatusBar:
    def __init__(self, get_color_fn):
        self.get_color = get_color_fn
        self.text = ft.Text("● Esperando...",
                            size=12, weight=ft.FontWeight.W_500,
                            color=get_color_fn("text_secondary"))


class MetronomeButton:
    def __init__(self, get_color_fn, on_click_fn):
        self.get_color = get_color_fn
        self.is_on = False
        
        # Texto centrado
        self.text = ft.Text(
            "CLICK OFF",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER
        )
        
        # Imagen de fondo (marca de agua)
        self.watermark_icon = icon("metronome3", size=80, color=ft.Colors.WHITE24)
        self.watermark = ft.Container(
            content=self.watermark_icon,
            alignment=ft.alignment.center
        )
        
        # Stack: imagen de fondo + texto encima
        self.button = ft.Container(
            content=ft.Stack(
                controls=[
                    self.watermark,  # Fondo
                    ft.Container(
                        content=self.text,
                        alignment=ft.alignment.center
                    )  # Texto encima
                ]
            ),
            width=220,
            height=150,
            border_radius=10,
            bgcolor=get_color_fn("button_metro"),
            on_click=on_click_fn,
            ink=True,
            alignment=ft.alignment.center
        )
    
    def set_state(self, is_on: bool):
        """Establece el estado - SÍNCRONO"""
        try:
            self.is_on = is_on
            self._update_style()
        except Exception as e:
            log_error(f"[ERROR] MetronomeButton.set_state: {e}", "UI", e)
    
    def _update_style(self):
        """Actualiza el estilo del botón"""
        try:
            # Actualizar texto
            self.text.value = "" if self.is_on else ""
            
            # Actualizar color de fondo
            self.button.bgcolor = self.get_color("button_metro_on" if self.is_on else "button_metro")
            
            # Actualizar marca de agua (más visible cuando está ON)
            icon_name = "metronome_off" if self.is_on else "metronome3"
            opacity = ft.Colors.WHITE38 if self.is_on else ft.Colors.WHITE24
            self.watermark.content = icon(icon_name, size=80, color=opacity)
            
        except Exception as e:
            log_error(f"[ERROR] MetronomeButton._update_style: {e}", "UI", e)