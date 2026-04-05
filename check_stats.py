import json
import re

with open('data/items_retro.js', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        items = json.loads(match.group())
    else:
        items = []

# Check items with actual stats
items_with_stats = [i for i in items if sum(i['elements'].values()) > 0]
print(f"Items with stats: {len(items_with_stats)}")

# Show sample items with stats
print("\nSample items with stats:")
for item in items_with_stats[:5]:
    print(f"  {item['name']}: {item['elements']}")

# Check by element
print("\nItems by primary element:")
for elem in ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite']:
    count = len([i for i in items if i['elements'][elem] > 0])
    print(f"  {elem}: {count}")
