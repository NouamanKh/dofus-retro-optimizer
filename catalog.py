"""Equipment catalog: items and set bonuses loaded from data/*.json."""

import json
import os

ALL_ELEMENTS = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite', 'prospection']
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


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
