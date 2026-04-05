import json
import re

with open('data/items_retro.js', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        items = json.loads(match.group())
    else:
        items = []

# Count items with vitality by type
vitality_by_type = {}
for item in items:
    if item['elements']['vitalite'] > 0:
        t = item['type']
        vitality_by_type[t] = vitality_by_type.get(t, 0) + 1

print("Items with vitality by type:")
for t, c in sorted(vitality_by_type.items()):
    print(f"  {t}: {c}")

# Show some items with good vitality
print("\nSample items with vitality:")
for item in items[:50]:
    if item['elements']['vitalite'] > 5:
        print(f"  {item['name']} (Lvl {item['level']}): {item['elements']['vitalite']} vitality, type: {item['type']}")
