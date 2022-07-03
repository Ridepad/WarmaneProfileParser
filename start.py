import json
import os
import re
import sys
from ctypes import windll

import pynput
import win32clipboard
from PyQt5 import QtCore, QtGui, QtWidgets

import profile_window
from constants import DIR_PATH, STATIC_DIR, json_write, json_read

SERVER_NAMES = ["Lordaeron", "Icecrown", "Frostmourne", "Blackrock"]

SERVER_FILE = os.path.join(DIR_PATH, "_server.cfg")
HOTKEYS_FILE = os.path.join(DIR_PATH, "_hotkeys.cfg")

MAIN_ICON = os.path.join(STATIC_DIR, "logo.ico")
EXIT_ICON = os.path.join(STATIC_DIR, "turn-off.png")
SETTINGS_ICON = os.path.join(STATIC_DIR, "wrench.png")
CLOSE_ALL_ICON = os.path.join(STATIC_DIR, "close.png")
NEW_WINDOW_ICON = os.path.join(STATIC_DIR, "new-page.png")
CHANGE_SERVER_ICON = os.path.join(STATIC_DIR, "server.png")

MODIFIERS = ['<ctrl>', '<alt>', '<shift>']
HOTKEYS = json_read(HOTKEYS_FILE) or {
    "new_window": "<ctrl>+<alt>+c",
    "close_all": "<ctrl>+<alt>+w",
    "change_server": "<ctrl>+<alt>+<f1>",
    "full_exit": "<ctrl>+<alt>+<f2>"
}
HOTKEYS_FUNC = {
    "New window": "new_window",
    "Close all": "close_all",
    "Change server": "change_server",
    "Full exit": "full_exit",
}

def swap_to_english():
    def is_english_layout():
        thread_id = windll.kernel32.GetCurrentThreadId()
        kb_layout = windll.user32.GetKeyboardLayout(thread_id)
        return kb_layout & 0x3ff == 9
    
    for _ in range(10):
        if is_english_layout():
            break
        windll.user32.ActivateKeyboardLayout(1, 0x00000100)

def get_clipboard():
    win32clipboard.OpenClipboard()
    try:
        cboard = win32clipboard.GetClipboardData()
        win32clipboard.EmptyClipboard()
    except Exception:
        cboard = ''
    win32clipboard.CloseClipboard()
    re_find: list[str] = re.findall('([A-Za-z]{2,12})', cboard, re.S)
    if re_find:
        return re_find[-1].lower().capitalize()

def parse_key(k: str):
    *mods, key = k.split('+')
    kb = [k in mods for k in MODIFIERS]
    kb.append(key)
    return kb

def show_message(parent_window):
    wndw = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Information,
        "",
        "Saved",
        QtWidgets.QMessageBox.Ok)
    wndw.setWindowFlags(
        QtCore.Qt.CustomizeWindowHint |
        QtCore.Qt.WindowStaysOnTopHint
        )
    wndw.exec_()
    parent_window.close()


class KeybindsChangeWindowKeybinds(QtCore.QThread):
    keypress = QtCore.pyqtSignal(str)

    def on_release(self, key: pynput.keyboard.Key):
        if key == pynput.keyboard.Key.esc:
            self.keypress.emit('')
            return
        try:
            k = str(key.char)
            try:
                o = ord(k)
                if o < 20 or o > 126:
                    k = ''
            except TypeError:
                k = ''
        except AttributeError:
            k = str(key)
            if '.f' not in k:
                return
            k = f"<{k[4:]}>"
        
        self.keypress.emit(k.lower())

    def run(self):
        swap_to_english()

        with pynput.keyboard.Listener(
                on_release=self.on_release,
            ) as self.listener:
            self.listener.join()

