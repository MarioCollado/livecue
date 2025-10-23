

---

# Manual de Usuario: LIVECUE.py (versión ejecutable)

> **Aviso:**  
> Esta aplicación está en *fase Alpha*. Pueden aparecer errores o comportamientos inesperados. Por favor, reporta cualquier bug a los desarrolladores.LIVECUE.py​

## Descripción

LIVECUE.py es una herramienta profesional para controlar y disparar localizadores (“cue points”) en Ableton Live desde una interfaz gráfica independiente. Facilita la gestión de listas de localizadores, control de reproducción, navegación entre secciones, y manipulación del metrónomo de Ableton Live mediante integración OSC.LIVECUE.py​

## Características principales

- Interfaz de usuario gráfica moderna y personalizable (múltiples paletas visuales).

- Escaneo automático de localizadores/cue points en Ableton Live.

- Lista central de tracks y cue points con arrastrar y soltar para reordenar.

- Botones para Play, Stop, Next, Previous y salto instantáneo al localizador seleccionado.

- Control visual y funcional del metrónomo.

- Feedback visual instantáneo del estado, errores y cambios de sección.

- Comunicación OSC bidireccional con Ableton Live.LIVECUE.py​

## Primer Uso

1. **Ejecución inicial**
   
   - Doble clic en el archivo `LIVECUE.exe`.
   
   - La app abrirá la ventana principal con las funciones disponibles.

2. **Configuración OSC en Ableton Live**
   
   - Verifica que Ableton Live tenga habilitada la extensión/script de control OSC, y que los puertos UDP predeterminados no estén bloqueados:
     
     - Envío a `127.0.0.1:11000`
     
     - Recepción en `0.0.0.0:11001`
   
   - Normalmente, si usas el ejecutable en la misma máquina, no necesitarás configuración extra, salvo abrir el software Ableton y tener una sesión activa.LIVECUE.py​

## Interfaz de Usuario

- **Selector de paleta de colores**  
  Cambia el estilo visual de la aplicación según tus preferencias.

- **Botón “SCAN”**  
  Escanea los localizadores del proyecto abierto en Ableton y actualiza la lista central.

- **Lista de localizadores (cue points)**  
  Haz clic para seleccionar y/o arrastra para reordenar tracks o secciones. El estado de selección y orden se indica de forma visual.

- **Controles principales**
  
  - **PLAY**: Reproduce desde el localizador seleccionado.
  
  - **STOP**: Detiene la reproducción.
  
  - **PREV/NEXT**: Navega rápidamente por la lista.
  
  - **METRONOME ON/OFF**: Activa o desactiva el metrónomo, el botón indica el estado actual con color e ícono.

- **Mensajes de estado y notificaciones**  
  Recibirás avisos según la acción (“Escaneando...”, “Selecciona un locator válido”, etc.) y advertencias si no se han escaneado localizadores.

## Funcionalidades Avanzadas

- Reordenamiento de localizadores mediante drag & drop para ajustar fácilmente la estructura del show.

- Cambia la visualización de la app para adaptarla a tu entorno: escenario, sala de ensayo, estudio.

- En caso de error de comunicación OSC (puerto ocupado/filtro), la app lo indicará en la barra de estado.LIVECUE.py​

## Consejos de Uso

- Utiliza el ejecutable en el mismo ordenador que ejecuta Ableton Live para optimizar la comunicación OSC.

- Si trabajas en escenarios o entornos complejos, ajusta la paleta visual según la iluminación del entorno.

- Para shows en vivo, realiza un escaneo inicial tras abrir Ableton para asegurarte del reconocimiento de todos los localizadores.

- Si la app no detecta localizadores, confirma que Ableton está abierto y la pista de control OSC está activa.

---

## Soporte y Contacto

En caso de errores, problemas o sugerencias, documenta el entorno y el error, y contacta al equipo de desarrollo indicando que se trata de la versión *Alpha* distribuida como ejecutable.LIVECUE.py​

---

**Gracias por participar en las pruebas de LIVECUE.py ejecutable.**
