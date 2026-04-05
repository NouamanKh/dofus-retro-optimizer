/**
 * MILP Optimizer using HiGHS solver (WASM)
 */

const SLOT_LIMITS_MILP = { "weapon": 1, "hat": 1, "cloak": 1, "amulet": 1, "ring": 2, "belt": 1, "boots": 1 };
const EQUIPMENT_SLOTS_MILP = Object.keys(SLOT_LIMITS_MILP);

function getItemElementValue(item, element) {
    return item.elements[element] || 0;
}

async function optimizeMilp(element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items, maxResults = 10) {
    console.log('MILP (HiGHS): Starting for', element);
    
    const validItems = items.filter(item => 
        EQUIPMENT_SLOTS_MILP.includes(item.type) && 
        item.level >= minLevel && 
        item.level <= maxLevel
    );
    
    console.log('MILP: Valid items:', validItems.length);
    
    const n = validItems.length;
    const itemIndex = {};
    validItems.forEach((item, idx) => itemIndex[item.id] = idx);
    
    const numVars = n;
    const numConstraints = 7 + 1 + 1;
    
    const a = [];
    const b = [];
    const c = validItems.map(item => getItemElementValue(item, element));
    const types = [];
    const names = validItems.map(item => 'x_' + item.id);
    const integrality = new Array(n).fill('I');
    
    let rowIdx = 0;
    
    for (const slot of EQUIPMENT_SLOTS_MILP) {
        const row = [];
        for (let j = 0; j < n; j++) {
            row.push(validItems[j].type === slot ? 1 : 0);
        }
        a.push(row);
        b.push(SLOT_LIMITS_MILP[slot]);
        types.push('U');
        rowIdx++;
    }
    
    if (maxPA > 0) {
        const row = [];
        for (let j = 0; j < n; j++) {
            row.push(validItems[j].pa || 0);
        }
        a.push(row);
        b.push(maxPA);
        types.push('U');
    }
    
    if (maxPM > 0) {
        const row = [];
        for (let j = 0; j < n; j++) {
            row.push(validItems[j].pm || 0);
        }
        a.push(row);
        b.push(maxPM);
        types.push('U');
    }
    
    console.log('MILP: Setting up model...');
    
    try {
        const model = {
            num_var: numVars,
            num_constr: numConstraints,
            a: a.flat(),
            b: b,
            c: c,
            types: types,
            names: names,
            integrality: integrality
        };
        
        const solution = await highs.solve(model);
        
        console.log('MILP: Solution status:', solution.Status);
        
        if (solution.Status === 'Optimal' || solution.Status === 'Feasible') {
            const selectedItems = [];
            
            for (let j = 0; j < n; j++) {
                const val = solution.primal_solution?.[j] || solution.value?.[j] || 0;
                if (val > 0.5) {
                    selectedItems.push(validItems[j]);
                }
            }
            
            console.log('MILP: Selected items:', selectedItems.length);
            
            const itemPA = selectedItems.reduce((s, i) => s + (i.pa || 0), 0);
            const itemPM = selectedItems.reduce((s, i) => s + (i.pm || 0), 0);
            console.log('MILP: itemPA =', itemPA, ', itemPM =', itemPM);
            
            return [createMilpResult(selectedItems, element)];
        }
        
        console.log('MILP: No feasible solution');
        return [];
        
    } catch (e) {
        console.error('MILP Error:', e);
        return [];
    }
}

function createMilpResult(items, element) {
    const baseScore = items.reduce((sum, item) => sum + getItemElementValue(item, element), 0);
    const setBonus = calculateSetBonusScore(items, element);
    const setDetails = getSetBonusDetails(items);
    
    return {
        items,
        totalElement: baseScore + setBonus,
        baseElement: baseScore,
        setBonus,
        setDetails
    };
}

function calculateSetBonusScore(items, element) {
    const setCounts = {};
    items.forEach(item => {
        if (item.set) {
            setCounts[item.set] = (setCounts[item.set] || 0) + 1;
        }
    });
    
    let totalBonus = 0;
    Object.entries(setCounts).forEach(([setName, count]) => {
        if (count >= 2) {
            const setData = SET_BONUSES[setName];
            if (setData) {
                const tiers = Object.keys(setData).map(Number).sort((a, b) => b - a);
                for (const tier of tiers) {
                    if (tier <= count) {
                        totalBonus += setData[tier][element] || 0;
                        break;
                    }
                }
            }
        }
    });
    
    return totalBonus;
}

function getSetBonusDetails(items) {
    const setCounts = {};
    items.forEach(item => {
        if (item.set) {
            setCounts[item.set] = (setCounts[item.set] || 0) + 1;
        }
    });
    
    const details = [];
    Object.entries(setCounts).forEach(([setName, count]) => {
        if (count >= 2) {
            const setData = SET_BONUSES[setName];
            if (setData) {
                const tiers = Object.keys(setData).map(Number).sort((a, b) => b - a);
                for (const tier of tiers) {
                    if (tier <= count) {
                        details.push({
                            setName,
                            pieces: count,
                            tier,
                            bonus: setData[tier]
                        });
                        break;
                    }
                }
            }
        }
    });
    
    return details;
}
