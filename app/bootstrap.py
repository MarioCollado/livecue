"""Bootstrap y ciclo de vida de LiveCue."""

from __future__ import annotations

import atexit
import os
import signal
import sys
import threading

import flet as ft

from core.license import license_manager
from core.constants import FLASK_PORT
from core.logger import get_logger, log_debug, log_error, log_info, log_warning
from core.state import state
from osc.server import create_server
from ui.app_ui import main as run_ui

logger = get_logger()
osc_server = None
server_thread = None
shutdown_complete = False


def get_app_data_path():
    """Obtiene la ruta de AppData para guardar datos persistentes."""

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        app_path = os.path.join(appdata, "LiveCue")
    elif sys.platform == "darwin":
        app_path = os.path.expanduser("~/Library/Application Support/LiveCue")
    else:
        app_path = os.path.expanduser("~/.local/share/LiveCue")

    os.makedirs(app_path, exist_ok=True)
    log_debug(f"App data path: {app_path}")
    return app_path


def get_assets_path():
    """Obtiene la ruta correcta de assets según si es ejecutable o no."""

    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(sys.executable)
        assets = os.path.join(base_path, "assets")
    else:
        assets = "assets"

    log_debug(f"Assets path: {assets}")
    return assets


def shutdown_server():
    """Cierra el servidor OSC de forma segura."""

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
    """Función de limpieza al cerrar la aplicación."""

    log_info("👋 Cerrando LiveCue...")
    shutdown_server()

    try:
        logger.create_session_summary()
        log_info("📊 Resumen de sesión creado")
    except Exception as e:
        log_warning(f"No se pudo crear resumen de sesión: {e}")


def signal_handler(sig, frame):
    """Maneja el cierre limpio con Ctrl+C."""

    log_warning("⚠️  Ctrl+C detectado, cerrando aplicación...")
    cleanup_and_exit()
    sys.exit(0)


def check_disk_space():
    """Verifica que haya suficiente espacio en disco."""

    import shutil

    try:
        base_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
        stat = shutil.disk_usage(base_path)
        free_mb = stat.free / (1024 * 1024)

        log_debug(f"Espacio libre en disco: {free_mb:.2f} MB")

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
        return True


def check_write_permissions():
    """Verifica que se puede escribir en AppData."""

    try:
        app_data = get_app_data_path()
        test_file = os.path.join(app_data, ".write_test")

        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("test")
            os.remove(test_file)
            log_debug("✓ Permisos de escritura verificados en AppData")
            return True
        except Exception as e:
            log_error("=" * 80)
            log_error("❌ ERROR: Sin permisos de escritura en AppData")
            log_error("=" * 80)
            log_error("")
            log_error(f"No se puede escribir en: {app_data}")
            log_error(f"Error: {e}")
            log_error("")
            log_error("SOLUCIÓN:")
            log_error("Contacta con el administrador del sistema")
            log_error("=" * 80)
            log_error("")
            return False
    except Exception as e:
        log_warning(f"No se pudo verificar permisos: {e}")
        return True


