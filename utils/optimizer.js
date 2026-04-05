const EQUIPMENT_SLOTS = ['weapon', 'hat', 'cloak', 'amulet', 'ring', 'belt', 'boots'];

const SLOT_LIMITS = {
    weapon: 1,
    hat: 1,
    cloak: 1,
    amulet: 1,
    ring: 2,
    belt: 1,
    boots: 1
};

// Convert SETS_RETRO to a more usable format
const SET_BONUSES = {};
SETS_RETRO.forEach(set => {
    SET_BONUSES[set.name] = {};
    set.bonus.forEach((bonusArr, index) => {
        if (bonusArr.length > 0) {
            const tierNum = index + 2; // bonus[0] is empty, bonus[1] is for 2 items, etc.
            const bonusObj = {};
            bonusArr.forEach(b => {
                const statKey = normalizeStat(b.type);
                if (statKey) {
                    bonusObj[statKey] = parseInt(b.value) || 0;
                }
            });
            SET_BONUSES[set.name][tierNum] = bonusObj;
        }
    });
});

function normalizeStat(stat) {
    if (!stat) return null;
    const lower = stat.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    if (lower.includes('vitalit')) return 'vitalite';
    if (lower.includes('sagesse')) return 'sagesse';
    if (lower.includes('force')) return 'force';
    if (lower.includes('intelligence')) return 'intelligence';
    if (lower.includes('chance')) return 'chance';
    if (lower.includes('agilit')) return 'agilite';
    return null;
}

function getItemsBySlot(items) {
    const bySlot = {};
    items.forEach(item => {
        if (!bySlot[item.type]) {
            bySlot[item.type] = [];
        }
        bySlot[item.type].push(item);
    });
    return bySlot;
}

function getItemElementValue(item, element) {
    return item.elements[element] || 0;
}

function calculateSetBonus(setItems, element) {
    const setCounts = {};
    setItems.forEach(item => {
        if (item.set) {
            setCounts[item.set] = (setCounts[item.set] || 0) + 1;
        }
    });

    let totalBonus = 0;
    
    Object.entries(setCounts).forEach(([setName, count]) => {
        const setData = SET_BONUSES[setName];
        if (setData && count >= 2) {
            // Find the highest tier that's <= count
            const tiers = Object.keys(setData).map(Number).sort((a, b) => b - a);
            for (const tier of tiers) {
                if (tier <= count) {
                    const tierBonus = setData[tier];
                    if (tierBonus && tierBonus[element]) {
                        totalBonus += tierBonus[element];
                    }
                    break;
                }
            }
        }
    });
    
    return totalBonus;
}

function getSetBonusDetails(setItems) {
    const setCounts = {};
    setItems.forEach(item => {
        if (item.set) {
            setCounts[item.set] = (setCounts[item.set] || 0) + 1;
        }
    });

    const bonuses = [];
    Object.entries(setCounts).forEach(([setName, count]) => {
        const setData = SET_BONUSES[setName];
        if (setData && count >= 2) {
            const tiers = Object.keys(setData).map(Number).sort((a, b) => b - a);
            let activeTier = null;
            for (const tier of tiers) {
                if (tier <= count) {
                    activeTier = tier;
                    break;
                }
            }
            
            if (activeTier) {
                bonuses.push({
                    setName,
                    pieces: count,
                    tier: activeTier,
                    bonus: setData[activeTier]
                });
            }
        }
    });
    
    return bonuses;
}

function greedySelectItems(element, minLevel, maxLevel, minPA, minPM, items) {
    const bySlot = getItemsBySlot(items);
    const selected = [];
    const slotCounts = {};
    
    Object.keys(SLOT_LIMITS).forEach(slot => {
        slotCounts[slot] = 0;
    });

    const itemsBySlot = {};
    Object.entries(bySlot).forEach(([slot, slotItems]) => {
        const filtered = slotItems.filter(item => 
            item.level >= minLevel && 
            item.level <= maxLevel &&
            getItemElementValue(item, element) >= -100
        );
        itemsBySlot[slot] = filtered
            .map(item => ({
                ...item,
                elementValue: getItemElementValue(item, element)
            }))
            .sort((a, b) => b.elementValue - a.elementValue);
    });

    for (let iteration = 0; iteration < 3; iteration++) {
        for (const slot of EQUIPMENT_SLOTS) {
            const limit = SLOT_LIMITS[slot];
            const currentCount = slotCounts[slot] || 0;
            
            if (currentCount >= limit) continue;
            
            const available = itemsBySlot[slot] || [];
            const alreadySelected = selected.filter(s => s.type === slot).map(s => s.id);
            const remaining = available.filter(item => !alreadySelected.includes(item.id));
            
            if (remaining.length === 0) continue;
            
            let bestItem = null;
            let bestScore = -Infinity;
            
            for (const item of remaining) {
                const testSelection = [...selected, item];
                const baseScore = testSelection.reduce((sum, i) => sum + getItemElementValue(i, element), 0);
                const setBonus = calculateSetBonus(testSelection, element);
                const totalScore = baseScore + setBonus;
                
                if (totalScore > bestScore) {
                    bestScore = totalScore;
                    bestItem = item;
                }
            }
            
            if (bestItem) {
                selected.push(bestItem);
                slotCounts[slot]++;
            }
        }
    }

    return { selected, itemsBySlot };
}

