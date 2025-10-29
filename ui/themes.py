# ui/themes.py
"""Paletas de colores unificadas - ÚNICA FUENTE DE VERDAD"""

SCHEMES = {
    "Mono Dark": {
        "bg_main": "#0D0D0D", "bg_secondary": "#232323", "bg_card": "#343434",
        "text_primary": "#E8E8E8", "text_secondary": "#B0B0B0",
        "accent": "#D4AF37", "select_bg": "#464646", "select_fg": "#FFFFFF",
        "button_scan": "#7A7A7A", "button_play": "#D4AF37", "button_stop": "#FF5E5B",
        "button_nav": "#464646", "button_metro": "#575757", "button_metro_on": "#D4AF37",
        "button_text": "#FFFFFF", "progress_bar_bg": "#06C000",
    },
    "Red Awakening": {
        "bg_main": "#140202", "bg_secondary": "#200404", "bg_card": "#2C0807",
        "text_primary": "#F5E9E7", "text_secondary": "#CBB3B0",
        "accent": "#B33939", "select_bg": "#732626", "select_fg": "#FFFFFF",
        "button_scan": "#662222", "button_play": "#B33939", "button_stop": "#661C1C",
        "button_nav": "#8C2E2E", "button_metro": "#992F2F", "button_metro_on": "#B33939",
        "button_text": "#FFFFFF", "progress_bar_bg": "#06C000",
    },
    "Stage Night": {
        "bg_main": "#0C0C0C", "bg_secondary": "#1A1A1A", "bg_card": "#232323",
        "text_primary": "#F0EAD6", "text_secondary": "#C6BFAE",
        "accent": "#D4AF37", "select_bg": "#D4AF37", "select_fg": "#0C0C0C",
        "button_scan": "#FF6F61", "button_play": "#00E676", "button_stop": "#FF3B5F",
        "button_nav": "#D4AF37", "button_metro": "#3A86FF", "button_metro_on": "#00E676",
        "button_text": "#000000", "progress_bar_bg": "#06C000",
    },
    "Ocean Light": {
        "bg_main": "#F4FBFF", "bg_secondary": "#01497C", "bg_card": "#E7F3F9",
        "text_primary": "#012A4A", "text_secondary": "#27638D",
        "accent": "#0275A8", "select_bg": "#2C7DA0", "select_fg": "#FFFFFF",
        "button_scan": "#5EA7C8", "button_play": "#80C4E0", "button_stop": "#01497C",
        "button_nav": "#2A6F97", "button_metro": "#80C4E0", "button_metro_on": "#01497C",
        "button_text": "#FFFFFF", "progress_bar_bg": "#06C000",
    },
    "Deep Space": {
        "bg_main": "#181A1D", "bg_secondary": "#101214", "bg_card": "#1C1F26",
        "text_primary": "#EDEDED", "text_secondary": "#A8A8A8",
        "accent": "#3B91F4", "select_bg": "#0974F1", "select_fg": "#FFFFFF",
        "button_scan": "#5CA5F6", "button_play": "#1A7EF2", "button_stop": "#9FCCFA",
        "button_nav": "#3B91F4", "button_metro": "#7EB8F8", "button_metro_on": "#1A7EF2",
        "button_text": "#FFFFFF", "progress_bar_bg": "#06C000"
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