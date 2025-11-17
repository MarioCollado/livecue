# core/license.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0

"""Sistema de licencias y periodo de prueba para LiveCue"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from core.logger import log_info, log_warning, log_error, log_debug


class LicenseManager:
    """Gestor de licencias con periodo de prueba"""
    
    TRIAL_DAYS = 14  # Días de prueba
    
    def __init__(self):
        self.license_file = self._get_license_path()
        self.license_data = self._load_license()
    
    def _get_license_path(self) -> Path:
        """Obtiene la ruta del archivo de licencia (en AppData)"""
        if sys.platform == 'win32':
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            base = Path(appdata) / 'LiveCue'
        elif sys.platform == 'darwin':
            base = Path.home() / 'Library' / 'Application Support' / 'LiveCue'
        else:
            base = Path.home() / '.local' / 'share' / 'LiveCue'
        
        base.mkdir(parents=True, exist_ok=True)
        return base / '.license'
    
    def _load_license(self) -> dict:
        """Carga o crea el archivo de licencia"""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                log_debug(f"Licencia cargada: {data.get('status', 'unknown')}")
                return data
            except Exception as e:
                log_warning(f"Error leyendo licencia: {e}")
        
        # Primera ejecución - crear trial
        data = {
            'status': 'trial',
            'first_run': datetime.now().isoformat(),
            'hardware_id': self._get_hardware_id()
        }
        self._save_license(data)
        log_info("🎁 Periodo de prueba iniciado")
        return data
    
    def _save_license(self, data: dict):
        """Guarda el archivo de licencia"""
        try:
            with open(self.license_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            log_error(f"Error guardando licencia: {e}")
    
    def _get_hardware_id(self) -> str:
        """Genera ID único del hardware (simple)"""
        import platform
        import uuid
        
        # Combinar varios identificadores
        machine_id = platform.node()  # Nombre del PC
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                       for i in range(0, 48, 8)])
        
        # Hash para ofuscar
        combined = f"{machine_id}-{mac}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def check_license(self) -> tuple[bool, str, int]:
        """
        Verifica el estado de la licencia
        Returns: (is_valid, message, days_remaining)
        """
        status = self.license_data.get('status')
        
        # Licencia activada
        if status == 'activated':
            key = self.license_data.get('license_key', 'N/A')
            log_debug(f"Licencia activada: {key}")
            return True, "Licencia activada ✓", -1
        
        # Periodo de prueba
        if status == 'trial':
            first_run = datetime.fromisoformat(self.license_data['first_run'])
            elapsed = datetime.now() - first_run
            days_remaining = self.TRIAL_DAYS - elapsed.days
            
            if days_remaining > 0:
                log_info(f"⏱️  Periodo de prueba: {days_remaining} días restantes")
                return True, f"Periodo de prueba: {days_remaining} días restantes", days_remaining
            else:
                log_warning("⏰ Periodo de prueba expirado")
                return False, "Periodo de prueba expirado", 0
        
        # Sin licencia válida
        return False, "Licencia inválida", 0
    
    def activate_license(self, license_key: str) -> bool:
        """
        Activa una licencia
        En producción, esto debería validar contra un servidor
        """
        # Validar formato básico
        if not license_key or len(license_key) < 16:
            log_error("Clave de licencia inválida")
            return False
        
        # Validar contra tu sistema (aquí implementa tu lógica)
        if self._validate_license_key(license_key):
            self.license_data['status'] = 'activated'
            self.license_data['license_key'] = license_key
            self.license_data['activation_date'] = datetime.now().isoformat()
            self._save_license(self.license_data)
            
            log_info(f"✅ Licencia activada correctamente")
            return True
        
        log_error("❌ Clave de licencia inválida")
        return False
    
    def _validate_license_key(self, key: str) -> bool:
        """
        Valida una clave de licencia
        IMPLEMENTA TU LÓGICA AQUÍ:
        - Validar contra base de datos
        - Validar contra servidor API
        - Validar checksum
        - Validar hardware_id
        """
        # Ejemplo simple: validar formato
        # En producción: llamar a tu API de validación
        
        # Clave de desarrollador (solo para ti)
        if key == "LIVECUE-DEV-UNLIMITED-2025":
            return True
        
        # Aquí implementarías validación real:
        # - Llamar a tu servidor
        # - Verificar en base de datos
        # - Validar firma digital
        
        # Ejemplo de validación simple (cambiar por tu sistema)
        expected_checksum = hashlib.sha256(
            (key + self.license_data['hardware_id']).encode()
        ).hexdigest()[:8]
        
        # Por ahora, aceptar claves que empiecen con LIVECUE-
        return key.startswith("LIVECUE-")
    
    def get_purchase_info(self) -> dict:
        """Información de compra para mostrar al usuario"""
        return {
            'email': 'mcolladorguez@gmail.com',
            'website': 'https://github.com/MarioCollado/LiveCue',
            'price': '29.99 EUR',  # Ajusta el precio
            'hardware_id': self.license_data.get('hardware_id', 'N/A')
        }


# Instancia global
_license_manager = None

def get_license_manager() -> LicenseManager:
    """Obtiene la instancia del gestor de licencias (Singleton)"""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager