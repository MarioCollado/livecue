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
      background: radial-gradient(circle at top left, #0f172a, #1e293b);
      font-family: 'Segoe UI', Roboto, sans-serif;
      color: #e2e8f0;
      overflow-x: hidden;
      -webkit-tap-highlight-color: transparent;
    }

    body {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px 16px 90px; /* margen inferior extra para scroll cómodo */
      box-sizing: border-box;
      min-height: 100vh;
    }

    h1 {
      margin: 10px 0 28px 0;
      font-size: 1.9em;
      background: linear-gradient(90deg, #38bdf8, #818cf8, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: 2px;
      text-transform: uppercase;
      font-weight: 700;
      text-shadow: 0 0 8px rgba(56, 189, 248, 0.3);
      text-align: center;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 22px;
      width: 100%;
      max-width: 520px;
      justify-items: center;
    }

    .track-btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 18px;
      backdrop-filter: blur(12px);
      color: #f1f5f9;
      font-size: 1.15em;
      font-weight: 600;
      padding: 22px;
      cursor: pointer;
      width: 100%;
      box-shadow: 0 4px 14px rgba(0,0,0,0.3), inset 0 0 10px rgba(255,255,255,0.04);
      transition: all 0.25s ease;
      text-shadow: 0 0 6px rgba(56, 189, 248, 0.4);
      backdrop-filter: blur(10px);
    }

    .track-btn:hover {
      background: rgba(56, 189, 248, 0.18);
      transform: scale(1.03);
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
    }

    .track-btn:active {
      transform: scale(0.97);
      background: rgba(56, 189, 248, 0.25);
    }

    form {
      width: 100%;
      margin: 0;
    }

    footer {
      position: fixed;
      bottom: 14px;
      left: 0;
      right: 0;
      text-align: center;
      font-size: 0.85em;
      opacity: 0.65;
      color: #94a3b8;
      pointer-events: none;
      text-shadow: 0 0 4px rgba(255,255,255,0.1);
    }

    /* Móvil pequeño */
    @media (max-width: 480px) {
      h1 {
        font-size: 1.6em;
        margin-bottom: 22px;
      }

      .grid {
        gap: 18px;
        max-width: 90%;
      }

      .track-btn {
        font-size: 1.05em;
        padding: 20px;
        border-radius: 16px;
      }

      footer {
        font-size: 0.8em;
        bottom: 10px;
      }
    }
  </style>
</head>
<body>
  <h1>Ableton Controller</h1>
  <div class="grid">
    <button id="stop-btn" class="track-btn" style="background: #de2d4c; color: white; font-size: 1.5em; margin-top: 38px;">
      ⏹ STOP
    </button>
    {% for i, t in tracks %}
      <form action="/play" method="post">
        <input type="hidden" name="index" value="{{ i }}">
        <button class="track-btn">▶ {{ t.title }}</button>
      </form>
    {% endfor %}
  </div>
  <footer>LiveCue Remote by mariocollado</footer>
  <script>
    document.getElementById('stop-btn').addEventListener('click', function(event) {
        event.preventDefault();
        fetch("/stop", {method: "POST"})
          .then(response => {
              if (!response.ok) {
                  alert("Error al enviar comando STOP");
              }
          });
    });
  </script>
</body>
</html>

"""
