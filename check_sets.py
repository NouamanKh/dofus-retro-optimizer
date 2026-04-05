import json
with open('data/sets_api.js', 'r', encoding='utf-8') as f:
    content = f.read()
    
start = content.find('[')
end = content.rfind(']') + 1
sets = json.loads(content[start:end])

print(f'Total sets: {len(sets)}')
print('\nSample sets:')
for s in sets[:10]:
    print(f"  {s['name']}: {s['bonuses']}")
