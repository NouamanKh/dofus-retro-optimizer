/**
 * MILP Optimizer - Custom Branch and Bound Implementation
 */

const SLOT_LIMITS_MILP = { "weapon": 1, "hat": 1, "cloak": 1, "amulet": 1, "ring": 2, "belt": 1, "boots": 1, "shield": 1 };
const EQUIPMENT_SLOTS_MILP = Object.keys(SLOT_LIMITS_MILP);

function getItemElementValueMilp(item, element) {
    return item.elements[element] || 0;
}

function calcSetBonusMilp(items, element) {
    const counts = {};
    items.forEach(i => { if (i.set) counts[i.set] = (counts[i.set] || 0) + 1; });
    let bonus = 0;
    Object.entries(counts).forEach(([name, count]) => {
        if (count >= 2) {
            const set = SET_BONUSES[name];
            if (set) {
                const tiers = Object.keys(set).map(Number).sort((a, b) => b - a);
                for (const t of tiers) {
                    if (t <= count) { bonus += set[t][element] || 0; break; }
                }
            }
        }
    });
    return bonus;
}

function scoreMilp(items, element) {
    return items.reduce((s, i) => s + getItemElementValueMilp(i, element), 0) + calcSetBonusMilp(items, element);
}

function getPAPMMilp(items) {
    return {
        pa: items.reduce((s, i) => s + (i.pa || 0), 0),
        pm: items.reduce((s, i) => s + (i.pm || 0), 0)
    };
}

function getSetDetailsMilp(items) {
    const counts = {};
    items.forEach(i => { if (i.set) counts[i.set] = (counts[i.set] || 0) + 1; });
    const details = [];
    Object.entries(counts).forEach(([name, count]) => {
        if (count >= 2) {
            const set = SET_BONUSES[name];
            if (set) {
                const tiers = Object.keys(set).map(Number).sort((a, b) => b - a);
                for (const t of tiers) {
                    if (t <= count) { details.push({ setName: name, pieces: count, tier: t, bonus: set[t] }); break; }
                }
            }
        }
    });
    return details;
}

function createResultMilp(items, element) {
    const elements = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite'];
    const baseStats = { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 0, agilite: 0 };
    items.forEach(item => {
        elements.forEach(el => { baseStats[el] += item.elements[el] || 0; });
    });
    const setBonuses = { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 0, agilite: 0 };
    const counts = {};
    items.forEach(i => { if (i.set) counts[i.set] = (counts[i.set] || 0) + 1; });
    Object.entries(counts).forEach(([name, count]) => {
        if (count >= 2) {
            const set = SET_BONUSES[name];
            if (set) {
                const tiers = Object.keys(set).map(Number).sort((a, b) => b - a);
                for (const t of tiers) {
                    if (t <= count) {
                        elements.forEach(el => { setBonuses[el] += set[t][el] || 0; });
                        break;
                    }
                }
            }
        }
    });
    const totalStats = {};
    elements.forEach(el => { totalStats[el] = baseStats[el] + setBonuses[el]; });
    const base = baseStats[element];
    const setBonus = setBonuses[element];
    return {
        items,
        totalElement: base + setBonus,
        baseElement: base,
        setBonus,
        setDetails: getSetDetailsMilp(items),
        baseStats,
        setBonuses,
        totalStats,
        avgLevel: items.length > 0 ? Math.round(items.reduce((s, i) => s + i.level, 0) / items.length) : 0
    };
}

function optimizeMilp(element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items, maxResults = 10) {
    console.log('MILP: Starting for', element, 'minPA=', minPA, 'minPM=', minPM, 'maxPA=', maxPA, 'maxPM=', maxPM);

    const validItems = items.filter(item =>
        EQUIPMENT_SLOTS_MILP.includes(item.type) &&
        item.level >= minLevel &&
        item.level <= maxLevel
    );

    const itemsBySlot = {};
    for (const slot of EQUIPMENT_SLOTS_MILP) {
        itemsBySlot[slot] = validItems
            .filter(i => i.type === slot)
            .sort((a, b) => getItemElementValueMilp(b, element) - getItemElementValueMilp(a, element))
            .slice(0, 25);
    }

    // Tighter upper bound: sum of best items per remaining slot (no flat +50)
    function getUpperBound(current, slotIdx) {
        let bound = scoreMilp(current, element);
        for (let i = slotIdx; i < EQUIPMENT_SLOTS_MILP.length; i++) {
            const slot = EQUIPMENT_SLOTS_MILP[i];
            const limit = SLOT_LIMITS_MILP[slot];
            const candidates = itemsBySlot[slot];
            for (let k = 0; k < Math.min(limit, candidates.length); k++) {
                bound += Math.max(0, getItemElementValueMilp(candidates[k], element));
            }
        }
        return bound;
    }

    const allResults = new Map();

    function runSearch(excludedItemIds) {
        let bestScore = -Infinity;
        let bestItems = [];
        let nodesVisited = 0;

        function branchAndBound(current, slotIdx) {
            nodesVisited++;
            if (slotIdx >= EQUIPMENT_SLOTS_MILP.length) {
                const { pa, pm } = getPAPMMilp(current);
                if (pa >= minPA && pm >= minPM && pa <= maxPA && pm <= maxPM) {
                    const s = scoreMilp(current, element);
                    if (s > bestScore) {
                        bestScore = s;
                        bestItems = [...current];
                    }
                }
                return;
            }
            if (getUpperBound(current, slotIdx) <= bestScore) return;

            const slot = EQUIPMENT_SLOTS_MILP[slotIdx];
            const limit = SLOT_LIMITS_MILP[slot];
            const candidates = itemsBySlot[slot].filter(i => !excludedItemIds.has(i.id));

            // Try skipping this slot
            branchAndBound(current, slotIdx + 1);

            // Try single items
            for (let i = 0; i < candidates.length; i++) {
                const item = candidates[i];
                branchAndBound([...current, item], slotIdx + 1);

                // Try pairs for slots with limit > 1 (rings)
                if (limit > 1) {
                    for (let j = i + 1; j < candidates.length; j++) {
                        branchAndBound([...current, item, candidates[j]], slotIdx + 1);
                    }
                }
            }
        }

        branchAndBound([], 0);
        console.log('MILP: Visited', nodesVisited, 'nodes, best =', bestScore);
        return bestItems;
    }

    // Find best solution
    const best = runSearch(new Set());
    if (best.length === 0) return [];

    const results = [];
    const seenKeys = new Set();

    function addResult(items) {
        if (items.length === 0) return;
        const key = items.map(i => i.id).sort().join('|');
        if (!seenKeys.has(key)) {
            seenKeys.add(key);
            results.push(createResultMilp(items, element));
        }
    }

    addResult(best);

    // Generate diverse alternatives by excluding items from the best solution one at a time
    for (const excludedItem of best) {
        if (results.length >= maxResults) break;
        const excluded = new Set([excludedItem.id]);
        const alt = runSearch(excluded);
        addResult(alt);
    }

    // Exclude pairs for more diversity
    for (let i = 0; i < best.length && results.length < maxResults; i++) {
        for (let j = i + 1; j < best.length && results.length < maxResults; j++) {
            const excluded = new Set([best[i].id, best[j].id]);
            const alt = runSearch(excluded);
            addResult(alt);
        }
    }

    results.sort((a, b) => b.totalElement - a.totalElement);
    return results.slice(0, maxResults);
}
