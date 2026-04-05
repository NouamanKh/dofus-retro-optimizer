/**
 * MILP Optimizer using javascript-lp-solver
 */

const SLOT_LIMITS_MILP = { "weapon": 1, "hat": 1, "cloak": 1, "amulet": 1, "ring": 2, "belt": 1, "boots": 1 };
const EQUIPMENT_SLOTS_MILP = Object.keys(SLOT_LIMITS_MILP);

function getItemElementValue(item, element) {
    return item.elements[element] || 0;
}

function optimizeMilp(element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items, maxResults = 10) {
    console.log('MILP: Starting for', element);
    
    const validItems = items.filter(item => 
        EQUIPMENT_SLOTS_MILP.includes(item.type) && 
        item.level >= minLevel && 
        item.level <= maxLevel
    );
    
    console.log('MILP: Valid items:', validItems.length);
    
    const model = {
        optimize: 'value',
        opType: 'max',
        constraints: {},
        variables: {},
        ints: {}
    };
    
    for (const slot of EQUIPMENT_SLOTS_MILP) {
        model.constraints['slot_' + slot] = { max: SLOT_LIMITS_MILP[slot] };
    }
    
    if (minPA > 0) {
        model.constraints.pa_min = { min: minPA };
    }
    
    if (minPM > 0) {
        model.constraints.pm_min = { min: minPM };
    }
    
    model.constraints.max_items = { max: 10 };
    
    for (const item of validItems) {
        const varName = 'item_' + item.id;
        
        model.variables[varName] = {
            value: getItemElementValue(item, element),
            slot: 1,
            max_items: 1,
            ['slot_' + item.type]: 1
        };
        
        if (item.pa > 0) {
            model.variables[varName].pa_min = item.pa;
        }
        if (item.pm > 0) {
            model.variables[varName].pm_min = item.pm;
        }
        
        model.ints[varName] = 1;
    }
    
    console.log('MILP: Model ready, solving...');
    console.log('MILP: Constraints:', model.constraints);
    
    try {
        const result = solver.Solve(model);
        console.log('MILP: Result status:', result.status);
        
        if (result.status === 'Optimal' || result.result !== undefined) {
            const selectedItems = [];
            
            for (const [varName, value] of Object.entries(result)) {
                if (varName.startsWith('item_') && value >= 1) {
                    const itemId = varName.replace('item_', '');
                    const item = validItems.find(i => i.id === itemId);
                    if (item) selectedItems.push(item);
                }
            }
            
            console.log('MILP: Selected items:', selectedItems.length);
            
            return [createMilpResult(selectedItems, element)];
        }
        
        console.log('MILP: No solution found');
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
