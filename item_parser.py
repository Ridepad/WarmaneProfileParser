import json
import logging
import os
import re

import requests
from PyQt5 import QtCore, QtGui

import ench_parser

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
CACHE = os.path.join(DIR_PATH, 'cache')
ICON_CACHE = os.path.join(CACHE, 'icons')
ITEM_CACHE = os.path.join(CACHE, 'items')
LOGGER = logging.getLogger("errors_logger")

ICONS: dict[str, QtGui.QPixmap] = {}
TOOLTIPS = {}
BASE_STATS = {'stamina', 'intellect', 'spirit', 'strength', 'agility'}
QUALITY_COLOR = ['FFFFFF', 'FFFFFF', '1EFF0B', '0560DD', 'A32AB9', 'FF8011', 'FFFFFF',  'ACBD80']
ENCHANTABLE = {'Head', 'Shoulder', 'Chest', 'Legs', 'Hands', 'Feet', 'Wrist', 'Back', 'Main Hand', 'Off Hand', 'One-Hand', 'Two-Hand'}
HEADERS = {'User-Agent': "WarmaneProfileParser ItemParser/1.0"}

UNIQUE_GEMS = {
    "of the Sea": {
        'socket': (0, 0, 1),
        'color_hex': '4444ff',
    },
}

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
    0: "armor",
    35: "resilience rating",
    45: "spell power",
    38: "attack power",
    36: "haste rating",
    32: "critical strike rating",
    31: "hit rating",
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
}

def write_to_file(data, path, mode):
    '''Creates cache'''
    if len(data) > 50:
        with open(path, mode) as f:
            f.write(data)

def get_raw_stats(q: str):
    raw_stats = q[q.index("tooltip_enus"):]
    return raw_stats[:raw_stats.index("_[")]

def get_prim_stats(q):
    return re.findall("-stat(\d)[^\d]+(\d{1,3})", q)

def get_add_stats(q):
    return re.findall("Equip: [IR][a-z]+[^%\d]+(\d\d)\D+(\d{1,3})", q)

def get_armor(q):
    armor_value = re.findall('(\d+) Armor<', q)
    if not armor_value:
        return []
    armor_value = armor_value[0]
    if 'tooltip_armorbonus' in q:
        armor_bonus = re.findall('tooltip_armorbonus, (\d+)', q)[0]
        armor_value = int(armor_value) - int(armor_bonus)*2
    return [[0, armor_value]]

def get_stats(q):
    stats = get_prim_stats(q)
    stats.extend(get_add_stats(q))
    stats.extend(get_armor(q))
    return [(STATS_DICT[int(x)], int(y)) for x, y in stats if int(x) in STATS_DICT]

def get_sockets(q):
    colors = re.findall("socket-([a-z]{3,6})", q)
    return [colors.count(color) for color in ("red", "yellow", "blue")]

def get_socket_bonus(q):
    value, stat = re.findall("Socket Bonus:.+?(\d{1,2}) (.+?)<", q)[0]
    if '5' in stat:
        stat = "mp5"
    return stat, int(value)

def get_additional_text(q):
    def format(line):
        line = re.sub("<[^>]+>", "", line)
        if '%' in line:
            line = re.sub("\(.+?\)", "", line)
        return line.replace("&nbsp;", "")
    additional_text = re.findall("(Equip: [^IR].+?)...span>", q, re.S)
    additional_text.extend(re.findall("(Use: .+?)...span>", q, re.S))
    return [format(line) for line in additional_text]

def get_missing_item_info(item_ID):
    item_url = f'https://wotlk.evowow.com/?item={item_ID}'
    item_raw = requests.get(item_url, headers=HEADERS).text
    item_stats = re.findall('g_items[^{]+({.+?})', item_raw)
    item: dict = json.loads(item_stats[0])
    # item = {'quality': 4, 'icon': 'inv_mace_115', 'name_enus': 'Royal Scepter of Terenas II'}
    item['name'] = item.pop('name_enus')
    # item = {'quality': 4, 'icon': 'inv_mace_115', 'name': 'Royal Scepter of Terenas II'}
    try:
        item['ilvl'] = re.findall('Level: (\d{1,3})', item_raw)[0]
    except IndexError:
        return item

    raw_stats = get_raw_stats(item_raw)

    item['heroic'] = 'Heroic' in raw_stats

    slot = re.findall('td>([A-z -]+?)<', raw_stats)[0]
    if slot == 'Head':
        item['meta'] = 'socket-meta' in raw_stats
    item['slot'] = slot

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

