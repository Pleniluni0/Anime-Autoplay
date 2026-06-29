"""
Native Messaging Host para Anime AutoPlay Host.
Recibe mensajes de la extensión Chrome y ejecuta clicks reales con pyautogui.

Instalar dependencia: pip install pyautogui
"""

import sys
import json
import struct
import time
import ctypes
import os
from datetime import datetime

# ── Logging a archivo para diagnóstico ────────────────────────────────────────
LOG_PATH = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'aap_host.log')
def log(msg):
    try:
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f'[{ts}] {msg}\n')
    except Exception:
        pass

log('=== HOST INICIADO ===')

# ── NOTA: NO usamos mutex. El mutex quedaba zombie al terminar el proceso
# y bloqueaba futuras instancias. Si Chrome lanza 2 copias (bug de Chrome),
# ambas se ejecutan — la segunda hereda stdin/stdout y la primera muere sola.

# ── DPI Awareness en Windows ──────────────────────────────────────────────────
if os.name == 'nt':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor V2
        log('DPI: Per-Monitor V2')
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Per-Monitor
            log('DPI: Per-Monitor')
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()  # System
                log('DPI: System')
            except Exception:
                log('DPI: FALLÓ - sin awareness')

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    HAS_PYAUTOGUI = True
    log('pyautogui OK')
except ImportError:
    HAS_PYAUTOGUI = False
    log('pyautogui NO DISPONIBLE')


def read_message():
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) < 4:
        return None
    length = struct.unpack('=I', raw_length)[0]
    if length == 0:
        return None
    data = sys.stdin.buffer.read(length)
    return json.loads(data.decode('utf-8'))


def send_message(obj):
    encoded = json.dumps(obj).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('=I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def _win_click(x, y):
    """Click usando Windows API directa (SetCursorPos + SendInput).
    Más fiable que pyautogui en setups multi-monitor con distinto DPI."""
    user32 = ctypes.windll.user32

    # Mover cursor
    result = user32.SetCursorPos(int(x), int(y))
    log(f'_win_click: SetCursorPos({int(x)},{int(y)}) → {result}')
    time.sleep(0.02)

    # Estructuras para SendInput
    class POINT(ctypes.Structure):
        _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [('dx', ctypes.c_long), ('dy', ctypes.c_long),
                    ('mouseData', ctypes.c_ulong), ('dwFlags', ctypes.c_ulong),
                    ('time', ctypes.c_ulong), ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))]
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [('wVk', ctypes.c_ushort), ('wScan', ctypes.c_ushort),
                    ('dwFlags', ctypes.c_ulong), ('time', ctypes.c_ulong),
                    ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))]
    class INPUT_UNION(ctypes.Union):
        _fields_ = [('mi', MOUSEINPUT), ('ki', KEYBDINPUT)]
    class INPUT(ctypes.Structure):
        _fields_ = [('type', ctypes.c_ulong), ('u', INPUT_UNION)]

    INPUT_MOUSE = 0
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    # Mouse down
    inp_down = INPUT()
    inp_down.type = INPUT_MOUSE
    inp_down.u.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
    # Mouse up
    inp_up = INPUT()
    inp_up.type = INPUT_MOUSE
    inp_up.u.mi.dwFlags = MOUSEEVENTF_LEFTUP

    ctypes.windll.user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
    time.sleep(0.02)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))
    log(f'_win_click: SendInput click completado en ({int(x)},{int(y)})')


def _find_chrome_window():
    """Busca la ventana de Chrome más probable (la del reproductor de anime).
    SOLO busca ventanas con clase Chrome_WidgetWin_1. Filtra ventanas de chat,
    settings, extensiones, etc. Sin fallbacks por título (peligrosos)."""
    user32 = ctypes.windll.user32

    # Pequeña pausa para que Chrome traiga la ventana al frente
    time.sleep(0.2)

    # Palabras que indican que NO es una ventana de anime/reproductor
    BAD_TITLES = [
        'chat', 'settings', 'configuración', 'extensions', 'extensiones',
        'devtools', 'developer tools', 'bookmark', 'history', 'historial',
        'downloads', 'descargas', 'new tab', 'nueva pestaña', 'incognito',
        'task manager', 'administrador', 'about:', 'chrome:',
        'odysseus', 'program manager',
    ]

    # Primero: foreground window (rápido, si es Chrome)
    fg = user32.GetForegroundWindow()
    if fg:
        class_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(fg, class_buf, 255)
        cls = class_buf.value
        title_len = user32.GetWindowTextLengthW(fg)
        title = ''
        if title_len > 0:
            buf = ctypes.create_unicode_buffer(title_len + 1)
            user32.GetWindowTextW(fg, buf, title_len + 1)
            title = buf.value
        log(f'_find_chrome: Foreground title="{title}" class="{cls}"')
        if cls == 'Chrome_WidgetWin_1':
            title_lower = title.lower()
            bad = any(b in title_lower for b in BAD_TITLES)
            if not bad or not title:
                log(f'_find_chrome: OK foreground (Chrome_WidgetWin_1, no es herramienta)')
                return fg
            else:
                log(f'_find_chrome: Foreground DESCARTADA (es herramienta/chat)')

    # Segundo: enumerar TODAS las ventanas Chrome_WidgetWin_1 visibles
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    found = []

    class RECT(ctypes.Structure):
        _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                    ('right', ctypes.c_long), ('bottom', ctypes.c_long)]

    def enum_proc(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 255)
            if class_buf.value == 'Chrome_WidgetWin_1':
                r = RECT()
                if user32.GetWindowRect(hwnd, ctypes.byref(r)):
                    w = r.right - r.left
                    h = r.bottom - r.top
                    # Filtrar por título
                    tlen = user32.GetWindowTextLengthW(hwnd)
                    title = ''
                    if tlen > 0:
                        tb = ctypes.create_unicode_buffer(tlen + 1)
                        user32.GetWindowTextW(hwnd, tb, tlen + 1)
                        title = tb.value
                    title_lower = title.lower()
                    bad = any(b in title_lower for b in BAD_TITLES)
                    if w > 400 and h > 300 and not bad:
                        found.append((hwnd, w * h, r.left, r.top, w, h, title))
        return True

    user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
    log(f'_find_chrome: {len(found)} ventanas Chrome_WidgetWin_1 válidas encontradas')

    if found:
        found.sort(key=lambda x: x[1], reverse=True)
        _, _, left, top, w, h, title = found[0]
        log(f'_find_chrome: elegida "{title}" ({w}x{h} en {left},{top})')
        return found[0][0]

    log('_find_chrome: NINGUNA ventana Chrome de anime encontrada')
    return None