function ensurePAPMConstraint(result, minPA, minPM) {
    const { selected, itemsBySlot } = result;
    
    const totalItemPA = selected.reduce((sum, i) => sum + (i.pa || 0), 0);
    const totalItemPM = selected.reduce((sum, i) => sum + (i.pm || 0), 0);
    
    let needsPA = minPA - totalItemPA;
    let needsPM = minPM - totalItemPM;
    
    if (needsPA <= 0 && needsPM <= 0) return selected;
    
    for (const slot of EQUIPMENT_SLOTS) {
        if (needsPA <= 0 && needsPM <= 0) break;
        
        const slotItems = itemsBySlot[slot] || [];
        const currentItem = selected.find(s => s.type === slot);
        
        let bestSwap = null;
        let bestSwapGain = -Infinity;
        
        for (const item of slotItems) {
            if (currentItem && item.id === currentItem.id) continue;
            
            const gainPA = (item.pa || 0) - (currentItem ? (currentItem.pa || 0) : 0);
            const gainPM = (item.pm || 0) - (currentItem ? (currentItem.pm || 0) : 0);
            
            const helpsPA = needsPA > 0 && gainPA > 0;
            const helpsPM = needsPM > 0 && gainPM > 0;
            
            if (helpsPA || helpsPM) {
                const totalGain = gainPA + gainPM;
                if (totalGain > bestSwapGain) {
                    bestSwapGain = totalGain;
                    bestSwap = item;
                }
            }
        }
        
        if (bestSwap) {
            if (currentItem) {
                const idx = selected.findIndex(s => s.id === currentItem.id);
                selected[idx] = bestSwap;
            } else {
                selected.push(bestSwap);
            }
            needsPA -= (bestSwap.pa || 0);
            needsPM -= (bestSwap.pm || 0);
        }
    }
    
    return selected;
}

function localSearchImprove(selected, element, minLevel, maxLevel, minPA, minPM, items) {
    let best = [...selected];
    let improved = true;
    let iterations = 0;
    const maxIterations = 100;
    
    while (improved && iterations < maxIterations) {
        improved = false;
        iterations++;
        
        const currentScore = calculateTotalScore(best, element);
        
        for (let i = 0; i < best.length; i++) {
            const removedItem = best[i];
            const otherItems = best.filter((_, idx) => idx !== i);
            
            const bySlot = getItemsBySlot(items);
            const slotItems = (bySlot[removedItem.type] || [])
                .filter(item => 
                    item.level >= minLevel && 
                    item.level <= maxLevel &&
                    getItemElementValue(item, element) >= -100 &&
                    item.id !== removedItem.id &&
                    !otherItems.some(sel => sel.id === item.id)
                );
            
            for (const candidate of slotItems) {
                const testSet = [...otherItems, candidate];
                const testScore = calculateTotalScore(testSet, element);
                
                if (testScore > currentScore) {
                    best = testSet;
                    improved = true;
                    break;
                }
            }
            
            if (improved) break;
        }
    }
    
    return best;
}

function calculateTotalScore(items, element) {
    const baseScore = items.reduce((sum, item) => sum + getItemElementValue(item, element), 0);
    const setBonus = calculateSetBonus(items, element);
    return baseScore + setBonus;
}

