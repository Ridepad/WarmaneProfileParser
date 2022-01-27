import json
import re
import threading

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

HEADERS = {'User-Agent': "EnchParser"}
ENCH_CACHE = 'Ench_cache'

CACHED: dict[str, dict] = {}
LOADING: dict[str, threading.Thread] = {}

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

def get_names(soup: BeautifulSoup):
    n0 = soup.find("title").text.split(' - ')[0]
    n1 = soup.find(id="topbar").find_next_sibling().text
    n1 = re.findall('name_enus":"([^"]+)', n1)[1]
    return [n0, n1]

def get_value(text):
    try:
        return text and "%" not in text and re.findall("(\d{1,3})", text)[0]
    except IndexError:
        return

def parse_each(td: Tag):
    small = td.find("small")
    if small is None:
        return

    value = small.text
    stat_tag = small.find_next_sibling()
    if stat_tag is None:
        if not td.text or "Defense: (Physical)" not in td.text:
            return
        stat = ["Armor"]
    elif not stat_tag.get("type"):
        value = td.find('a').text
        stat = re.findall("[A-z ]+", value)
    else:
        stat = re.findall("\['([a-z]+)", stat_tag.text)
    value = get_value(value)
    if value and stat:
        stat = stat[0].lower().replace('increased', '').strip()
        return SHORT_STATS.get(stat, stat), int(value)
    
def get_ench(ench_raw: str):
    soup = BeautifulSoup(ench_raw, features="html.parser")
    stats_table = soup.find(id="spelldetails")
    stats = [
        parse_each(td)
        for td in stats_table.find_all("td")
    ]
    stats = [x for x in stats if x]
    names = get_names(soup)
    for x in names:
        if "all stats" not in x.lower(): continue
        for s in BASE_STATS:
            stats.append((s, int(get_value(x))))
    return {
        "names": names,
        "stats": stats
    }

class EnchGetter(threading.Thread):
    def __init__(self, ench_ID) -> None:
        super().__init__()
        self.ench_ID = ench_ID
        self.file_name = f"{ENCH_CACHE}/{self.ench_ID}.json"

    def run(self):
        try:
            with open(self.file_name, 'r') as f:
                CACHED[self.ench_ID] = json.load(f)
        except FileNotFoundError:
            ench_raw = get_page(self.ench_ID)
            ench = get_ench(ench_raw)
            CACHED[self.ench_ID] = ench
            self.save(ench)

    def save(self, data):
        with open(self.file_name, 'w') as f:
            json.dump(data, f)

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
