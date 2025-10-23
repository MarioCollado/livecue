# 🎛️ Manual de Usuario - LIVECUE - Controlador de Cuelist para Ableton Live

## 📋 Descripción General

LIVECUE es una aplicación que te permite controlar los puntos de locación (cue points) de tu proyecto de Ableton Live de forma visual e intuitiva. Funciona como un controlador remoto que se comunica con Ableton via OSC (Open Sound Control).

---

## 🚀 Requisitos Previos

### 1. **Ableton Live Configuration**

- **Ableton Live 10+** (recomendado 11 o superior)
- **AbletonOSC** instalado y activado:
  - Descarga AbletonOSC desde: [https://github.com/ideoforms/AbletonOSC](https://github.com/ideoforms/AbletonOSC)
  - Sigue las instrucciones de instalación
  - **Importante**: Asegúrate de que AbletonOSC esté activo en tus preferencias de Ableton

### 2. **Configuración de Red**

- La aplicación usa puertos predeterminados:
  - **Envío a Ableton**: Puerto 11000
  - **Recepción desde Ableton**: Puerto 11001
- Ambos programas deben estar en la misma máquina (localhost)

---

## 🎮 Instalación y Ejecución

### Para Usuarios Windows (.exe)

1. Descarga el archivo `LIVECUE.exe`
2. Doble-click para ejecutar
3. **No requiere instalación de Python ni dependencias adicionales**

### Verificación de Conexión

1. Abre Ableton Live
2. Asegúrate de que AbletonOSC esté activo
3. Abre un proyecto con puntos de locación
4. Ejecuta LIVECUE.exe
5. Si todo está correcto, verás "● Esperando..." en la barra de estado

---

## 🎵 Funcionalidades Principales

### 🔍 Escaneo de Locators

- **Botón SCAN**: Obtiene todos los puntos de locación de tu proyecto actual
- Se actualiza automáticamente la lista visual

### ▶️ Control de Reproducción

- **PLAY**: Reproduce el locator seleccionado
- **STOP**: Detiene la reproducción
- **PREV/NEXT**: Navega entre locators y reproduce automáticamente

### 🎹 Metrónomo

- **Botón CLICK**: Activa/desactiva el metrónomo de Ableton
- Indicador visual del estado actual

### 🎚️ Reordenamiento Visual

- **Arrastra y suelta** los locators para reorganizarlos
- El orden se mantiene durante la sesión

### 🎨 Personalización Visual

- **Selector de paletas**: 10 esquemas de color diferentes
- Cambia entre temas oscuros y claros

---

## 🖱️ Interfaz de Usuario

### Secciones Principales:

1. **Barra Superior**: Selector de paleta + control de metrónomo
2. **Cabecera**: Título + estado de conexión
3. **Lista de Locators**: Lista visual de todos los puntos de cue
4. **Controles de Transporte**: Botones SCAN, PLAY, STOP, PREV, NEXT
5. **Pie**: Indicador de funcionalidad de arrastre

### Estados Visuales:

- **Locator seleccionado**: Resaltado con color de acento
- **Metrónomo activo**: Botón verde
- **Drag & Drop**: Feedback visual durante el arrastre

---

## ⚡ Flujo de Trabajo Recomendado

1. **Iniciar Sesión**:
   
   ```
   Ableton Live → Abrir proyecto → Activar AbletonOSC → Ejecutar LIVECUE.exe
   ```

2. **Cargar Locators**:
   
   ```
   Click SCAN → Ver lista actualizada
   ```

3. **Reproducir**:
   
   ```
   Seleccionar locator → Click PLAY
   O usar PREV/NEXT para navegación rápida
   ```

4. **Reorganizar**:
   
   ```
   Arrastrar locator a nueva posición → Orden actualizado
   ```

5. **Control de Metrónomo**:
   
   ```
   Click METRO para toggle on/off
   ```

---

## 🛠️ Solución de Problemas

### ❌ No se ven los locators

- Verifica que AbletonOSC esté activo
- Presiona SCAN nuevamente
- Revisa que tu proyecto tenga puntos de locación

### ❌ No hay comunicación

- Verifica que los puertos 11000 y 11001 estén libres
- Reinicia ambos programas
- Comprueba la configuración de red

### ❌ La aplicación no inicia

- Asegúrate de tener .NET Framework actualizado
- Ejecuta como administrador si hay problemas de permisos

---

## 💡 Consejos de Uso

### Para Presentaciones en Vivo:

- Organiza tus locators por canción o sección
- Usa nombres descriptivos en Ableton
- El reordenamiento visual ayuda al flujo del set

### Para Producción:

- SCAN después de agregar nuevos locators
- El metrónomo remoto es útil para sesiones de grabación

### Personalización:

- Experimenta con diferentes paletas de color
- El tema se adapta a diferentes condiciones de iluminación

---

## 🔄 Reinicio y Cierre

- **Cierre normal**: Cierra la ventana de LIVECUE
- **Reinicio**: Cierra y vuelve a abrir la aplicación
- **Los cambios en locators** se mantienen solo durante la sesión actual

---

## 📞 Soporte

Si experimentas problemas:

1. Revisa este manual
2. Verifica la configuración de AbletonOSC
3. Asegúrate de que los puertos no estén bloqueados por firewall

---

**¡Listo para controlar tu Ableton Live de forma visual! 🎶**
