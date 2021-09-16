import subprocess

import pynput
import win32clipboard


HOTKEY_NEW_WINDOW = '<ctrl>+<f1>'
HOTKEY_EXIT = '<ctrl>+<f2>'
WINDOWS = []
win32clipboard.OpenClipboard()
win32clipboard.EmptyClipboard()
win32clipboard.CloseClipboard()

def new_window():
    win32clipboard.OpenClipboard()
    try:
        _clipboard = win32clipboard.GetClipboardData()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        try: #release version
            w = subprocess.Popen(['main.exe', _clipboard])
        except FileNotFoundError: #developer debug version
            w = subprocess.Popen(['python', 'main.pyw', _clipboard])
        print('LOG:   NEW WINDOW FOR:', _clipboard)
        WINDOWS.append(w)
    except TypeError:
        print('ERROR: Clipboard is empty!')
        win32clipboard.CloseClipboard()

def _exit():
    for w in WINDOWS:
        subprocess.call(f'taskkill /pid {w.pid} /f /t')
    exit()

def main():
    _keys = {
        HOTKEY_NEW_WINDOW: new_window,
        HOTKEY_EXIT: _exit,
        }
    with pynput.keyboard.GlobalHotKeys(_keys) as listener:
        listener.join()

main()
