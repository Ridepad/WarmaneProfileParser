import os
import json
import logging

import requests


def new_folder_path(root, name):
    new_folder = os.path.join(root, name)
    if not os.path.exists(new_folder):
        os.makedirs(new_folder, exist_ok=True)
    return new_folder

def json_read(file_name) -> dict:
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}

def json_write(file_name, data, indent=None):
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=indent, default=sorted)

def setup_logger(logger_name, log_file):
    LOGGING_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s():%(lineno)s] %(message)s"
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter(LOGGING_FORMAT)
    fileHandler = logging.FileHandler(log_file)
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

def requests_get(page_url, headers, timeout=1, attempts=3):
    for _ in range(attempts):
        try:
            page = requests.get(page_url, headers=headers, timeout=timeout, allow_redirects=False)
            if page.status_code == 200:
                return page
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            pass
    LOGGER.error("Failed to load page:", page_url)
    return None

def requests_post(page_url, headers, data=None, timeout=1, attempts=3):
    for _ in range(attempts):
        try:
            return requests.post(page_url, data=data, headers=headers, timeout=timeout)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            pass
    
    LOGGER.error("Failed to load page:", page_url)
    return None

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
CACHE_DIR = new_folder_path(DIR_PATH, "cache")
ICON_CACHE_DIR = new_folder_path(CACHE_DIR, "icons")
ITEM_CACHE_DIR = new_folder_path(CACHE_DIR, "items")
ENCH_CACHE_DIR = new_folder_path(CACHE_DIR, "enchants")
CHAR_CACHE_DIR = new_folder_path(CACHE_DIR, "characters")

STATIC_DIR = new_folder_path(DIR_PATH, "static")
ACHIEVEMENTS_FILE = os.path.join(STATIC_DIR, 'achievements.json')
ACHIEVEMENTS_DATA = json_read(ACHIEVEMENTS_FILE)
CATEGORIES_FILE = os.path.join(STATIC_DIR, 'categories.json')
CATEGORIES_DATA = json_read(CATEGORIES_FILE)
SETS_FILE = os.path.join(STATIC_DIR, 'sets.json')
SETS_DATA = json_read(SETS_FILE)
SETS_ITEMS_IDS = set()
for x in SETS_DATA.get('items', {}).values():
    SETS_ITEMS_IDS.update(x)

SIZE_FILE = os.path.join(DIR_PATH, "_achi_size.cfg")

LOGFILE = os.path.join(DIR_PATH,'_errors.log')
LOGGER = setup_logger("errors_logger", LOGFILE)

ICON_URL = "https://wotlk.evowow.com/static/images/wow/icons/large"

BASE_STATS = {'stamina', 'intellect', 'spirit', 'strength', 'agility'}
SHORT_STATS = {
    'armorpenrtng': 'armor penetration rating',
    'resirtng': 'resilience rating',
    'hitrtng': 'hit rating',
    'splpwr': 'spell power',
    'atkpwr': 'attack power',
    'hastertng': 'haste rating',
    'critstrkrtng': 'critical strike rating',
    'exprtng': 'expertise rating',
    'defrtng': 'defense rating',
    'dodgertng': 'dodge rating',
    'parryrtng': 'parry rating',
    'manargn': 'mp5',
    'healthrgn': 'hp5',
    'sta': 'stamina',
    'int': 'intellect',
    'spi': 'spirit',
    'str': 'strength',
    'agi': 'agility',
}

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
