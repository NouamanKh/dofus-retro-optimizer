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
# The requirements the search can check, and the stat each asks more of. An item with any other
# (class, alignment, sex, job, rank, kamas, a stat under a value) is left out: nothing here tells if the character meets it
REQUIRED_STAT = {
    'Vitalité >': 'vitalite', 'Sagesse >': 'sagesse', 'Force >': 'force', 'Intelligence >': 'intelligence',
    'Chance >': 'chance', 'Agilité >': 'agilite', 'PM >': 'pm'
}
BIG = 10_000  # More than any stat total or required value (highest in the data: 1200)


def base_pa(level):
    return 7 if level >= 100 else 6


def _requirements(item):
    return item.get('requirements') or []


def _stat(item, stat):
    return item['elements'].get(stat) or item['stats'].get(stat) or item.get(stat) or 0


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


def optimize(catalog, element, level, total_pa, total_pm, exo_pa=0, exo_pm=0, excluded_ids=(), spells=()):
    """Best Build for `element` reaching at least the player's total PA/PM without the excluded items, or None if none can.

    With spells, maximises the average estimated damage in `element` of the best round the build can cast:
    any mix of the spells that its PA pay for. A spell is {'damageMin', 'damageMax', 'pa', 'castsMax'}, castsMax being per round.
    """
    return _search(catalog, element, level, total_pa, total_pm, exo_pa, exo_pm, excluded_ids, spells)()


def optimize_tradeoffs(catalog, element, level, total_pa, total_pm, exo_pa=0, exo_pm=0, excluded_ids=(), spells=(), count=5):
    """Up to `count` Builds from the most damage to the most Sagesse, each with the most damage for its Sagesse."""
    return _tradeoffs(_search(catalog, element, level, total_pa, total_pm, exo_pa, exo_pm, excluded_ids, spells), count)


def optimize_per_pa(catalog, element, level, total_pa, total_pm, exo_pa=0, exo_pm=0, excluded_ids=(), spells=(), tradeoffs=False):
    """The damage Builds worth comparing, from the most PA down: PA cost the most, so each total a build can stop at gets its best.

    A Build is only there if no other does as much damage on as few PA. With tradeoffs, each PA total gets
    its most damage, its most Sagesse and one in between, and Sagesse counts too.
    """
    solve = _search(catalog, element, level, total_pa, total_pm, exo_pa, exo_pm, excluded_ids, spells)
    builds, pa_max = [], None
    while True:
        found = _tradeoffs(solve, 3, pa_max=pa_max) if tradeoffs else [b for b in [solve(pa_max=pa_max)] if b]
        if not found:
            break
        builds += found
        # No build found goes over this, so the totals in between would give the same builds again
        pa_max = max(b['totalPA'] for b in found) - 1

    def worth(build):
        return (-build['totalPA'], build['roundAverage'], *([build['totalStats']['sagesse']] if tradeoffs else []))

    best = {worth(b): b for b in builds}
    return [b for w, b in sorted(best.items(), reverse=True, key=lambda wb: (-wb[0][0], *wb[0][1:]))
            if not any(o != w and all(x >= y for x, y in zip(o, w)) for o in best)]


def _tradeoffs(solve, count, **limits):
    builds = [solve(weights=(1, TIE_BREAK), **limits)]
    if not builds[0]:
        return []
    low = builds[0]['totalStats']['sagesse']
    most_sagesse = solve(weights=(TIE_BREAK, 1), **limits)
    high = most_sagesse['totalStats']['sagesse'] if most_sagesse else low
    if high > low:
        steps = [solve(weights=(1, TIE_BREAK), sagesse_min=low + (high - low) * step / (count - 1), **limits) for step in range(1, count)]
        builds += [b for b in steps if b]
    # Highest Sagesse first: a build only stays if it does more damage than every build with more Sagesse
    kept = []
    for build in sorted(builds, key=lambda b: (b['totalStats']['sagesse'], b['roundAverage']), reverse=True):
        if not kept or build['roundAverage'] > kept[-1]['roundAverage']:
            kept.append(build)
    return kept[::-1]


