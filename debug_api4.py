"""
Debug script - find what characteristic IDs exist
"""
import urllib.request
import json
from collections import Counter

def fetch(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

# Equipment type IDs
EQUIP_TYPES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 19, 20, 21, 22]

print("=== Collecting characteristic IDs from equipment effects ===")
char_counter = Counter()

for skip in range(0, 5000, 100):
    url = f"https://api.dofusdb.fr/items?$limit=100&$skip={skip}"
    data = fetch(url)
    
    if not data.get('data'):
        break
    
    for item in data['data']:
        type_id = item.get('typeId')
        if type_id not in EQUIP_TYPES:
            continue
            
        effects = item.get('effects', [])
        for effect in effects:
            char_id = effect.get('characteristic')
            if char_id is not None:
                char_counter[char_id] += 1
    
    if skip % 500 == 0:
        print(f"Checked {skip}...")

print("\n=== Top 30 characteristic IDs ===")
for char_id, count in char_counter.most_common(30):
    print(f"  {char_id}: {count} occurrences")

# Now let's find actual items with stat-like characteristic IDs
print("\n=== Items with characteristics 0-10 ===")
CHARACTERISTICS = {
    0: 'vitalite',
    1: 'agilite', 
    2: 'chance',
    3: 'intelligence',
    4: 'force',
    5: 'sagesse',
    10: 'vita_per',  # vitality percent?
    11: 'agilite_per',
    12: 'chance_per',
    13: 'intelligence_per',
    14: 'force_per',
    15: 'sagesse_per',
}

for skip in range(0, 5000, 100):
    url = f"https://api.dofusdb.fr/items?$limit=100&$skip={skip}"
    data = fetch(url)
    
    if not data.get('data'):
        break
    
    for item in data['data']:
        type_id = item.get('typeId')
        if type_id not in EQUIP_TYPES:
            continue
            
        effects = item.get('effects', [])
        stats = {}
        
        for effect in effects:
            char_id = effect.get('characteristic')
            value = effect.get('from', 0)
            if char_id in CHARACTERISTICS and value > 0:
                stats[CHARACTERISTICS[char_id]] = value
        
        if stats:
            name = item['name'].get('en', 'Unknown')
            level = item.get('level', 0)
            print(f"{name} (Lv{level}): {stats}")
