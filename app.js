const ELEMENT_COLORS = {
    vitalite: '#E74C3C',
    sagesse: '#9B59B6',
    force: '#E67E22',
    intelligence: '#3498DB',
    chance: '#2ECC71',
    agilite: '#F1C40F'
};

const ELEMENT_NAMES = {
    vitalite: 'Vitalité',
    sagesse: 'Sagesse',
    force: 'Force',
    intelligence: 'Intelligence',
    chance: 'Chance',
    agilite: 'Agilité'
};

let selectedElement = null;
let minLevel = 1;
let maxLevel = 200;

document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded');
    setupElementButtons();
    setupModal();
    
    const searchBtn = document.getElementById('searchBtn');
    console.log('Search button found:', searchBtn);
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            if (selectedElement) {
                runOptimization();
            }
        });
    }
});

function setupElementButtons() {
    const buttons = document.querySelectorAll('.element-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedElement = btn.dataset.element;
        });
    });
}

function setupModal() {
    const overlay = document.getElementById('modalOverlay');
    const closeBtn = document.getElementById('modalClose');

    closeBtn.addEventListener('click', () => {
        overlay.classList.remove('active');
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.classList.remove('active');
        }
    });
}

function runOptimization() {
    const levelInput = document.getElementById('playerLevel');
    const totalPAInput = document.getElementById('totalPA');
    const totalPMInput = document.getElementById('totalPM');
    
    const playerLevel = parseInt(levelInput.value) || 100;
    const totalPA = parseInt(totalPAInput.value) || 6;
    const totalPM = parseInt(totalPMInput.value) || 3;
    
    const basePA = playerLevel >= 100 ? 7 : 6;
    const basePM = 3;
    
    const minPAPool = Math.max(0, totalPA - basePA);
    const minPMPool = Math.max(0, totalPM - basePM);
    
    const results = optimizeGear(selectedElement, 1, playerLevel, minPAPool, minPMPool, ITEMS_RETRO, 10);
    
    results.forEach(r => {
        r.basePA = basePA;
        r.basePM = basePM;
    });
    displayResults(results);
}

function displayResults(results) {
    const resultsList = document.getElementById('resultsList');
    const resultsCount = document.getElementById('resultsCount');
    const emptyState = document.getElementById('emptyState');

    if (!results || results.length === 0 || !results[0] || !results[0].items || results[0].items.length === 0) {
        emptyState.style.display = 'flex';
        resultsCount.textContent = '0 combinaisons trouvées';
        resultsList.innerHTML = '';
        resultsList.appendChild(emptyState);
        return;
    }

    emptyState.style.display = 'none';
    resultsCount.textContent = results.length + ' combinaisons trouvées';
    
    resultsList.innerHTML = '';
    for (var i = 0; i < results.length; i++) {
        var r = results[i];
        
        var totalPA = (r.basePA || 6) + r.items.reduce(function(s,i){return s+(i.pa||0);},0);
        var totalPM = (r.basePM || 3) + r.items.reduce(function(s,i){return s+(i.pm||0);},0);
        
        var html = '<div class="result-card-new">';
        html += '<div class="result-header">';
        html += '<div class="result-rank">#' + (i+1) + '</div>';
        html += '<div class="result-main-stat">';
        html += '<span class="stat-name">' + ELEMENT_NAMES[selectedElement] + '</span>';
        html += '<span class="stat-value" style="color:' + ELEMENT_COLORS[selectedElement] + ';">' + r.totalElement + '</span>';
        html += '</div>';
        html += '</div>';
        
        html += '<div class="result-meta">';
        html += '<span class="meta-pa">PA: ' + totalPA + '</span>';
        html += '<span class="meta-pm">PM: ' + totalPM + '</span>';
        if (r.setBonus > 0) {
            html += '<span class="meta-set">+' + r.setBonus + ' set</span>';
        }
        html += '</div>';
        
        html += '<div class="result-all-stats">';
        const elements = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite'];
        elements.forEach(function(el) {
            const total = r.totalStats[el] || 0;
            if (total !== 0) {
                const base = r.baseStats[el] || 0;
                const setB = r.setBonuses[el] || 0;
                let statText = '<span class="all-stat" style="color:' + ELEMENT_COLORS[el] + ';">';
                statText += ELEMENT_NAMES[el] + ': ' + (total > 0 ? '+' : '') + total;
                if (setB > 0) {
                    statText += ' <small>(' + base + ' + ' + setB + ' set)</small>';
                }
                statText += '</span>';
                html += statText;
            }
        });
        html += '</div>';
        
        html += '<div class="result-items-grid">';
        for (var j = 0; j < r.items.length; j++) {
            var item = r.items[j];
            var itemStats = [];
            for (var key in item.elements) {
                if (item.elements[key] !== 0) {
                    var prefix = item.elements[key] > 0 ? '+' : '';
                    itemStats.push('<span style="color:' + ELEMENT_COLORS[key] + ';">' + prefix + item.elements[key] + '</span>');
                }
            }
            html += '<div class="item-card">';
            html += '<div class="item-header">';
            html += '<span class="item-type">' + getTypeAbbrev(item.type) + '</span>';
            html += '<span class="item-level">Lvl ' + item.level + '</span>';
            html += '</div>';
            html += '<div class="item-name">' + item.name + '</div>';
            if (item.set) {
                html += '<div class="item-set">' + item.set + '</div>';
            }
            html += '<div class="item-stats">';
            if (item.pa > 0 || item.pm > 0) {
                html += '<span class="item-papm">' + (item.pa > 0 ? '+' + item.pa + ' PA' : '') + ' ' + (item.pm > 0 ? '+' + item.pm + ' PM' : '') + '</span>';
            }
            html += itemStats.join(' ');
            html += '</div>';
            html += '</div>';
        }
        html += '</div></div>';
        
        resultsList.insertAdjacentHTML('beforeend', html);
    }
}

