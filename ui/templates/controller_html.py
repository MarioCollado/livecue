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
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
      background: radial-gradient(circle at top left, #0f172a, #1e293b);
      color: #e2e8f0;
      overflow-x: hidden;
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
    }

    body {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px 14px 80px;
      box-sizing: border-box;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }

    h1 {
      margin: 10px 0 26px 0;
      font-size: 1.9em;
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

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 18px;
      width: 100%;
      max-width: 480px;
      justify-items: center;
    }

    .track-btn {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 16px;
      color: #f1f5f9;
      font-size: 1.1em;
      font-weight: 600;
      padding: 18px;
      cursor: pointer;
      width: 100%;
      box-shadow: 0 3px 10px rgba(0,0,0,0.25);
      transition: transform 0.15s ease, background 0.2s ease, box-shadow 0.2s ease;
      text-shadow: 0 0 5px rgba(56, 189, 248, 0.3);
      will-change: transform;
      -webkit-user-select: none;
      user-select: none;
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
    }

    footer {
      position: fixed;
      bottom: 12px;
      left: 0;
      right: 0;
      text-align: center;
      font-size: 0.8em;
      opacity: 0.65;
      color: #94a3b8;
      pointer-events: none;
      text-shadow: 0 0 3px rgba(255,255,255,0.08);
    }

    /* Móviles pequeños */
    @media (max-width: 480px) {
      h1 {
        font-size: 1.6em;
        margin-bottom: 20px;
      }

      .grid {
        gap: 16px;
        max-width: 94%;
      }

      .track-btn {
        font-size: 1em;
        padding: 16px;
        border-radius: 14px;
      }
    }

    /* Tablets y pantallas medianas */
    @media (min-width: 600px) and (max-width: 1024px) {
      body {
        padding: 28px 24px 100px;
      }

      .grid {
        gap: 22px;
        max-width: 640px;
      }

      .track-btn {
        font-size: 1.2em;
        padding: 20px;
        border-radius: 18px;
      }

      h1 {
        font-size: 2.1em;
        margin-bottom: 30px;
      }
    }
  </style>
</head>
<body>
  <h1>Ableton Controller</h1>
  <div class="grid">
    <button id="stop-btn" class="track-btn" style="background: #de2d4c; color: white; font-size: 1.5em; margin-top: 38px; grid-column: span 2;">
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
