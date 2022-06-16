import json
import os
import sys
import webbrowser
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets

import AchiParser
import GS
import ItemParser
import ProfileParser


def new_folder_path(root, name):
    new_folder = os.path.join(root, name)
    if not os.path.exists(new_folder):
        os.makedirs(new_folder, exist_ok=True)
    return new_folder

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)

CACHE_DIR = new_folder_path(DIR_PATH, "cache")
STATIC_DIR = new_folder_path(DIR_PATH, "static")
ERRORS_DIR = new_folder_path(DIR_PATH, "errors")

SIZE_FILE = os.path.join(DIR_PATH, "_achi_size.cfg")
MAIN_ICON = os.path.join(STATIC_DIR, "logo.ico")

CACHES = {"enchants", "icons", "items"}
for cache_name in CACHES:
    new_folder_path(CACHE_DIR, cache_name)
CHAR_CACHE = new_folder_path(CACHE_DIR, "characters")

ICON = 56
ACHI_ICONS = {
    'ICC': os.path.join(STATIC_DIR, "icc.png"),
    'Naxx': os.path.join(STATIC_DIR, "naxx.png"),
    'Ulduar': os.path.join(STATIC_DIR, "ulduar.png"),
    'Other': os.path.join(STATIC_DIR, "rs.png"),
}

STYLESHEET = """
* {
    color: gainsboro;
    background-color: black;
}
QToolTip {
    border-radius: 3px;
    border: 1px solid gainsboro;
}
QLabel {
    font: 12pt "Lucida Console";
}
QPushButton {
    font-weight: 600;
    border-radius: 3px;
    border: 1px solid gainsboro;
    font: 12pt "Lucida Console";
}
"""

def open_json(filename) -> dict:
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def format_specs(profile: dict):
    _filter = {'Fishing', 'First Aid'}
    specs_profs = []
    for x in ['specs', 'profs']:
        t = [
            f'{name:<14}{value:>9}'
            for name, value in profile[x].items()
            if name not in _filter
        ]
        while len(t) < 3:
            t.append('')
        specs_profs.extend(t)
    return '\n'.join(specs_profs)


class GetProfile(QtCore.QThread):
    profile_loaded = QtCore.pyqtSignal(dict)
    def __init__(self, char_name: str, server: str):
        super().__init__()
        self.char_name = char_name
        self.server = server
    
    def run(self):
        profile = ProfileParser.get_profile(self.char_name, self.server)
        self.profile_loaded.emit(profile)


