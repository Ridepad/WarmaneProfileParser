# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import ProfileParser
import ItemParser
import GS
import re
import os
import sys
import json
import webbrowser
# from datetime 
import datetime

if not os.path.exists('Icons_cache'):
    os.makedirs('Icons_cache')
if not os.path.exists('Items_cache'):
    os.makedirs('Items_cache')
if not os.path.exists('Char_cache'):
    os.makedirs('Char_cache')

ICON = 56
toolTip_show = QtWidgets.QToolTip.showText
    
def stats_format(q):
    stat, value = q
    stat = ItemParser.STATS_DICT.get(stat, stat)
    return stat, value

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


class UpdateStats(QtCore.QThread):
    def __init__(self, new_stats):
        super().__init__()
        self.new_stats = new_stats
    
    def run(self):
        for stat, value in self.new_stats:
            if stat in main_window.FULL_STATS:
                main_window.FULL_STATS[stat] += value
            # else:
            #     print('MISSING STAT?', stat, value)
        stats_txt = '\n'.join(f'{value:>5} {stat}' for stat, value in main_window.FULL_STATS.items() if value > 30)
        stats_txt = stats_txt.replace(" rating", "").title()
        _txt = f'{main_window.MAIN_TEXT}\nStats:\n{stats_txt}'
        main_window.STATS_LABEL.setText(_txt)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, char_name, server="Lordaeron"):
        super().__init__()
        self.setWindowTitle(char_name)
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowCloseButtonHint)
        self.setStyleSheet("QMainWindow {background-color: black} QToolTip {background-color: black; color: white; border: 1px solid white; }")
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        self.labels = []
        self.item_parsers = []
        X, Y = 100, 100
        if len(sys.argv) > 3:
            X, Y = int(sys.argv[2]), int(sys.argv[3])
        stats_size = 230
        W = ICON * 2 + stats_size
        H = ICON * 9
        self.setGeometry(X, Y, W, H)
        self.setFixedSize(self.size())
        
        self.second_column = W - ICON
        for x in (0, 1):
            for y in range(8):
                self.add_icon(x*self.second_column, y*ICON)
        bottom_row = (ICON, (W-ICON)//2, self.second_column-ICON)
        for x in bottom_row:
            self.add_icon(x, 8 * ICON)
        
        self.STATS_LABEL = QtWidgets.QLabel(
            self,
            styleSheet="color: white",
            font=QtGui.QFont("Lucida Console", 12),
            alignment=QtCore.Qt.AlignTop)
        self.STATS_LABEL.setGeometry(ICON, 10, stats_size, ICON*6)

        
        self.forward_button = QtWidgets.QPushButton(self)
        self.forward_button.clicked.connect(self.change_set)
        self.forward_button.setGeometry(self.second_column - ICON//2, ICON*15//2, ICON//2, ICON//2)
        self.forward_button.setText('>')
        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.clicked.connect(self.change_set)
        self.back_button.setGeometry(ICON, ICON*15//2, ICON//2, ICON//2)
        self.back_button.setText('<')

        self.date_label = QtWidgets.QLabel(
            self,
            styleSheet="color: white",
            font=QtGui.QFont("Lucida Console", 12))
        self.date_label.setGeometry(ICON*1.5, ICON*15//2, stats_size-ICON, ICON//2)

        # profile = [{'51290': {'ench': '3820', 'gems': ['3621', '3520', '0'], 'transmog': '22718'}, '50724': {'gems': ['3520', '0', '0']}, '51292': {'ench': '3810', 'gems': ['3520', '0', '0']}, '54583': {'ench': '3859', 'gems': ['3520', '0', '0'], 'transmog': '20579'}, '51294': {'ench': '3832', 'gems': ['3520', '3560', '0']}, '52019': {'gems': ['0', '0', '0']}, '31778': {'gems': ['0', '0', '0']}, '54584': {'ench': '3758', 'gems': ['3563', '0', '0']}, '51291': {'ench': '3604', 'gems': ['3520', '0', '0']}, '50613': {'gems': ['3520', '3520', '3520']}, '50694': {'ench': '3719', 'gems': ['3520', '3545', '3560']}, '50699': {'ench': '3606', 'gems': ['3545', '3520', '0']}, '50664': {'gems': ['3520', '0', '0']}, '50398': {'gems': ['3560', '0', '0']}, '50365': {'gems': ['0', '0', '0']}, '54588': {'gems': ['0', '0', '0']}, '50734': {'ench': '3834', 'gems': ['3520', '0', '0'], 'transmog': '32500'}, '50719': {'transmog': '39199', 'gems': ['0', '0', '0']}, '50457': {'gems': ['0', '0', '0']}}, ['51290', '50724', '51292', '54583', '51294', '52019', '31778', '54584', '51291', '50613', '50694', '50699', '50664', '50398', '50365', '54588', '50734', '50719', '50457'], 'Illusion', 'Balance         58/0/13\nRestoration     18/0/53\n\nEngineering         450\nLeatherworking      450\n\nCooking             450\n']
        profile = ProfileParser.main(char_name, server)
        # print(profile)
        
  
        if not profile:
            show_error_message("Character with this name doesn't exist")
        try:
            with open(f'Char_cache/{char_name}.txt', 'r') as f:
                self.char_data = json.loads(f.read())
        except FileNotFoundError:
            self.char_data = {}
        if profile not in self.char_data.values():
            tm = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            self.char_data[tm] = profile
            with open(f'Char_cache/{char_name}.txt', 'w') as f:
                f.write(json.dumps(self.char_data))
        for k, v in self.char_data.items():
            if v == profile:
                self.date_label.setText(k)
        self.current_set_index = -1
        self.got_gear(profile)
    
    def nulify_stats(self):
        self.FULL_STATS = {x: 0 for x in ItemParser.STATS_DICT.values()}

    def change_set(self):
        print(self.sender().text)
        cur = -1 if self.sender().text == '<' else 1
        self.current_set_index = (self.current_set_index + cur) % len(self.char_data)
        k = list(self.char_data.keys())[self.current_set_index]
        self.date_label.setText(k)
        self.got_gear(self.char_data[k])

    def add_icon(self, x, y):
        _Label = QtWidgets.QLabel(self)
        _Label.setGeometry(x, y, ICON, ICON)
        self.labels.append(_Label)
    
    def got_gear(self, profile):
        self.nulify_stats()
        gearData, gearIDs, guild, specsProfs = profile
        _gear = GS.main(gearIDs)
        total_gs = GS.total_gs(_gear)
        self.MAIN_TEXT = f'GearScore: {total_gs}\n{guild}\n\n{specsProfs}'
        self.STATS_LABEL.setText(self.MAIN_TEXT)
        
        for label, item_ID in zip(self.labels, gearIDs):
            if item_ID:
                label.setObjectName(item_ID)
                label.installEventFilter(self)
                _Thread = ItemParser.Item(label, item_ID, gearData[item_ID])
                _Thread.item_loaded.connect(self.update_stats)
                _Thread.start()
                self.item_parsers.append(_Thread)
            else:
                label.removeEventFilter(self)
                label.setObjectName('')
    
    def update_stats(self, stats):
        _Thread = UpdateStats(stats)
        _Thread.start()
        self.item_parsers.append(_Thread)
        
    def eventFilter(self, object, event):
        if event.type() == 10:
            p = self.geometry()
            p = p.bottomRight() if self.x() > 1350 else p.bottomLeft()
            tool_tip_text = ItemParser.TTS.get(object, '')
            toolTip_show(p, tool_tip_text, self)
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
    old_ench = dict(ItemParser.ENCHANCEMENTS_DATA)
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(char_name)
    main_window.show()
    app.exec_()
    if old_ench != ItemParser.ENCHANCEMENTS_DATA:
        with open('ench_cache.txt', 'w') as f:
            f.write(json.dumps(ItemParser.ENCHANCEMENTS_DATA))
