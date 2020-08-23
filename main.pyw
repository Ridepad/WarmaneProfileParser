from PyQt5 import QtCore, QtGui, QtWidgets
from bs4 import BeautifulSoup
import requests
import sys
import json
import time
import re
import GS
import threading
import webbrowser
tm = time.time
st = tm()


TODO = '''

identify sets
"/5" - results 1
class=\"q\">Crimson Acolyte's Regalia<\/a> (0\/5)<

add all gems not just epic
add sets for player

errors
Pecatabe
'''


if True:
    GEMS = {
        'red': {
            'socket': (1, 0, 0),
            'color': 'ff0000'
        },
        'blue': {
            'socket': (0, 0, 1),
            'color': '4444ff'
        },
        'yellow': {
            'socket': (0, 1, 0),
            'color': 'edc600'
        },
        'green': {
            'socket': (0, 1, 1),
            'color': '00aa55'
        },
        'purple': {
            'socket': (1, 0, 1),
            'color': '6600bb'
        },
        'orange': {
            'socket': (1, 1, 0),
            'color': 'ff8800'
        }
    }
    
    GREEN = {'jagged', 'opaque', 'forceful', 'dazzling', 'enduring', 'sundered', 'timeless', 'lambent', 'vivid', 'energized', 'steady', 'intricate', 'radiant', "seer's", 'tense', 'shining', 'shattered', 'misty', 'turbid'}
    
    PURPLE = {'sovereign', 'shifting', 'balanced', 'tenuous', 'puissant', 'infused', "guardian's", 'royal', "defender's", 'glowing', 'regal', 'mysterious', 'purified'}
    
    ORANGE = {'durable', 'stark', 'luminous', 'pristine', 'potent', 'wicked', 'veiled', 'empowered', 'reckless', 'deft', 'inscribed', 'glinting', 'etched', 'deadly', 'fierce', 'lucent', 'resplendent', 'stalwart', "champion's", 'glimmering', 'accurate', 'resolute'}
    
    YELLOW = {'quick', 'smooth', 'thick', 'brilliant', "kharmaa's", 'rigid', 'mystic'}
   
    BLUE = {'solid', 'sparkling', 'lustrous', 'stormy'}
    
    RED = {'delicate', 'runed', 'bold', 'precise', 'bright', 'fractured', 'subtle', 'flashing'}
    
    ZIPPED_GEMS = [(GREEN, 'green'), (PURPLE, 'purple'), (ORANGE, 'orange'), (YELLOW, 'yellow'), (BLUE, 'blue'), (RED, 'red')]
    
    GREEN_STATS = {
        'attack power': 38,
        'spell power': 45,
        'haste rating': 36,
        'hit rating': 31,
        'critical strike rating': 32,
        'mp5': 43,
        'dodge rating': 13,
        'defense rating': 12,
        'parry rating': 14,
        'expertise rating': 37,
        'armor penetration rating': 44,
        'spell penetration': 47,
        'resilience rating': 35,
        'shield block': 15}
    
    PRIMARY_STATS = {
        'stamina': 7,
        'agility': 3,
        'strength': 4,
        'intellect': 5,
        'spirit': 6}
    
    QUALITY_COLOR = [
        'FFFFFF',
        'FFFFFF',
        '1EFF0B',
        '0560DD',
        'A32AB9',
        'FF8011',
        'FFFFFF',
        'ACBD80']

