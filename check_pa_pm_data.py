import json
import re

with open('data/items_retro.js', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        items = json.loads(match.group())
    else:
        items = []

# Check items with PA/PM
items_with_pa = [i for i in items if i.get('pa', 0) > 0]
items_with_pm = [i for i in items if i.get('pm', 0) > 0]

print(f"Items with PA: {len(items_with_pa)}")
print(f"Items with PM: {len(items_with_pm)}")

print("\nSample items with PA:")
for item in items_with_pa[:5]:
    print(f"  {item['name']}: PA={item['pa']}")

print("\nSample items with PM:")
for item in items_with_pm[:5]:
    print(f"  {item['name']}: PM={item['pm']}")
