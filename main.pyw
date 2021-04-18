from PyQt5 import QtCore, QtGui, QtWidgets
import ProfileParser
import ItemParser
import GS
import re
import os
import sys
import json
import time
import webbrowser

if not os.path.exists('Icons_cache'):
    os.makedirs('Icons_cache')
if not os.path.exists('Items_cache'):
    os.makedirs('Items_cache')

FULL_STATS = {x: 0 for x in ItemParser.STATS_DICT.values()}
    
def stats_format(q):
    stat, value = q
    stat = ItemParser.STATS_DICT.get(stat, stat)
    return stat, value

def wrong_name():
    msg = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Critical,
        "",
        "Character with this name doesn't exist",
        QtWidgets.QMessageBox.Ok)
    msg.setWindowFlags(
        QtCore.Qt.CustomizeWindowHint |
        QtCore.Qt.WindowStaysOnTopHint)
    msg.exec_()
    sys.exit()


class UpdateStats(QtCore.QThread):
    def __init__(self, new_stats):
        super().__init__()
        self.new_stats = new_stats
        
    def run(self):
        for bonus in self.new_stats.pop(-1):
            for B in bonus.split(' and '):
                try:
                    value, stat = B.split(' ', 1)
                    if '%' in value:
                        continue
                    value = int(value)
                    self.new_stats.append((stat, value))
                except ValueError:
                    print(f'WARNING: STAT MISSING: "{B}"')
        for q in self.new_stats:
            stat, value = stats_format(q)
            if stat == 'all stats':
                for i in range(3,8):
                    stat = ItemParser.STATS_DICT[i]
                    FULL_STATS[stat] += value
            elif stat in FULL_STATS:
                FULL_STATS[stat] += value
        stats_txt = '\n'.join(f'{value:>5} {stat}' for stat, value in FULL_STATS.items() if value > 30)
        stats_txt = stats_txt.replace(" rating", "").title()
        stats_txt = f'{main_window.MAIN_TEXT}\nStats:\n{stats_txt}'
        main_window.STATS_LABEL.setText(stats_txt)


class MainWindow(QtWidgets.QMainWindow):
    labels = []
    item_parsers = []
    ToolTip_show = QtWidgets.QToolTip.showText
    
    def __init__(self, char_name, server="Lordaeron"):
        super().__init__()

        self.setWindowTitle(char_name)
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowCloseButtonHint)
        self.setStyleSheet("QMainWindow {background-color: black} QToolTip {background-color: black; color: white; border: 1px solid white; }")
        
        try:
            mousex, mousey = int(sys.argv[2]), int(sys.argv[3])
        except IndexError:
            mousex, mousey = 100, 100
        
        icon = 56
        border = 3
        spacing = 2
        statsAdditionalSize = 60
        x = icon*5 + spacing*4 + border*2 + statsAdditionalSize
        y = icon*9 + spacing*8 + border*2
        self.setGeometry(mousex, mousey, x, y)
        self.setFixedSize(self.size())
        self.icon_size = QtCore.QSize(icon, icon)
        
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(*[border]*4)
        self.gridLayout.setSpacing(spacing)
        
        for x in (0, 4):
            for y in range(8):
                self.add_icon(x, y, x%4*y)
                
        for x in range(1, 4):
            self.add_icon(x, 9, x+15)
                
        stats_size = QtCore.QSize(icon*3 + spacing*2 + statsAdditionalSize, icon*8)
        self.STATS_LABEL = QtWidgets.QLabel(
            minimumSize=stats_size,
            maximumSize=stats_size,
            styleSheet="color: white",
            font=QtGui.QFont("Lucida Console", 12),
            alignment=QtCore.Qt.AlignTop
        )
        self.gridLayout.addWidget(self.STATS_LABEL, 0, 1, 8, 3)

        profile = ProfileParser.main(char_name, server)
        if not profile:
            wrong_name()
        self.got_gear(profile)
        
    def add_icon(self, x, y, n):
        _Label = QtWidgets.QLabel()
        _Label.installEventFilter(self)
        self.labels.append(_Label)
        self.gridLayout.addWidget(_Label, y, x, 1, 1)
    
    def got_gear(self, profile):
        self.gearData, self.gearIDs, guild, specsProfs = profile
        total_gs = sum(GS.main(self.gearIDs))
        self.MAIN_TEXT = f'GearScore: {total_gs}\n{guild}\n\n{specsProfs}'
        self.STATS_LABEL.setText(self.MAIN_TEXT)
        
        for label, item_ID in zip(self.labels, self.gearIDs):
            if item_ID:
                _Thread = ItemParser.Item(label, item_ID, self.gearData[item_ID])
                _Thread.item_loaded.connect(self.update_stats)
                _Thread.start()
                self.item_parsers.append(_Thread)
    
    def update_stats(self, stats):
        _Thread = UpdateStats(stats)
        _Thread.start()
        self.item_parsers.append(_Thread)
        
    def eventFilter(self, object, event):
        if event.type() == 10 and object in ItemParser.TTS:
            tool_tip_text = ItemParser.TTS[object]
            p = self.geometry()
            p = p.bottomRight() if self.x() > 1350 else p.bottomLeft()
            self.ToolTip_show(p, tool_tip_text, self)
        elif event.type() == 2 and event.button() == 1:
            item_ID = object.objectName()
            if item_ID:
                webbrowser.open(f'https://wotlk.evowow.com/?item={item_ID}')
        return False


if __name__ == "__main__":
    try:
        char_name = sys.argv[1]
        char_name = re.findall('[^A-z\(]?([A-z]{2,12})', char_name, re.S)[-1]
        char_name = char_name.lower().capitalize()
    except:
        char_name = "Nomadra"
    old_ench = dict(ItemParser.ENCHANCEMENTS_DATA)
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(char_name)
    # main_window = MainWindow(char_name, "Frostmourne")
    main_window.show()
    app.exec_()
    if old_ench != ItemParser.ENCHANCEMENTS_DATA:
        with open('ench_cache.txt', 'w') as f:
            f.write(json.dumps(ItemParser.ENCHANCEMENTS_DATA))