class Profile(QtCore.QThread):
    profile_signal = QtCore.pyqtSignal(list)
    def __init__(self, char_name, server='Lordaeron'):
        super().__init__()
        self.profile_url = f'http://armory.warmane.com/character/{char_name}/{server}/profile'
        
    def run(self):
        profile = self.get_profile()
        try:
            guild = profile.find(class_="guild-name").text
        except AttributeError:
            print("Character doesn't exist!")
            sys.exit()
        gear = self.get_gear(profile)
        specsProfs = self.get_SpecsProfs(profile)
        _emit = [gear, guild, specsProfs]
        self.profile_signal.emit(_emit)

    def get_profile(self):
        while 1:
            try:
                profile = requests.get(self.profile_url, timeout=3).text
                break
            except requests.exceptions.ConnectTimeout:
                pass
        return BeautifulSoup(profile, 'html.parser')

    def get_gear(self, profile):
        gearIDs = []
        gearData = dict()
        equipment = profile.find(class_="item-model").find_all('a')
        for slot in equipment:
            bonuses = slot.get('rel')
            if bonuses:
                tmp = [_B.split('=') for _B in bonuses[0].split('&')]
                item_ID = tmp[0][1]
                gearIDs.append(item_ID)
                
                _Slot = dict()
                for k, v in tmp[1:]:
                    if k == 'gems':
                        v = v.split(':')
                    _Slot[k] = v
                gearData[item_ID] = _Slot
            else:
                gearIDs.append('')
        return gearData, gearIDs


    def get_SpecsProfs(self, profile):
        SpecsProfs = {
            'Specialization': [],
            'Player vs Player': None,
            'Professions': [],
            'Secondary Skills': []
        }
        stats = profile.find(id='character-profile').find(class_="information-right")
        for _string in stats.stripped_strings:
            if _string == 'Recent Activity':
                break
            if _string in SpecsProfs:
                _cat_list = SpecsProfs[_string]
                _sub_list = []
            elif _cat_list is not None:
                _sub_list.append(_string)
                if '/' in _string:
                    _cat_list.append(_sub_list)
                    _sub_list = []
        
        list_of_specs_profs = []
        category_lists = [cat for cat in SpecsProfs.values() if cat]
        for category_list in category_lists:
            for name, value in sorted(category_list):
                value = value.split()
                if len(value) > 3:
                    value = ''.join(value)
                else:
                    value = value[0]
                list_of_specs_profs.append(f'{name:<14} {value:>8}')
            list_of_specs_profs.append('')
        return '\n'.join(list_of_specs_profs)


