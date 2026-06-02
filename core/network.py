"""Utilidades de red compartidas por LiveCue."""

from __future__ import annotations

import re
import socket
import subprocess


def _is_valid_ip(ip: str) -> bool:
    if not ip or ip.startswith("127."):
        return False
    if ip.startswith("169.254."):
        return False
    if ip.startswith("172.17.") or ip.startswith("172.18."):
        return False
    if ip.startswith("100."):
        return False
    return True


def _is_virtual_adapter(adapter_name: str) -> bool:
    if not adapter_name:
        return False
    adapter_lower = adapter_name.lower()
    virtual_keywords = [
        "virtualbox",
        "vmware",
        "vbox",
        "vethernet",
        "hyper-v",
        "docker",
        "wsl",
        "loopback",
    ]
    return any(keyword in adapter_lower for keyword in virtual_keywords)


def _prioritize_ip(ip: str) -> int:
    if ip.startswith("192.168.") or ip.startswith("10."):
        parts = ip.split(".")
        if len(parts) >= 3:
            third_octet = int(parts[2])
            if third_octet in [56, 99]:
                return 10
        return 1
    if ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
            return 1
    return 2


def get_local_ip() -> str:
    """Obtiene la IP local prioritaria sin depender de Internet."""

    try:
        import netifaces

        all_ips = []
        for interface in netifaces.interfaces():
            if _is_virtual_adapter(interface):
                continue

            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get("addr")
                    if _is_valid_ip(ip):
                        all_ips.append(ip)

        if all_ips:
            all_ips.sort(key=_prioritize_ip)
            return all_ips[0]
    except ImportError:
        pass
    except Exception:
        pass

    try:
        result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            all_ips = []
            current_adapter = None

            for line in result.stdout.split("\n"):
                if "adaptador" in line.lower() or "adapter" in line.lower():
                    current_adapter = line.strip()
                elif "IPv4" in line or "Dirección IPv4" in line:
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                    if match:
                        ip = match.group(1)
                        if current_adapter and _is_virtual_adapter(current_adapter):
                            continue
                        if _is_valid_ip(ip):
                            all_ips.append(ip)

            if all_ips:
                all_ips.sort(key=_prioritize_ip)
                return all_ips[0]
    except Exception:
        pass

    try:
        for cmd in [["ip", "-4", "addr"], ["ifconfig"]]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    all_ips = []
                    for match in re.finditer(r"inet (\d+\.\d+\.\d+\.\d+)", result.stdout):
                        ip = match.group(1)
                        if _is_valid_ip(ip):
                            all_ips.append(ip)

                    if all_ips:
                        all_ips.sort(key=_prioritize_ip)
                        return all_ips[0]
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if _is_valid_ip(ip):
            return ip
    except Exception:
        pass

    return "127.0.0.1"


def get_tailscale_ip() -> str | None:
    """Obtiene la IP de Tailscale si está disponible."""

    try:
        result = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            if ip.startswith("100."):
                return ip
    except Exception:
        pass

    try:
        import platform

        if platform.system() == "Windows":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                in_tailscale = False
                for line in lines:
                    if "Tailscale" in line or "tailscale" in line:
                        in_tailscale = True
                    elif in_tailscale and "IPv4" in line:
                        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                        if match:
                            ip = match.group(1)
                            if ip.startswith("100."):
                                return ip
                    elif in_tailscale and line.strip() == "":
                        in_tailscale = False
        else:
            result = subprocess.run(["ip", "-4", "addr", "show", "tailscale0"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
    except Exception:
        pass

    return None
