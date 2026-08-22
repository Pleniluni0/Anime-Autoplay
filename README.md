# Anime AutoPlay

Extensión de Chrome que convierte sitios de anime/donghua en una experiencia tipo Netflix: cuenta atrás al final del episodio, paso automático al siguiente, pantalla completa y salto de intro configurable.

> **Disponible en dos versiones:**
> - [Chrome Web Store](https://chrome.google.com/webstore) — versión oficial con un click por episodio
> - **GitHub** — misma versión + host nativo opcional para experiencia totalmente automática (cero clicks)

## 🚀 Novedades recientes

- **Soporte multi-monitor**: el host Python identifica la ventana correcta usando las coordenadas reales (`screenX`/`screenY`) enviadas desde el content script. Funciona aunque tengas ventanas de Chrome/Brave en varios monitores.
- **Clicks vía Windows API**: `SetCursorPos` + `SendInput` en lugar de `pyautogui.click()` — más fiable en setups con distinto DPI por monitor.
- **Delays optimizados**: reducidos drásticamente (~2s más rápido entre episodios) tras migrar la lógica de click al host Python.

## Sitios probados

- AnimeAV1
- AnimeFLV
- SeriesDonghua
- MundoDonghua
- DonghuaLife

Funciona en la mayoría de los reproductores embebidos (Dailymotion, Voe, JWPlayer, Streamtape, Filemoon, HLS/zilla-networks, Mega…).

## Modos de funcionamiento

### Modo automático (con host nativo) — Solo desde GitHub

Cuando el episodio termina, la extensión pasa al siguiente y activa el reproductor + pantalla completa **sin ninguna interacción del usuario**. Para lograrlo, un script Python local simula un click real del sistema operativo, lo que le da al navegador el gesto de usuario necesario para entrar en fullscreen.

```
Extensión → background.js → Native Messaging → Python → click real del SO
```

### Modo manual (versión Chrome Web Store)

Si el host no está instalado (versión de Store), la extensión funciona con un overlay de pantalla completa: el usuario pulsa una vez para activar el reproductor y la pantalla completa. El resto (autoplay, countdown, saltar intro…) funciona exactamente igual.

## Funcionalidades

- **Reproducción automática** con overlay de cuenta atrás (3–15 s). Botones *Ver ahora* / *Cancelar*.
- **Modo automático** (con host nativo, instalación separada): click automático vía host nativo, sin tocar nada.
- **Recordar reproductor**: guarda qué servidor elegiste y lo selecciona solo al cambiar de episodio.
- **Salto de intro/opening**: configura inicio y fin (ej. `0:00 → 1:30`).
  - *Manual*: botón flotante "⏩ Saltar intro" sobre el vídeo.
  - *Automático*: salta solo sin botón.
- **Salto de créditos/ending**: muestra la cuenta atrás *N* segundos antes del final.
- **Pausa al cambiar de pestaña**: el countdown se pausa si dejas de mirar la pestaña.

## Instalación

### Versión Chrome Web Store (recomendada)

1. Abre [Chrome Web Store](https://chrome.google.com/webstore) y busca "Anime AutoPlay".
2. Pulsa **Añadir a Chrome**.
3. Listo. La extensión funciona inmediatamente en los sitios soportados.

### Versión desde GitHub (desarrollador)

1. Abre `chrome://extensions/` en Chrome (o Edge/Brave/etc.).
2. Activa el **Modo de desarrollador** (esquina superior derecha).
3. Pulsa **Cargar descomprimida** y selecciona la carpeta del proyecto.
4. Copia el **ID** de la extensión que aparece debajo del nombre.

### Activar el modo automático (host nativo, solo desde GitHub)

Si quieres el modo totalmente automático necesitas instalar el host nativo:

**Requisito:** Python en el PATH con pyautogui instalado.

```bash
pip install pyautogui
```

Luego, desde la carpeta `host\`, ejecuta en PowerShell con el ID de tu extensión:

```powershell
.\install_host.ps1 -ExtensionId "tu_id_de_extension_aqui"
```

Reinicia Chrome. A partir de ahora el paso de episodio es completamente automático.

> **Nota:** El registro del host solo afecta a tu usuario de Windows (`HKCU`). No necesita permisos de administrador.

Si en el futuro mueves la carpeta de sitio, vuelve a ejecutar el `.ps1`.

## Configuración

Abre el popup pulsando el icono de la extensión:

| Opción | Descripción |
| --- | --- |
| Reproducción automática | Activa el paso al siguiente episodio |
| Fullscreen al cargar | Overlay de pantalla completa al pasar de episodio |
| Cuenta atrás | Segundos antes de saltar (3–15) |
| Recordar reproductor | Mantiene el mismo servidor entre episodios |
| Saltar intro / opening | Define rango y modo (manual/automático) |
| Saltar créditos / ending | Muestra cuenta atrás *N* s antes del final |

## Cómo funciona

La extensión usa cuatro scripts coordinados:

- **`main.js`** — corre en la página principal. Detecta el botón de "Siguiente episodio", muestra los overlays, gestiona flags entre navegaciones. Cuando aparece el overlay de fullscreen envía las coordenadas del click **y las coordenadas de la ventana** (`screenX`, `screenY`, `outerWidth`, `outerHeight`) al background para que el host encuentre la ventana correcta incluso en setups multi-monitor.
- **`background.js`** — service worker que recibe el mensaje de `main.js` y lo reenvía al host nativo vía `chrome.runtime.sendNativeMessage` (si está instalado).
- **`bridge.js`** — corre en iframes intermedios del mismo origen. Reenvía mensajes entre la página principal y los iframes cross-origin del reproductor real.
- **`player.js`** — corre en iframes de reproductores (Dailymotion, Voe, JWPlayer, etc.). Engancha el `<video>`, gestiona el salto de intro y el unmute tras autoplay.

## Estructura del repositorio

```
.
├── manifest.json          # Manifest V3 (sin nativeMessaging para Store)
├── main.js                # Script principal (top frame)
├── background.js          # Service worker — puente hacia el host nativo
├── bridge.js              # Relay de mensajes en iframes intermedios
├── player.js              # Script para iframes del reproductor
├── popup.html             # UI de configuración
├── popup.js               # Lógica del popup
├── overlay.css            # Estilos compartidos de overlays
├── PRIVACY.md             # Política de privacidad
├── DESCRIPTION.md         # Texto para la Chrome Web Store
├── icons/                 # Iconos de la extensión
└── host/                  # Host nativo (solo para instalación desde GitHub)
    ├── animeautoplay_host.py
    ├── animeautoplay_host.bat
    ├── com.animeautoplay.host.template.json
    └── install_host.ps1
```

## Licencia

MIT
