import json

with open("static/GS.json", 'r') as f:
    DATA = json.load(f)

SLOT_TYPES: list[str] = DATA['SLOT_TYPES']
LEGENDARY: dict[str, int] = DATA['LEGENDARY']
ITEM_TYPE: dict[str, int] = DATA['ITEM_TYPE']
ILVL_GS: dict[str, list[int]] = DATA['ILVL_GS']
GS_DATA: dict[str, dict[str, list[str]]] = DATA['GS_DATA']

def item_gs(item_ID: str, categoryName: str):
    if item_ID and categoryName != "":
        for ilvl, itemIDs in GS_DATA[categoryName].items():
            if item_ID in itemIDs:
                return ILVL_GS[ilvl][ITEM_TYPE[categoryName]]
    return 0 # not found/empty slot/tabard/shirt

def get_weapon_GS(item_ID):
    type = 'Legendary'
    weapon_GS = LEGENDARY.get(item_ID)
    if not weapon_GS:
        type = 'high'
        weapon_GS = item_gs(item_ID, type)
    if not weapon_GS:
        type = 'two_hand'
        weapon_GS = item_gs(item_ID, type)
    return weapon_GS, type

def main(gear):
    *armor_IDs, mainhand_item_ID, offhand_item_ID, ranged_item_ID = gear
    armor_GS = [item_gs(itemID, categoryName) for itemID, categoryName in zip(armor_IDs, SLOT_TYPES)]
    mainhand_GS, mainhand_type = get_weapon_GS(mainhand_item_ID)
    offhand_GS, offhand_type = get_weapon_GS(offhand_item_ID)
    if offhand_GS and offhand_type == 'two_hand':
        mainhand_GS = (mainhand_GS + offhand_GS) // 2
        offhand_GS = 0
    ranged_GS = item_gs(ranged_item_ID, 'ranged')
    return armor_GS + [mainhand_GS, offhand_GS, ranged_GS]

