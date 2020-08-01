import json

####################################################################################################
ilvls = '284  277  272  271  270  268  264  259  258  251  245  239  232  226  219  213  200'.split()

#Chest Head Legs MainHand Off-hand
highs = (551, 531, ' ', 514, 511, ' ', 494, ' ', 477, 457, 439, 422, 402, 385, 365, 348, 310)

#Feet Hands Shoulders Waist
mids  = (413, 398, ' ', 385, 383, ' ', 370, ' ', 357, 342, 329, 316, 301, 289, 274, 261, 233)

#Back Finger Neck Trink Wrist
lows  = (310, 298, 290, 289, ' ', 284, 278, 269, 268, 257, 247, 237, 226, 216, 205, 195, 174)

#Ranged Relic Thrown
wep3s = (174, 168, ' ', 162, 161, ' ', 156, ' ', 150, 144, 139, 133, 127, 121, 115, 110, 98)

#Two Hands
twoHs =(1103,1062, ' ',1028, ' ', ' ', 988, ' ', 954, 914, 879, 845, 805, 770, 730, 696, 621)

GS = {ilvl:gs for ilvl, *gs in zip(ilvls, highs, mids, lows, wep3s, twoHs)}
####################################################################################################

legendary = {'49623':1433, '46017':571}

with open('data.json', 'r') as f:
    GS_data = json.loads(f.read())

def main(gear):
    def item_gs(slotIndex, categoryIndex, categoryName):
        equippedItemID = gear[slotIndex-1]
        for ilvl, itemIDs in GS_data[categoryName].items():
            if equippedItemID in itemIDs:
                return GS[ilvl][categoryIndex]
        return 0 #Not Found
    
    slotIndexes = {
        'HighIDs': (1, 5, 11, 17, 18),
        'MidIDs' : (3, 9, 10, 12),
        'LowIDs' : (2, 4, 8, 13, 14, 15, 16),
        'Wep2IDs': (19, )}
    
    mainhandGS = legendary.get(gear[16])
    if not mainhandGS:
        mainhandGS = item_gs(17, 4, '2HandIDs')
    
    if mainhandGS:
        if gear[-2]:
            offhandGS = item_gs(18, 4, '2HandIDs')
            mainhandGS = (mainhandGS + offhandGS) // 2
        slotIndexes['HighIDs'] = (1, 5, 11)
        yield mainhandGS
        
    for categoryIndex, (categoryName, categorySlotIndexes) in enumerate(slotIndexes.items()):
        for slotIndex in categorySlotIndexes:
            yield item_gs(slotIndex, categoryIndex, categoryName)
