from PyQt5 import QtCore, QtGui, QtWidgets
import ProfileParser
import ItemParser
import GS
import re
import os
import sys
import json
import webbrowser
import datetime

for folder_name in ('Icons_cache', 'Items_cache', 'Char_cache'):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

ICON = 56
toolTip_show = QtWidgets.QToolTip.showText

def show_error_message(msg):
    wndw = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Critical,
        "",
        msg,
        QtWidgets.QMessageBox.Ok)
    wndw.setWindowFlags(
        QtCore.Qt.CustomizeWindowHint |
        QtCore.Qt.WindowStaysOnTopHint)
    wndw.exec_()
    sys.exit()


class GetProfile(QtCore.QThread):
    profile_loaded = QtCore.pyqtSignal(list)
    def __init__(self, char_name, server="Lordaeron"):
        super().__init__()
        self.char_name = char_name
        self.server = server
    
    def run(self):
        profile = ProfileParser.main(self.char_name, self.server)
        self.profile_loaded.emit(profile)


class UpdateStats(QtCore.QThread):
    def __init__(self, new_stats):
        super().__init__()
        self.new_stats = new_stats
    
    def run(self):
        for stat, value in self.new_stats:
            if stat in main_window.FULL_STATS:
                main_window.FULL_STATS[stat] += value
        current_stats = main_window.FULL_STATS.items()
        stats_txt = '\n'.join(f'{value:>5} {stat}' for stat, value in current_stats if value > 30)
        stats_txt = stats_txt.replace(" rating", "").title()
        _txt = f'{main_window.MAIN_TEXT}\nStats:\n{stats_txt}'
        main_window.STATS_LABEL.setText(_txt)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, char_name, server="Lordaeron"):
        super().__init__()

        self.profile_getter = GetProfile(char_name, server)
        self.profile_getter.start()
        self.profile_getter.profile_loaded.connect(self.got_profile)

        self.name = char_name
        self.setWindowTitle(char_name)
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowCloseButtonHint)
        self.setStyleSheet("QMainWindow {background-color: black} QToolTip {background-color: black; color: white; border: 1px solid white; }")

        self.labels = []
        self.item_parsers = []
        X, Y = 100, 100
        if len(sys.argv) > 3:
            X, Y = int(sys.argv[2]), int(sys.argv[3])
        self.stats_size = 230
        self.W = ICON * 2 + self.stats_size
        self.H = ICON * 9
        self.setGeometry(X, Y, self.W, self.H)
        self.setFixedSize(self.size())

        for col in (0, 1):
            for row in range(8):
                self.add_icon((self.W-ICON)*col, ICON*row)
        for col_x in (ICON, (self.W-ICON)//2, self.W-ICON*2):
            self.add_icon(col_x, ICON*8)
        
        self.STATS_LABEL = QtWidgets.QLabel(
            self,
            styleSheet="color: white",
            font=QtGui.QFont("Lucida Console", 12),
            alignment=QtCore.Qt.AlignTop)
        self.STATS_LABEL.setGeometry(ICON, 1, self.stats_size, ICON*15//2)
        
        self.add_set_change_row()
    
    def add_set_change_row(self):
        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.clicked.connect(self.change_set)
        self.back_button.setGeometry(ICON, ICON*15//2, ICON//2, ICON//2)
        self.back_button.setText('<')
        
        self.date_label = QtWidgets.QLabel(
            self,
            styleSheet="color: white",
            font=QtGui.QFont("Lucida Console", 12))
        self.date_label.setGeometry(ICON*3//2, ICON*15//2, self.stats_size-ICON, ICON//2)
        
        self.forward_button = QtWidgets.QPushButton(self)
        self.forward_button.clicked.connect(self.change_set)
        self.forward_button.setGeometry(self.W-ICON*3//2, ICON*15//2, ICON//2, ICON//2)
        self.forward_button.setText('>')

    def got_profile(self, profile):
        if not profile:
            show_error_message("Character with this name doesn't exist")
        try:
            with open(f'Char_cache/{self.name}.txt', 'r') as f:
                self.char_data = json.load(f)
        except FileNotFoundError:
            self.char_data = {}
        if profile not in self.char_data.values():
            tm = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            self.char_data[tm] = profile
            with open(f'Char_cache/{self.name}.txt', 'w') as f:
                json.dump(self.char_data, f)
        for date, gear in self.char_data.items():
            if gear == profile:
                self.date_label.setText(date)
        # self.current_set_index = -1
        self.dates = list(self.char_data.keys())
        self.set_gear(profile)
    
    def nullify_stats(self):
        self.FULL_STATS = {x: 0 for x in ItemParser.STATS_DICT.values()}

    def change_set(self):
        if len(self.dates) > 1:
            direction = -1 if self.sender().text() == '<' else 1
            current_date = self.date_label.text()
            date_index = self.dates.index(current_date)
            new_index = (date_index + direction) % len(self.char_data)
            # self.current_set_index = (self.current_set_index + cur) % len(self.char_data)
            # date = self.dates[self.current_set_index]
            date = self.dates[new_index]
            self.date_label.setText(date)
            self.set_gear(self.char_data[date])

    def add_icon(self, x, y):
        _Label = QtWidgets.QLabel(self)
        _Label.setGeometry(x, y, ICON, ICON)
        self.labels.append(_Label)
    
    def set_gear(self, profile):
        self.nullify_stats()
        gearData, gearIDs, guild, specs_profs, level_race_class = profile
        _gs = ''
        if int(level_race_class[:2]) == 80:
            _gear = GS.main(gearIDs)
            total_gs = GS.total_gs(_gear)
            _gs = f'GearScore: {total_gs}'
        self.MAIN_TEXT = f'{_gs}\n{level_race_class}\n{guild}\n\n{specs_profs}\n'
        self.STATS_LABEL.setText(self.MAIN_TEXT)
        
        for label, item_ID in zip(self.labels, gearIDs):
            if item_ID:
                self.make_item_slot(label, item_ID, gearData[item_ID])
            else:
                label.removeEventFilter(self)
                label.setObjectName('')
                label.setPixmap(QtGui.QPixmap())
    
    def make_item_slot(self, label, item_ID, data):
        label.setObjectName(item_ID)
        label.installEventFilter(self)
        _Thread = ItemParser.Item(label, item_ID, data)
        _Thread.item_loaded.connect(self.update_stats)
        _Thread.start()
        self.item_parsers.append(_Thread)

    def update_stats(self, stats):
        _Thread = UpdateStats(stats)
        _Thread.start()
        self.item_parsers.append(_Thread)
        
    def eventFilter(self, object, event):
        #Mouse hover
        if event.type() == 10:
            p = self.geometry()
            p = p.bottomRight() if self.x() > 1350 else p.bottomLeft()
            tool_tip_text = ItemParser.TTS.get(object, '')
            toolTip_show(p, tool_tip_text, self)
        #Mouse click, left
        elif event.type() == 2 and event.button() == 1:
            item_ID = object.objectName()
            webbrowser.open(f'https://wotlk.evowow.com/?item={item_ID}')
        return False


if __name__ == "__main__":
    try:
        char_name = sys.argv[1]
        char_name = re.findall('[^A-z\(]?([A-z]{2,12})', char_name, re.S)[-1]
        char_name = char_name.lower().capitalize()
    except: #default value if none provided
        char_name = "Nomadra"
    # old_ench = dict(ItemParser.ENCHANCEMENTS_DATA)
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(char_name)
    main_window.show()
    app.exec_()
    try:
        with open('ench_cache.txt','r') as f:
            old_ench = json.load(f)
    except FileNotFoundError:
        old_ench = {}
    if old_ench != ItemParser.ENCHANCEMENTS_DATA:
        with open('ench_cache.txt', 'w') as f:
            json.dump(ItemParser.ENCHANCEMENTS_DATA, f)
