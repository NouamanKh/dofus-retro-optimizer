"""
Debug script to find items with main stats
"""
import urllib.request
import json

CHARACTERISTICS = {
    0: 'vitalite',
    1: 'agilite', 
    2: 'chance',
    3: 'intelligence',
    4: 'force',
    5: 'sagesse',
}

def fetch(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

print("=== Looking for items with stats ===")
count = 0
stats_found = set()

for skip in range(0, 5000, 50):
    url = f"https://api.dofusdb.fr/items?$limit=50&$skip={skip}"
    data = fetch(url)
    
    if not data.get('data'):
        break
    
    for item in data['data']:
        effects = item.get('effects', [])
        stats = {}
        all_chars = []
        
        for e in effects:
            char = e.get('characteristic')
            val = e.get('from', 0)
            all_chars.append((char, val))
            
            if char in CHARACTERISTICS and val > 0:
                stats[CHARACTERISTICS[char]] = val
        
        if stats and len(stats) >= 1:
            print(f"{item['name']['en']} (Lv{item['level']}): {stats}")
            count += 1
            if count >= 30:
                break
    
    print(f"Checked {skip + 50} items...")
    
    if count >= 30:
        break

print(f"\n=== Summary ===")
print(f"Found {count} items with main stats")
