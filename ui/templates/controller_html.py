# ui/templates/controller_ui.py
# Copyright (c) 2026 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

CONTROLLER_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ableton Remote</title>  <style>
    /* === PALETA NEUTRA — LEGIBLE EN EXTERIORES === */
    :root {
      --bg-base:      #1a1d22;
      --bg-surface:   #22262e;
      --bg-elevated:  #2a2f3a;
      --border:       rgba(180, 195, 220, 0.14);
      --border-strong: rgba(180, 195, 220, 0.28);
      --text-primary: #f0f2f5;
      --text-secondary: #9aa5b4;
      --accent:       #5b8dee;
      --accent-muted: rgba(91, 141, 238, 0.18);
      --stop-bg:      #c0392b;
      --stop-bg-hover:#e74c3c;
      --metro-bg:     #4a5568;
      --metro-on:     #27ae60;
    }

    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      min-height: 100dvh;
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-base);
      color: var(--text-primary);
      overflow-x: hidden;
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
      position: relative;
    }

    body {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0;
      box-sizing: border-box;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }

    /* HEADER STICKY */
    .header {
      position: sticky;
      top: 0;
      left: 0;
      right: 0;
      z-index: 1000;
      background: rgba(26, 29, 34, 0.97);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
      padding: 16px 14px 14px;
      width: 100%;
      box-sizing: border-box;
    }

    h1 {
      margin: 0 0 14px 0;
      font-size: 1.6em;
      color: var(--text-primary);
      letter-spacing: 1px;
      text-transform: uppercase;
      font-weight: 700;
      text-align: center;
      user-select: none;
    }

    /* CONTROLES STICKY */
    .controls-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      width: 100%;
      max-width: 600px;
      margin: 0 auto;
    }

    .control-btn {
      width: 100%;
      box-sizing: border-box;
      background: var(--bg-elevated);
      border: 1.5px solid var(--border-strong);
      border-radius: 10px;
      color: var(--text-primary);
      font-size: 1.05em;
      font-weight: 700;
      padding: 20px 10px;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0,0,0,0.28);
      transition: transform 0.15s ease, background 0.2s ease, box-shadow 0.2s ease;
      will-change: transform;
      -webkit-user-select: none;
      user-select: none;
      min-width: 110px;
    }

    .control-btn:active {
      transform: scale(0.96);
      transition-duration: 0.05s;
    }

    #stop-btn {
      background: var(--stop-bg);
      border-color: rgba(192, 57, 43, 0.6);
    }

    #stop-btn:hover {
      background: var(--stop-bg-hover);
      box-shadow: 0 0 10px rgba(231, 76, 60, 0.45);
      transform: scale(1.02);
    }

    #metro-btn {
      background: var(--metro-bg);
      border-color: rgba(100, 116, 139, 0.45);
    }

    #metro-btn:hover {
      background: #5a6a80;
      box-shadow: 0 0 8px rgba(90, 106, 128, 0.4);
      transform: scale(1.02);
    }

    #metro-btn.active {
      background: var(--metro-on);
      border-color: rgba(39, 174, 96, 0.55);
      animation: pulse 1.5s ease-in-out infinite;
    }

    #metro-btn.active:hover {
      background: #219a52;
      box-shadow: 0 0 12px rgba(39, 174, 96, 0.6);
    }

    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 6px rgba(39, 174, 96, 0.35); }
      50% { box-shadow: 0 0 14px rgba(39, 174, 96, 0.7); }
    }

    /* CONTENEDOR DE TRACKS CON SCROLL */
    .tracks-container {
      flex: 1;
      width: 100%;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 18px 16px 48px;
      box-sizing: border-box;
      max-height: 100dvh;
    }

    /* GRID DE TRACKS — 1 COLUMNA CENTRADA (no ocupa todo el ancho en móvil) */
    .grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
      width: 85%;
      max-width: 420px;
      margin: 0 auto;
    }

    .track-btn {
      height: 86px;
      min-height: 86px;
      max-height: 86px;

      background: var(--bg-surface);
      border: 1.5px solid var(--border);
      border-radius: 10px;
      color: var(--text-primary);
      font-size: 0.9em;
      font-weight: 600;
      padding: 10px 8px;
      cursor: pointer;
      width: 100%;
      box-shadow: 0 2px 6px rgba(0,0,0,0.22);
      transition: transform 0.15s ease, background 0.2s ease, box-shadow 0.2s ease;
      will-change: transform;
      -webkit-user-select: none;
      user-select: none;

      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      word-wrap: break-word;
      overflow-wrap: break-word;
      hyphens: auto;
      line-height: 1.25;

      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
    }

    .track-btn:hover,
    .track-btn:focus-visible {
      background: var(--bg-elevated);
      border-color: var(--border-strong);
      transform: scale(1.02);
      box-shadow: 0 0 8px rgba(91, 141, 238, 0.22);
    }

    .track-btn:active {
      transform: scale(0.96);
      background: var(--accent-muted);
      border-color: rgba(91, 141, 238, 0.4);
      transition-duration: 0.05s;
    }

    form {
      width: 100%;
      margin: 0;
      height: 86px;
    }

    /* FOOTER FIJO */
    footer {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      text-align: center;
      font-size: 0.72em;
      opacity: 0.5;
      color: var(--text-secondary);
      pointer-events: none;
      background: linear-gradient(0deg, rgba(26, 29, 34, 0.92) 0%, transparent 100%);
      padding: 10px 0;
    }

    /* MÓVILES PEQUEÑOS */
    @media (max-width: 480px) {
      h1 {
        font-size: 1.35em;
        margin-bottom: 12px;
      }

      .header {
        padding: 12px 12px 12px;
      }

      .controls-row {
        gap: 8px;
      }

      .control-btn {
        font-size: 1em;
        padding: 18px 8px;
        min-width: 100px;
      }

      .tracks-container {
        padding: 14px 10px 60px;
      }

      .grid {
        gap: 8px;
        grid-template-columns: 1fr;
      }

      .track-btn {
        height: 78px;
        min-height: 78px;
        max-height: 78px;
        font-size: 0.84em;
        padding: 8px 6px;
      }

      form {
        height: 78px;
      }
    }

    /* TABLETS Y PANTALLAS MEDIANAS */
    @media (min-width: 600px) and (max-width: 1024px) {
      h1 {
        font-size: 1.75em;
        margin-bottom: 16px;
      }

      .header {
        padding: 20px 24px 16px;
      }

      .controls-row {
        gap: 14px;
        max-width: 650px;
      }

      .control-btn {
        font-size: 1.15em;
        padding: 22px 16px;
        min-width: 140px;
      }

      .tracks-container {
        padding: 22px 24px 80px;
      }

      .grid {
        gap: 14px;
        max-width: 480px;
        grid-template-columns: 1fr;
      }

      .track-btn {
        height: 100px;
        min-height: 100px;
        max-height: 100px;
        font-size: 1em;
        padding: 12px 10px;
      }

      form {
        height: 100px;
      }
    }

    /* PANTALLAS GRANDES — MÚLTIPLES COLUMNAS */
    @media (min-width: 1025px) {
      .header {
        padding: 22px 32px 16px;
      }

      .controls-row {
        max-width: 700px;
        gap: 16px;
      }

      .control-btn {
        font-size: 1.2em;
        padding: 16px 16px;
      }

      .tracks-container {
        padding: 26px 32px 90px;
      }

      .grid {
        max-width: 700px;
        gap: 16px;
        grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
      }

      .track-btn {
        height: 108px;
        min-height: 108px;
        max-height: 108px;
        font-size: 1.05em;
      }

      form {
        height: 108px;
      }
    }

    @supports (height: 100dvh) {
      body {
        height: 100dvh;
      }
    }

    /* === SPECTATOR MODE === */
    .header-top {
      display: flex;
      justify-content: center;
      align-items: center;
      position: relative;
      margin-bottom: 14px;
    }
    .header-top h1 {
      margin: 0;
    }
    #spectator-toggle {
      position: absolute;
      right: 0;
      background: var(--bg-elevated);
      border: 1.5px solid var(--border-strong);
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      cursor: pointer;
      color: var(--text-secondary);
      padding: 6px 11px;
      font-size: 0.70em;
      font-weight: 700;
      letter-spacing: 0.4px;
      text-transform: uppercase;
      transition: background 0.22s, border-color 0.22s, color 0.22s;
      -webkit-tap-highlight-color: transparent;
      outline: none;
      white-space: nowrap;
    }
    #spectator-toggle:hover {
      background: rgba(180, 195, 220, 0.12);
      border-color: rgba(180, 195, 220, 0.4);
      color: var(--text-primary);
    }
    #spectator-toggle.active {
      background: rgba(91, 141, 238, 0.18);
      border-color: rgba(91, 141, 238, 0.55);
      color: #7aacf5;
    }
    body.spectator-mode .controls-row {
      display: none;
    }
    body.spectator-mode .track-btn {
      pointer-events: none;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      box-shadow: none;
      font-size: 1.05em;
      color: var(--text-secondary);
    }
    body.spectator-mode .play-icon {
      display: none;
    }
    @media (max-width: 480px) {
      body.spectator-mode .track-btn {
        font-size: 0.92em;
      }
      #spectator-toggle {
        font-size: 0.62em;
        padding: 5px 8px;
        gap: 4px;
      }
    }

    /* === BANNER DE RECONEXIÓN === */
    #reconnect-banner {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 9999;
      background: #7c3a00;
      color: #fde68a;
      text-align: center;
      font-size: 0.82em;
      font-weight: 600;
      padding: 10px 16px;
      letter-spacing: 0.3px;
      border-bottom: 1.5px solid rgba(251, 191, 36, 0.4);
      animation: fadeInBanner 0.3s ease;
    }
    #reconnect-banner.visible {
      display: block;
    }
    @keyframes fadeInBanner {
      from { opacity: 0; transform: translateY(-100%); }
      to   { opacity: 1; transform: translateY(0); }
    }
  </style>
