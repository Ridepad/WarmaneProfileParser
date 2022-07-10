import json
import os
import re
from urllib import response

from PyQt5 import QtCore, QtGui

import ench_parser
from constants import (
    BASE_STATS, GEMS, ICON_CACHE_DIR, ITEM_CACHE_DIR, LOGGER, SETS_DATA, STATS_DICT,
    json_read, json_write, requests_get)

ICON_URL = "https://wotlk.evowow.com/static/images/wow/icons/large"
HEADERS = {"User-Agent": "WarmaneProfileParser item_parser/1.0"}
DEFAULT_GEM_DATA = {"socket": (0, 0, 0), 'color_hex': "ffffff"}
QUALITY_COLOR = ["FFFFFF", "FFFFFF", "1EFF0B", "0560DD", "A32AB9", "FF8011", "FFFFFF",  "ACBD80"]
ENCHANTABLE = {"Head", "Shoulder", "Chest", "Legs", "Hands", "Feet", "Wrist", "Back", "Main Hand", "Off Hand", "One-Hand", "Two-Hand"}
ICONS: dict[str, QtGui.QPixmap] = {}
TOOLTIPS = {}

SETS_ITEMS_IDS = set()
for x in SETS_DATA.get('items', {}).values():
    SETS_ITEMS_IDS.update(x)

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
    item_raw = requests_get(item_url, HEADERS).text
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

def get_item(item_ID: str):
    item_path = os.path.join(ITEM_CACHE_DIR, f"{item_ID}.json")
    item = json_read(item_path)
    if not item:
        item = get_missing_item_info(item_ID)
        json_write(item_path, item)
    return item

def save_icon(icon_path, icon_data):
    if len(icon_data) > 50:
        with open(icon_path, 'wb') as f:
            f.write(icon_data)
            
def get_icon(icon_name):
    '''Gets icon from cache if available, otherwise downloads and saves'''
    if icon_name in ICONS:
        return ICONS[icon_name]

    icon_path = os.path.join(ICON_CACHE_DIR, f"{icon_name}.jpg")
    try:
        with open(icon_path, 'rb') as img:
            icon = img.read()
    except FileNotFoundError:
        icon_url = f"{ICON_URL}/{icon_name}.jpg"
        icon = requests_get(icon_url, HEADERS).content
        save_icon(icon_path, icon)

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

def get_gem_data(gem_name: str):
    for gem_data in GEMS.values():
        if gem_name in gem_data['unique']:
            return gem_data
    prefix = gem_name.split(' ', 1)[0]
    for gem_data in GEMS.values():
        if prefix in gem_data['prefix']:
            return gem_data
    LOGGER.info(f'Missing gem info: {gem_name}')
    return DEFAULT_GEM_DATA

def gem_color(gem_name: str):
    return get_gem_data(gem_name)['color_hex']

def socket_bonus_matched(item_gems, item_sockets):
    for gem_name in item_gems:
        gem_data = get_gem_data(gem_name)
        socket_matches = gem_data['socket']
        item_sockets = [x-y for x, y in zip(item_sockets, socket_matches)]
    return all(x <= 0 for x in item_sockets)

def check_item_set(item_ID: str, player_class: str):
    item_set: dict[str, dict[str, list]]
    item_set = SETS_DATA[player_class]
    if item_ID in SETS_ITEMS_IDS:
        item_set = SETS_DATA["items"]
    
    for name, sets in item_set.items():
        if item_ID in sets['items']:
            return name, sets
    return None


