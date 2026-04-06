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

const API_URL = 'http://localhost:5000';

let selectedElement = null;

document.addEventListener('DOMContentLoaded', () => {
    setupElementButtons();
    setupModal();
    checkServerStatus();

    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            if (selectedElement) runOptimization();
        });
    }
});

async function checkServerStatus() {
    const el = document.getElementById('serverStatus');
    try {
        const res = await fetch(`${API_URL}/api/health`);
        if (res.ok) {
            el.textContent = '⬤ Serveur connecté';
            el.className = 'server-status online';
        } else {
            throw new Error();
        }
    } catch {
        el.textContent = '⬤ Serveur hors ligne';
        el.className = 'server-status offline';
    }
}

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

    closeBtn.addEventListener('click', () => overlay.classList.remove('active'));
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('active');
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') overlay.classList.remove('active');
    });
}

function setLoading(isLoading) {
    const btn = document.getElementById('searchBtn');
    const spinner = document.getElementById('loadingSpinner');
    btn.disabled = isLoading;
    btn.textContent = isLoading ? 'Recherche en cours...' : 'Rechercher';
    if (spinner) spinner.style.display = isLoading ? 'flex' : 'none';
}

async function runOptimization() {
    const playerLevel = parseInt(document.getElementById('playerLevel').value) || 100;
    const totalPA     = parseInt(document.getElementById('totalPA').value) || 6;
    const totalPM     = parseInt(document.getElementById('totalPM').value) || 3;
    const exoPA       = parseInt(document.getElementById('exoPA').value) || 0;
    const exoPM       = parseInt(document.getElementById('exoPM').value) || 0;

    const basePA = playerLevel >= 100 ? 7 : 6;
    const basePM = 3;

    const maxItemPA = Math.max(0, totalPA - basePA - exoPA);
    const maxItemPM = Math.max(0, totalPM - basePM - exoPM);
    const minItemPA = maxItemPA;
    const minItemPM = maxItemPM;

    setLoading(true);

    try {
        const response = await fetch(`${API_URL}/api/optimize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                element: selectedElement,
                maxLevel: playerLevel,
                minPA: minItemPA,
                minPM: minItemPM,
                maxPA: maxItemPA,
                maxPM: maxItemPM,
                maxResults: 10
            })
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const results = await response.json();

        results.forEach(r => {
            r.basePA = basePA;
            r.basePM = basePM;
            r.exoPA  = exoPA;
            r.exoPM  = exoPM;
        });

        displayResults(results);
    } catch (err) {
        console.error('Optimization error:', err);
        showError('Impossible de contacter le serveur. Assurez-vous que server.py tourne sur le port 5000.');
    } finally {
        setLoading(false);
    }
}

function showError(msg) {
    const resultsList = document.getElementById('resultsList');
    const resultsCount = document.getElementById('resultsCount');
    resultsCount.textContent = 'Erreur';
    resultsList.innerHTML = `<div class="error-state"><p>${msg}</p></div>`;
}

function displayResults(results) {
    const resultsList = document.getElementById('resultsList');
    const resultsCount = document.getElementById('resultsCount');
    const emptyState = document.getElementById('emptyState');

    if (!results || results.length === 0 || !results[0]?.items?.length) {
        emptyState.style.display = 'flex';
        resultsCount.textContent = '0 combinaisons trouvées';
        resultsList.innerHTML = '';
        resultsList.appendChild(emptyState);
        return;
    }

    emptyState.style.display = 'none';
    resultsCount.textContent = `${results.length} combinaisons trouvées (MILP Optimal)`;

    resultsList.innerHTML = '';
    results.forEach((r, i) => {
        const itemPA   = r.items.reduce((s, it) => s + (it.pa || 0), 0);
        const itemPM   = r.items.reduce((s, it) => s + (it.pm || 0), 0);
        const totalPA  = (r.basePA || 6) + (r.exoPA || 0) + itemPA;
        const totalPM  = (r.basePM || 3) + (r.exoPM || 0) + itemPM;

        const elements = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite'];

        const allStatsHtml = elements
            .filter(el => (r.totalStats[el] || 0) !== 0)
            .map(el => {
                const total  = r.totalStats[el] || 0;
                const base   = r.baseStats[el] || 0;
                const setB   = r.setBonuses[el] || 0;
                const prefix = total > 0 ? '+' : '';
                const setNote = setB > 0 ? ` <small>(${base} + ${setB} set)</small>` : '';
                return `<span class="all-stat" style="color:${ELEMENT_COLORS[el]};">${ELEMENT_NAMES[el]}: ${prefix}${total}${setNote}</span>`;
            }).join('');

        const itemsHtml = r.items.map(item => {
            const statsHtml = Object.entries(item.elements)
                .filter(([, v]) => v !== 0)
                .map(([key, val]) => {
                    const prefix = val > 0 ? '+' : '';
                    return `<span style="color:${ELEMENT_COLORS[key]};">${prefix}${val}</span>`;
                }).join('');

            const paPmHtml = (item.pa > 0 || item.pm > 0)
                ? `<span class="item-papm">${item.pa > 0 ? '+' + item.pa + ' PA' : ''}${item.pa > 0 && item.pm > 0 ? ' ' : ''}${item.pm > 0 ? '+' + item.pm + ' PM' : ''}</span>`
                : '';

            return `
                <div class="item-card">
                    <div class="item-header">
                        <span class="item-type">${getTypeAbbrev(item.type)}</span>
                        <span class="item-level">Lvl ${item.level}</span>
                    </div>
                    <div class="item-name">${item.name}</div>
                    ${item.set ? `<div class="item-set">${item.set}</div>` : ''}
                    <div class="item-stats">${paPmHtml}${statsHtml}</div>
                </div>`;
        }).join('');

        const setMetaHtml = r.setBonus > 0 ? `<span class="meta-set">+${r.setBonus} set</span>` : '';

        const html = `
            <div class="result-card-new" data-result-idx="${i}">
                <div class="result-header">
                    <div class="result-rank">#${i + 1}</div>
                    <div class="result-main-stat">
                        <span class="stat-name">${ELEMENT_NAMES[selectedElement]}</span>
                        <span class="stat-value" style="color:${ELEMENT_COLORS[selectedElement]};">${r.totalElement}</span>
                    </div>
                </div>
                <div class="result-meta">
                    <span class="meta-pa">PA: ${totalPA}</span>
                    <span class="meta-pm">PM: ${totalPM}</span>
                    ${setMetaHtml}
                    <span class="meta-details-btn">Voir détails →</span>
                </div>
                <div class="result-all-stats">${allStatsHtml}</div>
                <div class="result-items-grid">${itemsHtml}</div>
            </div>`;

        resultsList.insertAdjacentHTML('beforeend', html);
    });

    resultsList.querySelectorAll('.result-card-new').forEach(card => {
        card.addEventListener('click', () => {
            const idx = parseInt(card.dataset.resultIdx);
            openModal(results[idx]);
        });
    });
}

function getTypeAbbrev(type) {
    const abbrevs = {
        weapon: 'ARME', hat: 'CHAP', cloak: 'CAPE', amulet: 'AMUL',
        ring: 'BAGU', belt: 'CEIN', boots: 'BOTT', shield: 'BOUC'
    };
    return abbrevs[type] || type.slice(0, 4).toUpperCase();
}

function getTypeName(type) {
    const names = {
        weapon: 'Arme', hat: 'Chapeau', cloak: 'Cape', amulet: 'Amulette',
        ring: 'Anneau', belt: 'Ceinture', boots: 'Bottes', shield: 'Bouclier'
    };
    return names[type] || type;
}

function openModal(result) {
    const content = document.getElementById('modalContent');
    const overlay = document.getElementById('modalOverlay');

    const setDetailsHtml = result.setDetails?.length > 0 ? `
        <div class="modal-set-details">
            <h4>Bonus des Sets</h4>
            ${result.setDetails.map(set => `
                <div class="set-detail-row">
                    <span class="set-detail-name">${set.setName}</span>
                    <span class="set-detail-pieces">${set.pieces} pièces (Tier ${set.tier})</span>
                    <span class="set-detail-bonus">+${set.bonus[selectedElement] || 0} ${ELEMENT_NAMES[selectedElement]}</span>
                </div>
            `).join('')}
        </div>` : '';

    content.innerHTML = `
        <h2 class="modal-title">Combinaison ${ELEMENT_NAMES[selectedElement]}</h2>
        <p class="modal-subtitle">
            <strong>Total ${ELEMENT_NAMES[selectedElement]}:</strong>
            <span style="color:${ELEMENT_COLORS[selectedElement]};font-size:1.3em;font-weight:bold;">${result.totalElement}</span>
            <br>
            <small style="color:var(--text-secondary);">Base: ${result.baseElement} | Bonus Set: +${result.setBonus}</small>
        </p>
        ${setDetailsHtml}
        <div class="modal-items">
            ${result.items.map(item => createModalItem(item)).join('')}
        </div>`;

    overlay.classList.add('active');
}

function createModalItem(item) {
    const statBoxes = Object.entries(item.elements)
        .filter(([, val]) => val > 0)
        .map(([elem, val]) => `
            <div class="stat-box">
                <div class="stat-label">${ELEMENT_NAMES[elem]}</div>
                <div class="stat-value" style="color:${ELEMENT_COLORS[elem]};">+${val}</div>
            </div>`).join('');

    const paPmBoxes = [
        item.pa > 0 ? `<div class="stat-box"><div class="stat-label">PA</div><div class="stat-value" style="color:#3498DB;">+${item.pa}</div></div>` : '',
        item.pm > 0 ? `<div class="stat-box"><div class="stat-label">PM</div><div class="stat-value" style="color:#2ECC71;">+${item.pm}</div></div>` : ''
    ].join('');

    return `
        <div class="modal-item">
            <div class="modal-item-header">
                <span class="modal-item-type">${getTypeName(item.type)}</span>
                <span class="modal-item-name">${item.name}</span>
                ${item.set ? `<span class="modal-item-type" style="background:var(--secondary);color:var(--background);">${item.set}</span>` : ''}
            </div>
            <div class="modal-item-stats">
                <div class="stat-box">
                    <div class="stat-label">Niveau</div>
                    <div class="stat-value">${item.level}</div>
                </div>
                ${paPmBoxes}
                ${statBoxes}
            </div>
        </div>`;
}