def get_item(item_ID: str) -> dict:
    item_path = f'{ITEM_CACHE}/{item_ID}.json'
    try:
        with open(item_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        item = get_missing_item_info(item_ID)
        data = json.dumps(item)
        write_to_file(data, item_path, 'w')
        return item

def gem_color(gem_name: tuple[str, str]):
    hex: str
    name, type_ = gem_name
    
    if 'diamond' in type_:
        return '6666FF'
    
    if type_ in ['tear', 'sphere', 'pearl']:
        return 'A335EE'
    
    if type_ in UNIQUE_GEMS:
        hex = UNIQUE_GEMS[type_]['color_hex']
        return hex
    
    for g in GEMS.values():
        if name in g['names']:
            hex = g['color_hex']
            return hex

    #shouldnt reach here
    LOGGER.info(f'Missing gem info: f"{name}--{type_}')
    return 'FFFFFF'
            
def get_icon(icon_name):
    '''Gets icon from cache if available, otherwise downloads and saves'''
    if icon_name in ICONS:
        return ICONS[icon_name]

    icon_path = f'{ICON_CACHE}/{icon_name}.jpg'
    try:
        with open(icon_path,'rb') as img:
            icon = img.read()
    except FileNotFoundError:
        icon_url = f'https://wotlk.evowow.com/static/images/wow/icons/large/{icon_name}.jpg'
        icon = requests.get(icon_url, headers=HEADERS).content
        write_to_file(icon, icon_path, 'wb')

    _Pixmap = QtGui.QPixmap()
    _Pixmap.loadFromData(icon)
    ICONS[icon_name] = _Pixmap
    return _Pixmap

def format_line(body: str, color='', size=''):
    if color or size:
        if color:
            color = f' color="#{color}"'
        if size:
            size = f' size={size}'
        return f'<font{size}{color}>{body}</font>'
    return body

def socket_bonus_matched(item_gems, item_sockets):
    for name, type_ in item_gems:
        if type_ in ['tear', 'sphere', 'pearl']:
            item_sockets = [x-1 for x in item_sockets]
        elif type_ in UNIQUE_GEMS:
            socket_matches = UNIQUE_GEMS[type_]['socket']
            item_sockets = [x-y for x, y in zip(item_sockets, socket_matches)]
        elif type_ != 'diamond':
            for color in GEMS:
                if name in GEMS[color]['names']:
                    socket_matches = GEMS[color]['socket']
                    item_sockets = [x-y for x, y in zip(item_sockets, socket_matches)]
                    break
    return all(x <= 0 for x in item_sockets)


class Item(QtCore.QThread):
    item_loaded = QtCore.pyqtSignal(list)
    
    def __init__(self, item_data: dict[str, str], item_icon, is_enchanter: bool):
        super().__init__()
        self.tool_tip_width = 0
        self.item_icon = item_icon
        self.is_enchanter = is_enchanter
        self.item_ID = item_data['item']
        self.GEMS = item_data.get('gems')
        self.ENCHANT_ID = item_data.get('ench')
        self.stats_funcs = (
            self.get_self_stats,
            self.get_self_enchant,
            self.get_self_sockets,
            self.get_self_add)
            
    def run(self):
        self.ITEM = get_item(self.item_ID)
        
        try:
            icon_name = self.ITEM['icon']
            self.item_icon.setPixmap(get_icon(icon_name))
        except RuntimeError:
            LOGGER.exception('ItemParser run')
            return
        
        slot = self.ITEM["slot"]
        self.ENCHANTABLE = slot in ENCHANTABLE or slot == 'Finger' and self.is_enchanter
        self.TOTAL_STATS: list = self.ITEM['stats']
        self.item_loaded.emit(self.TOTAL_STATS)
        TOOLTIPS[self.item_icon] = self.make_tool_tip()

    def gem_data(self, socket_amount: int):
        if self.ITEM["slot"] == 'Waist' or self.ITEM["slot"] == 'Head' and self.ITEM['meta']:
            socket_amount += 1
        item_gems = []
        no_missing_gems = True

        for n in range(socket_amount):
            gem_ID = self.GEMS[n]
            if gem_ID == '0':
                yield 'Missing gem', 'FF0000'
                no_missing_gems = False
                continue
            gem = ench_parser.main(gem_ID)
            self.TOTAL_STATS.extend(gem['stats'])
            gem_stat, gem_name = gem['names']
            gem_name = gem_name.lower().replace('perfect ', '')
            gem_name = gem_name.split(' ', 1)
            item_gems.append(gem_name)
            _color = gem_color(gem_name)
            yield gem_stat, _color

        _color = '777777'
        stat, value = self.ITEM["socket bonus"]
        item_sockets = self.ITEM.get("sockets")
        if no_missing_gems and socket_bonus_matched(item_gems, item_sockets):
            self.TOTAL_STATS.append((stat.lower(), value))
            _color = '11DD11'
        yield f'+{value} {stat}', _color

    def update_max_tooltip_width(self, line) -> None:
        '''Updates tooltip width'''
        line_len = len(line)
        if line_len > self.tool_tip_width:
            self.tool_tip_width = line_len

    def get_self_stats(self):
        '''Stats of the item - base, additional stats and armor separated by blank line'''
        if not self.TOTAL_STATS:
            return
        
        tt = []
        for stat, value in self.TOTAL_STATS:
            if stat == 'armor':
                for _ in range(8 - len(tt)):
                    tt.append('')
            elif stat not in BASE_STATS and tt and '' not in tt:
                for _ in range(4 - len(tt)):
                    tt.append('')

            line = f'+{value:>3} {stat}'.title()
            tt.append(line)
            self.update_max_tooltip_width(line)
        return tt

    def format_enchant(self, enchant_name: str, color):
        self.update_max_tooltip_width(enchant_name)
        enchant_name = enchant_name.title().replace('And', 'and')
        return format_line(enchant_name, color)

    def get_self_enchant(self):
        if self.ENCHANT_ID:
            enchant = ench_parser.main(self.ENCHANT_ID)
            self.TOTAL_STATS.extend(enchant['stats'])
            enchant_name = enchant['names'][0]
            return [self.format_enchant(enchant_name, '11DD11')]
        elif self.ENCHANTABLE:
            return [format_line('Missing Enchant', 'FF0000')]
        else:
            return None

    def get_self_sockets(self):
        socket_amount = sum(self.ITEM.get("sockets", []))
        if not socket_amount:
            return

        return [
            self.format_enchant(gem_name, color)
            for gem_name, color in self.gem_data(socket_amount)
        ]
    
    def get_self_add(self):
        '''Additional text - On equip / on use'''
        additional_text = self.ITEM.get('add_text')
        if not additional_text:
            return
        
        return [format_line(text, '11DD11') for text in additional_text]

    def get_ilvl(self):
        _ilvl = self.ITEM["ilvl"]
        if self.ITEM['heroic']:
            _ilvl = format_line(_ilvl, '11DD11')
        return _ilvl
    
    def make_tool_tip(self):
        item_name = self.ITEM["name"]
        item_name_color = QUALITY_COLOR[self.ITEM['quality']]
        _toolTip = [
            format_line(item_name, item_name_color, 5),
            self.get_ilvl(),
            self.ITEM["slot"],
            self.ITEM.get('armor type', '')
        ]
        
        for f in self.stats_funcs:
            new_lines = f()
            if new_lines:
                _toolTip.append('')
                _toolTip.extend(new_lines)
        
        tt_width = max(300, (self.tool_tip_width+1) * 8, (len(item_name)+1) * 11)
        _toolTip = '\n'.join(_toolTip).strip('\n')
        _toolTip = _toolTip.replace('\n', '</td></tr><tr><td>')
        _toolTip = f'<table width={tt_width}><tr><td>{_toolTip}</td></tr></table>'
        _toolTip = f'<font face="Lucida Console" size=4>{_toolTip}</font>'
        return _toolTip
