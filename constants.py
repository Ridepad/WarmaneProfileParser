import json
import logging
import os
from time import sleep

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
    LOGGING_FORMAT = "[%(asctime)s] [%(levelname)s] %(filename)s:%(lineno)s:%(funcName)s() %(message)s"
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter(LOGGING_FORMAT)
    fileHandler = logging.FileHandler(log_file)
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

def requests_get(page_url, headers, timeout=2, attempts=3):
    for _ in range(attempts):
        try:
            page = requests.get(page_url, headers=headers, timeout=timeout, allow_redirects=False)
            if page.status_code == 200:
                return page
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            sleep(3)
    
    LOGGER.error(f"Failed to load page: {page_url}")
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

SIZE_FILE = os.path.join(DIR_PATH, "_achi_size.cfg")

LOGFILE = os.path.join(DIR_PATH,'_errors.log')
LOGGER = setup_logger("errors_logger", LOGFILE)

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

GEMS = {
    "red": {
        "socket": (1, 0, 0),
        "color_hex": "ff0000",
        "unique": {"blood garnet", "bloodstone", "cardinal ruby", "kailee's rose", "living ruby", "scarlet ruby", "test living ruby"},
        "prefix": {"bold", "bright", "crimson", "delicate", "don", "flashing", "fractured", "mighty", "precise", "runed", "stark", "subtle", "teardrop"}
    },
    "yellow": {
        "socket": (0, 1, 0),
        "color_hex": "edc600",
        "unique": {"autumn's glow", "blood of amber", "dawnstone", "facet of eternity", "golden draenite", "kharmaa's grace", "king's amber", "lionseye", "stone of blades", "sublime mystic dawnstone", "sun crystal"},
        "prefix": {"brilliant", "gleaming", "great", "mystic", "quick", "rigid", "smooth", "thick"}
    },
    "blue": {
        "socket": (0, 0, 1),
        "color_hex": "4444ff",
        "unique": {"azure moonstone", "chalcedony", "charmed amani jewel", "empyrean sapphire", "eye of the sea", "falling star", "majestic zircon", "sky sapphire", "star of elune"},
        "prefix": {"lustrous", "solid", "sparkling", "stormy"}
    },
    "orange": {
        "socket": (1, 1, 0),
        "color_hex": "ff8800",
        "unique": {"ametrine", "assassin's fire opal", "beaming fire opal", "enscribed fire opal", "flame spessarite", "glistening fire opal", "huge citrine", "infused fire opal", "iridescent fire opal", "monarch topaz", "mysterious fire opal", "nimble fire opal", "noble topaz", "pyrestone", "shining fire opal", "splendid fire opal"},
        "prefix": {"accurate", "champion's", "deadly", "deft", "durable", "empowered", "etched", "fierce", "glimmering", "glinting", "inscribed", "lucent", "luminous", "potent", "pristine", "reckless", "resolute", "resplendent", "stalwart", "stark", "unstable", "veiled", "wicked"}
    },
    "green": {
        "socket": (0, 1, 1),
        "color_hex": "00aa55",
        "unique": {"dark jade", "deep peridot", "effulgent chrysoprase", "eye of zul", "forest emerald", "polished chrysoprase", "rune covered chrysoprase", "seaspray emerald", "talasite", "test dazzling talasite", "unstable talasite"},
        "prefix": {"barbed", "dazzling", "enduring", "energized", "forceful", "intricate", "jagged", "lambent", "misty", "notched", "opaque", "radiant", "seer's", "shattered", "shining", "steady", "sundered", "tense", "timeless", "turbid", "vivid"}
    },
    "purple": {
        "socket": (1, 0, 1),
        "color_hex": "6600bb",
        "unique": {"blessed tanzanite", "brutal tanzanite", "dreadstone", "fluorescent tanzanite", "imperial tanzanite", "nightseye", "pulsing amethyst", "qa test blank purple gem", "shadowsong amethyst", "soothing amethyst", "twilight opal"},
        "prefix": {"balanced", "defender's", "glowing", "guardian's", "infused", "mysterious", "puissant", "purified", "regal", "royal", "shadow", "shifting", "sovereign", "tenuous"}
    },
    "prismatic": {
        "socket": (1, 1, 1),
        "color_hex": "a335ee",
        "unique": {"chromatic sphere", "enchanted pearl", "enchanted tear", "infinite sphere", "nightmare tear", "prismatic sphere", "soulbound test gem", "void sphere"},
        "prefix": {}
    },
    "meta": {
        "socket": (0, 0, 0),
        "color_hex": "6666ff",
        "unique": {"austere earthsiege diamond", "beaming earthsiege diamond", "brutal earthstorm diamond", "earthsiege diamond", "earthstorm diamond", "effulgent skyflare diamond", "imbued unstable diamond", "invigorating earthsiege diamond", "mystical skyfire diamond", "potent unstable diamond", "revitalizing skyflare diamond", "skyfire diamond", "skyflare diamond", "tenacious earthstorm diamond"},
        "prefix": {"bracing", "chaotic", "destructive", "ember", "enigmatic", "eternal", "forlorn", "impassive", "insightful", "persistent", "powerful", "relentless", "swift", "thundering", "tireless", "trenchant"}
    }
}

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
