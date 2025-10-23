# setlist/manager.py
from pathlib import Path
import json
import time
from core.constants import SETLISTS_DIR
from core import utils

# Asegurar la carpeta
SETLISTS_DIR.mkdir(parents=True, exist_ok=True)

def save_setlist(name, locator_list):
    """Guarda un setlist en formato JSON"""
    try:
        print(f"\n{'='*50}")
        print(f"[DEBUG SAVE] Iniciando guardado de setlist")
        print(f"[DEBUG SAVE] Nombre: '{name}'")
        print(f"[DEBUG SAVE] Directorio: {SETLISTS_DIR}")
        print(f"[DEBUG SAVE] Existe directorio: {SETLISTS_DIR.exists()}")
        print(f"[DEBUG SAVE] Número de locators: {len(locator_list)}")
        
        if not locator_list:
            print(f"[DEBUG SAVE] ❌ ERROR: Lista de locators vacía")
            return False
        
        safe_name = utils.sanitize_filename(name)
        filepath = SETLISTS_DIR / f"{safe_name}.json"
        print(f"[DEBUG SAVE] Ruta completa: {filepath}")
        
        data = {
            "name": name,
            "locators": [{"id": loc["id"], "name": loc["name"], "beat": loc["beat"]} for loc in locator_list],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"[DEBUG SAVE] Datos a guardar: {utils.pretty_json(data)}")
        
        SETLISTS_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"[DEBUG SAVE] ✅ Archivo guardado exitosamente")
            print(f"[DEBUG SAVE] Tamaño: {size} bytes")
            print(f"[DEBUG SAVE] Ruta: {filepath}")
            
            with open(filepath, "r", encoding="utf-8") as f:
                test_load = json.load(f)
                print(f"[DEBUG SAVE] ✅ Verificación de lectura OK: {len(test_load.get('locators', []))} locators")
            
            print(f"{'='*50}\n")
            return True
        else:
            print(f"[DEBUG SAVE] ❌ El archivo no existe después de guardarlo")
            print(f"{'='*50}\n")
            return False
            
    except Exception as e:
        print(f"[DEBUG SAVE] ❌ ERROR CRÍTICO: {e}")
        utils.log_exc("DEBUG SAVE")
        print(f"{'='*50}\n")
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
