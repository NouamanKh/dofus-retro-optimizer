import json
import re

with open('dofus-retro-items.json', 'r', encoding='utf-8') as f:
    raw_items = json.load(f)

with open('dofus-retro-sets.json', 'r', encoding='utf-8') as f:
    raw_sets = json.load(f)

category_to_type = {
    'Les boucliers': 'shield',
    'Les Epées': 'weapon', 'Les épées': 'weapon',
    'Les dagues': 'weapon', 'Les Arc': 'weapon',
    'Les bâtons': 'weapon', 'Les marteaux': 'weapon', 'Les Marteaux': 'weapon',
    'Les pelles': 'weapon', 'Les Pelles': 'weapon',
    'Les haches': 'weapon', 'Les Haches': 'weapon',
    'Les anneaux': 'ring', 'Les amulettes': 'amulet',
    'Les ceintures': 'belt', 'Les bottes': 'boots',
    'Les chapeaux': 'hat', 'Les capes': 'cloak'
}

def clean(s):
    """Decode latin-1 mojibake if needed, lowercase, strip."""
    if not s:
        return ''
    try:
        s = s.encode('latin-1').decode('utf-8')
    except Exception:
        pass
    return s.lower().strip()

def get_value(bonus):
    """Return the max value from a bonus entry."""
    v = bonus.get('values', 0)
    if isinstance(v, list):
        return max(v) if v else 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0

def classify(raw_type):
    """
    Map a raw bonus type string to a (stat_key, label) tuple.
    Returns None if the stat should be ignored (spell-specific bonuses etc.)
    """
    t = clean(raw_type)

    # Skip spell-specific bonuses — too verbose, not useful for gear comparison
    if any(kw in t for kw in ['sort ', 'lancer ', 'portee du sort', 'delai', 'cout en pa du sort',
                               'desactive', 'rend la portee', 'est une arme']):
        return None

    # ── Elemental stats ──
    if 'vitalit' in t:   return ('vitalite',      'Vitalité')
    if 'sagesse' in t:   return ('sagesse',        'Sagesse')
    if 'force' in t:     return ('force',          'Force')
    if 'intelligence' in t: return ('intelligence','Intelligence')
    if 'chance' in t:    return ('chance',         'Chance')
    if 'agilit' in t:    return ('agilite',        'Agilité')

    # ── PA / PM ──
    if t == 'pa':        return ('pa',  'PA')
    if t == 'pm':        return ('pm',  'PM')

    # ── Damages ──
    if '% de dommage au pi' in t: return ('pct_dmg_trap',  '% Dommages Pièges')
    if '% de dommage'      in t:  return ('pct_dmg',       '% Dommages')
    if 'dommage au pi'     in t:  return ('dmg_trap',      'Dommages Pièges')
    if 'dommages air'      in t:  return ('dmg_air',       'Dommages Air')
    if 'dommages eau'      in t:  return ('dmg_water',     'Dommages Eau')
    if 'dommages feu'      in t:  return ('dmg_fire',      'Dommages Feu')
    if 'dommages neutre'   in t:  return ('dmg_neutral',   'Dommages Neutre')
    if 'dommages terre'    in t:  return ('dmg_earth',     'Dommages Terre')
    if 'dommage'           in t:  return ('dmg',           'Dommages')

    # ── Resistances (% then flat) ──
    if '% de resistance neutre' in t or '% r' in t and 'neutre' in t:
        return ('pct_res_neutral', '% Rés. Neutre')
    if '% de resistance terre'  in t or '% r' in t and 'terre' in t:
        return ('pct_res_earth',   '% Rés. Terre')
    if '% de resistance feu'    in t or '% r' in t and 'feu' in t:
        return ('pct_res_fire',    '% Rés. Feu')
    if '% de resistance eau'    in t or '% r' in t and 'eau' in t:
        return ('pct_res_water',   '% Rés. Eau')
    if '% de resistance air'    in t or '% r' in t and 'air' in t:
        return ('pct_res_air',     '% Rés. Air')
    if '% faiblesse neutre'     in t: return ('pct_weak_neutral', '% Faiblesse Neutre')
    if '% faiblesse terre'      in t: return ('pct_weak_earth',   '% Faiblesse Terre')
    if '% faiblesse feu'        in t: return ('pct_weak_fire',    '% Faiblesse Feu')
    if '% faiblesse eau'        in t: return ('pct_weak_water',   '% Faiblesse Eau')
    if '% faiblesse air'        in t: return ('pct_weak_air',     '% Faiblesse Air')

    if 'resistance neutre' in t or 'r' in t and 'sistance neutre' in t:
        return ('res_neutral', 'Rés. Neutre')
    if 'resistance terre'  in t or 'r' in t and 'sistance terre' in t:
        return ('res_earth',   'Rés. Terre')
    if 'resistance feu'    in t or 'r' in t and 'sistance feu' in t:
        return ('res_fire',    'Rés. Feu')
    if 'resistance eau'    in t or 'r' in t and 'sistance eau' in t:
        return ('res_water',   'Rés. Eau')
    if 'resistance air'    in t or 'r' in t and 'sistance air' in t:
        return ('res_air',     'Rés. Air')

    # ── Steal ──
    if 'vole neutre' in t: return ('steal_neutral', 'Vol Neutre')
    if 'vole terre'  in t: return ('steal_earth',   'Vol Terre')
    if 'vole feu'    in t: return ('steal_fire',    'Vol Feu')
    if 'vole eau'    in t: return ('steal_water',   'Vol Eau')
    if 'vole air'    in t: return ('steal_air',     'Vol Air')
    if 'vole'        in t: return ('steal',         'Vol')

    # ── Other combat stats ──
    if 'coup critique'  in t or 'cc' == t: return ('crit',        'Coups Critiques')
    if 'echec critique' in t:              return ('fail_crit',   'Échec Critique')
    if 'renvoi'         in t:              return ('dmg_return',  'Renvoi Dommages')
    if 'pa perdu'       in t:              return ('pa_drain',    'PA Retirés')
    if 'pm perdu'       in t:              return ('pm_drain',    'PM Retirés')
    if 'soins'          in t:              return ('heals',       'Soins')
    if 'pv rendus'      in t:              return ('heals',       'Soins')
    if 'portee'         in t or 'port\u00e9e' in t: return ('range', 'Portée')
    if 'initiative'     in t:              return ('initiative',  'Initiative')
    if 'prospection'    in t:              return ('prospection', 'Prospection')
    if 'pods'           in t:              return ('pods',        'Pods')
    if 'creature'       in t or 'cr\u00e9ature' in t: return ('summons', 'Invocations')

    return None  # ignore everything else

