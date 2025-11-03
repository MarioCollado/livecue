# ui/web_server.py
from flask import Flask, render_template_string, request
from ui.templates.controller_html import CONTROLLER_HTML

import threading
import socket
from core.state import state 

class WebControllerServer:
    def __init__(self, playback_controller, state, port=5000):
        self.playback = playback_controller
        self.state = state
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):

        @self.app.route('/')
        def index():
            tracks = [(i, t) for i, t in enumerate(self.state.tracks)]
            return render_template_string(CONTROLLER_HTML, tracks=tracks)

        @self.app.route('/play', methods=['POST'])
        def play():
            try:
                index = int(request.form.get("index", 0))

                def worker(idx):
                    try:
                        print(f"[WEB->WORKER] ▶ Ejecutando play_track({idx}) en thread")
                        ok = self.playback.play_track(idx)
                        print(f"[WEB->WORKER] ✅ play_track({idx}) terminado ({ok})")
                    except Exception as e:
                        print(f"[WEB->WORKER] ❌ Error: {e}")
                    finally:
                        # Marcar que la UI necesita refrescarse
                        self.state.needs_ui_refresh = True

                threading.Thread(target=worker, args=(index,), daemon=True).start()

                # No redirigir ni cargar nueva página: solo devolver respuesta vacía
                return ("", 204)

            except Exception as e:
                print(f"[WEB] Error: {e}")
                return "FAIL", 500
            
        @self.app.route('/stop', methods=['POST'])
        def stop():
            try:
                def worker():
                    print("[WEB->WORKER] ⏹ Ejecutando stop en thread")
                    self.playback.stop()
                    self.state.needs_ui_refresh = True
                threading.Thread(target=worker, daemon=True).start()
                return ("", 204)  # Respuesta vacía OK sin recargar página
            except Exception as e:
                print(f"[WEB] Error en stop: {e}")
                return "FAIL", 500
            

    def start(self):
        import socket

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
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

        local_ip = get_wifi_ip()
        tailscale_ip = get_tailscale_ip()
        
        threading.Thread(target=run, daemon=True).start()

        print(f"\n[WEB] 🌐 Servidor Flask disponible en:")
        print(f"      📱 Local WiFi:    http://{local_ip}:{self.port}")
        if tailscale_ip:
            print(f"      🔒 Tailscale VPN: http://{tailscale_ip}:{self.port}")
        print(f"      💡 Abre cualquiera desde tu móvil/tablet\n")