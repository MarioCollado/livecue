# ============================================================================
# LiveCue - Ableton Setlist Controller
# Copyright (c) 2025 Mario Collado Rodríguez. Todos los derechos reservados.
# 
# Este software está protegido bajo Creative Commons BY-NC-SA 4.0.
# 
# TÉRMINOS PRINCIPALES:
# - ✓ Uso personal/educativo permitido
# - ✓ Modificaciones permitidas (deben compartirse igual)
# - ✗ Uso comercial PROHIBIDO sin licencia
# - ✗ NO puedes vender este software
# 
# Para licencias comerciales contacta: mcolladorguez@gmail.com
# Licencia completa: https://creativecommons.org/licenses/by-nc-sa/4.0/
# 
# Autor: Mario Collado Rodríguez
# GitHub: https://github.com/MarioCollado/LiveCue
# Versión: 2.0.0
# Fecha: Noviembre 2025
# ============================================================================

"""
main.py - Punto de entrada principal de LiveCue

Inicializa el sistema de logging, servidores OSC y web, y la interfaz gráfica.
Gestiona el ciclo de vida completo de la aplicación.
"""

import flet as ft
from ui.app_ui import main as run_ui
from osc.server import create_server
from core.state import state
from core.logger import get_logger, log_info, log_error, log_warning, log_debug
import threading
import sys
import signal
import atexit

# Variable global para el servidor
osc_server = None
server_thread = None
shutdown_complete = False

# Inicializar logger al inicio
logger = get_logger()

def shutdown_server():
    """Cierra el servidor OSC de forma segura"""
    global osc_server, shutdown_complete
    
    if shutdown_complete:
        return
    
    if osc_server:
        try:
            log_info("🔌 Cerrando servidor OSC...")
            osc_server.shutdown()
            shutdown_complete = True
            log_info("✓ Servidor OSC cerrado correctamente")
        except Exception as e:
            log_error(f"Error cerrando servidor OSC: {e}", exc=e)

def cleanup_and_exit():
    """Función de limpieza al cerrar la aplicación"""
    log_info("👋 Cerrando LiveCue...")
    shutdown_server()
    
    # Crear resumen de sesión
    try:
        logger.create_session_summary()
        log_info("📊 Resumen de sesión creado")
    except Exception as e:
        log_warning(f"No se pudo crear resumen de sesión: {e}")

def signal_handler(sig, frame):
    """Maneja el cierre limpio con Ctrl+C"""
    log_warning("⚠️  Ctrl+C detectado, cerrando aplicación...")
    cleanup_and_exit()
    sys.exit(0)

def main():
    """Función principal de la aplicación"""
    global osc_server, server_thread
    
    # Banner de inicio
    log_info("=" * 80)
    log_info("🎵 LiveCue - Ableton Setlist Controller v2.0.0")
    log_info("© 2025 Mario Collado Rodríguez")
    log_info("=" * 80)
    
    # Registrar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    # Registrar función de limpieza al salir
    atexit.register(cleanup_and_exit)
    
    try:
        # ===== CREAR Y ARRANCAR SERVIDOR OSC =====
        log_info("🔧 Creando servidor OSC...")
        log_debug(f"Puerto configurado: {state.CLIENT_LISTEN_PORT if hasattr(state, 'CLIENT_LISTEN_PORT') else '11001'}")
        
        osc_server = create_server()
        log_info("✓ Servidor OSC creado")
        
        log_info("🚀 Iniciando servidor OSC en background...")
        server_thread = threading.Thread(target=osc_server.serve_forever, daemon=True)
        server_thread.start()
        
        log_info("✓ Servidor OSC activo y escuchando")
        log_debug(f"Thread OSC: {server_thread.name} (daemon={server_thread.daemon})")
    
        # ===== INICIAR SERVIDOR WEB =====
        log_info("🌐 Iniciando servidor web Flask...")
        
        try:
            from core.playback import playback
            from osc.web_server import WebControllerServer

            web_server = WebControllerServer(playback, state, port=5000)
            web_server.start()
            log_info("✓ Servidor web iniciado")
            
        except Exception as e:
            log_warning(f"⚠️  Servidor web no pudo iniciarse: {e}")
            log_warning("La app funcionará sin control remoto")
        
        # ===== ARRANCAR INTERFAZ GRÁFICA =====
        log_info("🎨 Iniciando interfaz gráfica Flet...")
        log_debug("Assets dir: assets/")
        
        # La app se bloquea aquí hasta que se cierre la ventana
        ft.app(target=run_ui, assets_dir="assets")        
        
        log_info("🚪 Ventana cerrada por el usuario")
        
    except OSError as e:
        if e.errno == 10048 or "address already in use" in str(e).lower():
            log_error("=" * 80)
            log_error("❌ ERROR: Puerto OSC ya está en uso")
            log_error("=" * 80)
            log_error("")
            log_error("SOLUCIONES:")
            log_error("1. Cierra otras instancias de LiveCue")
            log_error("2. Windows: taskkill /F /IM python.exe")
            log_error("3. Linux/Mac: killall python")
            log_error("4. Cambia CLIENT_LISTEN_PORT en core/constants.py")
            log_error("=" * 80)
            log_error("")
            return 1
        else:
            log_error(f"Error OSC crítico: {e}", exc=e)
            return 1
    
    except KeyboardInterrupt:
        log_warning("⚠️  Aplicación interrumpida por el usuario (Ctrl+C)")
        return 0
    
    except Exception as e:
        log_error(f"❌ Error crítico en main(): {e}", exc=e)
        return 1
    
    finally:
        # Asegurar cierre limpio
        log_debug("Ejecutando limpieza final...")
        shutdown_server()
    
    log_info("=" * 80)
    log_info("👋 LiveCue cerrado correctamente")
    log_info("=" * 80)
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)