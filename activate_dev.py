import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from core.license import license_manager

print("--- License Debug Info ---")
print(f"Data keys: {list(license_manager.data.keys())}")
print(f"HWID (hwid): {license_manager.data.get('hwid')}")
print(f"HWID (hardware_id): {license_manager.data.get('hardware_id')}")

# Fix missing hwid if necessary
if 'hwid' not in license_manager.data and 'hardware_id' in license_manager.data:
    print("Migrating hardware_id to hwid...")
    license_manager.data['hwid'] = license_manager.data['hardware_id']

# Activate
print("\nActivating Dev License...")
key = "LIVECUE-DEV-UNLIMITED-2025"
success = license_manager.activate(key)

if success:
    print("✅ License activated successfully!")
else:
    print("❌ Activation failed.")
