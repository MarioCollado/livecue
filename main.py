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
import os
import signal
import atexit

# Variable global para el servidor
osc_server = None
server_thread = None
shutdown_complete = False

# Inicializar logger al inicio
logger = get_logger()

def get_assets_path():
    """Obtiene la ruta correcta de assets según si es ejecutable o no"""
    if getattr(sys, 'frozen', False):
        # Ejecutable compilado (PyInstaller, Nuitka, etc.)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller
            base_path = sys._MEIPASS
        else:
            # Nuitka u otros
            base_path = os.path.dirname(sys.executable)
        assets = os.path.join(base_path, 'assets')
    else:
        # Modo desarrollo
        assets = "assets"
    
    log_debug(f"Assets path: {assets}")
    return assets

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

def check_disk_space():
    """Verifica que haya suficiente espacio en disco"""
    import shutil
    
    try:
        # Obtener espacio libre en el disco donde está el ejecutable
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.getcwd()
        
        # Obtener espacio libre en MB
        stat = shutil.disk_usage(base_path)
        free_mb = stat.free / (1024 * 1024)
        
        log_debug(f"Espacio libre en disco: {free_mb:.2f} MB")
        
        # Requerir al menos 100 MB libres
        if free_mb < 100:
            log_error("=" * 80)
            log_error("❌ ERROR: Espacio en disco insuficiente")
            log_error("=" * 80)
            log_error("")
            log_error(f"Espacio disponible: {free_mb:.2f} MB")
            log_error("Espacio requerido: 100 MB")
            log_error("")
            log_error("SOLUCIÓN:")
            log_error("Libera al menos 100 MB de espacio en tu disco")
            log_error("=" * 80)
            log_error("")
            return False
        
        return True
    except Exception as e:
        log_warning(f"No se pudo verificar espacio en disco: {e}")
        return True  # Continuar si no se puede verificar

def main():
    """Función principal de la aplicación"""
    global osc_server, server_thread
    
    # Banner de inicio
    log_info("=" * 80)
    log_info("🎵 LiveCue - Ableton Setlist Controller v2.0.0")
    log_info("© 2025 Mario Collado Rodríguez")
    log_info("=" * 80)
    
    # Verificar espacio en disco
    if not check_disk_space():
        input("\nPresiona Enter para salir...")
        return 1
    
    # Detectar si estamos en ejecutable compilado
    if getattr(sys, 'frozen', False):
        log_info("🔧 Ejecutando desde ejecutable compilado")
        
        # CRÍTICO: Deshabilitar instalación de paquetes de Flet de múltiples formas
        try:
            # Método 1: Parchear flet.utils.pip
            import flet.utils.pip as flet_pip
            flet_pip.install_flet_package = lambda *args, **kwargs: None
            log_debug("✓ Parcheado flet.utils.pip.install_flet_package")
        except Exception as e:
            log_warning(f"No se pudo parchear flet.utils.pip: {e}")
        
        try:
            # Método 2: Parchear ensure_flet_desktop_package_installed
            import flet.utils.pip as flet_pip
            flet_pip.ensure_flet_desktop_package_installed = lambda *args, **kwargs: None
            log_debug("✓ Parcheado flet.utils.pip.ensure_flet_desktop_package_installed")
        except Exception as e:
            log_warning(f"No se pudo parchear ensure_flet_desktop: {e}")
        
        try:
            # Método 3: Monkey patch sys.frozen para que Flet lo detecte
            import flet
            if hasattr(flet, 'utils'):
                if hasattr(flet.utils, 'pip'):
                    # Reemplazar todas las funciones de instalación
                    flet.utils.pip.install_flet_package = lambda *args, **kwargs: None
                    flet.utils.pip.ensure_flet_desktop_package_installed = lambda *args, **kwargs: None
                    log_debug("✓ Parcheado completo de flet.utils.pip")
        except Exception as e:
            log_warning(f"Parche adicional falló: {e}")
        
        # Configurar variables de entorno
        os.environ["FLET_HIDE_CONSOLE"] = "1"
        os.environ["FLET_VIEW"] = "flet_app"
        os.environ["FLET_FORCE_EMBEDDED"] = "1"
    else:
        log_info("🔧 Ejecutando en modo desarrollo")
    
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
        
        # Obtener ruta correcta de assets
        assets_path = get_assets_path()
        log_debug(f"Assets directory: {assets_path}")
        
        # Verificar que assets existe
        if not os.path.exists(assets_path):
            log_warning(f"⚠️  Directorio assets no encontrado: {assets_path}")
        
        # Iniciar Flet con configuración para ejecutables
        if getattr(sys, 'frozen', False):
            # Modo ejecutable compilado - no especificar view
            ft.app(
                target=run_ui,
                assets_dir=assets_path
            )
        else:
            # Modo desarrollo
            ft.app(
                target=run_ui,
                assets_dir=assets_path
            )
        
        log_info("🚪 Ventana cerrada por el usuario")
        
    except OSError as e:
        err = str(e).lower()

        # Puerto ocupado
        if e.errno == 10048 or "address already in use" in err:
            log_error("=" * 80)
            log_error("❌ ERROR: Puerto OSC ya está en uso")
            log_error("=" * 80)
            log_error("")
            log_error("SOLUCIONES:")
            log_error("1. Cierra otras instancias de LiveCue")
            log_error("2. Windows: taskkill /F /IM LiveCue.exe /F")
            log_error("3. Windows: taskkill /F /IM python.exe")
            log_error("4. Cambia CLIENT_LISTEN_PORT en core/constants.py")
            log_error("=" * 80)
            log_error("")
            return 1

        # Firewall / permisos / WinError 10013
        elif e.errno == 10013 or "permission denied" in err or "forbidden" in err:
            log_error("=" * 80)
            log_error("❌ ERROR: Windows está bloqueando la comunicación OSC")
            log_error("        (WinError 10013 - Permiso denegado)")
            log_error("=" * 80)
            log_error("")
            log_error("CAUSAS COMUNES:")
            log_error(" • El Firewall de Windows está bloqueando LiveCue")
            log_error(" • El puerto 11001 requiere permisos de red")
            log_error(" • El ejecutable no tiene permisos suficientes")
            log_error("")
            log_error("SOLUCIONES:")
            log_error(" 1. Abre el Firewall de Windows → Permitir una app")
            log_error("    → Añade LiveCue.exe y habilita 'Privada' y 'Pública'")
            log_error("")
            log_error(" 2. O permite manualmente los puertos:")
            log_error("    Puerto OSC salida  → 11000")
            log_error("    Puerto OSC entrada → 11001")
            log_error("")
            log_error(" 3. Ejecuta LiveCue como administrador (clic derecho → Ejecutar como admin)")
            log_error("")
            log_error(" 4. Si usas antivirus tipo Avast/AVG/Bitdefender, marca LiveCue como aplicación permitida.")
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
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")
        sys.exit(1)