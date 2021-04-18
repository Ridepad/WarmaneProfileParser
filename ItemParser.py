import re
import json
import requests
import threading
from PyQt5 import QtCore, QtGui

with open('ench_cache.txt','r') as f:
    ENCHANCEMENTS_DATA = json.loads(f.read())

TTS = {}
ENCHANTABLE = {'Head', 'Shoulder', 'Chest', 'Legs', 'Hands', 'Feet', 'Main Hand', 'Off Hand', 'One-Hand', 'Two-Hand'}
QUALITY_COLOR = ['FFFFFF', 'FFFFFF', '1EFF0B', '0560DD', 'A32AB9', 'FF8011', 'FFFFFF',  'ACBD80']
GEMS = {
    'red': {
        'socket': (1, 0, 0),
        'color_hex': 'ff0000',
        'names': {
            'blood', 'bold', 'bright', 'crimson', 'delicate', 'don', 'flashing', 'fractured', "kailee's", 'mighty',
            "omar's", 'precise', 'runed', 'scarlet', 'stark', 'subtle', 'teardrop'}},
    'yellow': {
        'socket': (0, 1, 0),
        'color_hex': 'edc600',
        'names': {
            'blood', 'brilliant', 'facet', 'gleaming', 'great', "kharmaa's", 'mystic',
            'quick', 'rigid', 'smooth', 'stone', 'sublime', 'thick'}},
    'blue': {
        'socket': (0, 0, 1),
        'color_hex': '4444ff',
        'names': {'azure', 'charmed', 'empyrean', 'falling', 'lustrous', 'majestic', 'sky', 'solid', 'sparkling', 'star', 'stormy'}},
    'orange': {
        'socket': (1, 1, 0),
        'color_hex': 'ff8800',
        'names': {
            'accurate', "assassin's", 'beaming', "champion's", 'deadly', 'deft', 'durable', 'empowered', 'enscribed', 'etched',
            'fierce', 'glimmering', 'glinting', 'glistening',  'infused', 'inscribed', 'iridescent', 'lucent', 'luminous',
            'mysterious', 'nimble', 'potent', 'pristine', 'reckless', 'resolute', 'resplendent', 'shining', 'splendid', 'stalwart',
            'stark', 'unstable', 'veiled', 'wicked'}},
    'purple': {
        'socket': (1, 0, 1),
        'color_hex': '6600bb',
        'names': {
            'balanced', 'blessed', 'brutal', "defender's", 'fluorescent', 'glowing', "guardian's", 'imperial', 'infused',
            'mysterious', 'puissant', 'pulsing', 'purified', 'regal', 'royal', 'shifting', 'soothing', 'sovereign', 'tenuous'}},
    'green': {
        'socket': (0, 1, 1),
        'color_hex': '00aa55',
        'names': {
            'barbed', 'dazzling', 'effulgent', 'enduring', 'energized', 'forceful', 'intricate', 'jagged', 'lambent', 'misty',
            'notched', 'opaque', 'polished', 'radiant', 'rune', "seer's", 'shattered', 'shining', 'steady', 'sundered', 'tense',
            'timeless', 'turbid', 'unstable', 'vivid'}}}
STATS_DICT = {
    35: "resilience rating",
    31: "hit rating",
    45: "spell power",
    38: "attack power",
    36: "haste rating",
    32: "critical strike rating",
    37: "expertise rating",
    44: "armor penetration rating",
    12: "defense rating",
    13: "dodge rating",
    14: "parry rating",
    15: "shield block",
    43: "mp5",
    47: "spell penetration",
    7: "stamina",
    3: "agility",
    4: "strength",
    5: "intellect",
    6: "spirit",
    0: "armor",}

def format_line(body, color='', size=''):
    if color or size:
        if color:
            color = f' color="#{color}"'
        if size:
            size = f' size={size}'
        return f'<font{size}{color}>{body}</font>'