def check_required_folders():
    """Crea carpetas necesarias en AppData."""

    try:
        app_data = get_app_data_path()
        folders = ["logs", "setlist", "setlist/data"]

        for folder in folders:
            folder_path = os.path.join(app_data, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                log_debug(f"✓ Carpeta creada: {folder}")

        return True
    except Exception as e:
        log_error(f"❌ No se pudieron crear carpetas necesarias: {e}")
        return False


def main():
    """Función principal de la aplicación."""

    global osc_server, server_thread

    log_info("=" * 80)
    log_info("🎵 LiveCue - Ableton Setlist Controller v2.0.0")
    log_info("© 2026 Mario Collado Rodríguez")
    log_info("=" * 80)

    if not check_disk_space():
        input("\nPresiona Enter para salir...")
        return 1

    if not check_write_permissions():
        input("\nPresiona Enter para salir...")
        return 1

    if not check_required_folders():
        input("\nPresiona Enter para salir...")
        return 1

    license_mgr = license_manager
    is_valid, status_code, days_remaining = license_mgr.check_license()
    log_info(f"📜 {license_mgr.get_status_message()}")

    if not is_valid:
        log_error("=" * 80)
        log_error("⏰ PERIODO DE PRUEBA EXPIRADO")
        log_error("=" * 80)
        log_error("")
        log_error("Gracias por probar LiveCue durante 14 días.")
        log_error("")
        purchase_info = license_mgr.get_purchase_info()
        log_error("Para continuar usando LiveCue, adquiere una licencia:")
        log_error(f"  📧 Email: {purchase_info['email']}")
        log_error(f"  🌐 Web: {purchase_info['website']}")
        log_error(f"  💰 Precio: {purchase_info['price']}")
        log_error("")
        log_error(f"Tu ID de hardware: {purchase_info['hardware_id']}")
        log_error("(Proporciona este ID al comprar)")
        log_error("=" * 80)
        log_error("")
        input("Presiona Enter para salir...")
        return 1

    if 0 < days_remaining <= 3:
        log_warning("=" * 80)
        log_warning(f"⚠️  ¡ATENCIÓN! Tu periodo de prueba expira en {days_remaining} días")
        log_warning("=" * 80)
        purchase_info = license_mgr.get_purchase_info()
        log_warning(f"Adquiere tu licencia en: {purchase_info['email']}")
        log_warning("")

    if getattr(sys, "frozen", False):
        log_info("🔧 Ejecutando desde ejecutable compilado")
        try:
            import flet.utils.pip as flet_pip

            flet_pip.install_flet_package = lambda *args, **kwargs: None
            log_debug("✓ Parcheado flet.utils.pip.install_flet_package")
        except Exception as e:
            log_warning(f"No se pudo parchear flet.utils.pip: {e}")

        try:
            import flet.utils.pip as flet_pip

            flet_pip.ensure_flet_desktop_package_installed = lambda *args, **kwargs: None
            log_debug("✓ Parcheado ensure_flet_desktop_package_installed")
        except Exception as e:
            log_warning(f"No se pudo parchear ensure_flet_desktop: {e}")

        try:
            import flet

            if hasattr(flet, "utils") and hasattr(flet.utils, "pip"):
                flet.utils.pip.install_flet_package = lambda *args, **kwargs: None
                flet.utils.pip.ensure_flet_desktop_package_installed = lambda *args, **kwargs: None
                log_debug("✓ Parcheado completo de flet.utils.pip")
        except Exception as e:
            log_warning(f"Parche adicional falló: {e}")

        os.environ["FLET_HIDE_CONSOLE"] = "1"
        os.environ["FLET_VIEW"] = "flet_app"
        os.environ["FLET_FORCE_EMBEDDED"] = "1"
    else:
        log_info("🔧 Ejecutando en modo desarrollo")

    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(cleanup_and_exit)

    try:
        log_info("🔧 Creando servidor OSC...")
        log_debug(
            f"Puerto configurado: {state.CLIENT_LISTEN_PORT if hasattr(state, 'CLIENT_LISTEN_PORT') else '11001'}"
        )

        osc_server = create_server()
        log_info("✓ Servidor OSC creado")

        log_info("🚀 Iniciando servidor OSC en background...")
        server_thread = threading.Thread(target=osc_server.serve_forever, daemon=True)
        server_thread.start()

        log_info("✓ Servidor OSC activo y escuchando")
        log_debug(f"Thread OSC: {server_thread.name} (daemon={server_thread.daemon})")

        log_info("🌐 Iniciando servidor web Flask...")
        try:
            from osc.web_server import WebControllerServer
            from core.playback import playback

            web_server = WebControllerServer(playback, state, port=FLASK_PORT)
            web_server.start()
            log_info("✓ Servidor web iniciado")
        except Exception as e:
            log_warning(f"⚠️  Servidor web no pudo iniciarse: {e}")
            log_warning("La app funcionará sin control remoto")

        log_info("🎨 Iniciando interfaz gráfica Flet...")
        assets_path = get_assets_path()
        log_debug(f"Assets directory: {assets_path}")

        if not os.path.exists(assets_path):
            log_warning(f"⚠️  Directorio assets no encontrado: {assets_path}")

        ft.app(target=run_ui, assets_dir=assets_path)
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

        log_error(f"Error OSC crítico: {e}", exc=e)
        return 1

    except KeyboardInterrupt:
        log_warning("⚠️  Aplicación interrumpida por el usuario (Ctrl+C)")
        return 0

    except Exception as e:
        log_error(f"❌ Error crítico en main(): {e}", exc=e)
        return 1

    finally:
        log_debug("Ejecutando limpieza final...")
        shutdown_server()

    log_info("=" * 80)
    log_info("👋 LiveCue cerrado correctamente")
    log_info("=" * 80)
    return 0
