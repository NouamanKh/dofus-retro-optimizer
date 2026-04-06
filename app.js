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

const ALL_ELEMENTS = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite'];
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
        } else throw new Error();
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
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.classList.remove('active'); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') overlay.classList.remove('active'); });
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

    setLoading(true);
    try {
        const response = await fetch(`${API_URL}/api/optimize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                element: selectedElement,
                maxLevel: playerLevel,
                minPA: maxItemPA,
                minPM: maxItemPM,
                maxPA: maxItemPA,
                maxPM: maxItemPM
            })
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        const results = await response.json();
        results.forEach(r => { r.basePA = basePA; r.basePM = basePM; r.exoPA = exoPA; r.exoPM = exoPM; });
        displayResults(results);
    } catch (err) {
        console.error('Optimization error:', err);
        showError('Impossible de contacter le serveur. Assurez-vous que server.py tourne sur le port 5000.');
    } finally {
        setLoading(false);
    }
}

function showError(msg) {
    document.getElementById('resultsCount').textContent = 'Erreur';
    document.getElementById('resultsList').innerHTML = `<div class="error-state"><p>${msg}</p></div>`;
}

// Returns "+X" or "-X" string, colored span
function statSpan(val, color) {
    const prefix = val > 0 ? '+' : '';
    return `<span style="color:${color};font-weight:600;">${prefix}${val}</span>`;
}

function displayResults(results) {
    const resultsList  = document.getElementById('resultsList');
    const resultsCount = document.getElementById('resultsCount');
    const emptyState   = document.getElementById('emptyState');

    if (!results || results.length === 0 || !results[0]?.items?.length) {
        emptyState.style.display = 'flex';
        resultsCount.textContent = '0 combinaisons trouvées';
        resultsList.innerHTML = '';
        resultsList.appendChild(emptyState);
        return;
    }

    emptyState.style.display = 'none';
    resultsCount.textContent = 'Meilleure combinaison (MILP Optimal)';
    resultsList.innerHTML = '';

    results.forEach((r, i) => {
        const itemPA  = r.items.reduce((s, it) => s + (it.pa || 0), 0);
        const itemPM  = r.items.reduce((s, it) => s + (it.pm || 0), 0);
        const totalPA = (r.basePA || 6) + (r.exoPA || 0) + itemPA;
        const totalPM = (r.basePM || 3) + (r.exoPM || 0) + itemPM;

        // Total stats summary row — show all 6 elements always
        const summaryHtml = ALL_ELEMENTS.map(el => {
            const total = r.totalStats[el] || 0;
            const setB  = r.setBonuses[el] || 0;
            const base  = r.baseStats[el] || 0;
            const color = total > 0 ? ELEMENT_COLORS[el] : total < 0 ? '#888' : 'var(--text-secondary)';
            const prefix = total > 0 ? '+' : '';
            const setNote = setB !== 0 ? `<div class="summary-set-note">${base > 0 ? '+' : ''}${base} + ${setB > 0 ? '+' : ''}${setB} set</div>` : '';
            return `
                <div class="summary-stat">
                    <div class="summary-stat-name" style="color:${ELEMENT_COLORS[el]};">${ELEMENT_NAMES[el]}</div>
                    <div class="summary-stat-value" style="color:${color};">${prefix}${total}</div>
                    ${setNote}
                </div>`;
        }).join('');

        // Item cards — show all non-zero stats
        const itemsHtml = r.items.map(item => {
            const elStats = ALL_ELEMENTS
                .filter(el => (item.elements[el] || 0) !== 0)
                .map(el => {
                    const val = item.elements[el];
                    const prefix = val > 0 ? '+' : '';
                    const color = val > 0 ? ELEMENT_COLORS[el] : '#888';
                    return `<div class="istat"><span class="istat-name" style="color:${ELEMENT_COLORS[el]};">${ELEMENT_NAMES[el]}</span><span class="istat-val" style="color:${color};">${prefix}${val}</span></div>`;
                }).join('');

            const paPm = [
                item.pa ? `<div class="istat"><span class="istat-name" style="color:#3498DB;">PA</span><span class="istat-val" style="color:#3498DB;">+${item.pa}</span></div>` : '',
                item.pm ? `<div class="istat"><span class="istat-name" style="color:#2ECC71;">PM</span><span class="istat-val" style="color:#2ECC71;">+${item.pm}</span></div>` : ''
            ].join('');

            const ws = item.weapon_stats;
            const weaponHtml = ws ? `
                <div class="weapon-stats">
                    ${ws.AP        ? `<span class="wtag">Coût: ${ws.AP} PA</span>` : ''}
                    ${ws.scope     ? `<span class="wtag">Portée: ${ws.scope}</span>` : ''}
                    ${ws.critical_hit_prob ? `<span class="wtag">CC: 1/${ws.critical_hit_prob} (+${ws.critical_hit_bonus || 0})</span>` : ''}
                </div>` : '';

            return `
                <div class="item-card-full">
                    <div class="item-header">
                        <span class="item-type">${getTypeAbbrev(item.type)}</span>
                        <span class="item-level">Lvl ${item.level}</span>
                    </div>
                    <div class="item-name">${item.name}</div>
                    ${item.set ? `<div class="item-set">${item.set}</div>` : ''}
                    ${weaponHtml}
                    <div class="item-stats-list">${paPm}${elStats}</div>
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
                <div class="result-summary-grid">${summaryHtml}</div>
                <div class="result-items-grid">${itemsHtml}</div>
            </div>`;

        resultsList.insertAdjacentHTML('beforeend', html);
    });

    resultsList.querySelectorAll('.result-card-new').forEach(card => {
        card.addEventListener('click', () => openModal(results[parseInt(card.dataset.resultIdx)]));
    });
}

function getTypeAbbrev(type) {
    const abbrevs = { weapon: 'ARME', hat: 'CHAP', cloak: 'CAPE', amulet: 'AMUL', ring: 'BAGU', belt: 'CEIN', boots: 'BOTT', shield: 'BOUC' };
    return abbrevs[type] || type.slice(0, 4).toUpperCase();
}

function getTypeName(type) {
    const names = { weapon: 'Arme', hat: 'Chapeau', cloak: 'Cape', amulet: 'Amulette', ring: 'Anneau', belt: 'Ceinture', boots: 'Bottes', shield: 'Bouclier' };
    return names[type] || type;
}

function openModal(result) {
    const content = document.getElementById('modalContent');
    const overlay = document.getElementById('modalOverlay');

    const itemPA  = result.items.reduce((s, it) => s + (it.pa || 0), 0);
    const itemPM  = result.items.reduce((s, it) => s + (it.pm || 0), 0);
    const totalPA = (result.basePA || 6) + (result.exoPA || 0) + itemPA;
    const totalPM = (result.basePM || 3) + (result.exoPM || 0) + itemPM;

    const setDetailsHtml = result.setDetails?.length > 0 ? `
        <div class="modal-set-details">
            <h4>Bonus des Sets</h4>
            ${result.setDetails.map(s => `
                <div class="set-detail-row">
                    <span class="set-detail-name">${s.setName}</span>
                    <span class="set-detail-pieces">${s.pieces} pièces</span>
                    <div class="set-detail-bonuses">
                        ${ALL_ELEMENTS.filter(el => s.bonus[el]).map(el =>
                            `<span style="color:${ELEMENT_COLORS[el]};">+${s.bonus[el]} ${ELEMENT_NAMES[el]}</span>`
                        ).join('')}
                    </div>
                </div>`).join('')}
        </div>` : '';

    // Full totals table in modal
    const totalsHtml = `
        <div class="modal-totals">
            <div class="modal-totals-row">
                <span class="modal-totals-label">PA total</span>
                <span class="modal-totals-value" style="color:#3498DB;">${totalPA}</span>
            </div>
            <div class="modal-totals-row">
                <span class="modal-totals-label">PM total</span>
                <span class="modal-totals-value" style="color:#2ECC71;">${totalPM}</span>
            </div>
            ${ALL_ELEMENTS.map(el => {
                const total = result.totalStats[el] || 0;
                const base  = result.baseStats[el] || 0;
                const setB  = result.setBonuses[el] || 0;
                if (total === 0) return '';
                const prefix = total > 0 ? '+' : '';
                const color  = total > 0 ? ELEMENT_COLORS[el] : '#888';
                const note   = setB !== 0 ? ` <small style="color:var(--text-secondary);">(${base > 0 ? '+' : ''}${base} items + ${setB > 0 ? '+' : ''}${setB} set)</small>` : '';
                return `
                    <div class="modal-totals-row">
                        <span class="modal-totals-label" style="color:${ELEMENT_COLORS[el]};">${ELEMENT_NAMES[el]}</span>
                        <span class="modal-totals-value" style="color:${color};">${prefix}${total}${note}</span>
                    </div>`;
            }).join('')}
        </div>`;

    content.innerHTML = `
        <h2 class="modal-title">Combinaison Optimale — ${ELEMENT_NAMES[selectedElement]}</h2>
        ${totalsHtml}
        ${setDetailsHtml}
        <h4 class="modal-items-title">Équipements</h4>
        <div class="modal-items">
            ${result.items.map(item => createModalItem(item)).join('')}
        </div>`;

    overlay.classList.add('active');
}

function createModalItem(item) {
    const elStats = ALL_ELEMENTS
        .filter(el => (item.elements[el] || 0) !== 0)
        .map(el => {
            const val = item.elements[el];
            const prefix = val > 0 ? '+' : '';
            const color  = val > 0 ? ELEMENT_COLORS[el] : '#888';
            return `<div class="modal-stat-row"><span style="color:${ELEMENT_COLORS[el]};">${ELEMENT_NAMES[el]}</span><span style="color:${color};font-weight:600;">${prefix}${val}</span></div>`;
        }).join('');

    const paPm = [
        item.pa ? `<div class="modal-stat-row"><span style="color:#3498DB;">PA</span><span style="color:#3498DB;font-weight:600;">+${item.pa}</span></div>` : '',
        item.pm ? `<div class="modal-stat-row"><span style="color:#2ECC71;">PM</span><span style="color:#2ECC71;font-weight:600;">+${item.pm}</span></div>` : ''
    ].join('');

    const ws = item.weapon_stats;
    const weaponHtml = ws ? `
        <div class="modal-weapon-stats">
            ${ws.AP             ? `<span class="wtag">Coût: ${ws.AP} PA</span>` : ''}
            ${ws.scope          ? `<span class="wtag">Portée: ${ws.scope}</span>` : ''}
            ${ws.critical_hit_prob ? `<span class="wtag">CC: 1/${ws.critical_hit_prob} (+${ws.critical_hit_bonus || 0})</span>` : ''}
        </div>` : '';

    const reqHtml = item.requirements?.length > 0 ? `
        <div class="modal-requirements">
            ${item.requirements.map(req => `<span class="req-tag">${req.type} ${req.value}</span>`).join('')}
        </div>` : '';

    return `
        <div class="modal-item">
            <div class="modal-item-header">
                <div class="modal-item-title">
                    <span class="modal-item-type">${getTypeName(item.type)}</span>
                    <span class="modal-item-name">${item.name}</span>
                    <span class="modal-item-level">Niv. ${item.level}</span>
                </div>
                ${item.set ? `<span class="modal-item-set">${item.set}</span>` : ''}
            </div>
            ${reqHtml}
            ${weaponHtml}
            <div class="modal-stat-list">${paPm}${elStats}</div>
        </div>`;
}
