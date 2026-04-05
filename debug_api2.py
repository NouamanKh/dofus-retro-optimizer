"""
Debug script to find items with main stats from possibleEffects
"""
import urllib.request
import json

# Dofus effect IDs for main stats
EFFECT_IDS = {
    100: 'vitalite',  # Vitality
    118: 'force',      # Strength  
    119: 'agilite',    # Agility
    123: 'intelligence', # Intelligence
    124: 'chance',    # Chance
    125: 'sagesse',    # Wisdom
}

def fetch(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

print("=== Looking for equipment with main stats ===")
count = 0

# Equipment type IDs
EQUIP_TYPES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 19, 20, 21, 22]

for skip in range(0, 10000, 100):
    url = f"https://api.dofusdb.fr/items?$limit=100&$skip={skip}"
    data = fetch(url)
    
    if not data.get('data'):
        break
    
    for item in data['data']:
        # Check if equipment
        type_id = item.get('typeId')
        if type_id not in EQUIP_TYPES:
            continue
            
        # Check possibleEffects for main stat bonuses
        possible = item.get('possibleEffects', [])
        stats = {}
        
        for effect in possible:
            effect_id = effect.get('baseEffectId')
            value = effect.get('value', 0)
            
            if effect_id in EFFECT_IDS and value > 0:
                stats[EFFECT_IDS[effect_id]] = value
        
        if stats and len(stats) >= 1:
            name = item['name'].get('en', 'Unknown')
            level = item.get('level', 0)
            print(f"{name} (Lv{level}): {stats}")
            count += 1
            if count >= 40:
                break
    
    print(f"Checked {skip + 100} items...")
    
    if count >= 40:
        break

print(f"\n=== Found {count} equipment items with stats ===")
