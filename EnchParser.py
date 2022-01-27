import re
import requests

ench_url = "https://wotlk.evowow.com/?enchantment="
BASE_STATS = {'stamina', 'intellect', 'spirit', 'strength', 'agility'}
short_stats = {
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
    'sta': 'stamina',
    'int': 'intellect',
    'spi': 'spirit',
    'str': 'strength',
    'agi': 'agility',
    'armor': 'armor'}

loaded = {}
loading = set()
def get_ench_raw(ench_ID):
    if ench_ID in loaded:
        return loaded[ench_ID]
    elif ench_ID in loading:
        while ench_ID in loading:
            pass
        return loaded[ench_ID]
    loading.add(ench_ID)
    ench = loaded[ench_ID] = requests.get(f'{ench_url}{ench_ID}').text
    loading.remove(ench_ID)
    return ench

def get_names(ench_raw):
    n0 = re.findall('<title>(.*?) - Enchantment', ench_raw[:200], re.S)[0].lower()
    if 'mana ' in n0 and '5' in n0:
        mana = re.findall('(mana [^\+]+)', n0)[0]
        n0 = n0.replace(mana, 'mp5')
    n1 = re.findall('name_enus":"([^"]+)', ench_raw)[1].lower()
    return n0, n1

def parse_enchant(q):
    try:
        stat = re.findall("(\d+) ([a-z5\' ]+)", q)[0]
        return stat[1], int(stat[0])
    except:
        print('ERROR PARSING ENCHANT:', q)
        return '', ''

def get_ench(ench_raw):
    stats = set()
    names = get_names(ench_raw)
    n0 = names[0]
    if '+' in n0:  
        if "all stats" in n0:
            value = int(re.findall('(\d+)', n0)[0])
            stats |= {(stat, value) for stat in BASE_STATS}
        else:
            for stat in n0.split(' and '):
                if stat[1].isdigit() and '%' not in stat:
                    stats.add(parse_enchant(stat))
            #     print(x[1], x[1].isdigit(), x, v)
            # stats |= {parse_enchant(x) for x in n0.split(' and ') if x[1].isdigit()}
            # print(stats)
    if "Statistics" in ench_raw:
        stats_tmp = re.findall("Value: (\d\d?).+?traits..([^']*)", ench_raw, re.S)
        stats |= {(short_stats[stat], int(value)) for value, stat in stats_tmp if stat in short_stats}
    if 'Defense:' in ench_raw:
        armor = re.findall("Defense: .*?Value: (\d{1,3})<", ench_raw)[0]
        stats.add(('armor', int(armor)))
    stats = list(stats)
    return {'names': names, 'stats': stats}

if __name__ == "__main__":
    qq = [
        3633, 3628, 3605, 2933, 2938, 3294, 2679, 3789, 3623, 3548, 3590, 3820, 3859,
        3520, 3810, 3832, 3758, 3604, 3520, 3719, 3606, 3560, 3520, 3834, 3520, 3563,
        3545, 3859, 3232, 3747, 3243, 3247, 3722, 2673, 2381, 3546, 3819, 3627, 3244]
    for ench_ID in qq:
        print(ench_ID)
        ench_raw = get_ench_raw(ench_ID)
        ench = get_ench(ench_raw)
        print(ench)
