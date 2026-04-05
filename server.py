"""
Flask server to expose MILP optimizer as API
Requires: pip install flask pulp
Run: python server.py
"""

from flask import Flask, request, jsonify
import pulp
import json
import re

app = Flask(__name__)

ITEMS = None
SETS = None
SET_BONUSES = None

def load_data():
    global ITEMS, SETS, SET_BONUSES
    
    with open('data/items_retro.js', 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'\[.*\]', content, re.DOTALL)
        ITEMS = json.loads(match.group())
    
    with open('data/sets_retro.js', 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'\[.*\]', content, re.DOTALL)
        SETS = json.loads(match.group())
    
    SET_BONUSES = {}
    for s in SETS:
        SET_BONUSES[s['name']] = {}
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
                SET_BONUSES[s['name']][tier] = bonus_dict
    
    print(f"Loaded {len(ITEMS)} items, {len(SETS)} sets")

def normalize_stat(stat):
    if not stat:
        return None
    try:
        cleaned = stat.encode('latin-1').decode('utf-8')
    except:
        cleaned = stat
    cleaned = cleaned.lower()
    if 'vitalit' in cleaned: return 'vitalite'
    if 'sagesse' in cleaned: return 'sagesse'
    if 'force' in cleaned: return 'force'
    if 'intelligence' in cleaned: return 'intelligence'
    if 'chance' in cleaned: return 'chance'
    if 'agilit' in cleaned: return 'agilite'
    return None

SLOT_LIMITS = {
    "weapon": 1, "hat": 1, "cloak": 1, "amulet": 1,
    "ring": 2, "belt": 1, "boots": 1
}

@app.route('/api/optimize', methods=['POST'])
def optimize():
    data = request.json
    
    element = data.get('element', 'vitalite')
    min_level = int(data.get('minLevel', 1))
    max_level = int(data.get('maxLevel', 200))
    min_pa = int(data.get('minPA', 0))
    min_pm = int(data.get('minPM', 0))
    max_results = int(data.get('maxResults', 1))
    
    result = optimize_milp(element, min_level, max_level, min_pa, min_pm, max_results)
    
    return jsonify(result)

def optimize_milp(element, min_level, max_level, min_pa, min_pm, max_results=1):
    items_dict = {item["id"]: item for item in ITEMS}
    
    model = pulp.LpProblem(f"Maximize_{element}", pulp.LpMaximize)
    
    x = {item_id: pulp.LpVariable(f"x_{item_id}", cat="Binary") for item_id in items_dict}
    
    set_items = {}
    for item_id, item in items_dict.items():
        if item.get("set"):
            if item["set"] not in set_items:
                set_items[item["set"]] = []
            set_items[item["set"]].append(item_id)
    
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
    
    selected = []
    for item_id, var in x.items():
        if var.value() == 1:
            selected.append(items_dict[item_id])
    
    base_element = sum(item["elements"].get(element, 0) for item in selected)
    
    active_sets = {}
    for set_name, pieces_vars in y.items():
        for num_pieces, var in pieces_vars.items():
            if var.value() == 1:
                bonus = SET_BONUSES[set_name][num_pieces].get(element, 0)
                active_sets[set_name] = {"pieces": num_pieces, "bonus": bonus}
    
    set_bonus_total = sum(s["bonus"] for s in active_sets.values())
    
    return {
        "status": pulp.LpStatus[model.status],
        "totalElement": base_element + set_bonus_total,
        "baseElement": base_element,
        "setBonus": set_bonus_total,
        "items": selected,
        "activeSets": active_sets,
        "totalPA": int(pa_var.value()),
        "totalPM": int(pm_var.value())
    }

if __name__ == '__main__':
    load_data()
    print("Starting server on http://localhost:5000")
    app.run(debug=True, port=5000)
