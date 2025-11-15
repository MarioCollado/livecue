[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-red.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

# LiveCue - Ableton Setlist Controller

LiveCue es una herramienta profesional para el manejo de setlists y control de Ableton Live en tiempo real. Desarrollada en Python, ofrece una interfaz moderna y funcionalidades avanzadas para músicos y técnicos de sonido.

---

## 🎯 Características Principales

### Control de Setlist
- **Gestión de Tracks**: Visualización jerárquica de tracks con sus secciones (Intro, Verso, Estribillo, etc.)
- **Navegación Intuitiva**: Play, Stop, Next, Previous 
- **Reproducción desde Secciones**: 🔨 (En progreso) Click en cualquier sección para comenzar desde ese punto exacto
- **Drag & Drop**: Reordena tracks arrastrando para ajustar el orden del setlist sobre la marcha

### Comunicación OSC
- **Bidireccional**: Envía comandos y recibe estado de Ableton en tiempo real
- **Auto-Scan**: Detección automática de cue points, clips y estructura del arrangement
- **Listeners**: Seguimiento de playback position, tempo, time signature y metronome state

### Interfaz Visual
- **Temas Personalizables**: 🔨 (En progreso)
- **Beat Indicator**: Visualización del pulso en tiempo real sincronizada con Ableton
- **Progress Tracking**: (En progreso) Barra de progreso y marcadores visuales de posición
- **Cronómetro de Set**: Temporizador con start/pause/reset para medir la duración del directo

### Persistencia de Datos
- **Guardar/Cargar Setlists**: Almacenamiento JSON de locators, tracks y secciones
- **Recuperación Rápida**: Carga configuraciones previas sin necesidad de re-escanear

### Control Remoto Web
- **Servidor Flask Integrado**: Acceso desde móvil/tablet en la misma red
- **Detección de IP**: Muestra automáticamente IPs locales y Tailscale VPN
- **Control Completo**: Play, Stop, Metronome toggle desde cualquier dispositivo

---

## 🏗️ Arquitectura del Proyecto

```
LiveCue/
├── main.py                      # Punto de entrada principal
├── version_info.py              # Información de versión
│
├── core/                        # Lógica de negocio
│   ├── constants.py            # Configuración OSC y directorios
│   ├── state.py                # Estado global thread-safe (tracks, playback, tempo)
│   ├── playback.py             # Controlador de reproducción de Ableton
│   └── utils.py                # Utilidades generales
│
├── osc/                         # Comunicación OSC
│   ├── client.py               # Cliente OSC para enviar a Ableton
│   ├── server.py               # Servidor OSC para recibir de Ableton
│   ├── handlers.py             # Procesadores de mensajes OSC
│   └── web_server.py           # Servidor Flask para control remoto
│
├── setlist/                     # Gestión de setlists
│   └── manager.py              # Serialización/deserialización JSON
│
├── ui/                          # Interfaz gráfica
│   ├── app_ui.py               # Aplicación principal Flet
│   ├── components.py           # Componentes reutilizables (BeatIndicator, TempoDisplay, etc.)
│   ├── header_component.py     # Header con cronómetro y controles
│   ├── themes.py               # Paletas de colores
│   └── templates/
│       └── controller_html.py  # Template HTML para control web
│       └── stop_html.py        # Template HTML para stop button
│
└── setlist/data/                # Directorio de setlists guardados (JSON)
```

---

## 📋 Requisitos

### Software
- **Python 3.13+**
- **Ableton Live** con [AbletonOSC](https://github.com/ideoforms/AbletonOSC) instalado

### Dependencias Python
```bash
# Interfaz gráfica
flet>=0.28.3

# Comunicación OSC
python-osc>=1.8.0

# Servidor web
flask>=3.0.0

# Utilidades
pillow>=10.0.0
```

Instala todas las dependencias con:
```bash
pip install -r requirements.txt
```

---

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/MarioCollado/LiveCue.git
cd LiveCue
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Ableton Live
1. Instala [AbletonOSC](https://github.com/ideoforms/AbletonOSC)
2. En el arrangement de Ableton, crea **locators** con nomenclatura específica:
   ```
   START TRACK "Nombre del Track"
   
   END TRACK 
   ```

3. Crear un pista midi para identificar las diferentes secciones de los tracks:
   ```
   Intro
   Verso 1
   Estribillo
   Puente
   ```

3. Configura AbletonOSC para escuchar en:
   - **Puerto de envío**: `11000` (LiveCue → Ableton)
   - **Puerto de recepción**: `11001` (Ableton → LiveCue)

### 4. Ejecutar la Aplicación
```bash
python main.py
```

---

## 🎮 Modo de Uso

### Flujo Básico
1. **Abrir Ableton**: Carga tu proyecto con locators configurados
2. **Ejecutar LiveCue**: `python main.py`
3. **Scan**: Presiona el botón **SCAN** para detectar tracks y secciones
4. **Navegar**: Usa los controles para reproducir, saltar entre tracks o secciones específicas
5. **Guardar**: Guarda tu setlist configurado para recuperarlo después

### Controles Principales
- **SCAN**: Escanea cue points y clips desde Ableton
- **PLAY**: Reproduce el track seleccionado desde el inicio
- **STOP**: Detiene la reproducción
- **PREV/NEXT**: Navega entre tracks
- **Click en Sección**: 🔨 (En progreso) Reproduce desde esa sección específica (ideal para ensayos)
- **METRONOME**: Toggle del click de Ableton

### Control Remoto Web
1. LiveCue muestra las IPs disponibles en el header
2. Abre `http://[IP]:5000` desde tu móvil/tablet
3. Controla play/stop/metronome desde cualquier dispositivo en red

---

## 🎨 Temas Disponibles

🔨 (En progreso) Varios temas disponibles para una mayor personalización.

Cambia el tema desde el selector 🎨 en el header.

---

## 🔧 Configuración Avanzada

### Puertos OSC
Edita `core/constants.py`:
```python
LIVE_IP = "127.0.0.1"
LIVE_SEND_PORT = 11000      # Puerto donde Ableton escucha
CLIENT_LISTEN_PORT = 11001  # Puerto donde LiveCue escucha
```

### Directorio de Setlists
Por defecto: `C:\Users\[usuario]\Desktop\CUELIST_ABLETON_SETLIST\LIVECUE APP\setlist\data`

Personalízalo en `core/constants.py`:
```python
SETLISTS_DIR = Path(r"C:\tu\ruta\personalizada")
```

---

## 📦 Compilación con PyInstaller

Para crear un ejecutable standalone:

```bash
pyinstaller --onefile --windowed --icon=icon.ico main.py
```

El `.exe` se generará en `dist/main.exe`

---

## 🐛 Resolución de Problemas

### "No se detectan tracks al hacer SCAN"
- Verifica que AbletonOSC esté activo en Ableton
- Confirma que los puertos coincidan (11000/11001)
- Asegúrate de tener locators con formato `START TRACK "Nombre" / "END TRACK"`

### "Error al reproducir desde secciones"
- Las secciones deben estar dentro del rango de un track definido
- Verifica que los locators de inicio/fin estén correctamente colocados

### "El servidor web no es accesible desde otros dispositivos"
- Verifica que tu firewall permita conexiones en el puerto 5000
- Asegúrate de estar en la misma red WiFi/LAN
  

---

## 📄 Licencia

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

Este proyecto está licenciado bajo **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**.

**Copyright © 2025 Mario Collado Rodríguez. Todos los derechos reservados.**

### ✅ Puedes:
- Usar el software para fines personales y educativos
- Modificar y crear versiones derivadas
- Compartir con otros (con atribución)

### ❌ NO puedes:
- Usar el software con fines comerciales sin autorización escrita
- Vender el software o versiones modificadas
- Eliminar los avisos de copyright

### 📧 Licencias Comerciales
Para uso comercial, contacta: **mcolladorguez@gmail.com**

Ver archivo [LICENSE](LICENSE) para términos legales completos.

---

## 👨‍💻 Autor

**Mario Collado Rodríguez**  
[GitHub](https://github.com/MarioCollado) | [Email](mailto:mcolladorguez@gmail.com)

---

## 📸 Capturas de Pantalla

<img width="1920" height="1080" alt="imagen" src="https://github.com/user-attachments/assets/25077d2e-61f6-4ea7-a982-d4ab3f852517" />

---

**¿Preguntas o sugerencias?** Abre un [issue](https://github.com/MarioCollado/LiveCue/issues) en GitHub.