class KeybindsChangeWindow(QtWidgets.QMainWindow):
    closed = QtCore.pyqtSignal()

    def __init__(self):
        self.HOTKEYS = {
            func: parse_key(keybind)
            for func, keybind in HOTKEYS.items()
        }
        super().__init__()

        self.icon = QtGui.QIcon(MAIN_ICON)

        self.setWindowIcon(self.icon)
        self.setGeometry(900, 500, 173, 113)
        self.setFixedSize(self.size())
        self.setWindowTitle("KEYBINDS CHANGE")
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowCloseButtonHint
        )

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        self.grid_layout = QtWidgets.QGridLayout(self.centralwidget)
        self.centralwidget.setLayout(self.grid_layout)

        self.label2 = QtWidgets.QLabel('Keybind:', self)
        self.grid_layout.addWidget(self.label2, 0, 0)

        
        self.comboBox = QtWidgets.QComboBox()
        for func_name in HOTKEYS_FUNC:
            self.comboBox.addItem(f"- {func_name}")
        self.comboBox.currentTextChanged.connect(self.new_cat)
        self.grid_layout.addWidget(self.comboBox, 0, 1)

        self.lineedit = QtWidgets.QLineEdit()
        self.lineedit.setReadOnly(True)
        self.grid_layout.addWidget(self.lineedit, 1, 1, 2, 1)

        self.is_ctrl = QtWidgets.QCheckBox('Ctrl', self)
        self.grid_layout.addWidget(self.is_ctrl, 1, 0)

        self.is_alt = QtWidgets.QCheckBox('Alt', self)
        self.grid_layout.addWidget(self.is_alt, 2, 0)

        self.is_shift = QtWidgets.QCheckBox('Shift', self)
        self.grid_layout.addWidget(self.is_shift, 3, 0)

        self.last_cbox = self.comboBox.currentText()
        self.get_state()

        self.save_button = QtWidgets.QPushButton("Save", self)
        self.save_button.clicked.connect(self.save)
        self.grid_layout.addWidget(self.save_button, 3, 1)

        self.keyboard_hook = KeybindsChangeWindowKeybinds()
        self.keyboard_hook.keypress.connect(self.keypress)
        self.keyboard_hook.start()

    def keypress(self, s):
        self.lineedit.setText(s)

    def c_v(self):
        return HOTKEYS_FUNC[self.last_cbox[2:]]
    
    def get_state(self):
        ctrl, alt, shift, key = self.HOTKEYS[self.c_v()]
        self.is_ctrl.setChecked(ctrl)
        self.is_alt.setChecked(alt)
        self.is_shift.setChecked(shift)
        self.lineedit.setText(key)

    def save_state(self):
        self.HOTKEYS[self.c_v()] = [
            self.is_ctrl.isChecked(),
            self.is_alt.isChecked(),
            self.is_shift.isChecked(),
            self.lineedit.text()
        ]

    def new_cat(self):
        self.save_state()
        self.last_cbox = self.comboBox.currentText()
        self.get_state()

    def save(self):
        self.last_cbox = self.comboBox.currentText()
        self.save_state()
        for func, keybind in self.HOTKEYS.items():
            if not keybind[-1]:
                HOTKEYS[func] = ''
                continue
            k = [kv for kb, kv in zip(keybind, MODIFIERS) if kb]
            k.append(keybind[-1])
            HOTKEYS[func] = '+'.join(k)
        json_write(HOTKEYS_FILE, HOTKEYS, indent=2)
        show_message(self)

    def closeEvent(self, event):
        self.keyboard_hook.listener.stop()
        self.closed.emit()


class ServerChange(QtWidgets.QMainWindow):
    server_changed = QtCore.pyqtSignal(str)

    def __init__(self, server: str):
        super().__init__()
        self.server = server

        self.icon = QtGui.QIcon(MAIN_ICON)

        self.setWindowIcon(self.icon)
        self.setGeometry(900, 500, 224, 41)
        self.setFixedSize(self.size())
        self.setWindowTitle("Server change")
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowCloseButtonHint
        )

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
    
        self.verticalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.centralwidget.setLayout(self.verticalLayout)
        
        self.label = QtWidgets.QLabel()
        self.label.setText('Select server:')
        self.verticalLayout.addWidget(self.label)

        self.comboBox = QtWidgets.QComboBox()
        for server_name in SERVER_NAMES:
            self.comboBox.addItem(server_name)
        self.comboBox.setCurrentText(self.server)
        self.verticalLayout.addWidget(self.comboBox)

        self.save_button = QtWidgets.QPushButton("Save", self)
        h = self.save_button.sizeHint().height()
        self.save_button.setFixedSize(40, h)
        self.save_button.clicked.connect(self.save_server)
        self.verticalLayout.addWidget(self.save_button)

    def save_server(self):
        _server = self.comboBox.currentText()
        if _server != self.server:
            self.server = _server
            self.server_changed.emit(_server)
            with open(SERVER_FILE, 'w') as f:
                f.write(_server)
            show_message(self)


class MainWindowKeybinds(QtCore.QThread):
    for func, keybind in HOTKEYS.items():
        if keybind:
            vars()[func] = QtCore.pyqtSignal()

    def run(self):
        swap_to_english()

        _keys = {
            keybind: getattr(self, func).emit
            for func, keybind in HOTKEYS.items()
            if keybind
        }

        with pynput.keyboard.GlobalHotKeys(_keys) as self.listener:
            self.listener.join()


