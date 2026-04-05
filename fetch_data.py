"""
Script to fetch Dofus items and sets from DofusDB API.
"""

import urllib.request
import json

CHAR_PERCENTAGE = {
    10: "vitalite",
    11: "agilite", 
    12: "chance",
    13: "intelligence",
    14: "force",
    15: "sagesse",
}

CHAR_RAW = {
    0: "vitalite",
    1: "agilite", 
    2: "chance",
    3: "intelligence",
    4: "force",
    5: "sagesse",
}

TYPE_MAPPING = {
    1: "amulet",
    2: "weapon", 3: "weapon", 4: "weapon", 5: "weapon", 
    6: "weapon", 7: "weapon", 8: "weapon", 19: "weapon", 
    20: "weapon", 21: "weapon", 22: "weapon",
    9: "ring",
    10: "belt",
    11: "boots",
    16: "hat",
    17: "cloak",
}

def fetch_json(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def get_items():
    all_items = []
    skip = 0
    limit = 500
    
    while True:
        url = f"https://api.dofusdb.fr/items?$limit={limit}&$skip={skip}"
        data = fetch_json(url)
        
        if not data.get('data'):
            break
            
        all_items.extend(data['data'])
        skip += limit
        print(f"  Fetched {len(all_items)} items...")
        
        if skip >= min(data.get('total', 0), 25000):
            break
            
    return all_items

def get_sets():
    url = "https://api.dofusdb.fr/item-sets?$limit=500"
    data = fetch_json(url)
    return data.get('data', [])

def extract_stat_value(effect):
    """Extract stat value from an effect, handling both percentage and raw stats."""
    char_id = effect.get('characteristic')
    value = effect.get('from', 0)
    
    if value == 0:
        return None, 0
    
    # Raw stats (0-5)
    if char_id in CHAR_RAW:
        return CHAR_RAW[char_id], value
    
    # Percentage stats (10-15)
    if char_id in CHAR_PERCENTAGE:
        char_name = CHAR_PERCENTAGE[char_id]
        # Convert percentage to raw value (percentage is based on ~100 base)
        return char_name, int(value * 1.0)
    
    return None, 0

def convert_item(item, type_mapping):
    name = item.get('name', {}).get('en', 'Unknown')
    if name == 'Unknown':
        name = item.get('name', {}).get('fr', 'Unknown')
    
    type_id = item.get('typeId')
    item_type = type_mapping.get(type_id, None)
    if not item_type:
        return None
    
    level = item.get('level', 1)
    
    elements = {
        "vitalite": 0,
        "sagesse": 0,
        "force": 0,
        "intelligence": 0,
        "chance": 0,
        "agilite": 0
    }
    
    effects = item.get('effects', [])
    for effect in effects:
        char_name, value = extract_stat_value(effect)
        if char_name and value > 0:
            if char_name == 'vitalite' and value > 2000:
                continue
            elements[char_name] += value
    
    if sum(elements.values()) == 0:
        return None
    
    set_id = item.get('itemSetId')
    set_name = None
    if set_id and set_id > 0:
        set_obj = item.get('itemSet')
        if set_obj:
            set_name = set_obj.get('name', {}).get('en') or set_obj.get('name', {}).get('fr')
    
    item_id = f"dofus_{item.get('id', 0)}"
    
    return {
        "id": item_id,
        "name": name,
        "type": item_type,
        "level": level,
        "elements": elements,
        "set": set_name,
        "apiId": item.get('id'),
    }

def convert_set(set_data, items_dict):
    set_id = set_data.get('id')
    name = set_data.get('name', {}).get('en') or set_data.get('name', {}).get('fr', 'Unknown')
    
    bonuses = {}
    set_items = set_data.get('items', [])
    
    # Effects array is indexed by number of items (0-indexed)
    effects_array = set_data.get('effects', [])
    
    for tier_index, tier_effects in enumerate(effects_array):
        if not tier_effects:
            continue
        
        num_pieces = tier_index + 1  # 0-indexed array means tier 0 = 1 piece
        
        tier_bonus = {}
        for effect in tier_effects:
            char_name, value = extract_stat_value(effect)
            if char_name and value > 0:
                tier_bonus[char_name] = tier_bonus.get(char_name, 0) + value
        
        if tier_bonus:
            bonuses[num_pieces] = tier_bonus
    
    item_ids = [f"dofus_{item.get('id')}" for item in set_items if item.get('id')]
    
    return {
        "id": f"set_{set_id}",
        "name": name,
        "items": item_ids,
        "bonuses": bonuses
    }

def main():
    print("=== Fetching DofusDB Data ===\n")
    
    print("Fetching items...")
    raw_items = get_items()
    print(f"Total items fetched: {len(raw_items)}\n")
    
    print("Fetching sets...")
    raw_sets = get_sets()
    print(f"Total sets fetched: {len(raw_sets)}\n")
    
    print("Converting items...")
    items = []
    for item in raw_items:
        converted = convert_item(item, TYPE_MAPPING)
        if converted:
            items.append(converted)
    print(f"Equipment items with stats: {len(items)}\n")
    
    print("Converting sets...")
    items_dict = {item['apiId']: item for item in items}
    sets = []
    for set_data in raw_sets:
        converted = convert_set(set_data, items_dict)
        if converted['bonuses']:
            sets.append(converted)
    print(f"Sets with bonuses: {len(sets)}\n")
    
    print("Saving data...")
    
    with open('data/items_api.js', 'w', encoding='utf-8') as f:
        f.write(f"// Auto-generated from DofusDB API\n")
        f.write(f"// Generated: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write(f"// Total items: {len(items)}\n\n")
        f.write(f"const ITEMS = {json.dumps(items, ensure_ascii=False, indent=2)};\n")
    
    with open('data/sets_api.js', 'w', encoding='utf-8') as f:
        f.write(f"// Auto-generated from DofusDB API\n")
        f.write(f"// Generated: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write(f"// Total sets: {len(sets)}\n\n")
        f.write(f"const SET_BONUSES_API = {json.dumps(sets, ensure_ascii=False, indent=2)};\n")
    
    print("\n=== Sample Items (highest agility) ===")
    sorted_items = sorted(items, key=lambda x: x['elements'].get('agilite', 0), reverse=True)[:10]
    for item in sorted_items:
        stats = {k: v for k, v in item['elements'].items() if v > 0}
        print(f"  [{item['type']}] {item['name']} (Lv{item['level']}): {stats}")
    
    print("\n=== Sample Sets ===")
    for set_item in sets[:10]:
        print(f"  {set_item['name']}: {set_item['bonuses']}")
    
    print("\n=== Done! ===")
    print("Files saved: data/items_api.js, data/sets_api.js")

if __name__ == "__main__":
    main()
