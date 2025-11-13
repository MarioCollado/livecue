# ui/templates/stop_html.py
# Copyright (c) 2025 Mario Collado Rodríguez - CC BY-NC-SA 4.0
# NO uso comercial sin autorización - mcolladorguez@gmail.com

STOP_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reproduciendo</title>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
      background: radial-gradient(circle at top left, #1e293b, #0f172a);
      font-family: 'Segoe UI', Roboto, sans-serif;
      color: #f1f5f9;
    }

    button {
      font-size: 2em;
      padding: 40px 70px;
      background: #ef4444;
      color: white;
      border: none;
      border-radius: 16px;
      box-shadow: 0 0 20px rgba(239,68,68,0.4);
      cursor: pointer;
      transition: all 0.2s ease;
    }

    button:hover {
      background: #dc2626;
      box-shadow: 0 0 30px rgba(239,68,68,0.6);
      transform: scale(1.05);
    }

    button:active {
      transform: scale(0.96);
    }
  </style>
</head>
<body>
  <form action="/stop" method="post">
    <button type="submit">■ STOP</button>
  </form>
</body>
</html>
"""
