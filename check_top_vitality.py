import json
import re

with open('data/items_retro.js', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        items = json.loads(match.group())
    else:
        items = []

# Find items with the highest vitality
vitality_items = [(i['name'], i['level'], i['elements']['vitalite'], i['type']) for i in items]
vitality_items.sort(key=lambda x: -x[2])

print("Top 20 items by vitality:")
for name, lvl, vit, typ in vitality_items[:20]:
    print(f"  {name} (Lvl {lvl}): {vit} vitality, type: {typ}")