def parse_all_stats(bonuses):
    """Parse all bonus entries into a flat stats dict."""
    stats = {}
    if not bonuses or not isinstance(bonuses, list):
        return stats
    for bonus in bonuses:
        if not bonus or 'type' not in bonus:
            continue
        result = classify(bonus['type'])
        if result is None:
            continue
        key, _ = result
        val = get_value(bonus)
        if val == 0:
            continue
        stats[key] = stats.get(key, 0) + val
    return stats

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
    item_type = category_to_type.get(category)
    if item_type is None:
        continue

    for item in item_list:
        bonuses = item.get('bonus', [])
        all_stats = parse_all_stats(bonuses)

        elements = {
            'vitalite':     all_stats.pop('vitalite', 0),
            'sagesse':      all_stats.pop('sagesse', 0),
            'force':        all_stats.pop('force', 0),
            'intelligence': all_stats.pop('intelligence', 0),
            'chance':       all_stats.pop('chance', 0),
            'agilite':      all_stats.pop('agilite', 0),
        }
        pa = all_stats.pop('pa', 0)
        pm = all_stats.pop('pm', 0)

        set_name = set_lookup.get(item.get('name', '').lower())

        items.append({
            'id':           f'retro_{item_id}',
            'name':         item.get('name', ''),
            'type':         item_type,
            'level':        item.get('level', 1),
            'elements':     elements,
            'pa':           pa,
            'pm':           pm,
            'stats':        all_stats,   # all remaining stats (dmg, res, etc.)
            'set':          set_name,
            'recipe':       item.get('recipe', []),
            'requirements': item.get('requirements', []),
            'weapon_stats': item.get('weapon_stats'),
        })
        item_id += 1

# Build stat label map for the frontend
STAT_LABELS = {}
for category_obj in raw_items:
    for item_list in category_obj.values():
        for item in item_list:
            for bonus in item.get('bonus', []):
                result = classify(bonus.get('type', ''))
                if result:
                    key, label = result
                    STAT_LABELS[key] = label

with open('data/items_retro.js', 'w', encoding='utf-8') as f:
    f.write(f"const ITEMS_RETRO = {json.dumps(items, indent=2, ensure_ascii=False)};\n")
    f.write(f"const STAT_LABELS = {json.dumps(STAT_LABELS, indent=2, ensure_ascii=False)};\n")

with open('data/sets_retro.js', 'w', encoding='utf-8') as f:
    f.write(f"const SETS_RETRO = {json.dumps(raw_sets, indent=2, ensure_ascii=False)};\n")

print(f"Converted {len(items)} items")
print(f"Stat types found: {sorted(STAT_LABELS.keys())}")
