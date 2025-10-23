import flet as ft
from ui.app_ui import main as run_ui
from osc.server import create_server
import threading
import sys
import signal

# Variable global para el servidor
osc_server = None

def signal_handler(sig, frame):
    """Maneja el cierre limpio de la aplicación"""
    print("\n[SHUTDOWN] Cerrando aplicación...")
    if osc_server:
        osc_server.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    # Registrar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Crear servidor OSC
        print("[INIT] Creando servidor OSC...")
        osc_server = create_server()

        # Ejecutarlo en background
        print("[INIT] Iniciando servidor OSC en background...")
        server_thread = threading.Thread(target=osc_server.serve_forever, daemon=True)
        server_thread.start()
        
        print("[INIT] Servidor OSC iniciado correctamente")
        print("[INIT] Iniciando interfaz gráfica...")

        # Ejecutar la UI
        ft.app(target=run_ui)
        
    except OSError as e:
        if e.errno == 10048:
            print("\n" + "="*60)
            print("❌ ERROR: Puerto OSC ya está en uso")
            print("="*60)
            print("\nSOLUCIONES:")
            print("1. Cierra otras instancias de LiveCue")
            print("2. Ejecuta: taskkill /F /IM python.exe")
            print("3. Ejecuta: taskkill /F /IM LIVECUE*.exe")
            print("4. Cambia CLIENT_LISTEN_PORT en core/constants.py")
            print("="*60 + "\n")
        else:
            print(f"\n❌ Error OSC: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Aplicación cerrada por el usuario")
        if osc_server:
            osc_server.shutdown()
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # Asegurar cierre limpio del servidor
        if osc_server:
            try:
                osc_server.shutdown()
                print("[SHUTDOWN] Servidor OSC cerrado correctamente")
            except:
                pass