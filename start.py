import keyboard
import subprocess
import win32clipboard

#TODO: open new window to select server

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
        windows.append(w)
    except TypeError:
        print('ERROR: Clipboard is empty!')
        win32clipboard.CloseClipboard()

windows = []
win32clipboard.OpenClipboard()
win32clipboard.EmptyClipboard()
win32clipboard.CloseClipboard()
keyboard.add_hotkey('ctrl+F1', new_window, suppress=True)
keyboard.wait('ctrl+F2')
for w in windows:
    w.terminate()