function tryAddSetPiece(selected, element, minLevel, maxLevel, items) {
    const bySlot = getItemsBySlot(items);
    
    const currentSets = {};
    selected.forEach(item => {
        if (item.set) {
            currentSets[item.set] = (currentSets[item.set] || 0) + 1;
        }
    });

    const potentialUpgrades = [];
    
    for (const [setName, count] of Object.entries(currentSets)) {
        const setData = SET_BONUSES[setName];
        if (!setData) continue;
        
        const tiers = Object.keys(setData).map(Number).sort((a, b) => b - a);
        let activeTier = null;
        for (const tier of tiers) {
            if (tier <= count) {
                activeTier = tier;
                break;
            }
        }
        
        if (activeTier) {
            for (const [potentialTier, bonus] of Object.entries(setData)) {
                const tierNum = parseInt(potentialTier);
                if (tierNum > count) {
                    const currentBonus = setData[activeTier]?.[element] || 0;
                    const potentialBonus = bonus[element] || 0;
                    
                    if (potentialBonus > currentBonus) {
                        for (const slot of EQUIPMENT_SLOTS) {
                            const slotItems = bySlot[slot] || [];
                            for (const item of slotItems) {
                                if (item.set === setName && 
                                    item.level >= minLevel && 
                                    item.level <= maxLevel &&
                                    getItemElementValue(item, element) >= -100 &&
                                    !selected.some(s => s.id === item.id)) {
                                    potentialUpgrades.push({
                                        item,
                                        bonusGain: potentialBonus - currentBonus
                                    });
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    potentialUpgrades.sort((a, b) => b.bonusGain - a.bonusGain);
    
    for (const upgrade of potentialUpgrades) {
        const slotItems = selected.filter(s => s.type === upgrade.item.type);
        const slotLimit = SLOT_LIMITS[upgrade.item.type];
        
        if (slotItems.length < slotLimit) {
            const testSet = [...selected, upgrade.item];
            const testScore = calculateTotalScore(testSet, element);
            const currentScore = calculateTotalScore(selected, element);
            
            if (testScore > currentScore) {
                return upgrade.item;
            }
        }
    }
    
    return null;
}

function optimizeGear(element, minLevel, maxLevel, minPA, minPM, items, maxResults = 10) {
    const greedyResult = greedySelectItems(element, minLevel, maxLevel, minPA, minPM, items);
    let currentItems = ensurePAPMConstraint(greedyResult, minPA, minPM);
    let improved = localSearchImprove(currentItems, element, minLevel, maxLevel, minPA, minPM, items);
    improved = ensurePAPMConstraint({ selected: improved, itemsBySlot: getItemsBySlot(items) }, minPA, minPM);
    
    let currentBest = improved;
    
    for (let i = 0; i < 5; i++) {
        const newPiece = tryAddSetPiece(currentBest, element, minLevel, maxLevel, items);
        if (newPiece) {
            currentBest = [...currentBest, newPiece];
        }
    }
    
    let finalSet = localSearchImprove(currentBest, element, minLevel, maxLevel, minPA, minPM, items);
    finalSet = ensurePAPMConstraint({ selected: finalSet, itemsBySlot: getItemsBySlot(items) }, minPA, minPM);
    
    const results = [createResult(finalSet, element)];
    
    for (let r = 0; r < 3; r++) {
        let randomized = addRandomVariation(finalSet, element, minLevel, maxLevel, items);
        randomized = ensurePAPMConstraint({ selected: randomized, itemsBySlot: getItemsBySlot(items) }, minPA, minPM);
        let improved2 = localSearchImprove(randomized, element, minLevel, maxLevel, minPA, minPM, items);
        improved2 = ensurePAPMConstraint({ selected: improved2, itemsBySlot: getItemsBySlot(items) }, minPA, minPM);
        results.push(createResult(improved2, element));
    }
    
    results.sort((a, b) => b.totalElement - a.totalElement);
    
    return results.slice(0, maxResults);
}

function addRandomVariation(baseSet, element, minLevel, maxLevel, items) {
    const bySlot = getItemsBySlot(items);
    const result = [...baseSet];
    
    const slotsToModify = EQUIPMENT_SLOTS.filter(slot => Math.random() > 0.5);
    
    for (const slot of slotsToModify) {
        const currentItem = result.find(s => s.type === slot);
        const slotItems = (bySlot[slot] || [])
            .filter(item => 
                item.level >= minLevel && 
                item.level <= maxLevel &&
                getItemElementValue(item, element) >= -100 &&
                item.id !== currentItem?.id
            );
        
        if (slotItems.length > 0 && Math.random() > 0.3) {
            const randomItem = slotItems[Math.floor(Math.random() * slotItems.length)];
            if (currentItem) {
                const idx = result.findIndex(s => s.id === currentItem.id);
                result[idx] = randomItem;
            } else {
                result.push(randomItem);
            }
        }
    }
    
    return result;
}

function createResult(items, element) {
    const baseScore = items.reduce((sum, item) => sum + getItemElementValue(item, element), 0);
    const setBonus = calculateSetBonus(items, element);
    const setDetails = getSetBonusDetails(items);
    const avgLevel = items.length > 0 ? Math.round(items.reduce((sum, item) => sum + item.level, 0) / items.length) : 0;
    
    return {
        items,
        totalElement: baseScore + setBonus,
        baseElement: baseScore,
        setBonus,
        setDetails,
        avgLevel
    };
}
