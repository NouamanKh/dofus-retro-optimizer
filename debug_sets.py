import urllib.request
import json

CHAR_PERCENTAGE = {
    10: "vitalite",
    11: "agilite", 
    12: "chance",
    13: "intelligence",
    14: "force",
    15: "sagesse",
}

CHAR_RAW = {
    0: "vitalite",
    1: "agilite", 
    2: "chance",
    3: "intelligence",
    4: "force",
    5: "sagesse",
}

url = 'https://api.dofusdb.fr/item-sets?$limit=10'
req = urllib.request.Request(url, headers={'Accept': 'application/json'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    for s in data['data'][:3]:
        print(f"\n=== Set: {s['name']['en']} (Lv{s.get('level', '?')}) ===")
        print(f"Items in set: {len(s.get('items', []))}")
        print(f"Set effects field type: {type(s.get('effects'))}")
        if s.get('effects'):
            print(f"Effects: {json.dumps(s['effects'], indent=2)}")
        if 'bonusIsSecret' in s:
            print(f"Bonus is secret: {s['bonusIsSecret']}")
