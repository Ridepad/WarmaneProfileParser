import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

HEADERS = {'User-Agent': "WarmaneProfileParser/1.3"}

def get_character(char_name: str, server: str):
    url = f'http://armory.warmane.com/character/{char_name}/{server}'
    for _ in range(3):
        try:
            page = requests.get(url, headers=HEADERS, timeout=1, allow_redirects=False)
            if page.status_code == 200:
                return page.text
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            pass

def parse_slot(slot: Tag):
    if not slot.get('rel'): # Empty slot
        return {}
    # rel="item=51290&ench=3820&gems=3621:3520:0&transmog=22718"
    item_properties_list = slot['rel'][0].split('&')
    # item_properties = ['item=51290', 'ench=3820', 'gems=3621:3520:0', 'transmog=22718']
    item_properties = dict(property.split('=') for property in item_properties_list)
    # item_properties = {'item': '51290', 'ench': '3820', 'gems': '3621:3520:0', 'transmog': '22718'}
    item_properties['gems'] = item_properties.get('gems', '0:0:0').split(':')
    # item_properties = {'item': '51290', 'ench': '3820', 'gems': ['3621','3520','0'], 'transmog': '22718'}
    return item_properties

def get_gear(profile: BeautifulSoup):
    equipment = profile.find(class_="item-model").find_all('a')
    return [parse_slot(slot) for slot in equipment]

def get_data(stats: Tag, c: str):
    text: Tag
    for tag in stats.find_all(class_=c):
        for text in tag.find_all(class_='text'):
            try:
                specname, value = text.stripped_strings
                yield specname, value
            except ValueError:
                pass

def get_spec(stats: Tag):
    return {
        specname: value.replace(' ', '')
        for specname, value in get_data(stats, "specialization")
    }

def get_profs(stats: Tag):
    return {
        specname: value.split()[0]
        for specname, value in get_data(stats, "profskills")
    }

DOUBLE_RACES = ['Night', 'Blood']
DOUBLE_CLASSES = ['Knight']
def get_basic_info(profile: BeautifulSoup):
    level_race_class = profile.find(class_="level-race-class").text.strip()
    level_race_class = level_race_class.split(',')[0]
    level_race_class = level_race_class.split(' ')[1:]
    level = level_race_class[0]
    race = level_race_class[1]
    if race in DOUBLE_RACES:
        race = ' '.join(level_race_class[1:3])
    class_ = level_race_class[-1]
    if class_ in DOUBLE_CLASSES:
        class_ = ' '.join(level_race_class[-2:])

    return level, race, class_

def get_profile(char_name, server='Lordaeron'):
    profile_raw = get_character(char_name, server)
    if profile_raw is None or "guild-name" not in profile_raw:
        return {}
    profile_raw = BeautifulSoup(profile_raw, 'html.parser')
    level, race, class_ = get_basic_info(profile_raw)
    stats = profile_raw.find(id='character-profile').find(class_="information-right")
    
    return {
        'level': level,
        'race': race,
        'class': class_,
        "guild": profile_raw.find(class_="guild-name").text,
        "specs": get_spec(stats),
        "profs": get_profs(stats),
        "gear_data": get_gear(profile_raw),
    }


def __test():
    char_name = "Nomadra"
    profile = get_profile(char_name)
    print(profile)

if __name__ == "__main__":
    __test()
