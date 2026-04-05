const fs = require('fs');

const rawItems = JSON.parse(fs.readFileSync('./dofus-retro-items.json', 'utf8'));
const rawSets = JSON.parse(fs.readFileSync('./dofus-retro-sets.json', 'utf8'));

const categoryToType = {
  'Les boucliers': 'shield',
  'Les épées': 'weapon',
  'Les dagues': 'weapon',
  'Les arcs': 'weapon',
  'Les bâtons': 'weapon',
  'Les marteaux': 'weapon',
  'Les pelles': 'weapon',
  'Les haches': 'weapon',
  'Les anneaux': 'ring',
  'Les amulettes': 'amulet',
  'Les ceintures': 'belt',
  'Les bottes': 'boots',
  'Les coiffe': 'hat',
  'Les capes': 'cloak'
};

const statMapping = {
  'Vitalit\u00e9': 'vitalite',
  'vitalit\u00e9': 'vitalite',
  'Vie': 'vitalite',
  'Sagesse': 'sagesse',
  'sagesse': 'sagesse',
  'Force': 'force',
  'force': 'force',
  'Intelligence': 'intelligence',
  'intelligence': 'intelligence',
  'Chance': 'chance',
  'chance': 'chance',
  'Agilit\u00e9': 'agilite',
  'Agilit\u00e9': 'agilite',
  'agilit\u00e9': 'agilite',
  'agilit\u00e9': 'agilite',
  'Agilit\u00c3\u00a9': 'agilite'
};

function normalizeStat(stat) {
  const lower = stat.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  if (lower.includes('vitalit')) return 'vitalite';
  if (lower.includes('sagesse')) return 'sagesse';
  if (lower.includes('force')) return 'force';
  if (lower.includes('intelligence')) return 'intelligence';
  if (lower.includes('chance')) return 'chance';
  if (lower.includes('agilit')) return 'agilite';
  return null;
}

function parseBonusToElements(bonuses) {
  const elements = {
    vitalite: 0,
    sagesse: 0,
    force: 0,
    intelligence: 0,
    chance: 0,
    agilite: 0
  };

  if (!bonuses || !Array.isArray(bonuses)) return elements;

  for (const bonus of bonuses) {
    if (!bonus || !bonus.type) continue;
    
    const stat = normalizeStat(bonus.type);
    if (stat && elements.hasOwnProperty(stat)) {
      if (Array.isArray(bonus.values)) {
        elements[stat] = Math.max(...bonus.values);
      } else if (typeof bonus.values === 'number') {
        elements[stat] += bonus.values;
      } else if (typeof bonus.values === 'string') {
        elements[stat] += parseInt(bonus.values) || 0;
      }
    }
  }

  return elements;
}

function buildSetLookup() {
  const lookup = {};
  for (const set of rawSets) {
    for (const itemName of set.items) {
      lookup[itemName.toLowerCase()] = set.name;
    }
  }
  return lookup;
}

const setLookup = buildSetLookup();

let itemId = 1;
const items = [];

for (const [category, itemList] of Object.entries(rawItems)) {
  const type = categoryToType[category] || 'unknown';
  
  for (const item of itemList) {
    const elements = parseBonusToElements(item.bonus);
    const setName = setLookup[item.name.toLowerCase()] || null;
    
    items.push({
      id: `retro_${itemId}`,
      name: item.name,
      type: type,
      level: item.level,
      elements: elements,
      set: setName,
      recipe: item.recipe || [],
      requirements: item.requirements || [],
      weapon_stats: item.weapon_stats || null
    });
    
    itemId++;
  }
}

const output = {
  generated: new Date().toISOString(),
  source: 'Dofus Retro 1.29 (retro-craft/scrapstuff)',
  total_items: items.length,
  items: items
};

fs.writeFileSync('./data/items_retro.js', `const ITEMS_RETRO = ${JSON.stringify(items, null, 2)};\nmodule.exports = ITEMS_RETRO;`);
fs.writeFileSync('./data/sets_retro.js', `const SETS_RETRO = ${JSON.stringify(rawSets, null, 2)};\nmodule.exports = SETS_RETRO;`);

console.log(`Converted ${items.length} items`);
console.log(`Saved to data/items_retro.js and data/sets_retro.js`);