def _search(catalog, element, level, total_pa, total_pm, exo_pa, exo_pm, excluded_ids, spells):
    """Returns solve(pa_max=None, **goal), the best Build for that goal on at most pa_max PA, or None."""
    extra_pa = base_pa(level) + exo_pa
    extra_pm = BASE_PM + exo_pm
    limits = (catalog, level, max(0, total_pa - extra_pa), max(0, total_pm - extra_pm), excluded_ids, {'pa': extra_pa, 'pm': extra_pm})
    rounds = ()
    if spells:
        # The most PA a build can have bounds the rounds to look at
        most_pa = _solve('pa', *limits)
        rounds = most_pa and _rounds(spells, extra_pa + _gear_total(catalog, most_pa[0], 'pa'))
        if not rounds:
            return lambda **goal: None

    def solve(pa_max=None, **goal):
        castable = rounds if pa_max is None else [r for r in rounds if r[0] <= pa_max]
        if rounds and not castable:
            return None
        found = _solve(element, *limits, castable, None if pa_max is None else pa_max - extra_pa, **goal)
        # No gear is no build, even when the bare character can cast
        return _build(catalog, *found, element, extra_pa, extra_pm, spells) if found and found[0] else None

    return solve


def _gear_total(catalog, selected, stat):
    pieces = {}
    for item in selected:
        if item.get('set'):
            pieces[item['set']] = pieces.get(item['set'], 0) + 1
    return sum(_stat(item, stat) for item in selected) + sum(catalog.active_bonus(name, count).get(stat, 0) for name, count in pieces.items())


