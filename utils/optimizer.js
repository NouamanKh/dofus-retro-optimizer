const EQUIPMENT_SLOTS = ['weapon', 'hat', 'cloak', 'amulet', 'ring', 'belt', 'boots', 'shield'];

const SLOT_LIMITS = {
    weapon: 1,
    hat: 1,
    cloak: 1,
    amulet: 1,
    ring: 2,
    belt: 1,
    boots: 1,
    shield: 1
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

function greedySelectItems(element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items) {
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
                const testPA = testSelection.reduce((s, i) => s + (i.pa || 0), 0);
                const testPM = testSelection.reduce((s, i) => s + (i.pm || 0), 0);
                
                if (testPA > maxPA || testPM > maxPM) continue;
                
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

function ensurePAPMConstraint(result, minPA, minPM, maxPA, maxPM) {
    const { selected, itemsBySlot } = result;
    
    const totalItemPA = selected.reduce((sum, i) => sum + (i.pa || 0), 0);
    const totalItemPM = selected.reduce((sum, i) => sum + (i.pm || 0), 0);
    
    if (totalItemPA >= minPA && totalItemPM >= minPM && totalItemPA <= maxPA && totalItemPM <= maxPM) {
        return selected;
    }
    
    let needsPA = minPA - totalItemPA;
    let needsPM = minPM - totalItemPM;
    
    for (const slot of EQUIPMENT_SLOTS) {
        if (needsPA <= 0 && needsPM <= 0) break;
        
        const slotItems = itemsBySlot[slot] || [];
        const currentItem = selected.find(s => s.type === slot);
        
        let bestSwap = null;
        let bestSwapGain = -Infinity;
        
        for (const item of slotItems) {
            if (currentItem && item.id === currentItem.id) continue;
            
            const newPA = totalItemPA - (currentItem ? (currentItem.pa || 0) : 0) + (item.pa || 0);
            const newPM = totalItemPM - (currentItem ? (currentItem.pm || 0) : 0) + (item.pm || 0);
            
            if (newPA > maxPA || newPM > maxPM) continue;
            
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

function checkPAPMBetween(selected, minPA, minPM, maxPA, maxPM) {
    const totalPA = selected.reduce((sum, i) => sum + (i.pa || 0), 0);
    const totalPM = selected.reduce((sum, i) => sum + (i.pm || 0), 0);
    return totalPA >= minPA && totalPA <= maxPA && totalPM >= minPM && totalPM <= maxPM;
}

function enforcePAPMLimit(selected, minPA, minPM, maxPA, maxPM, items) {
    let result = [...selected];
    const bySlot = getItemsBySlot(items);
    
    let totalPA = result.reduce((s, i) => s + (i.pa || 0), 0);
    let totalPM = result.reduce((s, i) => s + (i.pm || 0), 0);
    
    while (totalPA > maxPA || totalPM > maxPM) {
        let worstItem = null;
        let worstGain = Infinity;
        
        for (const item of result) {
            const gain = (item.pa || 0) + (item.pm || 0);
            if (gain < worstGain) {
                worstGain = gain;
                worstItem = item;
            }
        }
        
        if (worstItem) {
            result = result.filter(i => i.id !== worstItem.id);
            totalPA -= (worstItem.pa || 0);
            totalPM -= (worstItem.pm || 0);
        } else {
            break;
        }
    }
    
    while (totalPA < minPA || totalPM < minPM) {
        let bestItem = null;
        let bestGain = -Infinity;
        
        for (const slot of EQUIPMENT_SLOTS) {
            const slotItems = bySlot[slot] || [];
            for (const item of slotItems) {
                if (result.some(r => r.id === item.id)) continue;
                
                const newPA = totalPA + (item.pa || 0);
                const newPM = totalPM + (item.pm || 0);
                
                if (newPA > maxPA || newPM > maxPM) continue;
                
                const gain = (item.pa || 0) + (item.pm || 0);
                if (gain > bestGain) {
                    bestGain = gain;
                    bestItem = item;
                }
            }
        }
        
        if (bestItem) {
            result.push(bestItem);
            totalPA += (bestItem.pa || 0);
            totalPM += (bestItem.pm || 0);
        } else {
            break;
        }
    }
    
    return result;
}

function localSearchImprove(selected, element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items) {
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
                const testPA = testSet.reduce((s, it) => s + (it.pa || 0), 0);
                const testPM = testSet.reduce((s, it) => s + (it.pm || 0), 0);
                
                if (testPA > maxPA || testPM > maxPM) continue;
                
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

function optimizeGear(element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items, maxResults = 10) {
    const greedyResult = greedySelectItems(element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items);
    let currentItems = ensurePAPMConstraint(greedyResult, minPA, minPM, maxPA, maxPM);
    let improved = localSearchImprove(currentItems, element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items);
    improved = ensurePAPMConstraint({ selected: improved, itemsBySlot: getItemsBySlot(items) }, minPA, minPM, maxPA, maxPM);
    
    let currentBest = improved;
    
    for (let i = 0; i < 5; i++) {
        const newPiece = tryAddSetPiece(currentBest, element, minLevel, maxLevel, items);
        if (newPiece) {
            currentBest = [...currentBest, newPiece];
        }
    }
    
    let finalSet = localSearchImprove(currentBest, element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items);
    finalSet = ensurePAPMConstraint({ selected: finalSet, itemsBySlot: getItemsBySlot(items) }, minPA, minPM, maxPA, maxPM);
    
    if (!checkPAPMBetween(finalSet, minPA, minPM, maxPA, maxPM)) {
        finalSet = enforcePAPMLimit(finalSet, minPA, minPM, maxPA, maxPM, items);
    }
    
    const allCombos = new Map();
    
    function addCombo(items) {
        const totalPA = items.reduce((s, i) => s + (i.pa || 0), 0);
        const totalPM = items.reduce((s, i) => s + (i.pm || 0), 0);
        
        if (totalPA > maxPA || totalPM > maxPM) return;
        if (totalPA < minPA || totalPM < minPM) return;
        
        const ids = items.map(i => i.id).sort().join('|');
        if (!allCombos.has(ids)) {
            const result = createResult(items, element);
            allCombos.set(ids, result);
        }
    }
    
    addCombo(finalSet);
    
    for (let r = 0; r < 20; r++) {
        let randomized = addRandomVariation(finalSet, element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items);
        randomized = ensurePAPMConstraint({ selected: randomized, itemsBySlot: getItemsBySlot(items) }, minPA, minPM, maxPA, maxPM);
        let improved2 = localSearchImprove(randomized, element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items);
        improved2 = ensurePAPMConstraint({ selected: improved2, itemsBySlot: getItemsBySlot(items) }, minPA, minPM, maxPA, maxPM);
        
        if (checkPAPMBetween(improved2, minPA, minPM, maxPA, maxPM)) {
            addCombo(improved2);
        }
    }
    
    const results = Array.from(allCombos.values());
    results.sort((a, b) => b.totalElement - a.totalElement);
    
    return results.slice(0, maxResults);
}

function addRandomVariation(baseSet, element, minLevel, maxLevel, minPA, minPM, maxPA, maxPM, items) {
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
            
            const currentPA = result.reduce((s, i) => s + (i.pa || 0), 0);
            const currentPM = result.reduce((s, i) => s + (i.pm || 0), 0);
            const newPA = currentPA - (currentItem ? (currentItem.pa || 0) : 0) + (randomItem.pa || 0);
            const newPM = currentPM - (currentItem ? (currentItem.pm || 0) : 0) + (randomItem.pm || 0);
            
            if (newPA <= maxPA && newPM <= maxPM) {
                if (currentItem) {
                    const idx = result.findIndex(s => s.id === currentItem.id);
                    result[idx] = randomItem;
                } else {
                    result.push(randomItem);
                }
            }
        }
    }
    
    return result;
}

function createResult(items, element) {
    const elements = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite'];
    
    const baseStats = { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 0, agilite: 0 };
    items.forEach(item => {
        elements.forEach(el => {
            baseStats[el] += item.elements[el] || 0;
        });
    });
    
    const setBonuses = calculateAllSetBonuses(items);
    
    const totalStats = {};
    elements.forEach(el => {
        totalStats[el] = baseStats[el] + (setBonuses[el] || 0);
    });
    
    const baseScore = baseStats[element];
    const setBonus = setBonuses[element] || 0;
    const setDetails = getSetBonusDetails(items);
    const avgLevel = items.length > 0 ? Math.round(items.reduce((sum, item) => sum + item.level, 0) / items.length) : 0;
    
    return {
        items,
        totalElement: baseScore + setBonus,
        baseElement: baseScore,
        setBonus,
        setDetails,
        avgLevel,
        baseStats,
        setBonuses,
        totalStats
    };
}

function calculateAllSetBonuses(items) {
    const elements = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite'];
    const setCounts = {};
    items.forEach(item => {
        if (item.set) {
            setCounts[item.set] = (setCounts[item.set] || 0) + 1;
        }
    });
    
    const bonuses = { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 0, agilite: 0 };
    
    Object.entries(setCounts).forEach(([setName, count]) => {
        if (count >= 2) {
            const setData = SET_BONUSES[setName];
            if (setData) {
                const tiers = Object.keys(setData).map(Number).sort((a, b) => b - a);
                for (const tier of tiers) {
                    if (tier <= count) {
                        elements.forEach(el => {
                            bonuses[el] += setData[tier][el] || 0;
                        });
                        break;
                    }
                }
            }
        }
    });
    
    return bonuses;
}
