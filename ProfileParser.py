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

#rewrite this
def get_SpecsProfs(profile):
    SpecsProfs = {
        'Specialization': [],
        'Player vs Player': None,
        'Professions': [],
        'Secondary Skills': []
    }
    stats = profile.find(id='character-profile').find(class_="information-right")
    for _string in stats.stripped_strings:
        if _string == 'Recent Activity':
            break
        if _string in SpecsProfs:
            _cat_list = SpecsProfs[_string]
            _sub_list = []
        elif _cat_list is not None:
            _sub_list.append(_string)
            if '/' in _string:
                _cat_list.append(_sub_list)
                _sub_list = []

    list_of_specs_profs = []
    category_lists = [cat for cat in SpecsProfs.values() if cat]
    for category_list in category_lists:
        for name, value in sorted(category_list):
            if name in ('First Aid', 'Fishing'):
                continue
            value = value.split()
            value = ''.join(value) if len(value) > 3 else value[0]
            list_of_specs_profs.append(f'{name:<14} {value:>8}')
        list_of_specs_profs.append('')
    return '\n'.join(list_of_specs_profs)

def get_profile(char_name, server):
    try:
        profile_url = f'http://armory.warmane.com/character/{char_name}/{server}'
        return requests.get(profile_url, timeout=5).text
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
        return ""

def main(char_name, server='Lordaeron'):
    profile_raw = get_profile(char_name, server)
    if "guild-name" in profile_raw:
        profile_raw = BeautifulSoup(profile_raw, 'html.parser')
        guild = profile_raw.find(class_="guild-name").text
        specsProfs = get_SpecsProfs(profile_raw)
        profile = get_gear(profile_raw)
        profile.append(guild)
        profile.append(specsProfs)
        return profile

if __name__ == "__main__":
    char_name = "Nomadra"
    profile = main(char_name)
    print(profile)
