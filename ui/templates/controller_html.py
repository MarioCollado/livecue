# Copyright (c) 2025 Mario Collado Rodríguez - MIT License

# ui/templates/controller_ui.py
CONTROLLER_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ableton Remote</title>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      min-height: 100dvh;
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
      background: radial-gradient(circle at top left, #0f172a, #1e293b);
      color: #e2e8f0;
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
      background: linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(15, 23, 42, 0.95) 100%);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
      padding: 16px 14px 14px;
      width: 100%;
      box-sizing: border-box;
    }

    h1 {
      margin: 0 0 14px 0;
      font-size: 1.7em;
      background: linear-gradient(90deg, #38bdf8, #818cf8, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      font-weight: 700;
      text-align: center;
      text-shadow: 0 0 6px rgba(56, 189, 248, 0.25);
      user-select: none;
    }

    /* CONTROLES STICKY */
    .controls-row {
      display: flex;
      gap: 10px;
      width: 100%;
      max-width: 500px;
      margin: 0 auto;
      justify-content: center;
    }

    .control-btn {
      flex: 1;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 12px;
      color: white;
      font-size: 1em;
      font-weight: 700;
      padding: 14px 8px;
      cursor: pointer;
      box-shadow: 0 3px 10px rgba(0,0,0,0.3);
      transition: transform 0.15s ease, background 0.2s ease, box-shadow 0.2s ease;
      will-change: transform;
      -webkit-user-select: none;
      user-select: none;
      min-width: 110px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .control-btn:active {
      transform: scale(0.96);
      transition-duration: 0.05s;
    }

    #stop-btn {
      background: linear-gradient(135deg, #dc2626, #991b1b);
      border-color: rgba(239, 68, 68, 0.5);
    }

    #stop-btn:hover {
      background: linear-gradient(135deg, #ef4444, #b91c1c);
      box-shadow: 0 0 12px rgba(220, 38, 38, 0.6);
      transform: scale(1.02);
    }

    #metro-btn {
      background: linear-gradient(135deg, #6b7280, #4b5563);
      border-color: rgba(156, 163, 175, 0.4);
    }

    #metro-btn:hover {
      background: linear-gradient(135deg, #9ca3af, #6b7280);
      box-shadow: 0 0 12px rgba(107, 114, 128, 0.5);
      transform: scale(1.02);
    }

    #metro-btn.active {
      background: linear-gradient(135deg, #d4af37, #b8952a);
      border-color: rgba(212, 175, 55, 0.5);
      animation: pulse 1.5s ease-in-out infinite;
    }

    #metro-btn.active:hover {
      background: linear-gradient(135deg, #dbb943, #c29f2f);
      box-shadow: 0 0 12px rgba(212, 175, 55, 0.7);
    }

    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 8px rgba(212, 175, 55, 0.4); }
      50% { box-shadow: 0 0 16px rgba(212, 175, 55, 0.8); }
    }

    /* CONTENEDOR DE TRACKS CON SCROLL */
    .tracks-container {
      flex: 1;
      width: 100%;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 20px 14px 40px;
      box-sizing: border-box;
      max-height: 100dvh;
    }

    /* GRID DE TRACKS - UNA COLUMNA EN MÓVIL/TABLET */
    .grid {
      display: grid;
      grid-template-columns: 1fr; /* Una columna por defecto */
      gap: 16px;
      width: 100%;
      max-width: 500px;
      margin: 0 auto;
    }

    .track-btn {
      height: 90px;
      min-height: 90px;
      max-height: 90px;
      
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      color: #f1f5f9;
      font-size: 1em;
      font-weight: 600;
      padding: 12px 10px;
      cursor: pointer;
      width: 100%;
      box-shadow: 0 3px 10px rgba(0,0,0,0.25);
      transition: transform 0.15s ease, background 0.2s ease, box-shadow 0.2s ease;
      text-shadow: 0 0 5px rgba(56, 189, 248, 0.3);
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
      line-height: 1.3;
      
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
    }

    .track-btn:hover,
    .track-btn:focus-visible {
      background: rgba(56, 189, 248, 0.16);
      transform: scale(1.02);
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.45);
    }

    .track-btn:active {
      transform: scale(0.96);
      background: rgba(56, 189, 248, 0.25);
      transition-duration: 0.05s;
    }

    form {
      width: 100%;
      margin: 0;
      height: 90px;
    }

    /* FOOTER FIJO */
    footer {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      text-align: center;
      font-size: 0.75em;
      opacity: 0.6;
      color: #94a3b8;
      pointer-events: none;
      background: linear-gradient(0deg, rgba(15, 23, 42, 0.9) 0%, transparent 100%);
      padding: 10px 0;
      text-shadow: 0 0 3px rgba(255,255,255,0.08);
    }

    /* MÓVILES PEQUEÑOS */
    @media (max-width: 480px) {
      h1 {
        font-size: 1.5em;
        margin-bottom: 12px;
      }

      .header {
        padding: 14px 12px 12px;
      }

      .controls-row {
        gap: 8px;
      }

      .control-btn {
        font-size: 0.9em;
        padding: 35px 6px;
        min-width: 100px;
      }

      .tracks-container {
        padding: 18px 12px 70px;
      }

      .grid {
        gap: 14px;
        grid-template-columns: 1fr; /* Una columna */
      }

      .track-btn {
        height: 85px;
        min-height: 85px;
        max-height: 85px;
        font-size: 0.95em;
        padding: 10px 8px;
      }

      form {
        height: 85px;
      }
    }

    /* TABLETS Y PANTALLAS MEDIANAS */
    @media (min-width: 600px) and (max-width: 1024px) {
      h1 {
        font-size: 1.9em;
        margin-bottom: 16px;
      }

      .header {
        padding: 20px 24px 16px;
      }

      .controls-row {
        gap: 14px;
        max-width: 600px;
      }

      .control-btn {
        font-size: 1.2em;
        padding: 16px 12px;
        min-width: 140px;
      }

      .tracks-container {
        padding: 24px 24px 90px;
      }

      .grid {
        gap: 20px;
        max-width: 600px;
        grid-template-columns: 1fr; /* Una columna */
      }

      .track-btn {
        height: 100px;
        min-height: 100px;
        max-height: 100px;
        font-size: 1.1em;
        padding: 14px 12px;
      }

      form {
        height: 100px;
      }
    }

    /* PANTALLAS GRANDES - MÚLTIPLES COLUMNAS */
    @media (min-width: 1025px) {
      .header {
        padding: 24px 32px 18px;
      }

      .controls-row {
        max-width: 700px;
        gap: 16px;
      }

      .control-btn {
        font-size: 1.3em;
        padding: 18px 16px;
      }

      .tracks-container {
        padding: 28px 32px 100px;
      }

      .grid {
        max-width: 700px;
        gap: 22px;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); /* Múltiples columnas en escritorio */
      }

      .track-btn {
        height: 110px;
        min-height: 110px;
        max-height: 110px;
        font-size: 1.15em;
      }

      form {
        height: 110px;
      }
    }
    
    @supports (height: 100dvh) {
      body {
        height: 100dvh;
      }
    }

  </style>
