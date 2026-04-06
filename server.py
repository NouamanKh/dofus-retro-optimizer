"""
Flask server - PuLP MILP optimizer for Dofus Retro equipment
Requires: pip install flask pulp flask-cors
Run: python server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pulp
import json
import re
import os

app = Flask(__name__)
CORS(app)

ITEMS = None
SETS = None
SET_BONUSES = None

SLOT_LIMITS = {
    "weapon": 1, "hat": 1, "cloak": 1, "amulet": 1,
    "ring": 2, "belt": 1, "boots": 1, "shield": 1
}

ALL_ELEMENTS = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite']


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
            if not bonus_arr:
                continue
            tier = idx + 2  # bonus[0]=empty, bonus[1]=2 items, etc.
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
    except Exception:
        cleaned = stat
    cleaned = cleaned.lower()
    if 'vitalit'     in cleaned: return 'vitalite'
    if 'sagesse'     in cleaned: return 'sagesse'
    if 'force'       in cleaned: return 'force'
    if 'intelligence'in cleaned: return 'intelligence'
    if 'chance'      in cleaned: return 'chance'
    if 'agilit'      in cleaned: return 'agilite'
    return None


def build_result(selected_items, element, set_bonuses_map):
    """Build a result dict from a list of selected item dicts."""
    base_stats = {el: 0 for el in ALL_ELEMENTS}
    for item in selected_items:
        for el in ALL_ELEMENTS:
            base_stats[el] += item['elements'].get(el, 0)

    # Compute set bonuses for all elements
    set_counts = {}
    for item in selected_items:
        if item.get('set'):
            set_counts[item['set']] = set_counts.get(item['set'], 0) + 1

    set_bonus_stats = {el: 0 for el in ALL_ELEMENTS}
    set_details = []
    for set_name, count in set_counts.items():
        if count < 2 or set_name not in set_bonuses_map:
            continue
        tiers = sorted(set_bonuses_map[set_name].keys(), reverse=True)
        for tier in tiers:
            if tier <= count:
                bonus = set_bonuses_map[set_name][tier]
                for el in ALL_ELEMENTS:
                    set_bonus_stats[el] += bonus.get(el, 0)
                set_details.append({
                    'setName': set_name,
                    'pieces': count,
                    'tier': tier,
                    'bonus': bonus
                })
                break

    total_stats = {el: base_stats[el] + set_bonus_stats[el] for el in ALL_ELEMENTS}
    total_pa = sum(item.get('pa', 0) or 0 for item in selected_items)
    total_pm = sum(item.get('pm', 0) or 0 for item in selected_items)

    return {
        'items': selected_items,
        'totalElement': total_stats[element],
        'baseElement': base_stats[element],
        'setBonus': set_bonus_stats[element],
        'setDetails': set_details,
        'baseStats': base_stats,
        'setBonuses': set_bonus_stats,
        'totalStats': total_stats,
        'totalPA': total_pa,
        'totalPM': total_pm,
        'avgLevel': round(sum(i['level'] for i in selected_items) / len(selected_items)) if selected_items else 0
    }


def solve_milp(element, min_level, max_level, min_pa, min_pm, max_pa, max_pm):
    """Solve the MILP and return the optimal list of selected item dicts, or None if infeasible."""

    # Filter items by level upfront
    valid_items = {
        item['id']: item for item in ITEMS
        if item['type'] in SLOT_LIMITS
        and min_level <= item['level'] <= max_level
    }
    if not valid_items:
        return None

    model = pulp.LpProblem(f"Maximize_{element}", pulp.LpMaximize)

    # Binary variable per item
    x = {iid: pulp.LpVariable(f"x_{iid}", cat="Binary") for iid in valid_items}

    # --- Set bonus variables ---
    # Group items by set
    set_item_ids = {}
    for iid, item in valid_items.items():
        if item.get('set'):
            set_item_ids.setdefault(item['set'], []).append(iid)

    # y[set_name][tier] = 1 if that tier bonus is active
    y = {}
    for set_name, iids in set_item_ids.items():
        if set_name not in SET_BONUSES:
            continue
        y[set_name] = {}
        for tier, bonuses in SET_BONUSES[set_name].items():
            if bonuses.get(element, 0) > 0:
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', set_name)
                y[set_name][tier] = pulp.LpVariable(f"y_{safe_name}_{tier}", cat="Binary")

    # --- Objective ---
    obj_terms = []
    for iid, item in valid_items.items():
        val = item['elements'].get(element, 0)
        if val != 0:
            obj_terms.append(x[iid] * val)
    for set_name, tier_vars in y.items():
        for tier, var in tier_vars.items():
            bonus = SET_BONUSES[set_name][tier].get(element, 0)
            if bonus > 0:
                obj_terms.append(var * bonus)
    model += pulp.lpSum(obj_terms)

    # --- Slot constraints ---
    for slot, limit in SLOT_LIMITS.items():
        slot_ids = [iid for iid, item in valid_items.items() if item['type'] == slot]
        if slot_ids:
            model += pulp.lpSum(x[iid] for iid in slot_ids) <= limit, f"slot_{slot}"

    # --- PA/PM constraints ---
    pa_expr = pulp.lpSum((item.get('pa', 0) or 0) * x[iid] for iid, item in valid_items.items())
    pm_expr = pulp.lpSum((item.get('pm', 0) or 0) * x[iid] for iid, item in valid_items.items())
    model += pa_expr >= min_pa, "min_pa"
    model += pa_expr <= max_pa, "max_pa"
    model += pm_expr >= min_pm, "min_pm"
    model += pm_expr <= max_pm, "max_pm"

    # --- Set bonus activation constraints ---
    for set_name, tier_vars in y.items():
        iids = set_item_ids.get(set_name, [])
        set_selected = pulp.lpSum(x[iid] for iid in iids if iid in x)

        # At most one tier active at a time
        if tier_vars:
            model += pulp.lpSum(tier_vars.values()) <= 1, f"one_tier_{re.sub(r'[^a-zA-Z0-9_]', '_', set_name)}"

        for tier, var in tier_vars.items():
            # Tier can only be active if enough set pieces are selected
            model += var * tier <= set_selected, f"tier_req_{re.sub(r'[^a-zA-Z0-9_]', '_', set_name)}_{tier}"

    # Solver output — set msg=0 to suppress
    model.solve(pulp.PULP_CBC_CMD(msg=1))

    status = pulp.LpStatus[model.status]
    print(f"\n[MILP] Status: {status} | Element: {element} | Level: ≤{max_level} | PA: {min_pa}-{max_pa} | PM: {min_pm}-{max_pm}")

    if status != 'Optimal':
        return None

    selected = [valid_items[iid] for iid, var in x.items() if var.value() and var.value() > 0.5]
    total_el = sum(i['elements'].get(element, 0) for i in selected)
    print(f"[MILP] {len(selected)} items | {element}: {total_el} | {[i['name'] for i in selected]}")
    return selected


@app.route('/api/optimize', methods=['POST'])
def optimize():
    data = request.json

    element   = data.get('element', 'vitalite')
    max_level = int(data.get('maxLevel', 200))
    min_pa    = int(data.get('minPA', 0))
    min_pm    = int(data.get('minPM', 0))
    max_pa    = int(data.get('maxPA', 99))
    max_pm    = int(data.get('maxPM', 99))

    selected = solve_milp(element, 1, max_level, min_pa, min_pm, max_pa, max_pm)

    if not selected:
        return jsonify([])

    result = build_result(selected, element, SET_BONUSES)
    return jsonify([result])


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'items': len(ITEMS), 'sets': len(SETS)})


if __name__ == '__main__':
    load_data()
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Called by gunicorn
    load_data()
