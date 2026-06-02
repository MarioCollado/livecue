# core/logger.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0

"""
Sistema de logging profesional para LiveCue
Organiza logs por fecha y sesión con rotación automática
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import traceback

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def get_logs_base_dir() -> Path:
    """Obtiene el directorio base para logs según el entorno"""
    
    # Si es ejecutable, usar AppData
    if getattr(sys, 'frozen', False):
        if sys.platform == 'win32':
            # Windows: %APPDATA%\LiveCue\logs
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            base = Path(appdata) / 'LiveCue' / 'logs'
        elif sys.platform == 'darwin':
            # macOS: ~/Library/Application Support/LiveCue/logs
            base = Path.home() / 'Library' / 'Application Support' / 'LiveCue' / 'logs'
        else:
            # Linux: ~/.local/share/LiveCue/logs
            base = Path.home() / '.local' / 'share' / 'LiveCue' / 'logs'
    else:
        # Modo desarrollo: carpeta local
        base = Path('logs')
    
    # Crear directorio si no existe
    base.mkdir(parents=True, exist_ok=True)
    return base


class LiveCueLogger:
    """Logger centralizado para LiveCue con gestión de sesiones"""
    
    def __init__(self, base_dir: str = None):
        # Usar AppData automáticamente si es ejecutable
        if base_dir is None:
            self.base_dir = get_logs_base_dir()
        else:
            self.base_dir = Path(base_dir)
        
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        
        # Estructura de directorios
        self.today_dir = self.base_dir / self.session_start.strftime("%Y-%m-%d")
        self.session_dir = self.today_dir / f"session_{self.session_id}"
        
        # Crear directorios
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar loggers
        self.main_logger = self._setup_main_logger()
        self.osc_logger = self._setup_module_logger("OSC", "osc.log")
        self.ui_logger = self._setup_module_logger("UI", "ui.log")
        self.playback_logger = self._setup_module_logger("Playback", "playback.log")
        self.error_logger = self._setup_error_logger()
        
        # Log de inicio de sesión
        self.main_logger.info("=" * 80)
        self.main_logger.info(f"🚀 LiveCue - Nueva sesión iniciada")
        self.main_logger.info(f"📅 Fecha: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        self.main_logger.info(f"🆔 Sesión ID: {self.session_id}")
        self.main_logger.info(f"💾 Logs guardados en: {self.session_dir}")
        self.main_logger.info("=" * 80)
    
    def _setup_main_logger(self) -> logging.Logger:
        """Logger principal de la aplicación"""
        logger = logging.getLogger("LiveCue")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
        # Formato detallado para archivos
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-15s | %(funcName)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Formato simple para consola
        console_formatter = logging.Formatter(
            '%(levelname)s | %(name)s | %(message)s'
        )
        
        # Handler para archivo principal de la sesión
        main_file = self.session_dir / "livecue_main.log"
        file_handler = RotatingFileHandler(
            main_file,
            maxBytes=10*1024*1024,  # 10MB por archivo
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Handler para consola (solo INFO y superior)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_module_logger(self, module_name: str, filename: str) -> logging.Logger:
        """Crea logger específico para un módulo"""
        logger = logging.getLogger(f"LiveCue.{module_name}")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Archivo específico del módulo
        module_file = self.session_dir / filename
        handler = RotatingFileHandler(
            module_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        return logger
    
    def _setup_error_logger(self) -> logging.Logger:
        """Logger dedicado solo a errores críticos"""
        logger = logging.getLogger("LiveCue.Errors")
        logger.setLevel(logging.ERROR)
        logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s\n'
            'Función: %(funcName)s (línea %(lineno)d)\n'
            'Mensaje: %(message)s\n'
            '-' * 80,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Archivo de errores
        error_file = self.session_dir / "errors.log"
        handler = logging.FileHandler(error_file, encoding='utf-8')
        handler.setLevel(logging.ERROR)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        return logger
    
    def log_exception(self, exc: Exception, context: str = ""):
        """Registra una excepción con contexto y traceback completo"""
        self.error_logger.error(
            f"{'[' + context + '] ' if context else ''}"
            f"{type(exc).__name__}: {exc}\n"
            f"Traceback:\n{''.join(traceback.format_tb(exc.__traceback__))}"
        )
    
    def create_session_summary(self):
        """Crea un resumen de la sesión al cerrar"""
        session_duration = datetime.now() - self.session_start
        
        summary_file = self.session_dir / "session_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RESUMEN DE SESIÓN - LiveCue\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"📅 Fecha inicio: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"📅 Fecha fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"⏱️  Duración: {session_duration}\n\n")
            
            # Contar errores
            error_file = self.session_dir / "errors.log"
            if error_file.exists():
                error_count = sum(1 for line in error_file.read_text(encoding='utf-8').split('\n') 
                                 if 'ERROR' in line or 'CRITICAL' in line)
                f.write(f"❌ Errores registrados: {error_count}\n")
            else:
                f.write("✅ Sin errores registrados\n")
            
            f.write("\n" + "=" * 80 + "\n")
        
        self.main_logger.info(f"📊 Resumen de sesión guardado en: {summary_file}")
    
    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Limpia logs antiguos (mantiene últimos N días)"""
        if not self.base_dir.exists():
            return
        
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 86400)
        deleted_count = 0
        
        for date_dir in self.base_dir.iterdir():
            if date_dir.is_dir():
                # Verificar si el directorio es más antiguo que cutoff
                if date_dir.stat().st_mtime < cutoff_date:
                    try:
                        import shutil
                        shutil.rmtree(date_dir)
                        deleted_count += 1
                        self.main_logger.info(f"🗑️  Logs antiguos eliminados: {date_dir.name}")
                    except Exception as e:
                        self.main_logger.warning(f"⚠️  No se pudo eliminar {date_dir}: {e}")
        
        if deleted_count > 0:
            self.main_logger.info(f"🧹 Limpieza completada: {deleted_count} directorio(s) eliminados")