class MainWindow(QtWidgets.QMainWindow):
    char_windows: list[profile_window.CharWindow] = []
    
    def __init__(self):
        super().__init__()

        self.icon = QtGui.QIcon(MAIN_ICON)

        self.setWindowIcon(self.icon)
        self.setGeometry(900, 500, 224, 41)
        self.setFixedSize(self.size())
        self.setWindowTitle("WarmaneProfileParser")
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowCloseButtonHint
        )

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
    
        self.verticalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.centralwidget.setLayout(self.verticalLayout)

        try:
            with open(SERVER_FILE) as f:
                self.server = f.read()
        except FileNotFoundError:
            self.server = "Lordaeron"

        self.change_server_window = ServerChange(self.server)
        self.change_server_window.server_changed.connect(self.server_changed)

        self.change_server_button = QtWidgets.QPushButton("Change server", self)
        self.change_server_button.clicked.connect(self.change_server)
        self.verticalLayout.addWidget(self.change_server_button)

        self.change_keybinds_button = QtWidgets.QPushButton("Change keybinds", self)
        self.change_keybinds_button.clicked.connect(self.open_keybinds_settings)
        self.verticalLayout.addWidget(self.change_keybinds_button)

        h = self.change_server_button.sizeHint().height()
        self.change_server_button.setFixedSize(100, h)
        self.change_keybinds_button.setFixedSize(100, h)

        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.icon)
        self.tray_icon.activated.connect(self.systemIcon)
        self.tray_icon.show()

        self.add_kb_hook()

    def server_changed(self, server):
        self.server = server
    
    def add_kb_hook(self):
        self.keyboard_hook = MainWindowKeybinds()
        for func, keybind in HOTKEYS.items():
            if keybind:
                getattr(self.keyboard_hook, func).connect(getattr(self, func))
        self.keyboard_hook.start()
        self.add_tray_menu()

    def add_tray_menu(self):
        def get_keybind(func):
            return HOTKEYS[HOTKEYS_FUNC[func]].title()
        
        tray_menu = QtWidgets.QMenu()

        _change_kb = QtWidgets.QAction("Change keybinds", self)
        _change_kb.setIcon(QtGui.QIcon(SETTINGS_ICON))
        _change_kb.triggered.connect(self.open_keybinds_settings)
        tray_menu.addAction(_change_kb)

        _kb = get_keybind("New window")
        _new_w = QtWidgets.QAction(f"Open new window {_kb}", self)
        _new_w.setIcon(QtGui.QIcon(NEW_WINDOW_ICON))
        _new_w.triggered.connect(self.new_window)
        tray_menu.addAction(_new_w)

        _kb = get_keybind("Close all")
        _close_all = QtWidgets.QAction(f"Close all windows {_kb}", self)
        _close_all.setIcon(QtGui.QIcon(CLOSE_ALL_ICON))
        _close_all.triggered.connect(self.close_all)
        tray_menu.addAction(_close_all)

        _kb = get_keybind("Change server")
        _server_change = QtWidgets.QAction(f"Change server {_kb}", self)
        _server_change.setIcon(QtGui.QIcon(CHANGE_SERVER_ICON))
        _server_change.triggered.connect(self.change_server)
        tray_menu.addAction(_server_change)

        _kb = get_keybind("Full exit")
        _exit = QtWidgets.QAction(f"Exit {_kb}", self)
        _exit.setIcon(QtGui.QIcon(EXIT_ICON))
        _exit.triggered.connect(self.full_exit)
        tray_menu.addAction(_exit)

        self.tray_icon.setContextMenu(tray_menu)

    def open_keybinds_settings(self):
        self.keyboard_hook.listener.stop()
        self.keybinds_settings_window = KeybindsChangeWindow()
        self.keybinds_settings_window.closed.connect(self.add_kb_hook)
        self.keybinds_settings_window.show()

    def change_server(self):
        self.change_server_window.show()


    def show_tray_msg(self, msg, warning=False):
        tray = QtWidgets.QSystemTrayIcon
        icon = tray.Critical if warning else tray.Information
        self.tray_icon.showMessage("WarmaneProfileParser", msg, icon)

    def remove_error(self, window: profile_window.CharWindow):
        self.char_windows.remove(window)
        self.show_tray_msg("Character with this name doesn't exist, maybe wrong server?", True)

    def new_window(self):
        char_name = get_clipboard()
        if char_name is None:
            return
        
        _window = profile_window.CharWindow(char_name, self.server)
        _window.is_terminated.connect(self.remove_error)
        self.char_windows.append(_window)
        _window.show()

    def close_all(self):
        for window in self.char_windows:
            window.close()
            window.deleteLater()
        self.char_windows.clear()
        

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.sender() is None:
            event.ignore()
            self.hide()
            self.show_tray_msg("Running in background")
        
    def systemIcon(self, action):
        if action == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show()

    def full_exit(self):
        QtWidgets.qApp.quit()


if __name__ == "__main__":
    try:
        with open(HOTKEYS_FILE) as f:
            HOTKEYS = json.load(f)
    except FileNotFoundError:
        pass

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    mw = MainWindow()
    mw.show_tray_msg("Running in background")
    app.exec_()