function createResultCard(result, rank) {
    let html = '<div style="border:2px solid purple;padding:20px;margin:10px;background:#fff;color:#000;">';
    html += '<h2>Combinaison ' + rank + '</h2>';
    html += '<p><b>Total ' + selectedElement + ':</b> ' + result.totalElement + '</p>';
    html += '<p><b>Items:</b></p><ul>';
    for (let i = 0; i < result.items.length; i++) {
        var item = result.items[i];
        html += '<li>' + item.name + ' (Lvl ' + item.level + ')';
        if (item.pa) html += ' PA+' + item.pa;
        if (item.pm) html += ' PM+' + item.pm;
        html += '</li>';
    }
    html += '</ul></div>';
    return html;
}

function calculateAllStats(items) {
    const totals = {
        vitalite: 0,
        sagesse: 0,
        force: 0,
        intelligence: 0,
        chance: 0,
        agilite: 0,
        pa: 0,
        pm: 0
    };
    items.forEach(item => {
        Object.keys(totals).forEach(stat => {
            if (stat === 'pa' || stat === 'pm') {
                totals[stat] += item[stat] || 0;
            } else {
                totals[stat] += item.elements[stat] || 0;
            }
        });
    });
    return totals;
}

function createItemChip(item) {
    const typeAbbrev = getTypeAbbrev(item.type);
    
    const elementLines = Object.entries(item.elements)
        .map(([key, value]) => {
            const color = ELEMENT_COLORS[key];
            const name = ELEMENT_NAMES[key];
            const prefix = value > 0 ? '+' : '';
            return `<div style="color: ${color}; font-size: 0.75rem;">${name}: ${prefix}${value}</div>`;
        })
        .join('');
    
    const paPmLine = [];
    if (item.pa > 0) paPmLine.push(`<span style="color: #3498DB;">PA: +${item.pa}</span>`);
    if (item.pm > 0) paPmLine.push(`<span style="color: #2ECC71;">PM: +${item.pm}</span>`);
    const paPmHtml = paPmLine.length > 0 ? `<div class="item-pa-pm">${paPmLine.join(' &nbsp; ')}</div>` : '';

    return `
        <div class="item-chip-full">
            <div class="item-chip-header">
                <span class="item-chip-type">${typeAbbrev}</span>
                <span class="item-chip-level">Lvl ${item.level}</span>
            </div>
            <div class="item-chip-name">${item.name}</div>
            ${item.set ? `<div class="item-chip-set">${item.set}</div>` : ''}
            ${paPmHtml}
            <div class="item-chip-stats">
                ${elementLines}
            </div>
        </div>
    `;
}

