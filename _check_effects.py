import json

with open('dofus-retro-items.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

rich = sorted(items, key=lambda x: len(x.get('effects', [])), reverse=True)[:3]
for item in rich:
    print(item.get('name', {}).get('fr', '?'), '- effects:')
    for e in item.get('effects', [])[:20]:
        print(' ', e)
    print()