</head>
<body>
  <!-- BANNER DE RECONEXIÓN (oculto por defecto) -->
  <div id="reconnect-banner">⚠ Sin conexión con el servidor — reconectando…</div>

  <!-- HEADER STICKY -->
  <div class="header">
    <div class="header-top">
      <h1 id="main-title">Ableton Controller</h1>
      <button id="spectator-toggle" title="Modo Espectador" aria-label="Toggle Spectator Mode">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
        <span id="spectator-label">Ver</span>
      </button>
    </div>
    
    <!-- CONTROLES STICKY -->
    <div class="controls-row">
      <button id="stop-btn" class="control-btn">
        ⏹ STOP
      </button>
      <button id="metro-btn" class="control-btn">
        <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: text-bottom; margin-right: 5px;">
          <path d="M5 21h14"/>
          <path d="m8 21 3-16a1 1 0 0 1 2 0l3 16"/>
          <path d="m12 6 3 9"/>
          <circle cx="15" cy="15" r="1.5" fill="currentColor"/>
        </svg>
        <span>CLICK OFF</span>
      </button>
    </div>
  </div>

  <!-- CONTENEDOR SCROLLABLE DE TRACKS -->
  <div class="tracks-container">
    <div class="grid">
      {% for i, t in tracks %}
        <form action="/play" method="post">
          <input type="hidden" name="index" value="{{ i }}">
          <button class="track-btn"><span class="play-icon">▶ </span>{{ t.title }}</button>
        </form>
      {% endfor %}
    </div>
  </div>

  <!-- FOOTER FIJO -->
  <footer>LiveCue Remote by mariocollado</footer>

  <script>
    // MODO ESPECTADOR
    const spectatorToggle = document.getElementById('spectator-toggle');
    const spectatorLabel = document.getElementById('spectator-label');
    const mainTitle = document.getElementById('main-title');
    let isSpectator = localStorage.getItem('spectatorMode') === 'true';

    function applySpectatorMode() {
      if (isSpectator) {
        document.body.classList.add('spectator-mode');
        spectatorToggle.classList.add('active');
        spectatorLabel.innerText = 'Viewer';
        mainTitle.innerText = 'Setlist Viewer';
      } else {
        document.body.classList.remove('spectator-mode');
        spectatorToggle.classList.remove('active');
        spectatorLabel.innerText = 'Ver';
        mainTitle.innerText = 'Ableton Controller';
      }
    }
    
    applySpectatorMode();

    spectatorToggle.addEventListener('click', () => {
      isSpectator = !isSpectator;
      localStorage.setItem('spectatorMode', isSpectator);
      applySpectatorMode();
    });

    // Validar formulario en modo espectador por seguridad
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', (e) => {
        if (isSpectator) {
          e.preventDefault();
        }
      });
    });

    // Estado del metrónomo
    let metronomeOn = false;

    // Botón STOP
    document.getElementById('stop-btn').addEventListener('click', function(event) {
      event.preventDefault();
      fetch("/stop", {method: "POST"})
        .then(response => {
          if (!response.ok) {
            alert("Error al enviar comando STOP");
          }
        })
        .catch(err => console.error("Error STOP:", err));
    });

    // Botón METRÓNOMO
    const metroBtn = document.getElementById('metro-btn');
    
    metroBtn.addEventListener('click', function(event) {
      event.preventDefault();
      
      fetch("/metronome", {method: "POST"})
        .then(response => response.json())
        .then(data => {
          metronomeOn = data.state;
          updateMetronomeButton();
        })
        .catch(err => {
          console.error("Error METRONOME:", err);
          alert("Error al cambiar metrónomo");
        });
    });

    // Actualizar visual del botón
    function updateMetronomeButton() {
      const svgIcon = `
        <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: text-bottom; margin-right: 5px;">
          <path d="M5 21h14"/>
          <path d="m8 21 3-16a1 1 0 0 1 2 0l3 16"/>
          <path d="m12 6 3 9"/>
          <circle cx="15" cy="15" r="1.5" fill="currentColor"/>
        </svg>
      `;
      if (metronomeOn) {
        metroBtn.classList.add('active');
        metroBtn.innerHTML = svgIcon + '<span>CLICK ON</span>';
      } else {
        metroBtn.classList.remove('active');
        metroBtn.innerHTML = svgIcon + '<span>CLICK OFF</span>';
      }
    }

    // === WATCHDOG DE CONEXIÓN ===
    // Usa el poll del metrónomo para detectar si el servidor está caído.
    // Si falla → muestra el banner. Cuando vuelve → recarga la página para
    // que el móvil pille la IP actualizada y el estado fresco.
    const reconnectBanner = document.getElementById('reconnect-banner');
    let serverOffline = false;
    let offlineCount = 0;

    function pollServerStatus() {
      fetch("/metronome/status", { signal: AbortSignal.timeout(3000) })
        .then(response => response.json())
        .then(data => {
          // Servidor accesible
          if (serverOffline) {
            // Acaba de volver → recargar para estado fresco
            serverOffline = false;
            offlineCount = 0;
            reconnectBanner.classList.remove('visible');
            window.location.reload();
            return;
          }
          offlineCount = 0;
          reconnectBanner.classList.remove('visible');
          if (data.state !== metronomeOn) {
            metronomeOn = data.state;
            updateMetronomeButton();
          }
        })
        .catch(() => {
          offlineCount++;
          // Mostrar banner tras 2 fallos consecutivos (≈4 s)
          if (offlineCount >= 2) {
            serverOffline = true;
            reconnectBanner.classList.add('visible');
          }
        });
    }

    // Consultar estado inicial
    fetch("/metronome/status")
      .then(response => response.json())
      .then(data => {
        metronomeOn = data.state;
        updateMetronomeButton();
      })
      .catch(err => console.error("Error obteniendo estado metrónomo:", err));

    // Poll cada 2 s (watchdog + estado metrónomo)
    setInterval(pollServerStatus, 2000);
  </script>
</body>
</html>
"""