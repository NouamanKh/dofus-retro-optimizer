import json
import re

with open('data/items_retro.js', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        items = json.loads(match.group())
    else:
        items = []

with open('data/sets_retro.js', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        sets = json.loads(match.group())
    else:
        sets = []

print(f'Items loaded: {len(items)}')
print(f'Items with sets: {len([i for i in items if i["set"]])}')
print(f'Items by type:')
for t, c in {}.items():
    pass

type_counts = {}
for item in items:
    t = item['type']
    type_counts[t] = type_counts.get(t, 0) + 1

for t, c in sorted(type_counts.items()):
    print(f'  {t}: {c}')

print(f'\nSets loaded: {len(sets)}')
print(f'First set: {sets[0]["name"]}')
