# ui/components.py
import flet as ft
import time
import threading

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
                controls=[self.circle_1, self.circle_2]
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
        return f"{self.tempo:.0f} BPM | {self.time_sig}/4"
    
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
            print(f"[ERROR] TempoDisplay.update: {e}")


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
        self.button = ft.ElevatedButton(
            icon=ft.Icons.MUSIC_OFF,
            text="CLICK OFF",
            on_click=on_click_fn,
            width=220,
            height=150
        )
        self._update_style()
    
    def set_state(self, is_on: bool):
        """Establece el estado - SÍNCRONO"""
        try:
            self.is_on = is_on
            self._update_style()
        except Exception as e:
            print(f"[ERROR] MetronomeButton.set_state: {e}")
    
    def _update_style(self):
        """Actualiza el estilo del botón"""
        try:
            self.button.icon = ft.Icons.MUSIC_NOTE if self.is_on else ft.Icons.MUSIC_OFF
            self.button.text = "CLICK ON" if self.is_on else "CLICK OFF"
            self.button.style = ft.ButtonStyle(
                color=self.get_color("button_text"),
                bgcolor=self.get_color("button_metro_on" if self.is_on else "button_metro")
            )
        except Exception as e:
            print(f"[ERROR] MetronomeButton._update_style: {e}")