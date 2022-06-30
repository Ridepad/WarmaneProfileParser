import json
import logging
import os
import re
import threading

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
CACHE = os.path.join(DIR_PATH, 'cache')
ENCH_CACHE = os.path.join(CACHE, 'enchants')
LOGGER = logging.getLogger("errors_logger")

CACHED: dict[str, dict[str, list[str, str]]] = {}
LOADING: dict[str, threading.Thread] = {}

HEADERS = {'User-Agent': "WarmaneProfileParser EnchParser/1.0"}
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

def get_page(ench_ID):
    url = f"https://wotlk.evowow.com/?enchantment={ench_ID}"
    for _ in range(3):
        try:
            page = requests.get(url, headers=HEADERS, timeout=2, allow_redirects=False)
            if page.status_code == 200:
                return page.text
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            pass
    
    return None

def get_value(text: str):
    try:
        if text and "%" not in text:
            s: str = re.findall("(\d{1,3})", text)[0]
            return s
    except IndexError:
        pass
    return None

def parse_each(td: Tag):
    small_tag = td.find("small")
    if small_tag is None:
        return None

    stats: list[str]
    value = small_tag.text
    stat_tag = small_tag.find_next_sibling()
    if stat_tag is None:
        if not td.text or "Defense: (Physical)" not in td.text:
            return None
        stats = ["Armor"]
    elif not stat_tag.get("type"):
        value = td.find('a').text
        stats = re.findall("[A-z ]+", value)
    else:
        stats = re.findall("\['([a-z]+)", stat_tag.text)
    
    value = get_value(value)
    if value is not None and len(stats) > 0:
        stat = stats[0].lower().replace('increased', '').strip()
        return SHORT_STATS.get(stat, stat), int(value)

    return None

def get_enchant_names(soup: BeautifulSoup) -> tuple[str, str]:
    n0 = soup.find("title").text.split(' - ')[0]
    n1 = soup.find(id="topbar").find_next_sibling().text
    n1 = re.findall('name_enus":"([^"]+)', n1)[1]
    return n0, n1
    
def get_ench(ench_raw: str):
    soup = BeautifulSoup(ench_raw, features="html.parser")
    stats_table = soup.find(id="spelldetails")
    stats = [
        parse_each(td)
        for td in stats_table.find_all("td")
    ]
    stats = [x for x in stats if x is not None]
    names = get_enchant_names(soup)
    for x in names:
        if "all stats" in x.lower():
            stats.extend((s, int(get_value(x))) for s in BASE_STATS)
    return {
        "names": names,
        "stats": stats
    }


class EnchGetter(threading.Thread):
    def __init__(self, ench_ID) -> None:
        super().__init__()
        self.ench_ID = ench_ID
        self.file_name = os.path.join(ENCH_CACHE, f"{self.ench_ID}.json")

    def run(self) -> None:
        try:
            with open(self.file_name, 'r') as f:
                CACHED[self.ench_ID] = json.load(f)
        except FileNotFoundError:
            try:
                ench_raw = get_page(self.ench_ID)
                ench = get_ench(ench_raw)
                CACHED[self.ench_ID] = ench
                self.save(ench)
            except Exception:
                LOGGER.exception('EnchParser run')

    def save(self, data) -> None:
        with open(self.file_name, 'w') as f:
            json.dump(data, f, default=list)


def main(ench_ID):
    if ench_ID in CACHED:
        return CACHED[ench_ID]
    ench_t = LOADING.get(ench_ID)
    if ench_t is None:
        ench_t = EnchGetter(ench_ID)
        ench_t.start()
        LOADING[ench_ID] = ench_t
    ench_t.join()
    return CACHED[ench_ID]


def __test():
    qq = [
        3633, 3628, 3605, 2933, 2938, 3294, 2679, 3789, 3623, 3548, 3590, 3820, 3859,
        3520, 3810, 3832, 3758, 3604, 3520, 3719, 3606, 3560, 3520, 3834, 3520, 3563,
        3545, 3859, 3232, 3747, 3243, 3247, 3722, 2673, 2381, 3546, 3819, 3627, 3244]
    for ench_ID in qq:
        ench = main(ench_ID)
        print(ench)

if __name__ == "__main__":
    __test()
