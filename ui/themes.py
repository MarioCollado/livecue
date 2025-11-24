# ui/themes.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

"""Paletas de colores unificadas - Diseño Bento Moderno"""

SCHEMES = {
    
    "Deep Space": {
        # Backgrounds - Azul oscuro profundo con gradación sutil
        "bg_main": "#0A0E14",
        "bg_secondary": "#0D1117",
        "bg_card": "#161B22",
        
        # Text - Alto contraste para legibilidad
        "text_primary": "#F0F6FC",
        "text_secondary": "#8B949E",
        
        # Accent - Azul brillante para destacar
        "accent": "#58A6FF",
        "accent_hover": "#79C0FF",
        "select_bg": "#1F6FEB",
        "select_fg": "#FFFFFF",
        
        # Buttons - Paleta azul coherente
        "button_scan": "#388BFD",
        "button_play": "#3FB950",
        "button_stop": "#F85149",
        
        "button_nav": "#21262D",
        "button_nav_hover": "#30363D",
        "button_metro": "#484F58",
        "button_metro_hover": "#6E7681",
        "button_metro_on": "#58A6FF",
        
        "button_text": "#FFFFFF",
        "progress_bar_bg": "#3FB950",
        
        # Effects - Para sombras y overlays
        "shadow": "#00000040",
        "overlay": "#0D111780",
        "border": "#30363D"
    },

    "Mono Dark": {
        # Backgrounds - Escala de grises elegante
        "bg_main": "#0D0D0D",
        "bg_secondary": "#1A1A1A",
        "bg_card": "#242424",
        
        # Text - Contraste óptimo
        "text_primary": "#ECECEC",
        "text_secondary": "#A0A0A0",
        
        # Accent - Dorado refinado
        "accent": "#FFD700",
        "accent_hover": "#FFC700",
        "select_bg": "#3A3A3A",
        "select_fg": "#FFFFFF",
        
        # Buttons - Paleta monocromática con acentos
        "button_scan": "#5A5A5A",
        "button_play": "#FFD700",
        "button_stop": "#FF4757",
        
        "button_nav": "#2E2E2E",
        "button_nav_hover": "#3A3A3A",
        "button_metro": "#404040",
        "button_metro_hover": "#4D4D4D",
        "button_metro_on": "#FFD700",
        
        "button_text": "#FFFFFF",
        "progress_bar_bg": "#00D26A",
        
        # Effects
        "shadow": "#00000060",
        "overlay": "#00000050",
        "border": "#333333"
    },

    "Crimson Dawn": {
        # Backgrounds - Rojo oscuro sofisticado
        "bg_main": "#1C0A0A",
        "bg_secondary": "#260D0D",
        "bg_card": "#331414",
        
        # Text - Tonos cálidos
        "text_primary": "#FFE8E8",
        "text_secondary": "#D4A5A5",
        
        # Accent - Rojo vibrante
        "accent": "#FF4757",
        "accent_hover": "#FF6B7A",
        "select_bg": "#CC2936",
        "select_fg": "#FFFFFF",
        
        # Buttons - Paleta roja coherente
        "button_scan": "#8C2F39",
        "button_play": "#FF4757",
        "button_stop": "#FF6B7A",
        
        "button_nav": "#4D1F26",
        "button_nav_hover": "#662831",
        "button_metro": "#B23850",
        "button_metro_hover": "#CC4055",
        "button_metro_on": "#FF4757",
        
        "button_text": "#FFFFFF",
        "progress_bar_bg": "#00D26A",
        
        # Effects
        "shadow": "#00000050",
        "overlay": "#1C0A0A70",
        "border": "#4D1F26"
    },
    
    "Ocean Breeze": {
        # Backgrounds - Azul claro fresco
        "bg_main": "#F0F9FF",
        "bg_secondary": "#E0F2FE",
        "bg_card": "#FFFFFF",
        
        # Text - Azul oscuro para contraste
        "text_primary": "#0C4A6E",
        "text_secondary": "#0369A1",
        
        # Accent - Turquesa vibrante
        "accent": "#06B6D4",
        "accent_hover": "#22D3EE",
        "select_bg": "#0891B2",
        "select_fg": "#FFFFFF",
        
        # Buttons - Paleta azul clara
        "button_scan": "#67E8F9",
        "button_play": "#10B981",
        "button_stop": "#EF4444",
        
        "button_nav": "#BAE6FD",
        "button_nav_hover": "#7DD3FC",
        "button_metro": "#A5F3FC",
        "button_metro_hover": "#67E8F9",
        "button_metro_on": "#06B6D4",
        
        "button_text": "#0C4A6E",
        "progress_bar_bg": "#10B981",
        
        # Effects
        "shadow": "#0369A120",
        "overlay": "#E0F2FE80",
        "border": "#BAE6FD"
    },

    "Forest Zen": {
        # Backgrounds - Verde natural
        "bg_main": "#0F1E13",
        "bg_secondary": "#1A2E1F",
        "bg_card": "#243B2A",
        
        # Text - Tonos tierra claros
        "text_primary": "#E8F5E9",
        "text_secondary": "#A5D6A7",
        
        # Accent - Verde vibrante
        "accent": "#4CAF50",
        "accent_hover": "#66BB6A",
        "select_bg": "#388E3C",
        "select_fg": "#FFFFFF",
        
        # Buttons - Paleta verde natural
        "button_scan": "#558B2F",
        "button_play": "#4CAF50",
        "button_stop": "#FF5252",
        
        "button_nav": "#2E4A33",
        "button_nav_hover": "#3A5A3F",
        "button_metro": "#689F38",
        "button_metro_hover": "#7CB342",
        "button_metro_on": "#4CAF50",
        
        "button_text": "#FFFFFF",
        "progress_bar_bg": "#4CAF50",
        
        # Effects
        "shadow": "#00000050",
        "overlay": "#1A2E1F70",
        "border": "#2E4A33"
    },

    "Purple Haze": {
        # Backgrounds - Púrpura profundo
        "bg_main": "#1A0B2E",
        "bg_secondary": "#231340",
        "bg_card": "#2D1B4E",
        
        # Text - Lavanda claro
        "text_primary": "#F3E5FF",
        "text_secondary": "#C4A7E7",
        
        # Accent - Púrpura brillante
        "accent": "#A855F7",
        "accent_hover": "#C084FC",
        "select_bg": "#7C3AED",
        "select_fg": "#FFFFFF",
        
        # Buttons - Paleta púrpura
        "button_scan": "#6D28D9",
        "button_play": "#A855F7",
        "button_stop": "#F472B6",
        
        "button_nav": "#3B2667",
        "button_nav_hover": "#4C3575",
        "button_metro": "#8B5CF6",
        "button_metro_hover": "#A78BFA",
        "button_metro_on": "#A855F7",
        
        "button_text": "#FFFFFF",
        "progress_bar_bg": "#10B981",
        
        # Effects
        "shadow": "#00000060",
        "overlay": "#23134070",
        "border": "#3B2667"
    },
}


class ThemeManager:
    """Gestor de temas con acceso optimizado"""
    
    def __init__(self, initial_theme: str = "Deep Space"):
        self._current = initial_theme
        self._cache = SCHEMES[self._current].copy()
    
    def get(self, key: str) -> str:
        """Obtiene un color del tema actual"""
        return self._cache.get(key, "#FFFFFF")
    
    def set_theme(self, theme_name: str):
        """Cambia el tema actual"""
        if theme_name in SCHEMES:
            self._current = theme_name
            self._cache = SCHEMES[theme_name].copy()
    
    @property
    def current_name(self) -> str:
        return self._current
    
    @staticmethod
    def list_themes() -> list:
        """Lista todos los temas disponibles"""
        return list(SCHEMES.keys())

# Instancia global
theme = ThemeManager()