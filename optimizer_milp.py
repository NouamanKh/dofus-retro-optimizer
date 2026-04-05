"""
Dofus Retro Element Optimizer - MILP Version
Requires: pip install pulp
"""

import json
import re
import pulp

def load_retro_data():
    with open('data/items_retro.js', 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'\[.*\]', content, re.DOTALL)
        return json.loads(match.group())

def load_sets_data():
    with open('data/sets_retro.js', 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'\[.*\]', content, re.DOTALL)
        return json.loads(match.group())

def convert_sets_to_bonuses(sets):
    bonuses = {}
    for s in sets:
        bonuses[s['name']] = {}
        for idx, bonus_arr in enumerate(s['bonus']):
            if idx == 0:
                continue
            tier = idx + 1
            bonus_dict = {}
            for b in bonus_arr:
                stat = normalize_stat(b.get('type', ''))
                if stat:
                    bonus_dict[stat] = int(b.get('value', 0))
            if bonus_dict:
                bonuses[s['name']][tier] = bonus_dict
    return bonuses

def normalize_stat(stat):
    if not stat:
        return None
    try:
        cleaned = stat.encode('latin-1').decode('utf-8')
    except:
        cleaned = stat
    cleaned = cleaned.lower()
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

SLOT_LIMITS = {
    "weapon": 1, "hat": 1, "cloak": 1, "amulet": 1,
    "ring": 2, "belt": 1, "boots": 1
}

def optimize_milp(element, min_level, max_level, min_pa, min_pm, items, sets_data, max_items=10):
    items_dict = {item["id"]: item for item in items}
    
    model = pulp.LpProblem(f"Maximize_{element}", pulp.LpMaximize)
    
    x = {item_id: pulp.LpVariable(f"x_{item_id}", cat="Binary") for item_id in items_dict}
    
    set_items = {}
    for item_id, item in items_dict.items():
        if item.get("set"):
            if item["set"] not in set_items:
                set_items[item["set"]] = []
            set_items[item["set"]].append(item_id)
    
    SET_BONUSES = convert_sets_to_bonuses(sets_data)
    
    y = {}
    for set_name, set_item_ids in set_items.items():
        if set_name in SET_BONUSES:
            y[set_name] = {}
            for num_pieces, bonuses in SET_BONUSES[set_name].items():
                if bonuses.get(element, 0) > 0:
                    y[set_name][num_pieces] = pulp.LpVariable(
                        f"y_{set_name}_{num_pieces}", cat="Binary"
                    )
    
    objective_terms = []
    
    for item_id, item in items_dict.items():
        value = item["elements"].get(element, 0)
        if value > 0:
            objective_terms.append(x[item_id] * value)
    
    for set_name, pieces_vars in y.items():
        for num_pieces, var in pieces_vars.items():
            bonus = SET_BONUSES[set_name][num_pieces].get(element, 0)
            if bonus > 0:
                objective_terms.append(var * bonus)
    
    model += pulp.lpSum(objective_terms)
    
    model += pulp.lpSum(x.values()) <= max_items, "max_items_constraint"
    
    for slot, limit in SLOT_LIMITS.items():
        slot_items = [item_id for item_id, item in items_dict.items() if item["type"] == slot]
        if slot_items:
            model += pulp.lpSum(x[item_id] for item_id in slot_items) <= limit, f"max_{limit}_{slot}"
    
    for item_id, item in items_dict.items():
        if item["level"] < min_level or item["level"] > max_level:
            model += x[item_id] == 0, f"level_filter_{item_id}"
    
    pa_var = pulp.LpVariable("total_pa", lowBound=0)
    pm_var = pulp.LpVariable("total_pm", lowBound=0)
    
    model += pa_var == pulp.lpSum((item.get("pa", 0) or 0) * x[item_id] for item_id, item in items_dict.items())
    model += pm_var == pulp.lpSum((item.get("pm", 0) or 0) * x[item_id] for item_id, item in items_dict.items())
    
    model += pa_var >= min_pa, "min_pa_constraint"
    model += pm_var >= min_pm, "min_pm_constraint"
    
    for set_name, set_item_ids in set_items.items():
        if set_name not in y:
            continue
            
        set_items_selected = pulp.lpSum(x[item_id] for item_id in set_item_ids if item_id in x)
        
        if len(y[set_name]) > 0:
            model += pulp.lpSum(y[set_name].values()) <= 1, f"only_one_bonus_{set_name}"
            
            for num_pieces, var in y[set_name].items():
                model += var * num_pieces <= set_items_selected, f"require_{num_pieces}_{set_name}"
    
    model.solve()
    
    print(f"Status: {pulp.LpStatus[model.status]}")
    print(f"Total {element}: {pulp.value(model.objective)}")
    print(f"Total PA: {pulp.value(pa_var)}, Total PM: {pulp.value(pm_var)}")
    
    selected = []
    for item_id, var in x.items():
        if var.value() == 1:
            selected.append(items_dict[item_id])
            print(f"  - {items_dict[item_id]['name']} (+{items_dict[item_id]['elements'].get(element, 0)}) [Lvl {items_dict[item_id]['level']}]")
    
    print("\nActive Set Bonuses:")
    for set_name, pieces_vars in y.items():
        for num_pieces, var in pieces_vars.items():
            if var.value() == 1:
                bonus = SET_BONUSES[set_name][num_pieces].get(element, 0)
                print(f"  - {set_name}: {num_pieces} pièces (+{bonus})")
    
    return selected

if __name__ == "__main__":
    print("Loading data...")
    items = load_retro_data()
    sets = load_sets_data()
    print(f"Loaded {len(items)} items, {len(sets)} sets")
    
    element = "vitalite"
    min_level = 1
    max_level = 60
    min_pa = 2
    min_pm = 0
    
    print(f"\n=== Optimisation {element.upper()} (Niv {min_level}-{max_level}, PA>={min_pa}, PM>={min_pm}) ===\n")
    selected = optimize_milp(element, min_level, max_level, min_pa, min_pm, items, sets)
