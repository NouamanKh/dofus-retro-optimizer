"""
Debug script - find what baseEffectIds exist
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

print("=== Collecting baseEffectIds from equipment ===")
effect_counter = Counter()

for skip in range(0, 2000, 100):
    url = f"https://api.dofusdb.fr/items?$limit=100&$skip={skip}"
    data = fetch(url)
    
    if not data.get('data'):
        break
    
    for item in data['data']:
        type_id = item.get('typeId')
        if type_id not in EQUIP_TYPES:
            continue
            
        possible = item.get('possibleEffects', [])
        for effect in possible:
            base_id = effect.get('baseEffectId')
            if base_id is not None:
                effect_counter[base_id] += 1
    
    print(f"Checked {skip + 100}...")
    
    if skip >= 1000:
        break

print("\n=== Top 30 baseEffectIds ===")
for effect_id, count in effect_counter.most_common(30):
    print(f"  {effect_id}: {count} occurrences")
