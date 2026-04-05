import json
import re

with open('dofus-retro-items.json', 'r', encoding='utf-8') as f:
    raw_items = json.load(f)

# Find PA/PM related bonuses
pa_pm_types = set()
for cat_obj in raw_items:
    for cat, items in cat_obj.items():
        for item in items:
            if item.get('bonus'):
                for b in item['bonus']:
                    if 'pa' in b.get('type', '').lower() or 'pm' in b.get('type', '').lower():
                        pa_pm_types.add(b.get('type'))

print("PA/PM related bonus types found:")
for t in sorted(pa_pm_types):
    print(f"  - {t}")

# Also check weapon stats for PA
print("\nWeapon stats keys:")
for cat_obj in raw_items[:5]:
    for cat, items in cat_obj.items():
        for item in items:
            if item.get('weapon_stats'):
                print(f"  {item['weapon_stats'].keys()}")
                break
        else:
            continue
        break