class Item(QtCore.QThread):
    item_error = QtCore.pyqtSignal()
    item_loaded = QtCore.pyqtSignal(list)
    item_set_loaded = QtCore.pyqtSignal(dict)

    def __init__(
        self,
        item_data: dict[str, str],
        item_icon,
        gear_ids: set[str],
        player_class: str,
        is_enchanter: bool
    ):
        super().__init__()
        self.tool_tip_width = 0
        self.item_icon = item_icon
        self.gear_ids = gear_ids
        self.player_class = player_class
        self.is_enchanter = is_enchanter
        self.item_ID = item_data['item']
        self.GEMS = item_data.get('gems')
        self.ENCHANT_ID = item_data.get('ench')
        self.TOTAL_STATS = []
        self.SET_BONUSES = []
        self.stats_funcs = (
            self.get_self_stats,
            self.get_self_enchant,
            self.get_self_sockets,
            self.get_self_add)
    
    def run(self):
        try:
            self.ITEM = get_item(self.item_ID)
            icon_name = self.ITEM['icon']
            pixmap = get_icon(icon_name)
            self.item_icon.setPixmap(pixmap)
        except AttributeError:
            self.item_error.emit()
            LOGGER.error('ItemParser run - item is None')
            return
        except RuntimeError:
            LOGGER.exception('ItemParser run')
            return
        
        self.get_item_set()
        slot = self.ITEM["slot"]
        self.ENCHANTABLE = slot in ENCHANTABLE or slot == 'Finger' and self.is_enchanter
        self.TOTAL_STATS.extend(self.ITEM['stats'])
        TOOLTIPS[self.item_icon] = self.make_tool_tip()
        self.item_loaded.emit(self.TOTAL_STATS)

    def check_item_set(self):
        item_set: dict[str, dict[str, list]]
        item_set = SETS_DATA[self.player_class]
        if self.item_ID in SETS_ITEMS_IDS:
            item_set = SETS_DATA["items"]
        
        for name, sets in item_set.items():
            if self.item_ID in sets['items']:
                return name, sets
        return None

    def get_item_set(self):
        _set = self.check_item_set()
        if _set is None:
            return

        set_name, set_data = _set
        only_stats = []
        _data = {'name': set_name, 'stats': only_stats}

        _set_ids = set(set_data["items"])
        equipped_set_pieces = len(self.gear_ids & _set_ids)
        max_set_pieces = len(set_data['sets'][0]['pieces'])
        set_name_with_pieces = f"{set_name} ({equipped_set_pieces}/{max_set_pieces})"
        self.SET_BONUSES.append(format_line(set_name_with_pieces, 'DBB402'))
        
        for pieces, set_bonus in set_data['set_bonus']:
            set_bonus_reached = pieces <= equipped_set_pieces
            if set_bonus_reached:
                _color = '11DD11'
            else:
                _color = '777777'
            
            if type(set_bonus) == list:
                stat, value = set_bonus
                line = f'+{value:>3} {stat}'.title()
                if set_bonus_reached:
                    only_stats.append(set_bonus)
            else:
                line = set_bonus

            line = f"- {pieces}: {line}"
            self.SET_BONUSES.append(format_line(line, _color))

        self.item_set_loaded.emit(_data)

    def get_gem_colors(self):
        item_sockets = self.ITEM.get("sockets", [])
        socket_amount = sum(item_sockets)
        if not socket_amount:
            return
        
        if self.ITEM["slot"] == 'Waist' or self.ITEM["slot"] == 'Head' and self.ITEM['meta']:
            socket_amount += 1
        
        item_gems = []
        for n in range(socket_amount):
            gem_ID = self.GEMS[n]
            if gem_ID == '0':
                yield 'Missing gem', 'FF0000'
                continue
            gem_data = ench_parser.main(gem_ID)
            self.TOTAL_STATS.extend(gem_data['stats'])
            gem_stat, gem_name = gem_data['names']
            gem_name = gem_name.lower().replace('perfect ', '')
            item_gems.append(gem_name)
            _color = gem_color(gem_name)
            yield gem_stat, _color

        _color = '777777'
        stat, value = self.ITEM["socket bonus"]
        if len(item_gems) == socket_amount and socket_bonus_matched(item_gems, item_sockets):
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
        return [
            self.format_enchant(gem_name, color)
            for gem_name, color in self.get_gem_colors()
        ]
    
    def get_self_add(self):
        '''Additional text - On equip / on use'''
        additional_text = self.ITEM.get('add_text')
        if not additional_text:
            return
        
        return [format_line(text, '11DD11') for text in additional_text]
    
    def get_self_add(self):
        '''Additional text - On equip / on use'''
        if self.SET_BONUSES:
            return self.SET_BONUSES
        
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