class Item(QtCore.QThread):
    item_loaded = QtCore.pyqtSignal(list)
    def __init__(self, item_ID, label, item_data):
        super().__init__()
        self.item_ID = item_ID
        self.label = label
        self.ENCHANT = item_data.get('ench')
        self.GEMS = item_data.get('gems', [])
    
    def run(self):
        self.ITEM = self.get_item()
        self.TOTAL_STATS = self.ITEM['stats']
        #armor_value = self.ITEM.get('armor', 0)
        #if armor_value:
        #    self.TOTAL_STATS.append(('armor', armor_value))
        self.ICON_NAME = self.ITEM['icon']
        self.label.setPixmap(self.get_icon())
        self.label.setToolTip(self.make_toolTip())
        self.label.setObjectName(self.item_ID)
        self.item_loaded.emit(self.TOTAL_STATS)
    
    def write_to_file(self, data):
        if type(data) == bytes:
            mode = 'wb'
            pth = f'Icons_cache/{self.ICON_NAME}.jpg'
        else:
            mode = 'w'
            pth = f'Items_cache/{self.item_ID}.txt'
        with open(pth, mode) as f:
            f.write(data)
    
    def get_item(self):
        try:
            with open(f'Items_cache/{self.item_ID}.txt', 'r') as f:
                f = f.read()
            return json.loads(f)
        except FileNotFoundError:
            print(f'Missing info: {self.item_ID}')
            
            item = self.get_missing_item_info()
            
            data = json.dumps(item)
            threading.Timer(0.3, self.write_to_file, args=(data, )).start()
            
            return item
    
    def get_missing_item_info(self):
        item_raw = requests.get(f'https://wotlk.evowow.com/?item={self.item_ID}').text
        #quality, icon, name
        item_re = re.search('g_items.*?(?P<core>{.+?})', item_raw)
        item = json.loads(item_re['core'])
        item['name'] = item.pop('name_enus')
        
        item['ilvl'] = re.findall('Level: (\d{1,3})', item_raw)[0]
        
        raw_stats = re.findall('tooltip_enus = "(.+?)";', item_raw)[0]
        
        item['heroic'] = int('Heroic' in raw_stats)
        
        item['slot'] = re.findall('td>([A-z -]+?)<', raw_stats)[0]
        
        #binds = re.findall('bo-->([A-z ]+?)<', raw_stats)
        binds = re.findall('(Binds.*?)<', raw_stats)
        if binds:
            item['binds'] = binds[0]
        
        armor_type = re.findall('-asc\d-->([A-z]+?)<', raw_stats)
        if armor_type:
            item['armor type'] = armor_type[0]
       
        stats = []
        for type_, list_stats in (('stat', PRIMARY_STATS), ('rtg', GREEN_STATS)):
            for stat, type_num in list_stats.items():
                value = re.findall(f'{type_}{type_num}[^\d]+(\d+)', raw_stats)
                if value:
                    stats.append([stat.lower(), value[0].lower()])
        armor_value = re.findall('(\d+) Armor', raw_stats)
        if armor_value:
            armor_value = armor_value[0]
            if 'tooltip_armorbonus' in raw_stats:
                armor_bonus = re.findall('tooltip_armorbonus, (\d+)', raw_stats)[0]
                armor_value = int(armor_value) - int(armor_bonus)*2
                armor_value = str(armor_value)
                print(armor_value, armor_bonus)
            stats.append(['armor', armor_value])
            #stats.extend((stat, re.findall(f'{type_}{type_num}[^\d]+(\d+)', raw_stats)) for stat, type_num in L.items())
        #item['stats'] = [[stat.lower(), value[0].lower()] for stat, value in stats if value]
        item['stats'] = stats
        
        sockets = [raw_stats.count(f'socket-{s_color}') for s_color in ('red', 'yellow', 'blue')]
        if sum(sockets):
            item['sockets'] = sockets
            _m = re.search(' Bonus:.*?>\+(?P<value>\d{1,2}) (?P<stat>[0-9A-z ]+)', raw_stats)
            _stat = _m['stat']
            if not _m:
                _m = re.search('Bonus.*?(?P<value>\d{1,2}) (?P<stat>[\w ]+)', raw_stats)
                _stat = _m['stat']
                if 'mana ' in _m['stat']:
                    _stat = 'mp5'
            item['socket bonus'] = (_stat, _m['value'])
        
        #_additional_text = []
        if 'Equip: <a href' in raw_stats:
            #_additional_text = re.findall('Equip: <a href.+?>(.+\.).+?>\w', raw_stats)
            if 0:
                _additional_text = re.findall('Equip: <a.*?>(.*?)\.>', raw_stats)
                for _ in _additional_text[:]:
                    tmp_add = _additional_text.pop(0)
                    if 'rtg' in tmp_add:
                        _replace = re.search('(?P<one><!--rtg..-->)\d{2,3}(?P<two><.+?>) ', tmp_add)
                        _replace = re.findall('(?P<one><!--rtg..-->)\d{2,3}(?P<two><.+?>) ', tmp_add)
                        #print(_replace['one'],_replace['two'])
                        tmp_add = tmp_add.replace(_replace['one'], '')
                        tmp_add = tmp_add.replace(_replace['two'], '')
                    _additional_text.append(tmp_add)
            _additional_text = re.findall('Equip: <a.*?>(.*?)\.<', raw_stats)
            for _ in _additional_text[:]:
                tmp_add = _additional_text.pop(0)
                tmp_add = re.sub('(&.*?\))', '', tmp_add)
                tmp_add = re.sub('(<.*?>)', '', tmp_add)
                print(tmp_add)
                _additional_text.append(tmp_add)
            item['add_text'] = _additional_text
        
        return item

    def get_icon(self):
        itemIconPath = f'Icons_cache/{self.ICON_NAME}.jpg'
        try:
            with open(itemIconPath,'rb') as img:
                icon = img.read()
        except FileNotFoundError:
            print(f'Missing icon: {self.item_ID}')
            iconUrl = f'https://wotlk.evowow.com/static/images/wow/icons/large/{self.ICON_NAME}.jpg'
            icon = requests.get(iconUrl).content
            threading.Timer(0.3, self.write_to_file, args=(icon, )).start()
        _Pixmap = QtGui.QPixmap()
        _Pixmap.loadFromData(icon)
        return _Pixmap

    def make_toolTip(self):
        def get_enh(enh_ID):
            if enh_ID in enhancements_data:
                return enhancements_data[enh_ID]
            return get_missing_enh_info(enh_ID)
        
        def get_missing_enh_info(enh_ID):
            enh_raw = requests.get(f'https://wotlk.evowow.com/?enchantment={enh_ID}').text
            _ENH = re.findall('name_enus":"([^"]+)', enh_raw)
            enh_value, enh_name, *_ = _ENH
            enh_value = enh_value.lower().replace('crit rating', 'critical strike rating')
            enh_name = enh_name.lower()
            if 'sec' in enh_value:
                i = enh_value.index('mana')
                enh_value = enh_value.replace(enh_value[i:], 'mp5')
            tmp_enh = enhancements_data[enh_ID] = (enh_name, enh_value)
            return tmp_enh
        
        def check_socket_bonus(gem_names):
            try:
                item_sockets = self.ITEM["sockets"]
            except:
                return
            
            if sum(item_sockets) > len(gem_names):
                return
            
            #gem_names = [name.split(' ', 1) for name in gem_names]
            #for name, type_ in gem_names:
            for gem_name in gem_names:
                name, type_ = gem_name.split(' ', 1)
                if 'diamond' in type_:
                    continue
                for gem_set, color in ZIPPED_GEMS:
                    if name in gem_set:
                        item_sockets = [x-y for x, y in zip(item_sockets, GEMS[color]['socket'])]
                        break
            for x in item_sockets:
                if x > 0:
                    return
            
            return True
        
        _toolTip = []
        bonuses = [] #additional stats via enchant+gems
        strings_len = [] #to determine tooltip width
        
        name_color = QUALITY_COLOR[self.ITEM['quality']]
        _name = self.ITEM["name"]
        _toolTip.append(f'<font size=5 color="#{name_color}">{_name}</font>')
        strings_len.append(len(_name) * 11)
        
        if self.ITEM['heroic']:
            _toolTip.append(f'<font color="#11DD11">Heroic</font>')
        
        _ilvl = self.ITEM["ilvl"]
        if _ilvl != '1':
            _toolTip.append(self.ITEM["ilvl"])
        
        _toolTip.append(self.ITEM["slot"])
        #_toolTip.append(self.ITEM.get('binds'))
        a_type = self.ITEM.get('armor type')
        if a_type:
            _toolTip.append(a_type)
        
        _Stats = self.ITEM['stats']
        if _Stats:
            _toolTip.append('')
            _sep = True
            for stat, value in _Stats:
                if _sep and stat in GREEN_STATS or stat == 'armor':
                    _toolTip.append('')
                    _sep = False
                _toolTip.append(f'+{value:>3} {stat.title()}')
                strings_len.append(len(stat) * 8)
        
        if self.ENCHANT:
            _Enchant = get_enh(self.ENCHANT)[1]
            bonuses.append(_Enchant)
            strings_len.append(len(_Enchant) * 8)
            _toolTip.append('')
            _toolTip.append(f'<font color="#11DD11">{_Enchant.title()}</font>')
        
        if self.GEMS:
            _toolTip.append('')
            socket_amount = sum(self.ITEM.get("sockets", []))
            if self.ITEM["slot"] in ('Waist', 'Head'):
                socket_amount += 1
            gem_names = []
            for gem_ID, _ in zip(self.GEMS, range(socket_amount)):
                if gem_ID == '0':
                    _toolTip.append('<font color="#FF0000">Missing gem</font>')
                    continue
                gem_name, gem_stat = get_enh(gem_ID)
                gem_name = gem_name.replace('perfect ', '')
                gem_names.append(gem_name)
                bonuses.append(gem_stat)
                name, type_ = gem_name.split(' ', 1)
                
                if 'diamond' in type_:
                    _color = '6666FF'
                elif 'tear' in type_:
                    _color = 'A335EE'
                else:
                    for gem_set, color in ZIPPED_GEMS:
                        if name in gem_set:
                            _color = GEMS[color]['color']
                            break
                    else:
                        print(name, '|', type_)
                        _color = 'FFFFFF'
                _toolTip.append(f'<font color="#{_color}">{gem_stat.title()}</font>')
                strings_len.append(len(gem_stat) * 8)
            try:
                stat, value = self.ITEM["socket bonus"]
                if check_socket_bonus(gem_names):
                    self.TOTAL_STATS.append([stat.lower(), value])
                    _color = '11DD11'
                else:
                    _color = '777777'
                _toolTip.append(f'<font color="#{_color}">+{value} {stat}</font>')
            except KeyError:
                pass
        
        self.TOTAL_STATS.append(bonuses)
        
        _additional_text = self.ITEM.get('add_text')
        if _additional_text:
            _toolTip.append('')
            for _add in _additional_text:
                _toolTip.append(f'<font color="#11DD11">{_add}</font>')
        
        #show item ID
        #_toolTip.append(f'<font color="#FFFFFF">{self.item_ID}</font>')
        
        _width = max(strings_len) + 10
        _toolTip = '</td></tr><tr><td>'.join(_toolTip)
        _toolTip = f'<table width={_width}><tr><td>{_toolTip}</td></tr></table>'
        _toolTip = f'<font face=\"Lucida Console\" size=4>{_toolTip}</font>'
        return _toolTip