def check_socket_bonus(item_gems, item_sockets):
    if not item_sockets or sum(item_sockets) > len(item_gems):
        return False

    for name, type_ in item_gems:
        if 'diamond' in type_:
            continue
        if name == 'nightmare':
            item_sockets = [x-1 for x in item_sockets]
            continue
        for color in GEMS:
            if name in GEMS[color]['names']:
                socket_matches = GEMS[color]['socket']
                item_sockets = [x-y for x, y in zip(item_sockets, socket_matches)]
                break
    return all(x <= 0 for x in item_sockets)

def get_prim_stats(q):
    return re.findall("-stat(\d)[^\d]+(\d{1,3})", q)

def get_add_stats(q):
    return re.findall("Equip: [IR][a-z]+[^%\d]+(\d\d)\D+(\d{1,3})", q)

def get_armor(q):
    armor_value = re.findall('(\d+) Armor<', q)
    if not armor_value:
        return 0
    armor_value = armor_value[0]
    if 'tooltip_armorbonus' in q:
        armor_bonus = re.findall('tooltip_armorbonus, (\d+)', q)[0]
        armor_value = int(armor_value) - int(armor_bonus)*2
    return armor_value

def get_stats(q):
    stats = get_prim_stats(q)
    stats.extend(get_add_stats(q))
    stats.append([0, get_armor(q)])
    return [[int(x), int(y)] for x,y in stats]

def get_sockets(q):
    S = re.findall("socket-([a-z]{3,6})", q)
    return [S.count(x) for x in ("red", "yellow", "blue")]

def get_raw_stats(q):
    raw_stats = q[q.index("tooltip_enus"):]
    return raw_stats[:raw_stats.index("_[")]

def get_additional_text(q):
    additional_text = re.findall("(Equip: [^IR].+?)...span>", q, re.S)
    additional_text.extend(re.findall("(Use: .+?)...span>", q, re.S))
    for _ in additional_text[:]:
        text = additional_text.pop(0)
        text = re.sub("<[^>]+>", "", text)
        text = re.sub("\(.+\)", "", text)
        text = text.replace("&nbsp;", "")
        additional_text.append(text)
    return additional_text

def get_socket_bonus(q):
    value, stat = re.findall("Socket Bonus:.+?(\d{1,2}) ([\w ]+)", q)[0]
    if '5' in stat:
        stat = "mp5"
    return stat, int(value)
    # value = int(f[0])
    # f = [stat, value]
    # return f

def get_missing_item_info(item_ID):
    item_raw = requests.get(f'https://wotlk.evowow.com/?item={item_ID}').text
    item_re = re.search('g_items.*?(?P<core>{.+?})', item_raw)
    item = json.loads(item_re['core'])
    item['name'] = item.pop('name_enus')
    try:
        item['ilvl'] = re.findall('Level: (\d{1,3})', item_raw)[0]
    except IndexError:
        return item

    raw_stats = get_raw_stats(item_raw)

    item['heroic'] = 'Heroic' in raw_stats

    item['slot'] = re.findall('td>([A-z -]+?)<', raw_stats)[0]

    # binds = re.findall('bo-->([A-z ]+?)<', raw_stats)
    # binds = re.findall('(Binds.*?)<', raw_stats)
    # if binds:
    #     item['binds'] = binds[0]

    armor_type = re.findall('-asc\d-->([^<]+)', raw_stats)
    if armor_type:
        item['armor type'] = armor_type[0]
    
    item['stats'] = get_stats(raw_stats)
    item['sockets'] = get_sockets(raw_stats)
    if sum(item['sockets']):
        item['socket bonus'] = get_socket_bonus(raw_stats)

    additional_text = get_additional_text(raw_stats)
    if additional_text:
        item['add_text'] = additional_text
    return item

__ench = "https://wotlk.evowow.com/?enchantment="
def get_ench2(ench_ID):
    ench_raw = requests.get(f'{__ench}{ench_ID}').text
    z = {}
    z['name'] = re.findall('<title>(.*?) - Enchantment', ench_raw[:100], re.S)[0]
    if "Statistics" in ench_raw:
        z['stats'] = re.findall("Value: (\d\d?).+?traits..([^']*)", ench_raw, re.S)
        z['use'] = re.findall("Use:.+?>([A-z ]+)<", ench_raw, re.S)
    return z