class CharWindow(QtWidgets.QMainWindow):
    is_terminated = QtCore.pyqtSignal(QtWidgets.QMainWindow)
    def __init__(self, char_name: str, server: str="Lordaeron", X: int=100, Y: int=100):
        super().__init__()
        self.stats_size = 230
        self.W = ICON * 2 + self.stats_size
        self.H = ICON * 9
        self.setGeometry(X, Y, self.W, self.H)
        self.setFixedSize(self.size())
        self.setWindowTitle(char_name)
        self.setWindowIcon(QtGui.QIcon(MAIN_ICON))
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowCloseButtonHint)
        self.setStyleSheet(STYLESHEET)
        
        self.STATS_LABEL = QtWidgets.QLabel(self)
        self.STATS_LABEL.setAlignment(QtCore.Qt.AlignTop)
        self.STATS_LABEL.setGeometry(ICON, 1, self.stats_size, ICON*14//2)

        self.char_name = char_name
        self.server = server
        self.item_icons: list[QtWidgets.QLabel] = []
        self.item_parsers: list[ItemParser.Item] = []
        self.dates: list[str] = []
        
        server_cache = new_folder_path(CHAR_CACHE, server)
        self.char_cache = os.path.join(server_cache, f"{char_name}.json")
        self.char_data: dict[str, dict] = open_json(self.char_cache)

        self.fetch_profile()
        self.add_gear_icons()
        self.add_achi_row()
        self.add_set_change_row()
        self.add_size_button()
        self.add_refresh_button()

    def fetch_profile(self):
        self.profile_getter = GetProfile(self.char_name, self.server)
        self.profile_getter.profile_loaded.connect(self.got_profile)
        self.profile_getter.start()

    def add_gear_icons(self):
        def add_icon(x, y):
            _Label = QtWidgets.QLabel(self)
            _Label.setGeometry(x, y, ICON, ICON)
            self.item_icons.append(_Label)
        
        for col in (0, 1):
            for row in range(8):
                add_icon((self.W-ICON)*col, ICON*row)
        for col_x in (ICON, (self.W-ICON)//2, self.W-ICON*2):
            add_icon(col_x, ICON*8)

    def add_achi_row(self):
        self.achi_labels = []
        self.achi_tooltips = {
            "10": {'done': {},'threads': {},},
            "25": {'done': {},'threads': {},},
        }
        for col, (cat_name, icon) in enumerate(ACHI_ICONS.items(), 1):
            _Label = QtWidgets.QLabel(self)
            _Label.setGeometry(ICON*col, ICON*7, ICON, ICON//2)
            _pixmap = QtGui.QPixmap(icon)
            _Label.setPixmap(_pixmap)
            _Label.setObjectName(cat_name)
            _Label.installEventFilter(self)
            self.achi_labels.append(_Label)
    
    def add_set_change_row(self):
        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.clicked.connect(self.change_set)
        self.back_button.setGeometry(ICON, ICON*15//2, ICON//2, ICON//2)
        self.back_button.setText('<')
        self.back_button.setObjectName('setPrevious')
        
        self.date_label = QtWidgets.QLabel(self)
        self.date_label.setGeometry(ICON*3//2, ICON*15//2, self.stats_size-ICON, ICON//2)
        
        self.forward_button = QtWidgets.QPushButton(self)
        self.forward_button.clicked.connect(self.change_set)
        self.forward_button.setGeometry(self.W-ICON*3//2, ICON*15//2, ICON//2, ICON//2)
        self.forward_button.setText('>')
        self.forward_button.setObjectName('setNext')

    def change_player_size(self):
        self.achi_player_size = "10" if self.achi_player_size == "25" else "25"
        self.player_size_button.setText(self.achi_player_size)
        with open(SIZE_FILE, 'w') as f:
            f.write(self.achi_player_size)
    
    def add_size_button(self):
        try:
            with open(SIZE_FILE, 'r') as f:
                self.achi_player_size = f.read()
        except FileNotFoundError:
            self.achi_player_size = "25"
        
        self.player_size_button = QtWidgets.QPushButton(self)
        self.player_size_button.setText(self.achi_player_size)
        self.player_size_button.setGeometry(0, ICON*8, 56, 56)
        self.player_size_button.clicked.connect(self.change_player_size)
        self.player_size_button.installEventFilter(self)
        self.player_size_button.setObjectName('size_change')

    def add_refresh_button(self):
        self.gear_refresh = QtWidgets.QPushButton(self)
        self.gear_refresh.setGeometry(self.W-ICON, ICON*8, 56, 56)
        self.gear_refresh.clicked.connect(self.fetch_profile)
        self.gear_refresh.setIcon(QtGui.QIcon('static/download.png'))
        self.gear_refresh.setIconSize(QtCore.QSize(50, 50))
        self.gear_refresh.installEventFilter(self)
        self.gear_refresh.setObjectName('gear_refresh')

    def got_profile(self, profile: dict):
        if not profile:
            self.close()
            self.deleteLater()
            self.is_terminated.emit(self)
            return
        
        if profile not in self.char_data.values():
            date = datetime.now().strftime("%y-%m-%d %H:%M:%S")
            self.char_data[date] = profile
            self.date_label.setText(date)
            save_json(self.char_cache, self.char_data)
        else:
            for date, data in self.char_data.items():
                if data == profile:
                    self.date_label.setText(date)

        self.dates = list(self.char_data)
        self.set_gear(profile)

    def change_set(self):
        if len(self.dates) < 2:
            return
        direction = -1 if self.sender().text() == '<' else 1
        current_date = self.date_label.text()
        date_index = self.dates.index(current_date)
        new_index = (date_index + direction) % len(self.char_data)
        date = self.dates[new_index]
        self.date_label.setText(date)
        profile = self.char_data[date]
        self.set_gear(profile)

    def update_stats(self, stats):
        for stat, value in stats:
            if stat in self.FULL_STATS:
                self.FULL_STATS[stat] += value
        current_stats = self.FULL_STATS.items()
        stats_txt = '\n'.join(f'{value:>5} {stat}' for stat, value in current_stats if value > 30)
        stats_txt = stats_txt.replace(" rating", "").title()
        _txt = f'{self.MAIN_TEXT}\nStats:\n{stats_txt}'
        self.STATS_LABEL.setText(_txt)
    
    def set_icons(self, profile):
        gear_data: list[dict[str, str]] = profile['gear_data']
        for item_icon, item_data in zip(self.item_icons, gear_data):
            if not item_data:
                item_icon.setObjectName('')
                item_icon.removeEventFilter(self)
                item_icon.setPixmap(QtGui.QPixmap())
                continue
            item_ID = item_data["item"]
            item_icon.setObjectName(item_ID)
            item_icon.installEventFilter(self)
            _Thread = ItemParser.Item(item_data, item_icon, self.is_enchanter)
            _Thread.item_loaded.connect(self.update_stats)
            _Thread.start()
            self.item_parsers.append(_Thread)
    
    def nullify_stats(self):
        self.FULL_STATS = {x: 0 for x in ItemParser.STATS_DICT.values()}
    
    def set_gear(self, profile):
        self.nullify_stats()
        _gs = ''
        if profile['level'] == "80":
            gear_IDs = [item_data.get('item') for item_data in profile['gear_data']]
            gear_GS = GS.main(gear_IDs)
            _gs = f'GearScore: {sum(gear_GS)}'
        level_race_class = " ".join(profile[x] for x in ['level', 'race', 'class'])
        specs_profs = format_specs(profile)
        self.MAIN_TEXT = f"{_gs}\n{level_race_class}\n{profile['guild']}\n\n{specs_profs}\n"
        self.is_enchanter = 'Enchanting' in profile['profs']
        self.STATS_LABEL.setText(self.MAIN_TEXT)

        self.set_icons(profile)
        
    def showToolTip(self, tool_tip_text):
        pos = self.geometry()
        pos = pos.bottomRight() if self.x() > 1350 else pos.bottomLeft()
        if QtWidgets.QToolTip.text() == tool_tip_text:
            tool_tip_text += " " # removes tooltip flickering
        QtWidgets.QToolTip.showText(pos, tool_tip_text, self)

    def get_tooltip(self, source: QtWidgets.QWidget):
        if type(source) == QtWidgets.QPushButton:
            button_name = source.objectName()
            if button_name == "gear_refresh":
                return '<font size=5>Refresh gear</font>'
            elif button_name == "size_change":
                return '<font size=5>Change achievements player size</font>'

        elif source.objectName().isdigit():
            return ItemParser.TOOLTIPS.get(source)

        else:
            ts = self.achi_tooltips[self.achi_player_size]
            if source in ts['done']:
                return ts['done'][source]
            elif source not in ts['threads']:
                t = AchiToolTip(self, source)
                t.tt_loaded.connect(self.showToolTip)
                t.start()
                ts['threads'][source] = t

    def eventFilter(self, source: QtWidgets.QWidget, event):
        if event.type() == 3:
            if event.button() == 1:
                item_ID = source.objectName()
                if item_ID.isdigit():
                    webbrowser.open(f'https://wotlk.evowow.com/?item={item_ID}')
        
        elif event.type() == 10:
            tool_tip_text = self.get_tooltip(source)
            if not tool_tip_text:
                tool_tip_text = '<font size=5>Loading...</font>'
            self.showToolTip(tool_tip_text)

        return False


class AchiToolTip(QtCore.QThread):
    tt_loaded = QtCore.pyqtSignal(str)
    def __init__(self, main_window: CharWindow, source: QtWidgets.QLabel):
        super().__init__()
        self.main_window = main_window
        self.source = source
        self.args = {
            "char_name": main_window.char_name,
            "server": main_window.server,
            "size": main_window.achi_player_size,
            "category_name": source.objectName(),
        }

    def save_cache(self, tooltip):
        tts = self.main_window.achi_tooltips
        size = self.main_window.achi_player_size
        tts[size]['done'][self.source] = tooltip

    def run(self):
        tooltip = AchiParser.make_toolTip(**self.args)
        self.save_cache(tooltip)
        self.tt_loaded.emit(tooltip)


if __name__ == "__main__":
    try:
        char_name = sys.argv[1]
    except IndexError: # default value if none provided
        char_name = "Nomadra"
    try:
        server = sys.argv[2]
    except IndexError: # default value if none provided
        server = "Lordaeron"

    __x, __y = 100, 100
    if len(sys.argv) > 3:
        __x, __y = int(sys.argv[2]), int(sys.argv[3])

    app = QtWidgets.QApplication(sys.argv)
    main_window = CharWindow(char_name, server=server, X=__x, Y=__y)
    main_window.show()
    app.exec_()
    