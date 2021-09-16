from constants import GS_DATA, SLOT_TYPES, LEGENDARY_GS, ITEM_TYPE, ILVL_GS

def item_gs(itemID, categoryName):
    if categoryName != "":
        for ilvl, itemIDs in GS_DATA[categoryName].items():
            if itemID in itemIDs:
                return ILVL_GS[ilvl][ITEM_TYPE[categoryName]]
    return 0 # not found/empty slot/tabard/shirt

def get_weapon_GS(item_ID):
    weapon_GS = LEGENDARY_GS.get(item_ID)
    if not weapon_GS:
        weapon_GS = item_gs(item_ID, 'HighIDs')
    if not weapon_GS:
        weapon_GS = item_gs(item_ID, '2HandIDs')
    return weapon_GS

def main(gear):
    *armor_IDs, mainhand_item_ID, offhand_item_ID, ranged_item_ID = gear
    armor_GS = [item_gs(itemID, categoryName) for itemID, categoryName in zip(armor_IDs, SLOT_TYPES)]
    mainhand_GS = get_weapon_GS(mainhand_item_ID)
    offhand_GS = get_weapon_GS(offhand_item_ID)
    ranged_GS = item_gs(ranged_item_ID, 'RangedIDs')
    return armor_GS + [mainhand_GS, offhand_GS, ranged_GS]

def total_gs(gear_gs):
    offhandGS = gear_gs[17]
    if offhandGS > 551:
        gear_gs[16] = (gear_gs[16] + offhandGS) // 2
        gear_gs[17] = 0
    return sum(gear_gs)