def get_ench(ench_ID):
    if ench_ID in ENCHANCEMENTS_DATA:
        return ENCHANCEMENTS_DATA[ench_ID]
    
    ench_raw = requests.get(f'https://wotlk.evowow.com/?enchantment={ench_ID}').text
    ench_value, ench_name, *_ = re.findall('name_enus":"([^"]+)', ench_raw)
    ench_value = ench_value.lower()
    ench_value = ench_value.replace('crit rating', 'critical strike rating')
    ench_name = ench_name.lower()
    if 'mana ' in ench_value:
        i = ench_value.index('mana')
        ench_value = ench_value.replace(ench_value[i:], 'mp5')
    ench = ENCHANCEMENTS_DATA[ench_ID] = (ench_name, ench_value)
    return ench

def gem_color(gem_name):
    name, type_ = gem_name
    if 'diamond' in type_:
        return '6666FF'
    if 'tear' in type_:
        return 'A335EE'
    for color in GEMS:
        if name in GEMS[color]['names']:
            return GEMS[color]['color_hex']
    #shouldnt reach here
    print('WARNING: MISSING GEM:', name, '|', type_)
    return 'FFFFFF'

def stats_(q):
    stat, value = q
    stat = STATS_DICT.get(stat, stat)
    return stat, value


class Item(QtCore.QThread):
    item_loaded = QtCore.pyqtSignal(list)
    
    def __init__(self, label, item_ID, item_data):
        super().__init__()
        self.item_ID = item_ID
        self.label = label
        self.GEMS = item_data.get('gems', [])
        self.ENCHANT = item_data.get('ench')
            
    def run(self):
        self.bonuses = []
        self.socket_bonus = True
        #rewrite item data icon write 
        self.ITEM = self.get_item()
        self.ICON_NAME = self.ITEM['icon']
        self.file_list = ((f'Icons_cache/{self.ICON_NAME}.jpg', 'wb'), (f'Items_cache/{self.item_ID}.txt', 'w'))
        self.label.setPixmap(self.get_icon())
        self.label.setObjectName(self.item_ID)
        self.TOTAL_STATS = self.ITEM['stats']
        TTS[self.label] = self.make_toolTip()
        self.TOTAL_STATS.append(self.bonuses)
        self.item_loaded.emit(self.TOTAL_STATS)
    
    def write_to_file(self, data, data_type):
        with open(*self.file_list[data_type]) as f:
            f.write(data)

    def get_item(self):
        try:
            with open(f'Items_cache/{self.item_ID}.txt', 'r') as f:
                f = f.read()
            return json.loads(f)
        except FileNotFoundError:
            item = get_missing_item_info(self.item_ID)
            data = json.dumps(item)
            threading.Timer(0.1, self.write_to_file, args=(data, 1)).start()
            return item

    def get_icon(self):
        itemIconPath = f'Icons_cache/{self.ICON_NAME}.jpg'
        try:
            with open(itemIconPath,'rb') as img:
                icon = img.read()
        except FileNotFoundError:
            iconUrl = f'https://wotlk.evowow.com/static/images/wow/icons/large/{self.ICON_NAME}.jpg'
            icon = requests.get(iconUrl).content
            threading.Timer(0.1, self.write_to_file, args=(icon, 0)).start()
        _Pixmap = QtGui.QPixmap()
        _Pixmap.loadFromData(icon)
        return _Pixmap

    def gem_data(self, socket_amount):
        if self.ITEM["slot"] in ('Waist', 'Head'):
            socket_amount += 1
        item_gems = []
        for n in range(socket_amount):
            gem_ID = self.GEMS[n]
            if gem_ID == '0':
                yield 'Missing gem', 'FF0000'
                self.socket_bonus = False
                continue
            gem_name, gem_stat = get_ench(gem_ID)
            self.bonuses.append(gem_stat)
            # rewrite
            gem_name = gem_name.replace('perfect ', '')
            gem_name = gem_name.split(' ', 1)
            item_gems.append(gem_name)

            _color = gem_color(gem_name)
            yield gem_stat, _color

        stat, value = stats_(self.ITEM["socket bonus"])
        item_sockets = self.ITEM.get("sockets")
        socket_bonus_color = '777777'
        if self.socket_bonus and check_socket_bonus(item_gems, item_sockets):
            self.TOTAL_STATS.append([stat.lower(), value])
            socket_bonus_color = '11DD11'
        yield f'+{value} {stat}', socket_bonus_color

    def get_self_stats(self):
        tt = []
        if self.TOTAL_STATS:
            tt.append('')
            _add_separator = True
            for STAT in self.TOTAL_STATS:
                stat, value = stats_(STAT)
                #if _add_separator and stat is not primary or stat is armor:
                if _add_separator and STAT[0] > 10 or stat == 'armor':
                    tt.append('')
                    _add_separator = False
                line = f'+{value:>3} {stat}'.title()
                tt.append(line)
        return tt

    def get_self_enchant(self):
        tt = []
        tt_w = []
        if self.ENCHANT:
            tt.append('')
            self.ENCHANT = get_ench(self.ENCHANT)[1]
            self.bonuses.append(self.ENCHANT)
            line = self.ENCHANT.title()
            tt.append(format_line(line, '11DD11'))
            tt_w.append(line)
        elif self.ITEM["slot"] in ENCHANTABLE:
            tt.append('')
            tt.append(format_line('Missing Enchant', 'FF0000'))
            tt_w.append('Missing Enchant')
        return tt, tt_w

    def get_self_sockets(self):
        tt = []
        tt_w = []
        socket_amount = sum(self.ITEM.get("sockets", []))
        if socket_amount:
            tt.append('')
            for line, color in self.gem_data(socket_amount):
                line = line.title()
                tt.append(format_line(line, color))
                tt_w.append(line)
        return tt, tt_w
    
    def get_self_add(self):
        tt = []
        additional_text = self.ITEM.get('add_text')
        if additional_text:
            tt.append('')
            for text in additional_text:
                tt.append(format_line(text, '11DD11'))
        return tt

    def get_ilvl(self):
        _ilvl = self.ITEM["ilvl"]
        # if _ilvl != '1':
        if self.ITEM['heroic']:
            _ilvl = format_line(_ilvl, '11DD11')
        return _ilvl
    
    def make_toolTip(self):
        _toolTip = []
        _toolTip_width = []

        _toolTip.append(self.get_ilvl())
        _toolTip.append(self.ITEM["slot"])
        #_toolTip.append(self.ITEM.get('binds'))
        _toolTip.append(self.ITEM.get('armor type', ''))
        
        _tt = self.get_self_stats()
        _toolTip.extend(_tt)
        _toolTip_width.append(max(_tt, default='', key=len))

        _ench, _tt_w = self.get_self_enchant()
        _toolTip.extend(_ench)
        _toolTip_width.append(max(_tt_w, default='', key=len))

        _sockets, _tt_w = self.get_self_sockets()
        _toolTip.extend(_sockets)
        _toolTip_width.append(max(_tt_w, default='', key=len))

        item_name = self.ITEM["name"]
        item_name_color = QUALITY_COLOR[self.ITEM['quality']]
        tt_width = len(item_name) * 11
        if _toolTip_width:
            L = max(len(x) for x in _toolTip_width) * 7
            if L > tt_width:
                tt_width = L
        tt_width += 10
        _toolTip = [x.title() for x in _toolTip]
        _toolTip.insert(0, format_line(item_name, item_name_color, 5))
       
        _toolTip.extend(self.get_self_add())

        _toolTip = '</td></tr><tr><td>'.join(_toolTip)
        _toolTip = f'<table width={tt_width}><tr><td>{_toolTip}</td></tr></table>'
        _toolTip = f'<font face=\"Lucida Console\" size=4>{_toolTip}</font>'
        _toolTip = _toolTip.replace(" Rating", "")
        return _toolTip
