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
from core.state import state 

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
                log_info(f"📱 Web: Play track {index} desde {request.remote_addr}", module="UI")

                def worker(idx):
                    try:
                        log_debug(f"Worker: Ejecutando play_track({idx})", module="UI")
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
                
                def worker():
                    log_debug("Worker: Ejecutando stop", module="UI")
                    self.playback.stop()
                    self.state.needs_ui_refresh = True

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
                import time
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

    def start(self):
        def get_wifi_ip():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            finally:
                s.close()
            return ip
        
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