class MainWindow(QtWidgets.QMainWindow):
    got_gear = QtCore.pyqtSignal()
    
    labels = []
    stats = {
        'resilience rating': 0,
        'attack power': 0,
        'spell power': 0,
        'hit rating': 0,
        'haste rating' : 0,
        'critical strike rating': 0,
        'armor penetration rating': 0,
        'expertise rating': 0,
        'mp5': 0,
        'defense rating': 0,
        'parry rating': 0,
        'dodge rating' : 0,
        'shield block' : 0,
        'strength': 0,
        'agility': 0,
        'stamina': 0,
        'intellect': 0,
        'spirit': 0,
        'armor': 0,}    
    
    def __init__(self, char_name):
        QtWidgets.QMainWindow.__init__(self)

        self.char_name = char_name
        
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setWindowTitle(char_name)
        self.setStyleSheet("QMainWindow {background-color: black} QToolTip {background-color: black; color: white; border: 1px solid white; }")
        
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowCloseButtonHint
        )
        
        try:
            mousex, mousey = sys.argv[2], sys.argv[3]
        except IndexError:
            mousex, mousey = 1400, 300
        icon = 56
        border = 3
        spacing = 2
        statsAdditionalSize = 60
        x = icon*5 + spacing*4 + border*2 + statsAdditionalSize
        y = icon*9 + spacing*8 + border*2
        self.setGeometry((int(mousex) - x), int(mousey), x, y)
        self.setFixedSize(self.size())
        icon_size = QtCore.QSize(icon, icon)
        stats_size = QtCore.QSize(icon*3 + spacing*2 + statsAdditionalSize, icon*8)
        
        self.centralwidget = QtWidgets.QWidget(self)
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(*[border]*4)
        self.gridLayout.setSpacing(spacing)
        
        def add_icon(x,y):
            _Label = QtWidgets.QLabel(
                minimumSize=icon_size,
                maximumSize=icon_size,
            )
            _Label.installEventFilter(self)
            self.labels.append(_Label)
            self.gridLayout.addWidget(_Label, y, x, 1, 1)
        
        for x in (0, 4):
            for y in range(8):
                add_icon(x, y)
                
        for x in range(1, 4):
            add_icon(x, 9)
                
            
        _Label = QtWidgets.QLabel(
            minimumSize=stats_size,
            maximumSize=stats_size,
            styleSheet="color: white",
            font=QtGui.QFont("Lucida Console", 12),
        )
        setattr(self, 'All_Stats', _Label)
        self.gridLayout.addWidget(_Label, 0, 1, 8, 3)
        
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.update()
        self.got_gear.connect(self.after_gear)
    
    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == 1:
            item_ID = object.objectName()
            if item_ID:
                webbrowser.open(f'https://wotlk.evowow.com/?item={item_ID}')
        return False
    
    def after_gear(self):
        for label, item_ID in zip(self.labels, self.gearIDs):
            if item_ID:
                _Thread = Item(item_ID, label, self.gearData[item_ID])
                _Thread.item_loaded.connect(self.update_stats)
                setattr(self, f'{item_ID}_Thread', _Thread)
                _Thread.start()
        
    def update_stats(self, _Stats):
        bonuses = _Stats.pop(-1)
        for bonus in bonuses:
            for B in bonus.split(' and '):
                try:
                    value, stat = B.split(' ', 1)
                    if '%' in value:
                        continue
                    _Stats.append((stat, value))
                except ValueError:
                    pass
                    
        for stat, value in _Stats:
            try:
                value = int(value)
                if stat == 'all stats':
                    for p_stat in PRIMARY_STATS:
                        self.stats[p_stat] += value
                elif stat in self.stats:
                    self.stats[stat] += value
                else:
                    print(f'"{stat}" MISSING! PLZ FIX')
            except:
                pass
        stats_txt = '\n'.join(f'{value:>4} {stat}' for stat, value in self.stats.items() if value > 30)
        self.All_Stats.setText(f'{self.main_label_text}\n\nStats:\n{stats_txt}')
        
        
    def on_load(self):
        self.thread = Profile(self.char_name)
        self.thread.profile_signal.connect(self.up_lbl)
        self.thread.start()
    
    def up_lbl(self, val):
        gear, guild, text = val
        self.gearData, self.gearIDs = gear
        self.got_gear.emit()
        total_gs = sum(GS.main(gear[1]))
        self.main_label_text = f'{self.char_name}\nGearScore: {total_gs}\n{guild}\n\n{text}'
        self.All_Stats.setText(self.main_label_text)

if __name__ == "__main__":
    with open('enh_cache.txt','r') as f:
        enhancements_data = json.loads(f.read())
    app = QtWidgets.QApplication(sys.argv)
    char_name = sys.argv[1]
    char_name = char_name.split('\n')[-1]
    char_name = char_name.strip()
    char_name = char_name.capitalize()
    main_window = MainWindow(char_name)
    main_window.show()
    main_window.on_load()
    app.exec_()
