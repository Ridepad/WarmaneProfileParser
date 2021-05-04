import requests
from bs4 import BeautifulSoup

def get_gear(profile):
    gearIDs = []
    gearData = {}
    equipment = profile.find(class_="item-model").find_all('a')
    for slot in equipment:
        try:
            item_stats = slot.get('rel')[0]
            # item_stats = item=51290&ench=3820&gems=3621:3520:0&transmog=22718
            item_stats = item_stats.split('&')
            # item_stats = ['item=51290', 'ench=3820', 'gems=3621:3520:0', 'transmog=22718']
            item_stats = [stat.split('=') for stat in item_stats]
            # item_stats = [['item', '51290'], ['ench', '3820'], ['gems', '3621:3520:0'], ['transmog', '22718']]
            item_ID = item_stats.pop(0)[1]
            gearIDs.append(item_ID)
            # item_stats = [['ench', '3820'], ['gems', '3621:3520:0'], ['transmog', '22718']]
            item_stats = dict(item_stats)
            # item_stats = {'ench': '3820', 'gems': '3621:3520:0', 'transmog': '22718'}
            item_stats['gems'] = item_stats['gems'].split(':') if 'gems' in item_stats else ["0"] * 3
            gearData[item_ID] = item_stats
        except TypeError: #Empty slot
            gearIDs.append('')
    return [gearData, gearIDs]

def format_line(name, value):
    value = value.replace(' ','')
    if value.count('/') == 1:
        value = value.split('/')[0]
    return f'{name:<14}{value:>9}'

def get_SpecsProfs(profile):
    stats = profile.find(id='character-profile').find(class_="information-right")
    stats = list(stats.stripped_strings)
    stats.remove('Specialization')
    if 'PvP Teams' in stats:
        stats = stats[:stats.index('PvP Teams')]
    else:
        stats = stats[:stats.index('Recent Activity')]
    if 'Professions' in stats:
        stats[stats.index('Player vs Player'):stats.index('Professions')+1] = ['','']
    else:
        del stats[stats.index('Player vs Player'):]
    if 'Secondary Skills' in stats:
        stats.remove('Secondary Skills')
    if 'Cooking' not in stats:
        stats.append('Cooking')
        stats.append('0')
    list_of_specs_profs=[format_line(name, value) for name, value in zip(stats[::2],stats[1::2]) if name not in ('First Aid', 'Fishing')]
    return '\n'.join(list_of_specs_profs)

def get_profile(char_name, server):
    try:
        profile_url = f'http://armory.warmane.com/character/{char_name}/{server}'
        return requests.get(profile_url, timeout=5).text
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
        return ""

def main(char_name, server='Lordaeron'):
    profile_raw = get_profile(char_name, server)
    if "guild-name" not in profile_raw:
        return []
    profile_raw = BeautifulSoup(profile_raw, 'html.parser')
    guild = profile_raw.find(class_="guild-name").text
    level_race_class = profile_raw.find(class_="level-race-class").text.strip()
    level_race_class = level_race_class.replace(',','')
    level_race_class = level_race_class.split(' ')[1:-1]
    level_race_class = ' '.join(level_race_class)
    specsProfs = get_SpecsProfs(profile_raw)
    profile = get_gear(profile_raw)
    profile.append(guild)
    profile.append(specsProfs)
    profile.append(level_race_class)
    return profile

if __name__ == "__main__":
    char_name = "Nomadra"
    profile = main(char_name)
    print(profile)
