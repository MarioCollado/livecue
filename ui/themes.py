# Copyright (c) 2025 Mario Collado Rodríguez - MIT License

# ui/themes.py
"""Paletas de colores unificadas"""


SCHEMES = {
    
    "Deep Space": {
        "bg_main": "#181A1D",
        "bg_secondary": "#101214",
        "bg_card": "#1C1F26",

        "text_primary": "#EDEDED",
        "text_secondary": "#A8A8A8",

        "accent": "#3B91F4",
        "select_bg": "#0974F1",
        "select_fg": "#FFFFFF",

        "button_scan": "#5CA5F6",
        "button_play": "#1A7EF2",
        "button_stop": "#9FCCFA",

        "button_nav": "#3B91F4",
        "button_metro": "#A8A8A8",
        "button_metro_on": "#1A7EF2",

        "button_text": "#FFFFFF",
        "progress_bar_bg": "#06C000"
    },

    "Mono Dark": {
        "bg_main": "#0D0D0D",
        "bg_secondary": "#1A1A1A",
        "bg_card": "#2A2A2A",

        "text_primary": "#E8E8E8",
        "text_secondary": "#B0B0B0",

        "accent": "#D4AF37",
        "select_bg": "#3C3C3C",
        "select_fg": "#FFFFFF",

        "button_scan": "#666666",
        "button_play": "#D4AF37",
        "button_stop": "#FF5E5B",

        "button_nav": "#3C3C3C",
        "button_metro": "#4A4A4A",
        "button_metro_on": "#D4AF37",

        "button_text": "#FFFFFF",
        "progress_bar_bg": "#06C000"
    },

    "Crimson Dawn": {
        "bg_main": "#1A0E0E",
        "bg_secondary": "#120A0A",
        "bg_card": "#241010",

        "text_primary": "#F5EAEA",
        "text_secondary": "#CFAFAF",

        "accent": "#E34242",
        "select_bg": "#B22A2A",
        "select_fg": "#FFFFFF",

        "button_scan": "#7A2C2C",
        "button_play": "#E34242",
        "button_stop": "#F76B6B",

        "button_nav": "#993333",
        "button_metro": "#CC4545",
        "button_metro_on": "#E34242",

        "button_text": "#FFFFFF",
        "progress_bar_bg": "#06C000"
    },
    
    "Red Awakening": {
        "bg_main": "#120000",
        "bg_secondary": "#1C0000",
        "bg_card": "#260000",

        "text_primary": "#FFEAEA",
        "text_secondary": "#E6BFBF",

        "accent": "#FF3B3B",
        "select_bg": "#B31818",
        "select_fg": "#FFFFFF",

        "button_scan": "#661010",
        "button_play": "#FF3B3B",
        "button_stop": "#FF1A1A",

        "button_nav": "#8C1C1C",
        "button_metro": "#B81818",
        "button_metro_on": "#FF3B3B",

        "button_text": "#FFFFFF",
        "progress_bar_bg": "#06C000"
    },

    "Stage Night": {
        "bg_main": "#0A0A0A",
        "bg_secondary": "#151515",
        "bg_card": "#202020",

        "text_primary": "#F0EAD6",
        "text_secondary": "#C6BFAE",

        "accent": "#D4AF37",
        "select_bg": "#D4AF37",
        "select_fg": "#0A0A0A",

        "button_scan": "#FF6F61",
        "button_play": "#00E676",
        "button_stop": "#FF3B5F",

        "button_nav": "#D4AF37",
        "button_metro": "#3A86FF",
        "button_metro_on": "#00E676",

        "button_text": "#000000",
        "progress_bar_bg": "#06C000"
    },

    "Ocean Light": {
        "bg_main": "#F5FAFD",
        "bg_secondary": "#01497C",
        "bg_card": "#E9F4FA",

        "text_primary": "#012A4A",
        "text_secondary": "#27638D",

        "accent": "#0284C7",
        "select_bg": "#2C7DA0",
        "select_fg": "#FFFFFF",

        "button_scan": "#5EA7C8",
        "button_play": "#80C4E0",
        "button_stop": "#01497C",

        "button_nav": "#2A6F97",
        "button_metro": "#80C4E0",
        "button_metro_on": "#01497C",

        "button_text": "#FFFFFF",
        "progress_bar_bg": "#06C000"
    },
}


class ThemeManager:
    """Gestor de temas con acceso optimizado"""
    
    def __init__(self, initial_theme: str = "Mono Dark"):
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