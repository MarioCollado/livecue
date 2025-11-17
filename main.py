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

def get_app_data_path():
    """Obtiene la ruta de AppData para guardar datos persistentes"""
    if sys.platform == 'win32':
        # Windows: %APPDATA%\LiveCue
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        app_path = os.path.join(appdata, 'LiveCue')
    elif sys.platform == 'darwin':
        # macOS: ~/Library/Application Support/LiveCue
        app_path = os.path.expanduser('~/Library/Application Support/LiveCue')
    else:
        # Linux: ~/.local/share/LiveCue
        app_path = os.path.expanduser('~/.local/share/LiveCue')
    
    # Crear directorio si no existe
    os.makedirs(app_path, exist_ok=True)
    log_debug(f"App data path: {app_path}")
    return app_path

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

def check_write_permissions():
    """Verifica que se puede escribir en el directorio actual"""
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.getcwd()
        
        # Intentar crear un archivo de prueba
        test_file = os.path.join(base_path, '.write_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            log_debug("✓ Permisos de escritura verificados")
            return True
        except Exception as e:
            log_error("=" * 80)
            log_error("❌ ERROR: Sin permisos de escritura")
            log_error("=" * 80)
            log_error("")
            log_error(f"No se puede escribir en: {base_path}")
            log_error("")
            log_error("SOLUCIONES:")
            log_error("1. Ejecuta como administrador (click derecho → Ejecutar como administrador)")
            log_error("2. Mueve LiveCue a tu carpeta de usuario (Documentos, Escritorio)")
            log_error("3. No ejecutes desde carpetas protegidas (Program Files, System32)")
            log_error("=" * 80)
            log_error("")
            return False
    except Exception as e:
        log_warning(f"No se pudo verificar permisos: {e}")
        return True

def check_required_folders():
    """Crea carpetas necesarias si no existen"""
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.getcwd()
        
        folders = ['logs', 'setlist', 'setlist/data']
        
        for folder in folders:
            folder_path = os.path.join(base_path, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                log_debug(f"✓ Carpeta creada: {folder}")
        
        return True
    except Exception as e:
        log_error(f"❌ No se pudieron crear carpetas necesarias: {e}")
        return False

def main():
    """Función principal de la aplicación"""
    global osc_server, server_thread
    
    # Banner de inicio
    log_info("=" * 80)
    log_info("🎵 LiveCue - Ableton Setlist Controller v2.0.0")
    log_info("© 2025 Mario Collado Rodríguez")
    log_info("=" * 80)
    
    # Verificaciones previas
    if not check_disk_space():
        input("\nPresiona Enter para salir...")
        return 1
    
    if not check_write_permissions():
        input("\nPresiona Enter para salir...")
        return 1
    
    if not check_required_folders():
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
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")
        sys.exit(1)