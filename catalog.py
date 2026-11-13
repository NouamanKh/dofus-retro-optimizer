"""Equipment catalog: items and set bonuses loaded from data/*.json."""

import json
import os

ALL_ELEMENTS = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite', 'prospection']
DAMAGE_ELEMENTS = ['force', 'intelligence', 'chance', 'agilite']
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
# The spell elements each stat adds damage to
SPELL_ELEMENTS = {'force': ('terre', 'neutre'), 'intelligence': ('feu',), 'chance': ('eau',), 'agilite': ('air',)}


class Catalog:
    def __init__(self, items, sets):
        self.items = items
        self.set_bonuses = {
            s['name']: {int(p): bonus for p, bonus in s['bonuses'].items()}
            for s in sets
        }

    def active_bonus(self, set_name, pieces):
        """Bonus of the highest tier reached with `pieces` worn; {} if none (or unknown set)."""
        tiers = [t for t in self.set_bonuses.get(set_name, {}) if t <= pieces]
        return self.set_bonuses[set_name][max(tiers)] if tiers else {}


def load(data_dir=DATA_DIR):
    """Read items_retro.json and sets_retro.json into a Catalog."""
    with open(os.path.join(data_dir, 'items_retro.json'), encoding='utf-8') as f:
        items = json.load(f)
    with open(os.path.join(data_dir, 'sets_retro.json'), encoding='utf-8') as f:
        sets = json.load(f)
    return Catalog(items, sets)


def load_spells(data_dir=DATA_DIR):
    """Read spells_retro.json: every class spell that does damage, with its 6 grades."""
    with open(os.path.join(data_dir, 'spells_retro.json'), encoding='utf-8') as f:
        return json.load(f)['spells']


def class_spells(spells, class_name, element, level):
    """The spells a `class_name` character of `level` can hit one target with in `element`, as the optimizer takes them.

    Each is at the highest grade the level allows, so taken as fully boosted with spell points.
    castsMax is for one round on one target: a spell with a cooldown is cast once.
    shortcut: poisons, traps and glyphs are left out and a line in another element counts for nothing, as the estimate is one stat's direct damage; add them when the estimate covers them.
    """
    found = []
    for spell in spells:
        grades = [g for g in spell['grades'] if g['level'] <= level]
        if spell['class'] != class_name or not grades:
            continue
        grade = grades[-1]
        # A line with a chance is one of several outcomes: it counts for its share
        lines = [(line['min'] * line.get('chance', 100) / 100, line['max'] * line.get('chance', 100) / 100) for line in grade['damage']
                 if line['element'] in SPELL_ELEMENTS[element] and 'duration' not in line and 'via' not in line]
        if lines:
            limits = [grade['castsPerTurn'], grade['castsPerTarget'], 1 if grade['cooldown'] else 0]
            found.append({'name': spell['name'], 'grade': len(grades), 'pa': grade['pa'], 'castsMax': min([n for n in limits if n] or [99]),
                          'damageMin': sum(low for low, _ in lines), 'damageMax': sum(high for _, high in lines)})
    return found