def _rounds(spells, pa_max):
    """The rounds worth casting with up to pa_max PA, as (PA, casts, summed base damage, casts of each spell).

    A round does base x (100 + stat + % damage) / 100 + casts x flat damage, so for a cost and a number of casts only the most base damage matters.
    A round is dropped when another costs no more with as many casts and as much base damage: a cast is taken never to hurt.
    """
    best = {(0, 0): (0, ())}
    for spell in spells:
        base = (spell['damageMin'] + spell['damageMax']) / 2
        step = {}
        for (pa, casts), (damage, counts) in best.items():
            for n in range(min(spell['castsMax'], (pa_max - pa) // spell['pa']) + 1):
                key = (pa + n * spell['pa'], casts + n)
                if key not in step or damage + n * base > step[key][0]:
                    step[key] = (damage + n * base, counts + (n,))
        best = step
    rounds = [(pa, casts, damage, counts) for (pa, casts), (damage, counts) in best.items() if casts]
    return [r for r in rounds if not any(o != r and o[0] <= r[0] and o[1] >= r[1] and o[2] >= r[2] for o in rounds)]


def _without_dominated(items, value):
    """Drops items a build never needs: set-less ones whose slot's places can be filled with free items at least as good on every value.

    Set pieces stay on both sides, as wearing one can change a set bonus.
    Items with requirements can be dropped but never drop another, as a build may not get to wear them.
    """
    def beaten(item):
        return sum(all(a >= b for a, b in zip(value(rival), value(item))) for rival in kept.get(item['type'], ())) >= SLOT_LIMITS[item['type']]

    kept = {}
    for item in sorted((i for i in items if not i.get('set') and not _requirements(i)), key=value, reverse=True):
        if not beaten(item):
            kept.setdefault(item['type'], []).append(item)
    return ([i for i in items if i.get('set') or (_requirements(i) and not beaten(i))]
            + [i for better in kept.values() for i in better])


def _solve(element, catalog, level, gear_pa, gear_pm, excluded_ids, own=None, rounds=(), gear_pa_max=None, weights=(1, 0), sagesse_min=None):
    """Solve the MILP and return the optimal (selected item dicts, casts of each spell), or None if infeasible.

    Maximises weights[0] x the target + weights[1] x Sagesse, with at least sagesse_min Sagesse and at most gear_pa_max PA from gear.
    The target is the element's score, or with rounds (see _rounds) the average damage of the best of them.
    `own` is what the character has without gear, which counts toward item requirements and casts.
    """
    # shortcut: only PA and PM are known, so stat points count as 0 and a build must meet requirements on gear alone; pass the points here once the app asks for them
    own = own or {}

    # Same name and type is one item to the player: the catalog repeats some (11 identical "Patte d'Ecaflip")
    excluded = {(item['name'], item['type']) for item in catalog.items if item['id'] in excluded_ids}

    # Filter items by level upfront
    candidates = [
        item for item in catalog.items
        if item['type'] in SLOT_LIMITS
        and 1 <= item['level'] <= level
        and (item['name'], item['type']) not in excluded
        and all(req['type'] in REQUIRED_STAT for req in _requirements(item))
    ]
    def value(item):
        # Spells weigh the stat and flat damage differently, so damage takes both
        target = (_stat(item, element) + _stat(item, 'pct_dmg'), _stat(item, 'dmg')) if rounds else (_score({**item['elements'], **item['stats']}, element),)
        # Under a PA limit less PA can be what a build needs, so only an item with the same PA can stand in for another
        return (*target, _stat(item, 'pa'), *([-_stat(item, 'pa')] if gear_pa_max is not None else []), _stat(item, 'pm'), _stat(item, 'sagesse'),
                *(_stat(item, stat) for stat in required))

    # A stat a kept item requires is worth having, so it keeps more items: repeat until no new stat is required
    required = []
    while True:
        kept = _without_dominated(candidates, value)
        missing = {REQUIRED_STAT[req['type']] for item in kept for req in _requirements(item)} - set(required)
        if not missing:
            break
        required += sorted(missing)
    valid_items = {item['id']: item for item in kept}
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
    tiers = []
    for set_name, iids in set_item_ids.items():
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', set_name)
        worn = pulp.lpSum(x[iid] for iid in iids)
        prev = {}
        for tier, bonus in sorted(catalog.set_bonuses.get(set_name, {}).items()):
            z = pulp.LpVariable(f"z_{safe_name}_{tier}", cat="Binary")
            model += tier * z <= worn, f"reach_{safe_name}_{tier}"
            model += worn - (tier - 1) <= len(iids) * z, f"auto_{safe_name}_{tier}"
            tiers.append((z, bonus, prev))
            prev = bonus

    def total(*stats):
        """What the worn gear gives of these stats together, set bonuses included."""
        return (pulp.lpSum(sum(_stat(item, stat) for stat in stats) * x[iid] for iid, item in valid_items.items())
                + pulp.lpSum(z * sum(bonus.get(stat, 0) - prev.get(stat, 0) for stat in stats) for z, bonus, prev in tiers))

    def reach(*stats):
        """At least as far from 0 as any build's total of these stats."""
        by_slot = {}
        for item in valid_items.values():
            by_slot.setdefault(item['type'], []).append(abs(sum(_stat(item, stat) for stat in stats)))
        by_set = [max((abs(sum(bonus.get(stat, 0) for stat in stats)) for bonus in catalog.set_bonuses.get(name, {}).values()), default=0)
                  for name in set_item_ids]
        # A build wears at most one set per place
        places = sum(SLOT_LIMITS.values())
        return sum(sum(sorted(values)[-SLOT_LIMITS[slot]:]) for slot, values in by_slot.items()) + sum(sorted(by_set)[-places:])

    # --- Objective ---
    chosen = []
    if rounds:
        percent, flat = total(element, 'pct_dmg'), total('dmg')
        most_percent, most_flat = reach(element, 'pct_dmg'), reach('dmg')
        # A round's damage multiplies its casts by the gear's totals, which isn't linear.
        # So each round gets its own copy of the totals, held at 0 unless the round is chosen: the copies add up to the totals.
        parts = []
        for r, (pa, casts, base, _) in enumerate(rounds):
            chosen.append(pulp.LpVariable(f"round_{r}", cat="Binary"))
            for name, most, weight in (("percent", most_percent, base / 100), ("flat", most_flat, casts)):
                part = pulp.LpVariable(f"{name}_{r}", -most, most)
                model += part <= most * chosen[r], f"{name}_high_{r}"
                model += part >= -most * chosen[r], f"{name}_low_{r}"
                parts.append((name, weight, part))
        model += pulp.lpSum(chosen) == 1, "one_round"
        model += pulp.lpSum(part for name, _, part in parts if name == "percent") == percent, "percent_parts"
        model += pulp.lpSum(part for name, _, part in parts if name == "flat") == flat, "flat_parts"
        model += pulp.lpSum(pa * c for (pa, *_), c in zip(rounds, chosen)) <= own.get('pa', 0) + total('pa'), "round_pa"
        target = pulp.lpSum(base * c for (_, _, base, _), c in zip(rounds, chosen)) + pulp.lpSum(weight * part for _, weight, part in parts)
    else:
        target = total(element) + (total('chance') / 10 if element == 'prospection' else 0)
    sagesse = total('sagesse')
    model += weights[0] * target + weights[1] * sagesse
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
    model += total('pa') >= gear_pa, "pa_min"
    if gear_pa_max is not None:
        model += total('pa') <= gear_pa_max, "pa_max"
    model += total('pm') >= gear_pm, "pm_min"

    # --- Item requirements ---
    # An item is put on with the rest of the build already worn, so its own stats don't help it.
    # shortcut: a set bonus the item completes still counts for it, and two items may each lean on the other; subtract those if a build ever shows it
    # One variable per total keeps each requirement's row short: the solver is several times slower on rows that repeat the whole sum
    totals = {stat: pulp.LpVariable(f"total_{stat}", -BIG, BIG) for stat in required}
    for stat, var in totals.items():
        model += var == total(stat), f"total_{stat}"
    for iid, item in valid_items.items():
        for n, req in enumerate(_requirements(item)):
            stat = REQUIRED_STAT[req['type']]
            model += (own.get(stat, 0) + totals[stat] - _stat(item, stat) * x[iid]
                      >= req['value'] + 1 - BIG * (1 - x[iid])), f"req_{n}_{iid}"

    # Solver output — set msg=0 to suppress
    model.solve(pulp.PULP_CBC_CMD(msg=1))

    status = pulp.LpStatus[model.status]
    print(f"\n[MILP] Status: {status} | Element: {element} | Level: ≤{level} | PA: {gear_pa} | PM: {gear_pm}")

    if status != 'Optimal':
        return None

    selected = [valid_items[iid] for iid, var in x.items() if var.value() and var.value() > 0.5]
    print(f"[MILP] {len(selected)} items | {element}: {pulp.value(target)} | {[i['name'] for i in selected]}")
    return selected, next((counts for (*_, counts), c in zip(rounds, chosen) if c.value() > 0.5), ())


def _build(catalog, selected, casts, element, extra_pa, extra_pm, spells):
    """Build a result dict from selected items and the casts of each spell; extra_pa/extra_pm are the character's base + exo PA/PM."""
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
    # Each cast rounds on its own, as in game
    cast_spells = [
        {**spell, 'casts': count, 'damageRange': [math.floor(roll + _score(totals, element, roll)) for roll in (spell['damageMin'], spell['damageMax'])]}
        for spell, count in zip(spells, casts)
    ]
    bases = [(spell['damageMin'] + spell['damageMax']) / 2 for spell in spells]
    average = sum(count * (base + _score(totals, element, base)) for base, count in zip(bases, casts)) if spells else _score(totals, element)

    return {
        'items': selected,
        'totalElement': math.floor(average),
        'spells': cast_spells,
        'roundDamage': [sum(s['casts'] * s['damageRange'][end] for s in cast_spells) for end in (0, 1)] if spells else None,
        'roundAverage': round(average, 6),  # Rounded so equal builds compare equal
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