function createSetBadge(setDetails) {
    if (!setDetails || setDetails.length === 0) return '';
    
    return setDetails.map(set => `
        <span class="set-name">
            ${set.setName} (${set.pieces})
        </span>
    `).join('');
}

function createItemChip(item) {
    const elementValue = item.elements[selectedElement] || 0;
    const typeAbbrev = getTypeAbbrev(item.type);

    return `
        <div class="item-chip" style="--element-color: ${ELEMENT_COLORS[selectedElement]}">
            <div class="item-type-icon">${typeAbbrev}</div>
            <div class="item-info">
                <div class="item-name" title="${item.name}">${item.name}</div>
                <div class="item-level">Niv ${item.level}${item.set ? ` • ${item.set}` : ''}</div>
            </div>
            ${elementValue > 0 ? `<div class="item-element" style="color: ${ELEMENT_COLORS[selectedElement]}">+${elementValue}</div>` : ''}
        </div>
    `;
}

function getTypeAbbrev(type) {
    const abbrevs = {
        weapon: 'ARME',
        hat: 'CHAP',
        cloak: 'CAPE',
        amulet: 'AMUL',
        ring: 'BAGU',
        belt: 'CEIN',
        boots: 'BOTT',
        shield: 'BOUC'
    };
    return abbrevs[type] || type.slice(0, 3).toUpperCase();
}

function getTypeName(type) {
    const names = {
        weapon: 'Arme',
        hat: 'Chapeau',
        cloak: 'Cape',
        amulet: 'Amulette',
        ring: 'Anneau',
        belt: 'Ceinture',
        boots: 'Bottes',
        shield: 'Bouclier'
    };
    return names[type] || type;
}

function getSetNames(items) {
    const sets = items.filter(item => item.set).map(item => item.set);
    const uniqueSets = [...new Set(sets)];
    return uniqueSets.join(', ');
}

function openModal(result) {
    const modal = document.getElementById('itemModal');
    const content = document.getElementById('modalContent');
    const overlay = document.getElementById('modalOverlay');

    content.innerHTML = `
        <h2 class="modal-title">Set ${ELEMENT_NAMES[selectedElement]}</h2>
        <p class="modal-subtitle">
            <strong>Total ${ELEMENT_NAMES[selectedElement]}:</strong> <span style="color: ${ELEMENT_COLORS[selectedElement]}; font-size: 1.3em; font-weight: bold;">${result.totalElement}</span>
            <br>
            <small style="color: var(--text-secondary);">
                Base: ${result.baseElement} | Bonus Set: +${result.setBonus}
            </small>
        </p>
        ${result.setDetails.length > 0 ? `
            <div class="modal-set-details">
                <h4>Bonus des Sets</h4>
                ${result.setDetails.map(set => `
                    <div class="set-detail-row">
                        <span class="set-detail-name">${set.setName}</span>
                        <span class="set-detail-pieces">${set.pieces} pièces (Tier ${set.tier})</span>
                        <span class="set-detail-bonus">+${set.bonus[selectedElement] || 0} ${ELEMENT_NAMES[selectedElement]}</span>
                    </div>
                `).join('')}
            </div>
        ` : ''}
        <div class="modal-items">
            ${result.items.map(item => createModalItem(item)).join('')}
        </div>
    `;

    overlay.classList.add('active');
}

function createModalItem(item) {
    return `
        <div class="modal-item">
            <div class="modal-item-header">
                <span class="modal-item-type">${getTypeName(item.type)}</span>
                <span class="modal-item-name">${item.name}</span>
                ${item.set ? `<span class="modal-item-type" style="background: var(--secondary); color: var(--background)">${item.set}</span>` : ''}
            </div>
            <div class="modal-item-stats">
                <div class="stat-box">
                    <div class="stat-label">Niveau</div>
                    <div class="stat-value">${item.level}</div>
                </div>
                ${Object.entries(item.elements).map(([elem, val]) => `
                    ${val > 0 ? `
                        <div class="stat-box">
                            <div class="stat-label">${ELEMENT_NAMES[elem]}</div>
                            <div class="stat-value ${elem}">+${val}</div>
                        </div>
                    ` : ''}
                `).join('')}
            </div>
        </div>
    `;
}