def handle(msg):
    log(f'handle: recibido {json.dumps(msg)}')

    if not isinstance(msg, dict):
        log('handle: mensaje no es dict')
        return {'ok': False, 'error': 'invalid message'}

    action = msg.get('action') or msg.get('type')
    log(f'handle: action={action}')

    # ── PRESS_F: simular tecla F real (fullscreen toggle) ─────────────────
    if action in ('PRESS_F', 'press_f'):
        if not HAS_PYAUTOGUI:
            log('PRESS_F: pyautogui no disponible')
            return {'ok': False, 'error': 'pyautogui not installed'}
        delay_ms = msg.get('delay', 100)
        time.sleep(delay_ms / 1000.0)
        try:
            pyautogui.press('f')
            log('PRESS_F: OK')
            return {'ok': True, 'action': 'press_f'}
        except Exception as e:
            log(f'PRESS_F: error {e}')
            return {'ok': False, 'error': str(e)}

    # ── CLICK_CENTER: click en centro de ventana Chrome ──────────────────
    if action in ('CLICK_CENTER', 'click_center'):
        if not HAS_PYAUTOGUI:
            return {'ok': False, 'error': 'pyautogui not installed'}
        delay_ms = msg.get('delay', 300)
        time.sleep(delay_ms / 1000.0)

        if os.name == 'nt':
            hwnd = _find_chrome_window()
            if not hwnd:
                # Fallback: usar coordenadas del mensaje si existen
                fb_x = msg.get('x')
                fb_y = msg.get('y')
                if fb_x is not None and fb_y is not None:
                    log(f'CLICK_CENTER: fallback a coordenadas ({fb_x}, {fb_y})')
                    _win_click(fb_x, fb_y)
                    return {'ok': True, 'clicked': [fb_x, fb_y], 'fallback': True}
                log('CLICK_CENTER: no se encontró ventana Chrome')
                return {'ok': False, 'error': 'no se encontró ventana de Chrome'}

            class RECT(ctypes.Structure):
                _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                            ('right', ctypes.c_long), ('bottom', ctypes.c_long)]
            rect = RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

            cx = (rect.left + rect.right) // 2
            cy = rect.top + int((rect.bottom - rect.top) * 0.58)
            log(f'CLICK_CENTER: ventana=({rect.left},{rect.top})-({rect.right},{rect.bottom}), click=({cx},{cy})')
            _win_click(cx, cy)
            return {'ok': True, 'clicked': [cx, cy],
                    'window': [rect.left, rect.top,
                               rect.right - rect.left, rect.bottom - rect.top]}
        else:
            w, h = pyautogui.size()
            cx, cy = w // 2, h // 2
            pyautogui.click(cx, cy)
            return {'ok': True, 'clicked': [cx, cy]}

    # ── AUTO_CLICK: click en coordenadas (usa Windows API directa) ──────
    if action in ('AUTO_CLICK', 'click'):
        if not HAS_PYAUTOGUI:
            return {'ok': False, 'error': 'pyautogui not installed'}
        delay_ms = msg.get('delay', 300)
        x = msg.get('x')
        y = msg.get('y')
        if x is None or y is None:
            return {'ok': False, 'error': 'missing x/y'}
        log(f'AUTO_CLICK: ({x}, {y}) delay={delay_ms}')
        time.sleep(delay_ms / 1000.0)
        _win_click(x, y)
        return {'ok': True, 'clicked': [x, y]}

    log(f'handle: acción desconocida "{action}"')
    return {'ok': False, 'error': f'unknown action: {action}'}


def main():
    log('main: entrando en bucle')
    while True:
        msg = read_message()
        if msg is None:
            log('main: stdin cerrado, saliendo')
            break
        response = handle(msg)
        send_message(response)


if __name__ == '__main__':
    main()
