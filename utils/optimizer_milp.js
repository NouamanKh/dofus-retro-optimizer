/**
 * MILP Optimizer - Custom Branch and Bound Implementation
 */

const SLOT_LIMITS_MILP = { "weapon": 1, "hat": 1, "cloak": 1, "amulet": 1, "ring": 2, "belt": 1, "boots": 1 };
const EQUIPMENT_SLOTS_MILP = Object.keys(SLOT_LIMITS_MILP);

function getItemElementValue(item, element) {
    return item.elements[element] || 0;
}

function optimizeMilp(element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items, maxResults = 10) {
    console.log('MILP: Starting for', element);
    console.log('MILP: minPA=', minPA, 'minPM=', minPM, 'maxPA=', maxPA, 'maxPM=', maxPM);
    
    const validItems = items.filter(item => 
        EQUIPMENT_SLOTS_MILP.includes(item.type) && 
        item.level >= minLevel && 
        item.level <= maxLevel
    );
    
    console.log('MILP: Valid items:', validItems.length);
    
    const itemsBySlot = {};
    for (const slot of EQUIPMENT_SLOTS_MILP) {
        itemsBySlot[slot] = validItems
            .filter(i => i.type === slot)
            .sort((a, b) => getItemElementValue(b, element) - getItemElementValue(a, element))
            .slice(0, 30);
    }
    
    let bestScore = -Infinity;
    let bestItems = [];
    let solutionsFound = 0;
    let nodesVisited = 0;
    
    function calcSetBonus(items) {
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
    
    function score(items) {
        return items.reduce((s, i) => s + getItemElementValue(i, element), 0) + calcSetBonus(items);
    }
    
    function getPAPM(items) {
        return {
            pa: items.reduce((s, i) => s + (i.pa || 0), 0),
            pm: items.reduce((s, i) => s + (i.pm || 0), 0)
        };
    }
    
    function isValid(items) {
        const { pa, pm } = getPAPM(items);
        const paValid = minPA <= pa && (maxPA === undefined || pa <= maxPA);
        const pmValid = minPM <= pm && (maxPM === undefined || pm <= maxPM);
        return paValid && pmValid;
    }
    
    function getUpperBound(current, slotIdx) {
        let bound = score(current);
        for (let i = slotIdx; i < EQUIPMENT_SLOTS_MILP.length; i++) {
            const slot = EQUIPMENT_SLOTS_MILP[i];
            const best = itemsBySlot[slot][0];
            if (best) bound += Math.max(0, getItemElementValue(best, element));
        }
        return bound + 50;
    }
    
    function branchAndBound(current, slotIdx) {
        nodesVisited++;
        
        if (nodesVisited % 100000 === 0) {
            console.log('MILP: Visited', nodesVisited, 'solutions:', solutionsFound);
        }
        
        if (slotIdx >= EQUIPMENT_SLOTS_MILP.length) {
            if (isValid(current)) {
                const s = score(current);
                if (s > bestScore) {
                    bestScore = s;
                    bestItems = [...current];
                    solutionsFound++;
                    console.log('MILP: New best =', s, 'PA:', getPAPM(current).pa, 'PM:', getPAPM(current).pm);
                }
            }
            return;
        }
        
        if (getUpperBound(current, slotIdx) <= bestScore) return;
        
        const slot = EQUIPMENT_SLOTS_MILP[slotIdx];
        const limit = SLOT_LIMITS_MILP[slot];
        const candidates = itemsBySlot[slot];
        
        branchAndBound(current, slotIdx + 1);
        
        for (let i = 0; i < candidates.length && i < limit; i++) {
            const item = candidates[i];
            if (current.some(c => c.id === item.id)) continue;
            branchAndBound([...current, item], slotIdx + 1);
            
            if (limit > 1) {
                for (let j = i + 1; j < candidates.length && j < limit; j++) {
                    const item2 = candidates[j];
                    if (current.some(c => c.id === item2.id)) continue;
                    branchAndBound([...current, item, item2], slotIdx + 1);
                }
            }
        }
    }
    
    const start = Date.now();
    branchAndBound([], 0);
    
    console.log('MILP: Done! Visited', nodesVisited, 'nodes, found', solutionsFound, 'solutions in', Date.now() - start, 'ms');
    console.log('MILP: Best =', bestScore);
    
    if (bestItems.length > 0) {
        console.log('MILP: Items:', bestItems.map(i => i.name).join(', '));
    }
    
    return bestItems.length > 0 ? [createResult(bestItems, element)] : [];
}

function createResult(items, element) {
    const base = items.reduce((s, i) => s + getItemElementValue(i, element), 0);
    const setBonus = calcSetBonus(items);
    return { items, totalElement: base + setBonus, baseElement: base, setBonus, setDetails: getSetDetails(items) };
}

function calcSetBonus(items) {
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

function getSetDetails(items) {
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
