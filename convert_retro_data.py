import json
import re

with open('dofus-retro-items.json', 'r', encoding='utf-8') as f:
    raw_items = json.load(f)

with open('dofus-retro-sets.json', 'r', encoding='utf-8') as f:
    raw_sets = json.load(f)

category_to_type = {
    'Les boucliers': 'shield',
    'Les Epées': 'weapon',
    'Les épées': 'weapon',
    'Les dagues': 'weapon',
    'Les Arc': 'weapon',
    'Les bâtons': 'weapon',
    'Les marteaux': 'weapon',
    'Les Marteaux': 'weapon',
    'Les pelles': 'weapon',
    'Les Pelles': 'weapon',
    'Les haches': 'weapon',
    'Les Haches': 'weapon',
    'Les anneaux': 'ring',
    'Les amulettes': 'amulet',
    'Les ceintures': 'belt',
    'Les bottes': 'boots',
    'Les chapeaux': 'hat',
    'Les capes': 'cloak'
}

def normalize_stat(stat):
    if not stat:
        return None
    try:
        cleaned = stat.encode('latin-1').decode('utf-8')
    except:
        cleaned = stat
    cleaned = cleaned.lower().strip()
    cleaned = ''.join(c if c.isalnum() or c == ' ' else '' for c in cleaned)
    
    if 'vitalit' in cleaned:
        return 'vitalite'
    if 'sagesse' in cleaned:
        return 'sagesse'
    if 'force' in cleaned:
        return 'force'
    if 'intelligence' in cleaned:
        return 'intelligence'
    if 'chance' in cleaned:
        return 'chance'
    if 'agilit' in cleaned:
        return 'agilite'
    return None

def parse_bonus_to_elements(bonuses):
    elements = {
        'vitalite': 0,
        'sagesse': 0,
        'force': 0,
        'intelligence': 0,
        'chance': 0,
        'agilite': 0
    }
    
    if not bonuses or not isinstance(bonuses, list):
        return elements
    
    for bonus in bonuses:
        if not bonus or 'type' not in bonus:
            continue
        
        stat = normalize_stat(bonus['type'])
        if stat and stat in elements:
            values = bonus.get('values', 0)
            if isinstance(values, list):
                elements[stat] = max(values)
            elif isinstance(values, (int, float)):
                elements[stat] += values
            elif isinstance(values, str):
                try:
                    elements[stat] += int(values)
                except ValueError:
                    pass
    
    return elements

def parse_pa_pm(bonuses):
    pa = 0
    pm = 0
    
    if not bonuses or not isinstance(bonuses, list):
        return pa, pm
    
    for bonus in bonuses:
        if not bonus or 'type' not in bonus:
            continue
        
        try:
            cleaned = bonus['type'].encode('latin-1').decode('utf-8')
        except:
            cleaned = bonus['type']
        cleaned = cleaned.lower()
        
        if cleaned == 'pa':
            values = bonus.get('values', 0)
            if isinstance(values, list):
                pa = max(values)
            else:
                pa = int(values) if isinstance(values, (int, float)) else 0
        
        if cleaned == 'pm':
            values = bonus.get('values', 0)
            if isinstance(values, list):
                pm = max(values)
            else:
                pm = int(values) if isinstance(values, (int, float)) else 0
    
    return pa, pm

def build_set_lookup():
    lookup = {}
    for s in raw_sets:
        for item_name in s.get('items', []):
            lookup[item_name.lower()] = s.get('name', '')
    return lookup

set_lookup = build_set_lookup()

items = []
item_id = 1

for category_obj in raw_items:
    category = list(category_obj.keys())[0]
    item_list = category_obj[category]
    item_type = category_to_type.get(category, None)
    
    if item_type is None:
        continue
    
    for item in item_list:
        elements = parse_bonus_to_elements(item.get('bonus', []))
        pa, pm = parse_pa_pm(item.get('bonus', []))
        set_name = set_lookup.get(item.get('name', '').lower(), None)
        
        items.append({
            'id': f'retro_{item_id}',
            'name': item.get('name', ''),
            'type': item_type,
            'level': item.get('level', 1),
            'elements': elements,
            'pa': pa,
            'pm': pm,
            'set': set_name,
            'recipe': item.get('recipe', []),
            'requirements': item.get('requirements', []),
            'weapon_stats': item.get('weapon_stats', None)
        })
        
        item_id += 1

output = {
    'generated': __import__('datetime').datetime.now().isoformat(),
    'source': 'Dofus Retro 1.29 (retro-craft/scrapstuff)',
    'total_items': len(items),
    'items': items
}

with open('data/items_retro.js', 'w', encoding='utf-8') as f:
    f.write(f"const ITEMS_RETRO = {json.dumps(items, indent=2, ensure_ascii=False)};\nmodule.exports = ITEMS_RETRO;")

with open('data/sets_retro.js', 'w', encoding='utf-8') as f:
    f.write(f"const SETS_RETRO = {json.dumps(raw_sets, indent=2, ensure_ascii=False)};\nmodule.exports = SETS_RETRO;")

print(f"Converted {len(items)} items")
print("Saved to data/items_retro.js and data/sets_retro.js")
