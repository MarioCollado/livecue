[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-red.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

# LiveCue - Ableton Setlist Controller

LiveCue es una app de escritorio para controlar setlists de Ableton Live con UI en Flet, comunicacion OSC y panel web integrado.

La aplicacion esta pensada para:
- escanear locators y secciones desde Ableton
- navegar entre tracks y secciones
- guardar y cargar setlists locales
- controlar la reproduccion desde una interfaz desktop o desde el navegador
- activar o desactivar el click/metronomo con un boton dedicado

## Stack actual

- **UI desktop:** Flet
- **Backend OSC:** python-osc
- **Panel web:** Flask
- **Persistencia:** JSON local para setlists
- **Lenguaje:** Python 3.12+

## Estructura del proyecto

```text
livecue/
|-- main.py
|-- app/
|   `-- bootstrap.py
|-- core/
|   |-- config.py
|   |-- constants.py
|   |-- state.py
|   |-- playback.py
|   |-- network.py
|   |-- logger.py
|   |-- utils.py
|   |-- i18n.py
|   `-- license.py
|-- domain/
|   `-- models.py
|-- services/
|   `-- playback_service.py
|-- osc/
|   |-- client.py
|   |-- handlers.py
|   |-- server.py
|   `-- web_server.py
|-- setlist/
|   `-- manager.py
|-- ui/
|   |-- app_ui.py
|   |-- components.py
|   |-- control_panel.py
|   |-- dialogs.py
|   |-- header_component.py
|   |-- managers.py
|   |-- track_list.py
|   |-- themes.py
|   |-- welcome_dialog.py
|   `-- templates/
`-- web/
    `-- server.py
```

### Notas de arquitectura

- `main.py` es solo el punto de entrada.
- `app/bootstrap.py` centraliza arranque y apagado.
- `core/config.py` concentra puertos, rutas y variables de entorno.
- `core/constants.py`, `core/playback.py` y `osc/web_server.py` siguen como capas de compatibilidad.
- `domain/` contiene los modelos de datos de la app.
- `services/` separa la logica de negocio mas pesada.
- `web/server.py` contiene el servidor Flask real.

## Requisitos

### Software

- Python **3.12** o superior
- Ableton Live
- AbletonOSC instalado y configurado en Ableton

### Dependencias Python

Las dependencias se gestionan con **Poetry** desde `pyproject.toml`.

Instalacion recomendada:

```bash
poetry install
```

Si prefieres el flujo legacy, puedes seguir usando `requirements.txt`, pero Poetry es la fuente de verdad actual.

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/MarioCollado/LiveCue.git
cd LiveCue
```

### 2. Instalar dependencias

```bash
poetry install
```

### 3. Configurar Ableton Live

1. Instala [AbletonOSC](https://github.com/ideoforms/AbletonOSC).
2. Configura Ableton para exponer los puertos OSC que usa LiveCue:
   - `LIVE_SEND_PORT = 11000`
   - `CLIENT_LISTEN_PORT = 11001`
3. En el arrangement, crea locators con el formato que usa el proyecto:

```text
START TRACK "Nombre del Track"
...
END TRACK
```

4. Para las secciones, usa nombres coherentes en tus clips o marcadores, por ejemplo:

```text
Intro
Verso 1
Estribillo
Puente
```

### 4. Ejecutar la aplicacion

```bash
poetry run livecue
```

Tambien puedes lanzarla directamente con:

```bash
python main.py
```

## Uso basico

1. Abre tu proyecto en Ableton Live.
2. Ejecuta LiveCue.
3. Pulsa **SCAN** para detectar tracks y secciones.
4. Usa **PLAY**, **STOP**, **PREV**, **NEXT** y **CLICK ON/OFF** para navegar y controlar el click.
5. Guarda el setlist cuando quieras reutilizarlo despues.

## Panel web

LiveCue levanta un servidor Flask integrado para control remoto.

- Puerto por defecto: `5000`
- URL local: `http://127.0.0.1:5000`
- En red: usa la IP que muestre el header de la app
- Desde el movil puedes abrir esa IP directamente para controlar LiveCue sin estar frente al ordenador

Si tienes Tailscale o una red local accesible, el header tambien muestra la IP disponible para abrir el panel desde movil o tablet.

## Configuracion

Las opciones principales viven en `core/config.py` y se pueden sobrescribir por variables de entorno.

```bash
SETLISTS_DIR=...
LIVE_SEND_PORT=11000
CLIENT_LISTEN_PORT=11001
FLASK_PORT=5000
```

### Directorio de setlists

Por defecto, LiveCue guarda los setlists en una carpeta local de la app. Si quieres cambiarlo, define `SETLISTS_DIR` antes de arrancar.

## Flujo de trabajo recomendado

1. Arranca Ableton.
2. Abre LiveCue.
3. Haz un **SCAN** inicial.
4. Ajusta el orden de tracks si hace falta.
5. Guarda el setlist.
6. Usa el panel web para control remoto si lo necesitas.

## Desarrollo

Comprobacion rapida de sintaxis:

```bash
python -m compileall app core domain osc services ui web setlist
```

## Solucion de problemas

### No se detectan tracks al hacer SCAN

- Verifica que AbletonOSC este activo.
- Comprueba que los puertos coincidan con la configuracion.
- Asegurate de que los locators sigan el formato esperado.

### El panel web no abre desde otro dispositivo

- Revisa el firewall del sistema.
- Comprueba que ambos dispositivos esten en la misma red.
- Verifica que el puerto `5000` no este ocupado por otra app.

### No se ven setlists guardados

- Comprueba que `SETLISTS_DIR` apunta a una ruta valida.
- Verifica que la app tenga permisos de escritura en esa carpeta.

## Licencia

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

Este proyecto esta licenciado bajo **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**.

### Puedes

- Usar el software para fines personales y educativos
- Modificar y crear versiones derivadas
- Compartir el proyecto con atribucion

### No puedes

- Usarlo con fines comerciales sin autorizacion escrita
- Vender el software o sus derivados
- Eliminar los avisos de copyright

Para licencias comerciales, contacta: **mcolladorguez@gmail.com**

Consulta el archivo [LICENSE](LICENSE) para los terminos completos.

## Autor

**Mario Collado Rodriguez**  
[GitHub](https://github.com/MarioCollado) | [Email](mailto:mcolladorguez@gmail.com)

## Captura

<img width="1920" height="1080" alt="imagen" src="https://github.com/user-attachments/assets/25077d2e-61f6-4ea7-a982-d4ab3f852517" />
