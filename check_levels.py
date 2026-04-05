import json
import re

with open('data/items_retro.js', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        items = json.loads(match.group())
    else:
        items = []

# Check level distribution
levels = [i['level'] for i in items if i['type'] in ['weapon', 'hat', 'cloak', 'amulet', 'ring', 'belt', 'boots']]
print(f"Level range: {min(levels)} to {max(levels)}")
print(f"Items at level 20 or below: {len([l for l in levels if l <= 20])}")
print(f"Items above level 20: {len([l for l in levels if l > 20])}")

# Check a few items at different levels
print("\nSample items:")
for level in [1, 10, 20, 50, 100, 150, 200]:
    item = next((i for i in items if i['level'] == level and i['type'] == 'weapon'), None)
    if item:
        print(f"  Level {level}: {item['name']} - vit:{item['elements']['vitalite']}")
