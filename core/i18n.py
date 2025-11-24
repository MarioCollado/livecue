# core/i18n.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0

import locale
import sys
from core.logger import log_info

TRANSLATIONS = {
    "es": {
        # General
        "app_name": "LiveCue",
        "version_beta": "Versión BETA",
        "version_dev": "Versión en Desarrollo",
        "accept": "Aceptar",
        "cancel": "Cancelar",
        "close": "Cerrar",
        "save": "Guardar",
        "load": "Cargar",
        "start": "Iniciar",
        "pause": "Pausar",
        "reset": "Reiniciar",
        "waiting": "Esperando...",
        "click_on": "CLICK ON",
        "click_off": "CLICK OFF",
        
        # Welcome Dialog
        "welcome_title": "LiveCue Beta",
        "welcome_warning_title": "Versión en Desarrollo",
        "welcome_warning_text": "Esta versión puede contener errores. Se recomienda guardar frecuentemente.",
        "welcome_feature_1": "Interfaz optimizada para directos",
        "welcome_feature_2": "Gestión avanzada de setlists",
        "welcome_feature_3": "Integración con Ableton Live (OSC)",
        "welcome_feature_4": "Reporta bugs en GitHub",
        "welcome_info_title": "Información Importante",
        "welcome_license_title": "Licencia CC BY-NC-SA 4.0",
        "welcome_license_text": "Uso personal gratuito. Prohibido uso comercial sin licencia.",
        "welcome_start_btn": "Comenzar",
        
        # About Dialog
        "about_subtitle": "Ableton Setlist Controller",
        "about_dev_title": "DESARROLLO",
        "about_author": "Autor",
        "about_copyright": "Copyright",
        "about_license_title": "LICENCIA",
        "about_license_personal": "Uso personal y educativo",
        "about_license_commercial": "Uso comercial sin permiso",
        "about_disclaimer": "Este software se proporciona 'tal cual', sin garantías explícitas o implícitas.",
        "about_view_license": "Ver Licencia",
        
        # Header
        "header_save_tooltip": "Guardar Setlist",
        "header_load_tooltip": "Cargar Setlist",
        "header_theme_tooltip": "Tema: {}",
        "header_about_tooltip": "Acerca de LiveCue",
        
        # License
        "license_trial_started": "Periodo de prueba iniciado",
        "license_activated": "Licencia activada",
        "license_invalid": "Licencia inválida",
        "license_trial_days_left": "Prueba: {} días restantes",
        "license_trial_expired": "Periodo de prueba expirado",
        "license_key_invalid": "Clave de licencia inválida",
    },
    "en": {
        # General
        "app_name": "LiveCue",
        "version_beta": "BETA Version",
        "version_dev": "Development Version",
        "accept": "Accept",
        "cancel": "Cancel",
        "close": "Close",
        "save": "Save",
        "load": "Load",
        "start": "Start",
        "pause": "Pause",
        "reset": "Reset",
        "waiting": "Waiting...",
        "click_on": "CLICK ON",
        "click_off": "CLICK OFF",
        
        # Welcome Dialog
        "welcome_title": "LiveCue Beta",
        "welcome_warning_title": "Development Version",
        "welcome_warning_text": "This version may contain bugs. Frequent saving is recommended.",
        "welcome_feature_1": "Optimized interface for live shows",
        "welcome_feature_2": "Advanced setlist management",
        "welcome_feature_3": "Ableton Live integration (OSC)",
        "welcome_feature_4": "Report bugs on GitHub",
        "welcome_info_title": "Important Information",
        "welcome_license_title": "CC BY-NC-SA 4.0 License",
        "welcome_license_text": "Free for personal use. Commercial use prohibited without license.",
        "welcome_start_btn": "Get Started",
        
        # About Dialog
        "about_subtitle": "Ableton Setlist Controller",
        "about_dev_title": "DEVELOPMENT",
        "about_author": "Author",
        "about_copyright": "Copyright",
        "about_license_title": "LICENSE",
        "about_license_personal": "Personal and educational use",
        "about_license_commercial": "Commercial use without permission",
        "about_disclaimer": "This software is provided 'as is', without express or implied warranties.",
        "about_view_license": "View License",
        
        # Header
        "header_save_tooltip": "Save Setlist",
        "header_load_tooltip": "Load Setlist",
        "header_theme_tooltip": "Theme: {}",
        "header_about_tooltip": "About LiveCue",
        
        # License
        "license_trial_started": "Trial period started",
        "license_activated": "License activated",
        "license_invalid": "Invalid license",
        "license_trial_days_left": "Trial: {} days left",
        "license_trial_expired": "Trial period expired",
        "license_key_invalid": "Invalid license key",
    }
}

class LanguageManager:
    _instance = None
    
    def __init__(self):
        self.lang = self._detect_language()
        log_info(f"Language detected: {self.lang}")
        
    def _detect_language(self) -> str:
        try:
            # Intentar obtener el idioma del sistema
            if sys.platform == 'win32':
                import ctypes
                windll = ctypes.windll.kernel32
                lang_id = windll.GetUserDefaultUILanguage()
                # 0x0C0A es español moderno, pero simplificamos checking el código primario
                # Español es 0x0a (10)
                primary_lang = lang_id & 0x3ff
                if primary_lang == 0x0a:
                    return 'es'
            
            # Fallback a locale estándar
            lang_code, _ = locale.getdefaultlocale()
            if lang_code and lang_code.lower().startswith('es'):
                return 'es'
                
        except Exception:
            pass
            
        return 'en' # Default a inglés
    
    def get(self, key: str, *args) -> str:
        """Obtiene un texto traducido"""
        text = TRANSLATIONS.get(self.lang, TRANSLATIONS['en']).get(key, key)
        if args:
            return text.format(*args)
        return text

def get_i18n():
    if not LanguageManager._instance:
        LanguageManager._instance = LanguageManager()
    return LanguageManager._instance

# Acceso rápido
i18n = get_i18n()
