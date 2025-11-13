# setlist/manager.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

import json
import time
from pathlib import Path
from core.constants import SETLISTS_DIR
from core.state import Track, Section, Locator

class SetlistManager:
    """Gestor de setlists con serialización/deserialización"""
    
    def __init__(self):
        SETLISTS_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Limpia nombre para usar como archivo"""
        safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        return safe if safe else "setlist"
    
    def save(self, name: str, locators: list, tracks: list = None) -> bool:
        """Guarda un setlist en JSON"""
        try:
            if not locators:
                return False
            
            filepath = SETLISTS_DIR / f"{self._sanitize_filename(name)}.json"
            
            data = {
                "name": name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "locators": [self._serialize_locator(loc) for loc in locators],
            }
            
            if tracks:
                data["tracks"] = [self._serialize_track(track) for track in tracks]
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"[SETLIST] ✓ Guardado: {filepath}")
            return True
            
        except Exception as e:
            print(f"[SETLIST] ✗ Error guardando: {e}")
            return False
    
    def load(self, name: str) -> dict:
        """Carga un setlist desde JSON"""
        try:
            filepath = SETLISTS_DIR / f"{name}.json"
            
            if not filepath.exists():
                print(f"[SETLIST] ✗ No existe: {filepath}")
                return None
            
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Deserializar objetos
            data["locators"] = [self._deserialize_locator(loc) for loc in data.get("locators", [])]
            if "tracks" in data:
                data["tracks"] = [self._deserialize_track(t) for t in data["tracks"]]
            
            print(f"[SETLIST] ✓ Cargado: {name}")
            return data
            
        except Exception as e:
            print(f"[SETLIST] ✗ Error cargando: {e}")
            return None
    
    def list_all(self) -> list:
        """Lista todos los setlists guardados"""
        try:
            return sorted([f.stem for f in SETLISTS_DIR.glob("*.json")])
        except Exception as e:
            print(f"[SETLIST] ✗ Error listando: {e}")
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