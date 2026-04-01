# core/i18n.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0

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
        "about_donation_title": "¿Te gusta LiveCue?",
        "about_donation_text": "LiveCue es gratis y siempre lo será. Si te resulta útil, considera hacer una donación.",
        
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
        
        # Dialogs - Save/Load Setlist
        "dialog_save_title": "💾 Guardar Setlist",
        "dialog_save_name_label": "Nombre del setlist",
        "dialog_save_name_hint": "Ej: Concierto 2024",
        "dialog_save_warning_no_locators": "⚠️ Sin locators. Presiona SCAN primero",
        "dialog_save_error_empty_name": "⚠️ Debes ingresar un nombre",
        "dialog_save_error_failed": "✖ Error al guardar",
        "dialog_save_info": "Se guardarán {} locators y {} tracks",
        "dialog_save_success": "✓ '{}' guardado ({} locators, {} tracks, {} sections)",
        "dialog_load_title": "📂 Cargar Setlist",
        "dialog_load_dropdown_label": "Setlists guardados",
        "dialog_load_count": "📁 {} setlist(s) disponible(s)",
        "dialog_load_error": "✖ Error al cargar",
        "dialog_load_success": "✓ '{}' cargado ({} locators, {} tracks, {} sections)",
        "dialog_load_empty": "No hay setlists guardados",
        "dialog_load_empty_hint": "💡 Usa el botón 💾 para guardar tu primer setlist",
        "btn_save": "💾 Guardar",
        "btn_load": "📂 Cargar",
        
        # Control Panel - Status Messages
        "status_waiting": "● Esperando...",
        "status_metronome": "● Metrónomo: {}",
        "status_metronome_on": "ON",
        "status_metronome_off": "OFF",
        "status_no_track_selected": "● Sin track seleccionado",
        "status_play": "● ▶ Play: {}",
        "status_play_error": "● Error al reproducir",
        "status_stop": "● ▪ Stop",
        "status_next": "● ▶ Next: {}",
        "status_prev": "● ▶ Prev: {}",
        "status_last_track": "● ⊘ Último track",
        "status_first_track": "● ⊘ Primer track",
        "status_selected": "Seleccionado: {}",
        "status_reordered": "✓ Reordenado: {}",
        "status_scan_complete": "✓ Scan completo: {} tracks",
        "status_scan_error": "✗ Error en scan",
        "status_no_tracks": "⚠ Sin tracks detectados",
        "status_palette": "● Paleta: {}",
        
        # Control Panel - Scan Button
        "scan_btn": "SCAN",
        "scan_scanning": "Escaneando...",
        "scan_starting": "Iniciando escaneo...",
        "scan_connecting": "Conectando con Ableton Live...",
        "scan_detecting": "Detectando locators...",
        "scan_processing": "Procesando tracks...",
        "scan_sections": "Identificando secciones...",
        "scan_finalizing": "Finalizando...",
        "scan_updating_ui": "Actualizando interfaz...",
        "scan_found": "✓ {} tracks encontrados",
        "scan_error": "✗ Error en escaneo",
        "scan_error_critical": "✗ Error crítico",
        
        # Track List
        "track_sections_count": "{} sections",
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
        "about_donation_title": "Do you like LiveCue?",
        "about_donation_text": "LiveCue is free and always will be. If you find it useful, consider making a donation.",
        
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
        
        # Dialogs - Save/Load Setlist
        "dialog_save_title": "💾 Save Setlist",
        "dialog_save_name_label": "Setlist name",
        "dialog_save_name_hint": "Ex: Concert 2024",
        "dialog_save_warning_no_locators": "⚠️ No locators. Press SCAN first",
        "dialog_save_error_empty_name": "⚠️ You must enter a name",
        "dialog_save_error_failed": "✖ Error saving",
        "dialog_save_info": "{} locators and {} tracks will be saved",
        "dialog_save_success": "✓ '{}' saved ({} locators, {} tracks, {} sections)",
        "dialog_load_title": "📂 Load Setlist",
        "dialog_load_dropdown_label": "Saved setlists",
        "dialog_load_count": "📁 {} setlist(s) available",
        "dialog_load_error": "✖ Error loading",
        "dialog_load_success": "✓ '{}' loaded ({} locators, {} tracks, {} sections)",
        "dialog_load_empty": "No saved setlists",
        "dialog_load_empty_hint": "💡 Use the 💾 button to save your first setlist",
        "btn_save": "💾 Save",
        "btn_load": "📂 Load",
        
        # Control Panel - Status Messages
        "status_waiting": "● Waiting...",
        "status_metronome": "● Metronome: {}",
        "status_metronome_on": "ON",
        "status_metronome_off": "OFF",
        "status_no_track_selected": "● No track selected",
        "status_play": "● ▶ Play: {}",
        "status_play_error": "● Playback error",
        "status_stop": "● ▪ Stop",
        "status_next": "● ▶ Next: {}",
        "status_prev": "● ▶ Prev: {}",
        "status_last_track": "● ⊘ Last track",
        "status_first_track": "● ⊘ First track",
        "status_selected": "Selected: {}",
        "status_reordered": "✓ Reordered: {}",
        "status_scan_complete": "✓ Scan complete: {} tracks",
        "status_scan_error": "✗ Scan error",
        "status_no_tracks": "⚠ No tracks detected",
        "status_palette": "● Palette: {}",
        
        # Control Panel - Scan Button
        "scan_btn": "SCAN",
        "scan_scanning": "Scanning...",
        "scan_starting": "Starting scan...",
        "scan_connecting": "Connecting to Ableton Live...",
        "scan_detecting": "Detecting locators...",
        "scan_processing": "Processing tracks...",
        "scan_sections": "Identifying sections...",
        "scan_finalizing": "Finalizing...",
        "scan_updating_ui": "Updating interface...",
        "scan_found": "✓ {} tracks found",
        "scan_error": "✗ Scan error",
        "scan_error_critical": "✗ Critical error",
        
        # Track List
        "track_sections_count": "{} sections",
    },
    "fr": {
        # General
        "app_name": "LiveCue",
        "version_beta": "Version BÊTA",
        "version_dev": "Version de Développement",
        "accept": "Accepter",
        "cancel": "Annuler",
        "close": "Fermer",
        "save": "Enregistrer",
        "load": "Charger",
        "start": "Démarrer",
        "pause": "Pause",
        "reset": "Réinitialiser",
        "waiting": "En attente...",
        "click_on": "CLICK ON",
        "click_off": "CLICK OFF",
        
        # Welcome Dialog
        "welcome_title": "LiveCue Beta",
        "welcome_warning_title": "Version de Développement",
        "welcome_warning_text": "Cette version peut contenir des erreurs. Il est recommandé de sauvegarder fréquemment.",
        "welcome_feature_1": "Interface optimisée pour les concerts",
        "welcome_feature_2": "Gestion avancée des setlists",
        "welcome_feature_3": "Intégration avec Ableton Live (OSC)",
        "welcome_feature_4": "Signalez les bugs sur GitHub",
        "welcome_info_title": "Informations Importantes",
        "welcome_license_title": "Licence CC BY-NC-SA 4.0",
        "welcome_license_text": "Utilisation personnelle gratuite. Usage commercial interdit sans licence.",
        "welcome_start_btn": "Commencer",
        
        # About Dialog
        "about_subtitle": "Contrôleur de Setlist Ableton",
        "about_dev_title": "DÉVELOPPEMENT",
        "about_author": "Auteur",
        "about_copyright": "Copyright",
        "about_license_title": "LICENCE",
        "about_license_personal": "Usage personnel et éducatif",
        "about_license_commercial": "Usage commercial sans autorisation",
        "about_disclaimer": "Ce logiciel est fourni 'tel quel', sans garanties expresses ou implicites.",
        "about_view_license": "Voir la Licence",
        "about_donation_title": "Vous aimez LiveCue ?",
        "about_donation_text": "LiveCue est gratuit et le restera toujours. Si vous le trouvez utile, pensez à faire un don.",
        
        # Header
        "header_save_tooltip": "Enregistrer Setlist",
        "header_load_tooltip": "Charger Setlist",
        "header_theme_tooltip": "Thème : {}",
        "header_about_tooltip": "À propos de LiveCue",
        
        # License
        "license_trial_started": "Période d'essai démarrée",
        "license_activated": "Licence activée",
        "license_invalid": "Licence invalide",
        "license_trial_days_left": "Essai : {} jours restants",
        "license_trial_expired": "Période d'essai expirée",
        "license_key_invalid": "Clé de licence invalide",
        
        # Dialogs - Save/Load Setlist
        "dialog_save_title": "💾 Enregistrer Setlist",
        "dialog_save_name_label": "Nom du setlist",
        "dialog_save_name_hint": "Ex : Concert 2024",
        "dialog_save_warning_no_locators": "⚠️ Pas de locators. Appuyez d'abord sur SCAN",
        "dialog_save_error_empty_name": "⚠️ Vous devez entrer un nom",
        "dialog_save_error_failed": "✖ Erreur lors de l'enregistrement",
        "dialog_save_info": "{} locators et {} tracks seront enregistrés",
        "dialog_save_success": "✓ '{}' enregistré ({} locators, {} tracks, {} sections)",
        "dialog_load_title": "📂 Charger Setlist",
        "dialog_load_dropdown_label": "Setlists enregistrés",
        "dialog_load_count": "📁 {} setlist(s) disponible(s)",
        "dialog_load_error": "✖ Erreur lors du chargement",
        "dialog_load_success": "✓ '{}' chargé ({} locators, {} tracks, {} sections)",
        "dialog_load_empty": "Aucun setlist enregistré",
        "dialog_load_empty_hint": "💡 Utilisez le bouton 💾 pour enregistrer votre premier setlist",
        "btn_save": "💾 Enregistrer",
        "btn_load": "📂 Charger",
        
        # Control Panel - Status Messages
        "status_waiting": "● En attente...",
        "status_metronome": "● Métronome : {}",
        "status_metronome_on": "ON",
        "status_metronome_off": "OFF",
        "status_no_track_selected": "● Aucun track sélectionné",
        "status_play": "● ▶ Lecture : {}",
        "status_play_error": "● Erreur de lecture",
        "status_stop": "● ▪ Stop",
        "status_next": "● ▶ Suivant : {}",
        "status_prev": "● ▶ Précédent : {}",
        "status_last_track": "● ⊘ Dernier track",
        "status_first_track": "● ⊘ Premier track",
        "status_selected": "Sélectionné : {}",
        "status_reordered": "✓ Réorganisé : {}",
        "status_scan_complete": "✓ Scan terminé : {} tracks",
        "status_scan_error": "✗ Erreur de scan",
        "status_no_tracks": "⚠ Aucun track détecté",
        "status_palette": "● Palette : {}",
        
        # Control Panel - Scan Button
        "scan_btn": "SCAN",
        "scan_scanning": "Scan en cours...",
        "scan_starting": "Démarrage du scan...",
        "scan_connecting": "Connexion à Ableton Live...",
        "scan_detecting": "Détection des locators...",
        "scan_processing": "Traitement des tracks...",
        "scan_sections": "Identification des sections...",
        "scan_finalizing": "Finalisation...",
        "scan_updating_ui": "Mise à jour de l'interface...",
        "scan_found": "✓ {} tracks trouvés",
        "scan_error": "✗ Erreur de scan",
        "scan_error_critical": "✗ Erreur critique",
        
        # Track List
        "track_sections_count": "{} sections",
    },
    "de": {
        # General
        "app_name": "LiveCue",
        "version_beta": "BETA-Version",
        "version_dev": "Entwicklungsversion",
        "accept": "Akzeptieren",
        "cancel": "Abbrechen",
        "close": "Schließen",
        "save": "Speichern",
        "load": "Laden",
        "start": "Starten",
        "pause": "Pause",
        "reset": "Zurücksetzen",
        "waiting": "Warten...",
        "click_on": "CLICK ON",
        "click_off": "CLICK OFF",
        
        # Welcome Dialog
        "welcome_title": "LiveCue Beta",
        "welcome_warning_title": "Entwicklungsversion",
        "welcome_warning_text": "Diese Version kann Fehler enthalten. Häufiges Speichern wird empfohlen.",
        "welcome_feature_1": "Optimierte Oberfläche für Live-Auftritte",
        "welcome_feature_2": "Erweiterte Setlist-Verwaltung",
        "welcome_feature_3": "Ableton Live Integration (OSC)",
        "welcome_feature_4": "Fehler auf GitHub melden",
        "welcome_info_title": "Wichtige Informationen",
        "welcome_license_title": "CC BY-NC-SA 4.0 Lizenz",
        "welcome_license_text": "Kostenlos für persönliche Nutzung. Kommerzielle Nutzung ohne Lizenz verboten.",
        "welcome_start_btn": "Starten",
        
        # About Dialog
        "about_subtitle": "Ableton Setlist Controller",
        "about_dev_title": "ENTWICKLUNG",
        "about_author": "Autor",
        "about_copyright": "Copyright",
        "about_license_title": "LIZENZ",
        "about_license_personal": "Persönliche und Bildungsnutzung",
        "about_license_commercial": "Kommerzielle Nutzung ohne Genehmigung",
        "about_disclaimer": "Diese Software wird 'wie sie ist' bereitgestellt, ohne ausdrückliche oder stillschweigende Garantien.",
        "about_view_license": "Lizenz anzeigen",
        "about_donation_title": "Gefällt Ihnen LiveCue?",
        "about_donation_text": "LiveCue ist kostenlos und wird es immer bleiben. Wenn Sie es nützlich finden, erwägen Sie eine Spende.",
        
        # Header
        "header_save_tooltip": "Setlist speichern",
        "header_load_tooltip": "Setlist laden",
        "header_theme_tooltip": "Thema: {}",
        "header_about_tooltip": "Über LiveCue",
        
        # License
        "license_trial_started": "Testphase gestartet",
        "license_activated": "Lizenz aktiviert",
        "license_invalid": "Ungültige Lizenz",
        "license_trial_days_left": "Test: {} Tage verbleibend",
        "license_trial_expired": "Testphase abgelaufen",
        "license_key_invalid": "Ungültiger Lizenzschlüssel",
        
        # Dialogs - Save/Load Setlist
        "dialog_save_title": "💾 Setlist speichern",
        "dialog_save_name_label": "Setlist-Name",
        "dialog_save_name_hint": "z.B.: Konzert 2024",
        "dialog_save_warning_no_locators": "⚠️ Keine Locators. Drücken Sie zuerst SCAN",
        "dialog_save_error_empty_name": "⚠️ Sie müssen einen Namen eingeben",
        "dialog_save_error_failed": "✖ Fehler beim Speichern",
        "dialog_save_info": "{} Locators und {} Tracks werden gespeichert",
        "dialog_save_success": "✓ '{}' gespeichert ({} Locators, {} Tracks, {} Sections)",
        "dialog_load_title": "📂 Setlist laden",
        "dialog_load_dropdown_label": "Gespeicherte Setlists",
        "dialog_load_count": "📁 {} Setlist(s) verfügbar",
        "dialog_load_error": "✖ Fehler beim Laden",
        "dialog_load_success": "✓ '{}' geladen ({} Locators, {} Tracks, {} Sections)",
        "dialog_load_empty": "Keine gespeicherten Setlists",
        "dialog_load_empty_hint": "💡 Verwenden Sie die 💾-Taste, um Ihre erste Setlist zu speichern",
        "btn_save": "💾 Speichern",
        "btn_load": "📂 Laden",
        
        # Control Panel - Status Messages
        "status_waiting": "● Warten...",
        "status_metronome": "● Metronom: {}",
        "status_metronome_on": "AN",
        "status_metronome_off": "AUS",
        "status_no_track_selected": "● Kein Track ausgewählt",
        "status_play": "● ▶ Wiedergabe: {}",
        "status_play_error": "● Wiedergabefehler",
        "status_stop": "● ▪ Stop",
        "status_next": "● ▶ Nächster: {}",
        "status_prev": "● ▶ Vorheriger: {}",
        "status_last_track": "● ⊘ Letzter Track",
        "status_first_track": "● ⊘ Erster Track",
        "status_selected": "Ausgewählt: {}",
        "status_reordered": "✓ Neu angeordnet: {}",
        "status_scan_complete": "✓ Scan abgeschlossen: {} Tracks",
        "status_scan_error": "✗ Scan-Fehler",
        "status_no_tracks": "⚠ Keine Tracks erkannt",
        "status_palette": "● Palette: {}",
        
        # Control Panel - Scan Button
        "scan_btn": "SCAN",
        "scan_scanning": "Scannen...",
        "scan_starting": "Scan wird gestartet...",
        "scan_connecting": "Mit Ableton Live verbinden...",
        "scan_detecting": "Locators werden erkannt...",
        "scan_processing": "Tracks werden verarbeitet...",
        "scan_sections": "Sections werden identifiziert...",
        "scan_finalizing": "Wird abgeschlossen...",
        "scan_updating_ui": "Oberfläche wird aktualisiert...",
        "scan_found": "✓ {} Tracks gefunden",
        "scan_error": "✗ Scan-Fehler",
        "scan_error_critical": "✗ Kritischer Fehler",
        
        # Track List
        "track_sections_count": "{} Sections",
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
                primary_lang = lang_id & 0x3ff
                # Español=0x0a(10), Francés=0x0c(12), Alemán=0x07(7)
                if primary_lang == 0x0a:
                    return 'es'
                elif primary_lang == 0x0c:
                    return 'fr'
                elif primary_lang == 0x07:
                    return 'de'
            
            # Fallback a locale estándar
            lang_code, _ = locale.getdefaultlocale()
            if lang_code:
                if lang_code.lower().startswith('es'):
                    return 'es'
                elif lang_code.lower().startswith('fr'):
                    return 'fr'
                elif lang_code.lower().startswith('de'):
                    return 'de'
                
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
