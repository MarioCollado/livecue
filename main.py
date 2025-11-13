# ============================================================================
# LiveCue - Copyright (c) 2025 Mario Collado Rodríguez
# Licensed under MIT License - See LICENSE file
# ============================================================================

# main.py
import flet as ft
from flask import Flask, jsonify
from ui.app_ui import main as run_ui
from osc.server import create_server
from core.state import state
import threading
import sys
import signal
import atexit

# Variable global para el servidor
osc_server = None
server_thread = None
shutdown_complete = False

def shutdown_server():
    """Cierra el servidor OSC de forma segura"""
    global osc_server, shutdown_complete
    
    if shutdown_complete:
        return
    
    if osc_server:
        try:
            print("[SHUTDOWN] Cerrando servidor OSC...")
            osc_server.shutdown()
            shutdown_complete = True
            print("[SHUTDOWN] ✓ Servidor OSC cerrado correctamente")
        except Exception as e:
            print(f"[SHUTDOWN] Error cerrando servidor: {e}")

def signal_handler(sig, frame):
    """Maneja el cierre limpio con Ctrl+C"""
    print("\n[SHUTDOWN] Ctrl+C detectado, cerrando aplicación...")
    shutdown_server()
    sys.exit(0)

def main():
    """Función principal de la aplicación"""
    global osc_server, server_thread
    
    # Registrar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    # Registrar función de limpieza al salir
    atexit.register(shutdown_server)
    
    try:
        # ===== CREAR Y ARRANCAR SERVIDOR OSC =====
        print("[INIT] Creando servidor OSC...")
        osc_server = create_server()
        
        print("[INIT] Iniciando servidor OSC en background...")
        server_thread = threading.Thread(target=osc_server.serve_forever, daemon=True)
        server_thread.start()
        
        print("[INIT] Servidor OSC iniciado correctamente")
    
        # ===== INICIAR SERVIDOR WEB =====
        from core.playback import playback
        from osc.web_server import WebControllerServer

        web_server = WebControllerServer(playback, state)
        web_server.start()
        
        # ===== ARRANCAR INTERFAZ GRÁFICA =====
        print("[INIT] Iniciando interfaz gráfica...\n")
        ft.app(target=run_ui, assets_dir="assets")        
        
        # La app se bloquea aquí hasta que se cierre la ventana
        print("\n[SHUTDOWN] Ventana cerrada por el usuario")
        
    except OSError as e:
        if e.errno == 10048 or "address already in use" in str(e).lower():
            print("\n" + "="*60)
            print("❌ ERROR: Puerto OSC ya está en uso")
            print("="*60)
            print("\nSOLUCIONES:")
            print("1. Cierra otras instancias de LiveCue")
            print("2. Windows: taskkill /F /IM python.exe")
            print("3. Linux/Mac: killall python")
            print("4. Cambia CLIENT_LISTEN_PORT en core/constants.py")
            print("="*60 + "\n")
            return 1
        else:
            print(f"\n❌ Error OSC: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Aplicación interrumpida por el usuario")
        return 0
    
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Asegurar cierre limpio
        shutdown_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())