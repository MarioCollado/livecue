# osc/web_server.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

"""
Servidor web Flask para control remoto desde móvil/tablet
Permite reproducir tracks, detener y controlar metrónomo vía HTTP
"""

from flask import Flask, render_template_string, request, jsonify
from ui.templates.controller_html import CONTROLLER_HTML
from core.logger import log_info, log_error, log_warning, log_debug
import threading
import socket
import time
from core.state import state 

# 🆕 DEBOUNCER para evitar múltiples plays rápidos
class PlaybackDebouncer:
    def __init__(self, delay=0.3):
        self.delay = delay
        self.last_play_time = 0
        self.lock = threading.Lock()
    
    def can_play(self):
        """Retorna True si ha pasado suficiente tiempo desde el último play"""
        with self.lock:
            now = time.time()
            if now - self.last_play_time > self.delay:
                self.last_play_time = now
                return True
            log_debug(f"⏱️  Play throttled (esperando {self.delay}s)", module="UI")
            return False
    
    def reset(self):
        """Resetea el timer (útil después de un stop)"""
        with self.lock:
            self.last_play_time = 0

play_debouncer = PlaybackDebouncer(delay=0.3)

class WebControllerServer:
    def __init__(self, playback_controller, state, port=5000):
        self.playback = playback_controller
        self.state = state
        self.port = port
        self.app = Flask(__name__)
        
        # Deshabilitar logs de Flask (muy verbose)
        import logging
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)
        
        self._setup_routes()
        log_debug(f"WebControllerServer inicializado (puerto {port})", module="UI")

    def _setup_routes(self):

        @self.app.route('/')
        def index():
            tracks = [(i, t) for i, t in enumerate(self.state.tracks)]
            log_debug(f"📱 Acceso web desde {request.remote_addr}", module="UI")
            return render_template_string(CONTROLLER_HTML, tracks=tracks)

        @self.app.route('/play', methods=['POST'])
        def play():
            try:
                index = int(request.form.get("index", 0))
                
                # 🆕 DEBOUNCE: Rechazar si es muy rápido
                if not play_debouncer.can_play():
                    log_warning(f"📱 Web: Play {index} rechazado (throttling)", module="UI")
                    return jsonify({"status": "throttled", "message": "Too fast, wait a moment"}), 429
                
                log_info(f"📱 Web: Play track {index} desde {request.remote_addr}", module="UI")

                def worker(idx):
                    try:
                        log_debug(f"Worker: Ejecutando play_track({idx})", module="UI")
                        
                        # 🆕 STOP PREVIO para limpiar cualquier reproducción
                        self.playback.stop()
                        time.sleep(0.1)  # Pequeña pausa
                        
                        ok = self.playback.play_track(idx)
                        log_debug(f"Worker: play_track({idx}) = {ok}", module="UI")
                    except Exception as e:
                        log_error(f"Worker: Error en play_track({idx})", module="UI", exc=e)
                    finally:
                        self.state.needs_ui_refresh = True

                threading.Thread(target=worker, args=(index,), daemon=True).start()
                return ("", 204)

            except Exception as e:
                log_error(f"Web: Error en /play", module="UI", exc=e)
                return "FAIL", 500

        @self.app.route('/stop', methods=['POST'])
        def stop():
            try:
                log_info(f"📱 Web: Stop desde {request.remote_addr}", module="UI")
                
                # 🆕 Resetear debouncer al hacer stop
                play_debouncer.reset()
                
                def worker():
                    try:
                        log_debug("Worker: Ejecutando stop", module="UI")
                        
                        # 🆕 STOP MÚLTIPLE para asegurar que mata todo
                        for _ in range(2):
                            self.playback.stop()
                            time.sleep(0.05)
                        
                        self.state.needs_ui_refresh = True
                        log_debug("Worker: Stop completado", module="UI")
                    except Exception as e:
                        log_error("Worker: Error en stop", module="UI", exc=e)

                threading.Thread(target=worker, daemon=True).start()
                return ("", 204)

            except Exception as e:
                log_error("Web: Error en /stop", module="UI", exc=e)
                return "FAIL", 500

        @self.app.route('/metronome', methods=['POST'])
        def toggle_metronome():
            """Toggle metrónomo - Retorna estado nuevo"""
            try:
                log_info(f"📱 Web: Toggle metrónomo desde {request.remote_addr}", module="UI")
                
                def worker():
                    log_debug("Worker: Toggle metrónomo", module="UI")
                    self.playback.toggle_metronome()
                    self.state.needs_ui_refresh = True

                threading.Thread(target=worker, daemon=True).start()
                
                # Esperar un poquito a que se actualice el estado
                time.sleep(0.05)
                
                # Retornar estado actual
                is_on = self.state.metronome_on
                log_debug(f"Metrónomo: {'ON' if is_on else 'OFF'}", module="UI")
                return jsonify({"state": is_on})

            except Exception as e:
                log_error("Web: Error en toggle metrónomo", module="UI", exc=e)
                return jsonify({"error": str(e)}), 500

        @self.app.route('/metronome/status', methods=['GET'])
        def metronome_status():
            """Consultar estado actual del metrónomo"""
            try:
                is_on = self.state.metronome_on
                return jsonify({"state": is_on})
            except Exception as e:
                log_error("Web: Error obteniendo estado metrónomo", module="UI", exc=e)
                return jsonify({"error": str(e)}), 500

        # 🆕 NUEVO ENDPOINT: Panic button
        @self.app.route('/panic', methods=['POST'])
        def panic_stop():
            """Stop de emergencia - mata todo"""
            try:
                log_warning(f"📱 Web: PANIC STOP desde {request.remote_addr}", module="UI")
                
                # Resetear debouncer
                play_debouncer.reset()
                
                def worker():
                    try:
                        # Stop múltiple agresivo
                        for i in range(3):
                            self.playback.stop()
                            time.sleep(0.05)
                        
                        self.state.is_playing = False
                        self.state.needs_ui_refresh = True
                        log_info("✓ Panic stop completado", module="UI")
                    except Exception as e:
                        log_error("Worker: Error en panic stop", module="UI", exc=e)
                
                threading.Thread(target=worker, daemon=True).start()
                return jsonify({"status": "ok", "message": "Panic stop executed"})
                
            except Exception as e:
                log_error("Web: Error en panic stop", module="UI", exc=e)
                return jsonify({"error": str(e)}), 500

    def start(self):
        def get_wifi_ip():
            """Obtiene la IP local (funciona sin Internet)"""
            import re
            
            def is_valid_ip(ip):
                """Filtra IPs inválidas"""
                if not ip or ip.startswith("127."):
                    return False
                if ip.startswith("169.254."):
                    return False
                if ip.startswith("172.17.") or ip.startswith("172.18."):
                    return False
                if ip.startswith("100."):  # Tailscale
                    return False
                return True
            
            def is_virtual_adapter(adapter_name):
                """Detecta si es un adaptador virtual"""
                if not adapter_name:
                    return False
                adapter_lower = adapter_name.lower()
                virtual_keywords = [
                    'virtualbox', 'vmware', 'vbox', 'vethernet',
                    'hyper-v', 'docker', 'wsl', 'loopback'
                ]
                return any(keyword in adapter_lower for keyword in virtual_keywords)
            
            def prioritize_ip(ip):
                """Asigna prioridad a las IPs (menor = mejor)"""
                if ip.startswith("192.168.") or ip.startswith("10."):
                    # Evitar rangos de VirtualBox (192.168.56.x, 192.168.99.x)
                    parts = ip.split(".")
                    if len(parts) >= 3:
                        third_octet = int(parts[2])
                        if third_octet in [56, 99]:  # VirtualBox común
                            return 10  # Baja prioridad
                    return 1
                if ip.startswith("172."):
                    parts = ip.split(".")
                    if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
                        return 1
                return 2
            
            # Método 1: netifaces
            try:
                import netifaces
                all_ips = []
                for interface in netifaces.interfaces():
                    # Filtrar interfaces virtuales por nombre
                    if is_virtual_adapter(interface):
                        continue
                    
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            ip = addr.get('addr')
                            if is_valid_ip(ip):
                                all_ips.append(ip)
                
                if all_ips:
                    all_ips.sort(key=prioritize_ip)
                    return all_ips[0]
            except ImportError:
                pass
            except Exception:
                pass
            
            # Método 2: Comandos del sistema
            try:
                import platform
                import subprocess
                if platform.system() == "Windows":
                    result = subprocess.run(
                        ["ipconfig"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        all_ips = []
                        current_adapter = None
                        
                        for line in result.stdout.split('\n'):
                            # Detectar nombre del adaptador
                            if "adaptador" in line.lower() or "adapter" in line.lower():
                                current_adapter = line.strip()
                            
                            # Buscar IPv4
                            elif "IPv4" in line or "Dirección IPv4" in line:
                                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                                if match:
                                    ip = match.group(1)
                                    # Filtrar si el adaptador es virtual
                                    if current_adapter and is_virtual_adapter(current_adapter):
                                        continue
                                    if is_valid_ip(ip):
                                        all_ips.append(ip)
                        
                        if all_ips:
                            all_ips.sort(key=prioritize_ip)
                            return all_ips[0]
                else:
                    for cmd in [["ip", "-4", "addr"], ["ifconfig"]]:
                        try:
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=2
                            )
                            if result.returncode == 0:
                                all_ips = []
                                for match in re.finditer(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout):
                                    ip = match.group(1)
                                    if is_valid_ip(ip):
                                        all_ips.append(ip)
                                
                                if all_ips:
                                    all_ips.sort(key=prioritize_ip)
                                    return all_ips[0]
                        except (FileNotFoundError, subprocess.TimeoutExpired):
                            continue
            except Exception:
                pass
            
            # Método 3: Fallback antiguo
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                if is_valid_ip(ip):
                    return ip
            except Exception:
                pass
            
            return "127.0.0.1"
        
        def get_tailscale_ip():
            """Detecta IP de Tailscale"""
            try:
                import subprocess
                result = subprocess.run(
                    ["tailscale", "ip", "-4"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout.strip().startswith("100."):
                    return result.stdout.strip()
            except:
                pass
            return None

        def run():
            try:
                log_info(f"🌐 Iniciando servidor Flask en 0.0.0.0:{self.port}", module="UI")
                self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
            except Exception as e:
                log_error("Error en servidor Flask", module="UI", exc=e)

        local_ip = get_wifi_ip()
        tailscale_ip = get_tailscale_ip()
        
        log_debug(f"IP Local WiFi: {local_ip}", module="UI")
        if tailscale_ip:
            log_debug(f"IP Tailscale: {tailscale_ip}", module="UI")
        
        threading.Thread(target=run, daemon=True).start()

        log_info("=" * 70, module="UI")
        log_info("🌐 Servidor Web Control Remoto Disponible:", module="UI")
        log_info(f"   📱 Local WiFi:    http://{local_ip}:{self.port}", module="UI")
        if tailscale_ip:
            log_info(f"   🔒 Tailscale VPN: http://{tailscale_ip}:{self.port}", module="UI")
        log_info("   💡 Abre desde tu móvil/tablet en la misma red", module="UI")
        log_info("=" * 70, module="UI")