# setlist/manager.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

"""Gestor de setlists con serialización/deserialización JSON"""

import json
import time
from pathlib import Path
from core.constants import SETLISTS_DIR
from core.state import Track, Section, Locator
from core.logger import log_info, log_error, log_warning, log_debug

class SetlistManager:
    """Gestor de setlists con serialización/deserialización"""
    
    def __init__(self):
        SETLISTS_DIR.mkdir(parents=True, exist_ok=True)
        log_debug(f"SetlistManager inicializado (directorio: {SETLISTS_DIR})", module="Playback")
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Limpia nombre para usar como archivo"""
        safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        sanitized = safe if safe else "setlist"
        log_debug(f"Nombre sanitizado: '{name}' → '{sanitized}'", module="Playback")
        return sanitized
    
    def save(self, name: str, locators: list, tracks: list = None) -> bool:
        """Guarda un setlist en JSON"""
        log_info(f"💾 Guardando setlist: '{name}'", module="Playback")
        
        try:
            if not locators:
                log_warning("No hay locators para guardar", module="Playback")
                return False
            
            filepath = SETLISTS_DIR / f"{self._sanitize_filename(name)}.json"
            log_debug(f"Ruta destino: {filepath}", module="Playback")
            
            data = {
                "name": name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "locators": [self._serialize_locator(loc) for loc in locators],
            }
            
            if tracks:
                data["tracks"] = [self._serialize_track(track) for track in tracks]
                sections_count = sum(len(t.sections) for t in tracks)
                log_debug(f"Serializando {len(tracks)} tracks con {sections_count} secciones", module="Playback")
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            file_size = filepath.stat().st_size
            log_info(f"✓ Setlist guardado: '{filepath.name}' ({file_size} bytes)", module="Playback")
            return True
            
        except Exception as e:
            log_error(f"Error guardando setlist '{name}'", module="Playback", exc=e)
            return False
    
    def load(self, name: str) -> dict:
        """Carga un setlist desde JSON"""
        log_info(f"📂 Cargando setlist: '{name}'", module="Playback")
        
        try:
            filepath = SETLISTS_DIR / f"{name}.json"
            
            if not filepath.exists():
                log_error(f"Setlist no encontrado: {filepath}", module="Playback")
                return None
            
            log_debug(f"Leyendo archivo: {filepath}", module="Playback")
            
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Deserializar objetos
            locators_count = len(data.get("locators", []))
            data["locators"] = [self._deserialize_locator(loc) for loc in data.get("locators", [])]
            log_debug(f"Deserializados {locators_count} locators", module="Playback")
            
            if "tracks" in data:
                tracks_count = len(data["tracks"])
                data["tracks"] = [self._deserialize_track(t) for t in data["tracks"]]
                sections_count = sum(len(t.sections) for t in data["tracks"])
                log_debug(f"Deserializados {tracks_count} tracks con {sections_count} secciones", module="Playback")
            
            timestamp = data.get("timestamp", "desconocido")
            log_info(f"✓ Setlist cargado: '{name}' (guardado: {timestamp})", module="Playback")
            return data
            
        except json.JSONDecodeError as e:
            log_error(f"Archivo JSON corrupto: '{name}'", module="Playback", exc=e)
            return None
        except Exception as e:
            log_error(f"Error cargando setlist '{name}'", module="Playback", exc=e)
            return None
    
    def list_all(self) -> list:
        """Lista todos los setlists guardados"""
        try:
            setlists = sorted([f.stem for f in SETLISTS_DIR.glob("*.json")])
            log_debug(f"Setlists encontrados: {len(setlists)}", module="Playback")
            return setlists
        except Exception as e:
            log_error("Error listando setlists", module="Playback", exc=e)
            return []
    
    @staticmethod
    def _serialize_locator(loc) -> dict:
        """Convierte Locator a dict"""
        if isinstance(loc, Locator):
            return {
                "id": loc.id,
                "original_id": loc.original_id,
                "name": loc.name,
                "beat": loc.beat
            }
        return loc  # Ya es dict
    
    @staticmethod
    def _deserialize_locator(data: dict) -> Locator:
        """Convierte dict a Locator"""
        return Locator(
            id=data.get("id"),
            original_id=data.get("original_id", data.get("id")),
            name=data["name"],
            beat=data["beat"]
        )
    
    @staticmethod
    def _serialize_track(track) -> dict:
        """Convierte Track a dict"""
        if isinstance(track, Track):
            return {
                "title": track.title,
                "start": track.start,
                "end": track.end,
                "track_number": track.track_number,
                "start_locator_id": track.start_locator_id,
                "sections": [
                    {
                        "name": sec.name,
                        "beat": sec.beat,
                        "time": sec.time,
                        "relative_beat": sec.relative_beat
                    }
                    for sec in track.sections
                ]
            }
        return track  # Ya es dict
    
    @staticmethod
    def _deserialize_track(data: dict) -> Track:
        """Convierte dict a Track"""
        track = Track(
            title=data["title"],
            start=data["start"],
            end=data["end"],
            track_number=data["track_number"],
            start_locator_id=data.get("start_locator_id")
        )
        
        for sec_data in data.get("sections", []):
            section = Section(
                name=sec_data["name"],
                beat=sec_data["beat"],
                time=sec_data.get("time", sec_data["beat"]),
                relative_beat=sec_data.get("relative_beat", 0)
            )
            track.sections.append(section)
        
        return track

# Instancia global
manager = SetlistManager()
log_info("✓ Instancia global de SetlistManager creada", module="Playback")