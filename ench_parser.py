import os
import re
import threading

from bs4 import BeautifulSoup
from bs4.element import Tag

from constants import LOGGER, ENCH_CACHE_DIR, BASE_STATS, SHORT_STATS, json_read, json_write, requests_get

HEADERS = {'User-Agent': "WarmaneProfileParser ench_parser/1.0"}
CACHED: dict[str, dict[str, list[str, str]]] = {}
LOADING: dict[str, threading.Thread] = {}

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

    def run(self) -> None:
        ench_file_name = os.path.join(ENCH_CACHE_DIR, f"{self.ench_ID}.json")
        ench = json_read(ench_file_name)
        if ench:
            CACHED[self.ench_ID] = ench
            return
        try:
            url = f"https://wotlk.evowow.com/?enchantment={self.ench_ID}"
            ench_raw = requests_get(url, HEADERS).text
            ench = get_ench(ench_raw)
            CACHED[self.ench_ID] = ench
            json_write(ench_file_name, ench)
        except Exception:
            LOGGER.exception('EnchParser run')


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
