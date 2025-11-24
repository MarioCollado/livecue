# core/license.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0

import sys
import os
import json
import hashlib
import platform
import uuid
from pathlib import Path
from datetime import datetime
from core.logger import log_info, log_warning, log_error, log_debug

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
    
    def check_license(self) -> tuple[bool, str, int]:
        status = self.data.get('status')
        
        if status == 'activated':
            return True, "Activated", -1
        
        if status == 'trial':
            start = datetime.fromisoformat(self.data['first_run'])
            days_left = self.TRIAL_DAYS - (datetime.now() - start).days
            
            if days_left > 0:
                return True, f"Trial: {days_left} days left", days_left
            
            return False, "Trial expired", 0
        
        return False, "Invalid license", 0
    
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
        if key == "LIVECUE-DEV-UNLIMITED-2025":
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

_instance = None

def get_license_manager() -> LicenseManager:
    global _instance
    if not _instance:
        _instance = LicenseManager()
    return _instance