# ============================================================================
# INSTANCIA GLOBAL
# ============================================================================

# Crear logger global
_logger_instance = None

def get_logger() -> LiveCueLogger:
    """Obtiene la instancia del logger (Singleton)"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LiveCueLogger()
        # Limpieza automática de logs antiguos al iniciar
        _logger_instance.cleanup_old_logs(days_to_keep=7)
    return _logger_instance


# ============================================================================
# HELPERS RÁPIDOS
# ============================================================================

def log_info(message: str, module: str = "Main"):
    """Helper para logs INFO"""
    logger = get_logger()
    getattr(logger, f"{module.lower()}_logger", logger.main_logger).info(message)

def log_warning(message: str, module: str = "Main"):
    """Helper para logs WARNING"""
    logger = get_logger()
    getattr(logger, f"{module.lower()}_logger", logger.main_logger).warning(message)

def log_error(message: str, module: str = "Main", exc: Exception = None):
    """Helper para logs ERROR"""
    logger = get_logger()
    target_logger = getattr(logger, f"{module.lower()}_logger", logger.main_logger)
    target_logger.error(message)
    if exc:
        logger.log_exception(exc, context=module)

def log_debug(message: str, module: str = "Main"):
    """Helper para logs DEBUG"""
    logger = get_logger()
    getattr(logger, f"{module.lower()}_logger", logger.main_logger).debug(message)


# ============================================================================
# DECORADOR PARA LOGGING AUTOMÁTICO
# ============================================================================

def log_function_call(module: str = "Main"):
    """Decorador para loguear llamadas a funciones automáticamente"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            target_logger = getattr(logger, f"{module.lower()}_logger", logger.main_logger)
            
            target_logger.debug(f"→ Llamando a {func.__name__}()")
            try:
                result = func(*args, **kwargs)
                target_logger.debug(f"✓ {func.__name__}() completado")
                return result
            except Exception as e:
                target_logger.error(f"✗ Error en {func.__name__}(): {e}")
                logger.log_exception(e, context=f"{module}.{func.__name__}")
                raise
        return wrapper
    return decorator
