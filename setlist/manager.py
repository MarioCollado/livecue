# setlist/manager.py
from pathlib import Path
import json
import time
from core.constants import SETLISTS_DIR
from core import utils

# Asegurar la carpeta
SETLISTS_DIR.mkdir(parents=True, exist_ok=True)

def save_setlist(name, locator_list, tracks_list=None):
    """Guarda un setlist en formato JSON con locators y tracks"""
    try:
        print(f"\n{'='*50}")
        print(f"[DEBUG SAVE] Guardando: '{name}'")
        print(f"[DEBUG SAVE] Locators: {len(locator_list)}")
        print(f"[DEBUG SAVE] Tracks: {len(tracks_list) if tracks_list else 0}")
        
        if not locator_list:
            return False
        
        safe_name = utils.sanitize_filename(name)
        filepath = SETLISTS_DIR / f"{safe_name}.json"
        
        # Guardar locators con original_id
        data = {
            "name": name,
            "locators": [
                {
                    "id": loc.get("id"), 
                    "original_id": loc.get("original_id", loc.get("id")),
                    "name": loc["name"], 
                    "beat": loc["beat"]
                } 
                for loc in locator_list
            ],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Guardar tracks con sections si están disponibles
        if tracks_list:
            data["tracks"] = [
                {
                    "title": track["title"],
                    "start": track["start"],
                    "end": track["end"],
                    "start_locator_id": track.get("start_locator_id"),
                    "track_number": track["track_number"],
                    "sections": [
                        {
                            "name": sec["name"],
                            "beat": sec["beat"],
                            "time": sec.get("time", sec["beat"]),
                            "relative_beat": sec.get("relative_beat", 0)
                        }
                        for sec in track.get("sections", [])
                    ]
                }
                for track in tracks_list
            ]
        
        SETLISTS_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[DEBUG SAVE] ✅ Guardado en: {filepath}")
        if tracks_list:
            total_sections = sum(len(t.get("sections", [])) for t in tracks_list)
            print(f"[DEBUG SAVE] Guardados {len(tracks_list)} tracks con {total_sections} sections")
        print(f"{'='*50}\n")
        return True
            
    except Exception as e:
        print(f"[DEBUG SAVE] ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_setlist(name):
    """Carga un setlist desde archivo JSON"""
    try:
        filepath = SETLISTS_DIR / f"{name}.json"
        print(f"[DEBUG LOAD] Cargando: {filepath}")
        
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[DEBUG LOAD] ✅ Cargado: {data.get('name')} con {len(data.get('locators', []))} locators")
                if "tracks" in data:
                    total_sections = sum(len(t.get("sections", [])) for t in data["tracks"])
                    print(f"[DEBUG LOAD] ✅ {len(data['tracks'])} tracks con {total_sections} sections")
                return data
        else:
            print(f"[DEBUG LOAD] ❌ Archivo no existe: {filepath}")
    except Exception as e:
        print(f"[DEBUG LOAD] ❌ Error cargando setlist: {e}")
        utils.log_exc("DEBUG LOAD")
    return None

def list_setlists():
    """Lista todos los setlists guardados"""
    try:
        setlists = sorted([f.stem for f in SETLISTS_DIR.glob("*.json")])
        print(f"[DEBUG] Setlists encontrados: {setlists}")
        return setlists
    except Exception as e:
        print(f"[DEBUG] Error listando setlists: {e}")
        utils.log_exc("SETLIST LIST")
        return []