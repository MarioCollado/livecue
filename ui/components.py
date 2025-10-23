# ui/components.py
import flet as ft
from ui.themes import color_schemes
from core import state

def make_beat_indicators(get_color, time_signature_num, current_tempo, page_ref):
    beat_indicators = []
    for i in range(4):
        indicator = ft.Container(
            width=45,
            height=45,
            border_radius=22,
            bgcolor=get_color("bg_card"),
            alignment=ft.alignment.center,
            content=ft.Text(str(i+1), size=16, weight=ft.FontWeight.BOLD, color=get_color("text_secondary")),
        )
        beat_indicators.append(indicator)
    # tempo display también lo devuelve para que UI lo use
    tempo_display = ft.Text(f"{current_tempo} BPM", size=12, weight=ft.FontWeight.W_600, color=get_color("text_primary"))
    return beat_indicators, tempo_display
