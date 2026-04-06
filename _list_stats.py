import json

with open('dofus-retro-items.json', 'r', encoding='utf-8') as f:
    raw_items = json.load(f)

types = set()
for cat_obj in raw_items:
    for item_list in cat_obj.values():
        for item in item_list:
            for b in item.get('bonus', []):
                t = b.get('type', '')
                try:
                    t = t.encode('latin-1').decode('utf-8')
                except:
                    pass
                types.add(t.strip())

for t in sorted(types):
    print(repr(t))
