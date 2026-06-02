"""Servidor web Flask para control remoto desde móvil/tablet."""

from __future__ import annotations

import platform
import subprocess
import threading
import time

from core.constants import FLASK_PORT
from core.logger import log_debug, log_error, log_info, log_warning
from core.network import get_local_ip, get_tailscale_ip
from ui.templates.controller_html import CONTROLLER_HTML

try:
    from flask import Flask, jsonify, render_template_string, request
except ImportError:
    Flask = None

    def jsonify(*args, **kwargs):
        return args[0] if args else {}

    def render_template_string(template, **kwargs):
        return template

    class _DummyRequest:
        remote_addr = "127.0.0.1"
        form = {}

    request = _DummyRequest()


class PlaybackDebouncer:
    def __init__(self, delay=0.3):
        self.delay = delay
        self.last_play_time = 0
        self.lock = threading.Lock()

    def can_play(self):
        with self.lock:
            now = time.time()
            if now - self.last_play_time > self.delay:
                self.last_play_time = now
                return True
            log_debug(f"⏱️  Play throttled (esperando {self.delay}s)", module="UI")
            return False

    def reset(self):
        with self.lock:
            self.last_play_time = 0


class MetronomeDebouncer:
    def __init__(self, delay=0.3):
        self.delay = delay
        self.last_toggle_time = 0
        self.lock = threading.Lock()

    def can_toggle(self):
        with self.lock:
            now = time.time()
            if now - self.last_toggle_time > self.delay:
                self.last_toggle_time = now
                return True
            log_debug(f"⏱️  Metronome toggle throttled (esperando {self.delay}s)", module="UI")
            return False


play_debouncer = PlaybackDebouncer(delay=0.3)
metronome_debouncer = MetronomeDebouncer(delay=0.3)


class WebControllerServer:
    def __init__(self, playback_controller, state, port=FLASK_PORT):
        self.playback = playback_controller
        self.state = state
        self.port = port
        self.app = Flask(__name__) if Flask is not None else None

        import logging

        logging.getLogger("werkzeug").setLevel(logging.ERROR)

        if self.app is not None:
            self._setup_routes()
        else:
            log_warning("Flask no está instalado; el servidor web quedará deshabilitado.", module="UI")

        log_debug(f"WebControllerServer inicializado (puerto {port})", module="UI")

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            tracks = [(i, t) for i, t in enumerate(self.state.tracks)]
            log_debug(f"📱 Acceso web desde {request.remote_addr}", module="UI")
            return render_template_string(CONTROLLER_HTML, tracks=tracks)

        @self.app.route("/play", methods=["POST"])
        def play():
            try:
                index = int(request.form.get("index", 0))

                if not play_debouncer.can_play():
                    log_warning(f"📱 Web: Play {index} rechazado (throttling)", module="UI")
                    return jsonify({"status": "throttled", "message": "Too fast, wait a moment"}), 429

                log_info(f"📱 Web: Play track {index} desde {request.remote_addr}", module="UI")

                def worker(idx):
                    try:
                        log_debug(f"Worker: Ejecutando play_track({idx})", module="UI")
                        self.playback.stop()
                        time.sleep(0.1)
                        ok = self.playback.play_track(idx)
                        log_debug(f"Worker: play_track({idx}) = {ok}", module="UI")
                    except Exception as e:
                        log_error(f"Worker: Error en play_track({idx})", module="UI", exc=e)
                    finally:
                        self.state.needs_ui_refresh = True

                threading.Thread(target=worker, args=(index,), daemon=True).start()
                return ("", 204)
            except Exception as e:
                log_error("Web: Error en /play", module="UI", exc=e)
                return "FAIL", 500

        @self.app.route("/stop", methods=["POST"])
        def stop():
            try:
                log_info(f"📱 Web: Stop desde {request.remote_addr}", module="UI")
                play_debouncer.reset()

                def worker():
                    try:
                        log_debug("Worker: Ejecutando stop", module="UI")
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

        @self.app.route("/metronome", methods=["POST"])
        def toggle_metronome():
            try:
                log_info(f"📱 Web: Toggle metrónomo desde {request.remote_addr}", module="UI")

                if not metronome_debouncer.can_toggle():
                    log_warning("📱 Web: Metrónomo throttled (esperar)", module="UI")
                    is_on = self.state.metronome_on
                    return jsonify({"state": is_on})

                def worker():
                    log_debug("Worker: Toggle metrónomo", module="UI")
                    try:
                        self.playback.toggle_metronome()
                        self.state.needs_ui_refresh = True
                    except Exception as e:
                        log_error("Worker: Error en toggle metrónomo", module="UI", exc=e)

                threading.Thread(target=worker, daemon=True).start()
                time.sleep(0.05)

                is_on = self.state.metronome_on
                log_debug(f"Metrónomo: {'ON' if is_on else 'OFF'}", module="UI")
                return jsonify({"state": is_on})
            except Exception as e:
                log_error("Web: Error en toggle metrónomo", module="UI", exc=e)
                return jsonify({"error": str(e)}), 500

        @self.app.route("/metronome/status", methods=["GET"])
        def metronome_status():
            try:
                return jsonify({"state": self.state.metronome_on})
            except Exception as e:
                log_error("Web: Error obteniendo estado metrónomo", module="UI", exc=e)
                return jsonify({"error": str(e)}), 500

        @self.app.route("/panic", methods=["POST"])
        def panic_stop():
            try:
                log_warning(f"📱 Web: PANIC STOP desde {request.remote_addr}", module="UI")
                play_debouncer.reset()

                def worker():
                    try:
                        for _ in range(3):
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

    def _ensure_firewall_rule(self):
        if platform.system() != "Windows":
            return

        rule_name = f"LiveCue Web Server (TCP {self.port})"

        try:
            check = subprocess.run(
                ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if check.returncode == 0 and rule_name in check.stdout:
                log_debug(f"✓ Regla de firewall ya existe: {rule_name}", module="UI")
                return
        except Exception:
            pass

        log_info(f"🔐 Solicitando permisos para abrir puerto {self.port} en el firewall...", module="UI")

        cmd_args = (
            f'advfirewall firewall add rule name="{rule_name}" '
            f"dir=in action=allow protocol=TCP localport={self.port} "
            f'profile=private,public '
            f'description="LiveCue - Control remoto desde movil/tablet"'
        )

        try:
            import ctypes

            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", "netsh", cmd_args, None, 0)
            if ret > 32:
                time.sleep(1)
                log_info(f"🔒 Regla de firewall creada correctamente: {rule_name}", module="UI")
            else:
                log_warning(
                    f"⚠️  No se pudo crear la regla de firewall (código: {ret}).\n"
                    f"    Para conectar desde el móvil, ejecuta manualmente como administrador:\n"
                    f"    netsh {cmd_args}",
                    module="UI",
                )
        except Exception as e:
            log_warning(
                f"⚠️  Error configurando firewall: {e}\n"
                f"    Para conectar desde el móvil, abre el puerto {self.port} manualmente\n"
                f"    en el Firewall de Windows (Configuración > Firewall > Reglas de entrada).",
                module="UI",
            )

    def start(self):
        if self.app is None:
            log_warning("Servidor web deshabilitado porque Flask no está instalado.", module="UI")
            return

        self._ensure_firewall_rule()

        def run():
            try:
                log_info(f"🌐 Iniciando servidor Flask en 0.0.0.0:{self.port}", module="UI")
                self.app.run(host="0.0.0.0", port=self.port, debug=False, use_reloader=False)
            except Exception as e:
                log_error("Error en servidor Flask", module="UI", exc=e)

        local_ip = get_local_ip()
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
