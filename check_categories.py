import json
import re

with open('dofus-retro-items.json', 'r', encoding='utf-8') as f:
    raw_items = json.load(f)

categories = set()
for cat_obj in raw_items:
    for cat in cat_obj.keys():
        categories.add(cat)

print("All categories in raw data:")
for c in sorted(categories):
    print(f"  '{c}'")
