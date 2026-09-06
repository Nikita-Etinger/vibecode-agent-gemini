import time
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

def click(x: int, y: int, button: str = "left", clicks: int = 1, duration: float = 0.2):
    pyautogui.moveTo(x, y, duration=duration)
    pyautogui.click(x=x, y=y, clicks=clicks, button=button)
    return f"Клик [{button}] в ({x}, {y}) выполнен (кол-во: {clicks})"

def drag(from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5, button: str = "left"):
    pyautogui.moveTo(from_x, from_y)
    pyautogui.dragTo(to_x, to_y, duration=duration, button=button)
    return f"Перетаскивание из ({from_x}, {from_y}) в ({to_x}, {to_y}) выполнено"

def write(text: str, interval: float = 0.05):
    pyautogui.write(text, interval=interval)
    return f"Напечатан текст: '{text}'"

def paste(text: str):
    import pyperclip
    pyperclip.copy(text)
    time.sleep(0.05)
    pyautogui.hotkey('ctrl', 'v')
    return f"Вставлен текст из буфера: '{text}'"

def pin_window(window_title: str):
    import ctypes
    user32 = ctypes.windll.user32
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    found = False
    def enum_cb(hwnd, lparam):
        nonlocal found
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if window_title.lower() in buf.value.lower():
                    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)
                    found = True
        return True
    cb = EnumWindowsProc(enum_cb)
    user32.EnumWindows(cb, 0)
    return f"Окно '{window_title}' закреплено поверх остальных: {found}"

def hotkey(*keys, **kwargs):
    actual_keys = list(keys)
    if "keys" in kwargs:
        k = kwargs["keys"]
        if isinstance(k, (list, tuple)):
            actual_keys.extend(k)
        else:
            actual_keys.append(k)
    pyautogui.hotkey(*actual_keys)
    return f"Нажата комбинация: {' + '.join(actual_keys)}"

def press(key: str):
    pyautogui.press(key)
    return f"Нажата клавиша: {key}"

def scroll(clicks: int):
    pyautogui.scroll(clicks)
    return f"Прокрутка колесика: {clicks}"
