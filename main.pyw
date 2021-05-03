from PyQt5 import QtCore, QtGui, QtWidgets
import ProfileParser
import ItemParser
import GS
import re
import os
import sys
import json
import webbrowser

if not os.path.exists('Icons_cache'):
    os.makedirs('Icons_cache')
if not os.path.exists('Items_cache'):
    os.makedirs('Items_cache')

FULL_STATS = {x: 0 for x in ItemParser.STATS_DICT.values()}
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
            if stat in FULL_STATS:
                FULL_STATS[stat] += value
            # else:
            #     print('MISSING STAT?', stat, value)
        stats_txt = '\n'.join(f'{value:>5} {stat}' for stat, value in FULL_STATS.items() if value > 30)
        stats_txt = stats_txt.replace(" rating", "").title()
        _txt = f'{main_window.MAIN_TEXT}\nStats:\n{stats_txt}'
        main_window.STATS_LABEL.setText(_txt)
        print(_txt)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, char_name, server="Lordaeron"):
        super().__init__()

        self.labels = []
        self.item_parsers = []
        self.setWindowTitle(char_name)
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowCloseButtonHint)
        self.setStyleSheet("QMainWindow {background-color: black} QToolTip {background-color: black; color: white; border: 1px solid white; }")
        
        icon = 56
        border = 3
        spacing = 2
        statsAdditionalSize = 60
        W = icon*5 + spacing*4 + border*2 + statsAdditionalSize
        H = icon*9 + spacing*8 + border*2
        try:
            X, Y = int(sys.argv[2]), int(sys.argv[3])
        except IndexError:
            X, Y = 100, 100
        self.setGeometry(X, Y, W, H)
        self.setFixedSize(self.size())
        # self.icon_size = QtCore.QSize(icon, icon)
        
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
            show_error_message("Character with this name doesn't exist")
        self.got_gear(profile)
        
    def add_icon(self, x, y, n):
        _Label = QtWidgets.QLabel()
        self.labels.append(_Label)
        self.gridLayout.addWidget(_Label, y, x, 1, 1)
    
    def got_gear(self, profile):
        gearData, gearIDs, guild, specsProfs = profile
        _gear = GS.main(gearIDs)
        total_gs = GS.total_gs(_gear)
        self.MAIN_TEXT = f'GearScore: {total_gs}\n{guild}\n\n{specsProfs}'
        self.STATS_LABEL.setText(self.MAIN_TEXT)
        
        for label, item_ID in zip(self.labels, gearIDs):
            label.removeEventFilter(self)
            if item_ID:
                label.setObjectName(item_ID)
                label.installEventFilter(self)
                _Thread = ItemParser.Item(label, item_ID, gearData[item_ID])
                _Thread.item_loaded.connect(self.update_stats)
                _Thread.start()
                self.item_parsers.append(_Thread)
    
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
