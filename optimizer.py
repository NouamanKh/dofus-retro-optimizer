"""PuLP MILP optimizer for Dofus Retro equipment."""

import math
import re

import pulp

from catalog import ALL_ELEMENTS

SLOT_LIMITS = {
    "weapon": 1, "hat": 1, "cloak": 1, "amulet": 1,
    "ring": 2, "belt": 1, "boots": 1, "shield": 1, "pet": 1, "mount": 1
}
BASE_PM = 3
# Weight of the other objective, so it only settles ties: 1000 Sagesse is worth 0.1 damage
TIE_BREAK = 1e-4


def base_pa(level):
    return 7 if level >= 100 else 6


def _score(stats, element, damage_base=0):
    """Target value of a stat dict. Prospection also gets 1 per 10 Chance, as in game.

    With a spell's base damage, it is the gear's share of
    floor(base x (100 + element + % damage) / 100) + flat damage.
    The character's own stat points are a constant here, so they can't change which gear wins.
    """
    if damage_base:
        return damage_base * (stats.get(element, 0) + stats.get('pct_dmg', 0)) / 100 + stats.get('dmg', 0)
    if element == 'prospection':
        return stats.get('prospection', 0) + stats.get('chance', 0) / 10
    return stats.get(element, 0)


def optimize(catalog, element, level, total_pa, total_pm, exo_pa=0, exo_pm=0, excluded_ids=(), damage_range=None):
    """Best Build for `element` reaching at least the player's total PA/PM without the excluded items, or None if none can.

    With damage_range (a spell's min and max damage), maximises its average estimated damage in `element`.
    """
    gear_pa = max(0, total_pa - base_pa(level) - exo_pa)
    gear_pm = max(0, total_pm - BASE_PM - exo_pm)
    damage_base = sum(damage_range) / 2 if damage_range else 0
    selected = _solve(catalog, element, level, gear_pa, gear_pm, excluded_ids, damage_base)
    if not selected:
        return None
    return _build(catalog, selected, element, base_pa(level) + exo_pa, BASE_PM + exo_pm, damage_base, damage_range)


def optimize_tradeoffs(catalog, element, level, total_pa, total_pm, exo_pa=0, exo_pm=0, excluded_ids=(), damage_range=(1, 1), count=5):
    """Up to `count` Builds from the most damage to the most Sagesse, each with the most damage for its Sagesse."""
    gear_pa = max(0, total_pa - base_pa(level) - exo_pa)
    gear_pm = max(0, total_pm - BASE_PM - exo_pm)
    damage_base = sum(damage_range) / 2

    def solve(**goal):
        return _solve(catalog, element, level, gear_pa, gear_pm, excluded_ids, damage_base, **goal)

    def build(selected):
        return _build(catalog, selected, element, base_pa(level) + exo_pa, BASE_PM + exo_pm, damage_base, damage_range)

    most_damage = solve(weights=(1, TIE_BREAK))
    if not most_damage:
        return []
    builds = [build(selected) for selected in (most_damage, solve(weights=(TIE_BREAK, 1))) if selected]
    low, high = builds[0]['totalStats']['sagesse'], builds[-1]['totalStats']['sagesse']
    if high > low:
        for step in range(1, count - 1):
            selected = solve(weights=(1, TIE_BREAK), sagesse_min=low + (high - low) * step / (count - 1))
            if selected:
                builds.append(build(selected))
    unique = {(b['totalStats']['sagesse'], b['totalElement']): b for b in builds}
    return sorted(unique.values(), key=lambda b: b['totalStats']['sagesse'])


