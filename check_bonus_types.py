import json

with open('dofus-retro-items.json', 'r', encoding='utf-8') as f:
    raw_items = json.load(f)

print("Sample items with their bonuses:")
for cat_obj in raw_items[:3]:
    for cat, items in cat_obj.items():
        for item in items[:2]:
            print(f"\n{item['name']} (Level {item['level']}):")
            if item.get('bonus'):
                for b in item['bonus'][:3]:
                    print(f"  - {b}")