</head>
<body>
  <!-- HEADER STICKY -->
  <div class="header">
    <h1>Ableton Controller</h1>
    
    <!-- CONTROLES STICKY -->
    <div class="controls-row">
      <button id="stop-btn" class="control-btn">
        ⏹ STOP
      </button>
      <button id="metro-btn" class="control-btn">
        🎵 CLICK OFF
      </button>
    </div>
  </div>

  <!-- CONTENEDOR SCROLLABLE DE TRACKS -->
  <div class="tracks-container">
    <div class="grid">
      {% for i, t in tracks %}
        <form action="/play" method="post">
          <input type="hidden" name="index" value="{{ i }}">
          <button class="track-btn">▶ {{ t.title }}</button>
        </form>
      {% endfor %}
    </div>
  </div>

  <!-- FOOTER FIJO -->
  <footer>LiveCue Remote by mariocollado</footer>

  <script>
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
      if (metronomeOn) {
        metroBtn.classList.add('active');
        metroBtn.innerHTML = '🎵 CLICK ON';
      } else {
        metroBtn.classList.remove('active');
        metroBtn.innerHTML = '🎵 CLICK OFF';
      }
    }

    // Consultar estado inicial
    fetch("/metronome/status")
      .then(response => response.json())
      .then(data => {
        metronomeOn = data.state;
        updateMetronomeButton();
      })
      .catch(err => console.error("Error obteniendo estado metrónomo:", err));

    // Actualizar cada 2 segundos
    setInterval(() => {
      fetch("/metronome/status")
        .then(response => response.json())
        .then(data => {
          if (data.state !== metronomeOn) {
            metronomeOn = data.state;
            updateMetronomeButton();
          }
        })
        .catch(err => console.error("Error actualizando estado:", err));
    }, 2000);
  </script>
</body>
</html>
"""