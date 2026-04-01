# core/license.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0

import sys
import os
import json
import hashlib
import platform
import uuid
from pathlib import Path
from datetime import datetime
from core.logger import log_info, log_warning, log_error, log_debug
from core.i18n import i18n

class LicenseManager:
    TRIAL_DAYS = 14
    
    def __init__(self):
        self.license_file = self._get_license_path()
        self.data = self._load()
    
    def _get_license_path(self) -> Path:
        if sys.platform == 'win32':
            base = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'LiveCue'
        elif sys.platform == 'darwin':
            base = Path.home() / 'Library' / 'Application Support' / 'LiveCue'
        else:
            base = Path.home() / '.local' / 'share' / 'LiveCue'
        
        base.mkdir(parents=True, exist_ok=True)
        return base / '.license'
    
    def _load(self) -> dict:
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log_warning(f"Corrupt license file: {e}")
        
        # Init trial
        data = {
            'status': 'trial',
            'first_run': datetime.now().isoformat(),
            'hwid': self._get_hwid()
        }
        self._save(data)
        log_info("Trial period started")
        return data
    
    def _save(self, data: dict):
        try:
            with open(self.license_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            log_error(f"Failed to save license: {e}")
    
    def _get_hwid(self) -> str:
        machine = platform.node()
        mac = uuid.getnode()
        raw = f"{machine}-{mac}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    def check_license(self):
        status = self.data.get('status')

        # Activated
        if status == 'activated':
            return True, "valid", 9999  # o 0, como prefieras

        # Trial
        if status == 'trial':
            start = datetime.fromisoformat(self.data['first_run'])
            days_left = self.TRIAL_DAYS - (datetime.now() - start).days

            if days_left > 0:
                return False, "trial", days_left

            return False, "expired", 0

        # Invalid
        return False, "invalid", 0

    def get_days_remaining(self) -> int:
        if self.data.get('status') == 'trial':
            start = datetime.fromisoformat(self.data['first_run'])
            days_left = self.TRIAL_DAYS - (datetime.now() - start).days
            return max(0, days_left)
        return 0
    
    def activate(self, key: str) -> bool:
        if not key or len(key) < 16:
            return False
        
        if self._validate_key(key):
            self.data.update({
                'status': 'activated',
                'key': key,
                'activated_at': datetime.now().isoformat()
            })
            self._save(self.data)
            log_info("License activated")
            return True
        
        log_error("Invalid license key")
        return False
    
    def _validate_key(self, key: str) -> bool:
        # Dev override
        if key == "LIVECUE-DEV-UNLIMITED-2026":
            return True
            
        # Basic format check for now
        return key.startswith("LIVECUE-") and len(key) >= 20

    @property
    def info(self) -> dict:
        return {
            'email': 'mcolladorguez@gmail.com',
            'website': 'https://github.com/MarioCollado/LiveCue',
            'hwid': self.data.get('hwid', 'N/A')
        }

    def get_purchase_info(self):
        """Devuelve información para la compra de la licencia."""
        return {
            'email': 'mcolladorguez@gmail.com',
            'website': 'https://github.com/MarioCollado/LiveCue',
            'price': 'Consultar / Consult',
            'hardware_id': self.data.get('hwid', 'N/A')
        }

    def get_status_message(self):
        """Devuelve un mensaje de estado legible."""
        is_valid, status, days_left = self.check_license()
        
        if status == "valid":
            return i18n.get("license_valid")
            
        if status == "trial":
            return i18n.get("license_trial", days_left)
            
        if status == "expired":
            return i18n.get("license_expired")
            
        return i18n.get("license_invalid")

# Instancia global
license_manager = LicenseManager()