def _solve(catalog, element, level, gear_pa, gear_pm, excluded_ids, damage_base, weights=(1, 0), sagesse_min=None):
    """Solve the MILP and return the optimal list of selected item dicts, or None if infeasible.

    Maximises weights[0] x the target score + weights[1] x Sagesse, with at least sagesse_min Sagesse.
    """

    # Same name and type is one item to the player: the catalog repeats some (11 identical "Patte d'Ecaflip")
    excluded = {(item['name'], item['type']) for item in catalog.items if item['id'] in excluded_ids}

    # Filter items by level upfront
    valid_items = {
        item['id']: item for item in catalog.items
        if item['type'] in SLOT_LIMITS
        and 1 <= item['level'] <= level
        and (item['name'], item['type']) not in excluded
    }
    if not valid_items:
        return None

    model = pulp.LpProblem(f"Maximize_{element}", pulp.LpMaximize)

    # Binary variable per item
    x = {iid: pulp.LpVariable(f"x_{iid}", cat="Binary") for iid in valid_items}

    # Group items by set
    set_item_ids = {}
    for iid, item in valid_items.items():
        if item.get('set'):
            set_item_ids.setdefault(item['set'], []).append(iid)

    # --- Set bonuses ---
    # z = 1 exactly when at least `tier` pieces are worn; the worn bonus is the highest reached
    # tier's, written as the sum of each reached tier's increment over the previous one.
    set_score, set_pa, set_pm, set_sagesse = [], [], [], []
    for set_name, iids in set_item_ids.items():
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', set_name)
        worn = pulp.lpSum(x[iid] for iid in iids)
        prev = {}
        for tier, bonus in sorted(catalog.set_bonuses.get(set_name, {}).items()):
            z = pulp.LpVariable(f"z_{safe_name}_{tier}", cat="Binary")
            model += tier * z <= worn, f"reach_{safe_name}_{tier}"
            model += worn - (tier - 1) <= len(iids) * z, f"auto_{safe_name}_{tier}"
            set_score.append(z * (_score(bonus, element, damage_base) - _score(prev, element, damage_base)))
            set_pa.append(z * (bonus.get('pa', 0) - prev.get('pa', 0)))
            set_pm.append(z * (bonus.get('pm', 0) - prev.get('pm', 0)))
            set_sagesse.append(z * (bonus.get('sagesse', 0) - prev.get('sagesse', 0)))
            prev = bonus

    # --- Objective ---
    obj_terms = []
    for iid, item in valid_items.items():
        val = _score({**item['elements'], **item['stats']}, element, damage_base)
        if val != 0:
            obj_terms.append(x[iid] * val)
    sagesse = pulp.lpSum(item['elements'].get('sagesse', 0) * x[iid] for iid, item in valid_items.items()) + pulp.lpSum(set_sagesse)
    model += weights[0] * pulp.lpSum(obj_terms + set_score) + weights[1] * sagesse
    if sagesse_min is not None:
        model += sagesse >= sagesse_min, "sagesse_min"

    # --- Slot constraints ---
    for slot, limit in SLOT_LIMITS.items():
        slot_ids = [iid for iid, item in valid_items.items() if item['type'] == slot]
        if slot_ids:
            model += pulp.lpSum(x[iid] for iid in slot_ids) <= limit, f"slot_{slot}"
    # The game allows a pet or a mount, never both
    model += pulp.lpSum(x[iid] for iid, item in valid_items.items() if item['type'] in ('pet', 'mount')) <= 1, "pet_or_mount"

    # --- PA/PM minimum from gear (items + set bonuses) ---
    pa_expr = pulp.lpSum((item.get('pa', 0) or 0) * x[iid] for iid, item in valid_items.items())
    pm_expr = pulp.lpSum((item.get('pm', 0) or 0) * x[iid] for iid, item in valid_items.items())
    model += pa_expr + pulp.lpSum(set_pa) >= gear_pa, "pa_min"
    model += pm_expr + pulp.lpSum(set_pm) >= gear_pm, "pm_min"

    # Solver output — set msg=0 to suppress
    model.solve(pulp.PULP_CBC_CMD(msg=1))

    status = pulp.LpStatus[model.status]
    print(f"\n[MILP] Status: {status} | Element: {element} | Level: ≤{level} | PA: {gear_pa} | PM: {gear_pm}")

    if status != 'Optimal':
        return None

    selected = [valid_items[iid] for iid, var in x.items() if var.value() and var.value() > 0.5]
    total_el = sum(_score({**i['elements'], **i['stats']}, element, damage_base) for i in selected)
    print(f"[MILP] {len(selected)} items | {element}: {total_el} | {[i['name'] for i in selected]}")
    return selected


def _build(catalog, selected, element, extra_pa, extra_pm, damage_base, damage_range):
    """Build a result dict from selected items; extra_pa/extra_pm are the character's base + exo PA/PM."""
    base_stats = {el: 0 for el in ALL_ELEMENTS}
    for item in selected:
        for el in ALL_ELEMENTS:
            base_stats[el] += item['elements'].get(el, 0)

    # Compute set bonuses for all elements
    set_counts = {}
    for item in selected:
        if item.get('set'):
            set_counts[item['set']] = set_counts.get(item['set'], 0) + 1

    set_bonus_stats = {el: 0 for el in ALL_ELEMENTS + ['pa', 'pm', 'dmg', 'pct_dmg']}
    set_details = []
    for set_name, count in set_counts.items():
        bonus = catalog.active_bonus(set_name, count)
        if not bonus:
            continue
        for stat in set_bonus_stats:
            set_bonus_stats[stat] += bonus.get(stat, 0)
        set_details.append({'setName': set_name, 'pieces': count, 'bonus': bonus})

    total_stats = {el: base_stats[el] + set_bonus_stats[el] for el in ALL_ELEMENTS}
    total_dmg = set_bonus_stats['dmg'] + sum(item['stats'].get('dmg', 0) for item in selected)
    total_pct_dmg = set_bonus_stats['pct_dmg'] + sum(item['stats'].get('pct_dmg', 0) for item in selected)
    totals = {**total_stats, 'dmg': total_dmg, 'pct_dmg': total_pct_dmg}

    return {
        'items': selected,
        'totalElement': math.floor(damage_base + _score(totals, element, damage_base)),  # for the average roll when damage_base is set
        'spellRoll': damage_range,
        'damageRange': [math.floor(roll + _score(totals, element, roll)) for roll in damage_range] if damage_range else None,
        'totalDmg': total_dmg,
        'totalPctDmg': total_pct_dmg,
        'baseElement': base_stats[element],
        'setBonus': set_bonus_stats[element],
        'setDetails': set_details,
        'baseStats': base_stats,
        'setBonuses': {el: set_bonus_stats[el] for el in ALL_ELEMENTS},
        'totalStats': total_stats,
        'totalPA': extra_pa + set_bonus_stats['pa'] + sum(item.get('pa', 0) or 0 for item in selected),
        'totalPM': extra_pm + set_bonus_stats['pm'] + sum(item.get('pm', 0) or 0 for item in selected),
        'avgLevel': round(sum(i['level'] for i in selected) / len(selected))
    }
