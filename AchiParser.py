import json
import re

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

TOOLTIPS = {}
ACHI_CACHE = {}

HEADERS = {'User-Agent': "WarmaneAchiParser/1.0"}

try:
    with open("static/achievements.json", 'r') as f:
        ACHIEVS = json.load(f)
except FileNotFoundError:
    ACHIEVS = {}

try:
    with open("static/categories.json", 'r') as f:
        CATEGORIES = json.load(f)
except FileNotFoundError:
    CATEGORIES = {}

def parse_date(achi: Tag):
    _date = achi.find(class_="date")
    if not _date:
        return ""
    _date = _date.text.strip()
    m, d, y = re.findall('(\d\d)/(\d\d)/(\d\d\d\d)', _date)[0]
    return f"{y}-{m}-{d}"

def get_achi_dates(achievements: str):
    char_achievements = {}
    achi: Tag
    achievs = BeautifulSoup(achievements, features="html.parser")
    for achi in achievs.find_all(class_="achievement"):
        _id = achi["id"].replace('ach', '')
        _date = parse_date(achi)
        char_achievements[_id] = _date
    return char_achievements

def get_achievs(char_name: str, server: str, category_id: int):
    url = f"http://armory.warmane.com/character/{char_name}/{server}/achievements"
    _achs = ACHI_CACHE.setdefault(url, {})
    if category_id in _achs:
        return _achs[category_id]

    def get_post(attempt=0):
        if attempt > 2:
            return
        try:
            return requests.post(url, data={"category": category_id}, headers=HEADERS, timeout=1)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            return get_post(attempt+1)
    
    response = get_post()
    try:
        achievements = response.json()['content']
        _dates = get_achi_dates(achievements)
        _achs[category_id] = _dates
        return _dates
    except json.decoder.JSONDecodeError:
        return {}

def format_line(body, color='', size=''):
    if color or size:
        if color:
            color = f' color="#{color}"'
        if size:
            size = f' size={size}'
        return f'<font{size}{color}>{body}</font>'
    return body

def make_toolTip(char_name, server, size, category_name):
    c = TOOLTIPS.setdefault(server, {}).setdefault(char_name, {}).setdefault(size, {})
    if category_name in c:
        return c[category_name]
    _cat = CATEGORIES[category_name][size]
    all_achi = {}
    for category_id in _cat['cats']:
        all_achi.update(get_achievs(char_name, server, category_id))
    
    _toolTip = []
    for cat_id, cat_name in _cat['sep'].items():
        _toolTip.append(format_line(cat_name, 'FFFFFF', 5))
        for achi_id, achi_name in ACHIEVS[cat_id].items():
            color = '00FF00' if all_achi.get(achi_id) else 'AAAAAA'
            _toolTip.append(format_line(achi_name, color))
    _toolTip = '</td></tr><tr><td>'.join(_toolTip)
    _toolTip = f'<table><tr><td>{_toolTip}</td></tr></table>'
    _toolTip = f'<font face="Lucida Console" size=4>{_toolTip}</font>'
    return _toolTip
