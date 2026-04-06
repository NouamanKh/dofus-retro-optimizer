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
const API_URL = 'https://dofus-retro-optimizer.onrender.com';

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
    // Retry once — Render free tier may need a moment to wake up
    for (let attempt = 1; attempt <= 2; attempt++) {
        try {
            const res = await fetch(`${API_URL}/api/health`);
            if (res.ok) {
                el.textContent = '⬤ Serveur connecté';
                el.className = 'server-status online';
                return;
            }
        } catch {
            if (attempt === 1) {
                el.textContent = '⬤ Réveil du serveur...';
                await new Promise(r => setTimeout(r, 5000));
            }
        }
    }
    el.textContent = '⬤ Serveur hors ligne';
    el.className = 'server-status offline';
}

function setupElementButtons() {
    const buttons = document.querySelectorAll('.element-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedElement = btn.dataset.element;
            gtag('event', 'select_element', { element: selectedElement });
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

        gtag('event', 'search', {
            element: selectedElement,
            level: playerLevel,
            total_pa: totalPA,
            total_pm: totalPM,
            result_score: results[0]?.totalElement ?? 0
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
    document.getElementById('resultsCount').textContent = 'Erreur';
    document.getElementById('resultsList').innerHTML = `<div class="error-state"><p>${msg}</p></div>`;
}

// Ordered display groups for extra stats
const STAT_DISPLAY_ORDER = [
    // Damages
    'pct_dmg', 'dmg', 'dmg_fire', 'dmg_water', 'dmg_earth', 'dmg_air', 'dmg_neutral', 'dmg_trap', 'pct_dmg_trap',
    // Resistances %
    'pct_res_neutral', 'pct_res_earth', 'pct_res_fire', 'pct_res_water', 'pct_res_air',
    // Resistances flat
    'res_neutral', 'res_earth', 'res_fire', 'res_water', 'res_air',
    // Weaknesses
    'pct_weak_neutral', 'pct_weak_earth', 'pct_weak_fire', 'pct_weak_water', 'pct_weak_air',
    // Steal
    'steal', 'steal_fire', 'steal_water', 'steal_earth', 'steal_air', 'steal_neutral',
    // Combat
    'crit', 'fail_crit', 'dmg_return', 'pa_drain', 'pm_drain', 'heals', 'range',
    // Misc
    'initiative', 'prospection', 'pods', 'summons'
];

const STAT_LABELS_JS = {
    pct_dmg: '% Dommages', dmg: 'Dommages',
    dmg_fire: 'Dom. Feu', dmg_water: 'Dom. Eau', dmg_earth: 'Dom. Terre',
    dmg_air: 'Dom. Air', dmg_neutral: 'Dom. Neutre',
    dmg_trap: 'Dom. Pièges', pct_dmg_trap: '% Dom. Pièges',
    pct_res_neutral: '% Rés. Neutre', pct_res_earth: '% Rés. Terre',
    pct_res_fire: '% Rés. Feu', pct_res_water: '% Rés. Eau', pct_res_air: '% Rés. Air',
    res_neutral: 'Rés. Neutre', res_earth: 'Rés. Terre',
    res_fire: 'Rés. Feu', res_water: 'Rés. Eau', res_air: 'Rés. Air',
    pct_weak_neutral: '% Faib. Neutre', pct_weak_earth: '% Faib. Terre',
    pct_weak_fire: '% Faib. Feu', pct_weak_water: '% Faib. Eau', pct_weak_air: '% Faib. Air',
    steal: 'Vol', steal_fire: 'Vol Feu', steal_water: 'Vol Eau',
    steal_earth: 'Vol Terre', steal_air: 'Vol Air', steal_neutral: 'Vol Neutre',
    crit: 'Coups Critiques', fail_crit: 'Échec Critique',
    dmg_return: 'Renvoi Dom.', pa_drain: 'PA Retirés', pm_drain: 'PM Retirés',
    heals: 'Soins', range: 'Portée', initiative: 'Initiative',
    prospection: 'Prospection', pods: 'Pods', summons: 'Invocations'
};

const STAT_COLORS = {
    pct_dmg: '#E67E22', dmg: '#E67E22',
    dmg_fire: '#E74C3C', dmg_water: '#3498DB', dmg_earth: '#8B6914',
    dmg_air: '#F1C40F', dmg_neutral: '#95A5A6', dmg_trap: '#E67E22', pct_dmg_trap: '#E67E22',
    pct_res_neutral: '#2ECC71', pct_res_earth: '#2ECC71', pct_res_fire: '#2ECC71',
    pct_res_water: '#2ECC71', pct_res_air: '#2ECC71',
    res_neutral: '#27AE60', res_earth: '#27AE60', res_fire: '#27AE60',
    res_water: '#27AE60', res_air: '#27AE60',
    pct_weak_neutral: '#E74C3C', pct_weak_earth: '#E74C3C', pct_weak_fire: '#E74C3C',
    pct_weak_water: '#E74C3C', pct_weak_air: '#E74C3C',
    steal: '#9B59B6', steal_fire: '#9B59B6', steal_water: '#9B59B6',
    steal_earth: '#9B59B6', steal_air: '#9B59B6', steal_neutral: '#9B59B6',
    crit: '#F1C40F', fail_crit: '#E74C3C', dmg_return: '#E67E22',
    pa_drain: '#3498DB', pm_drain: '#2ECC71',
    heals: '#2ECC71', range: '#F4E4BC', initiative: '#F4E4BC',
    prospection: '#F1C40F', pods: '#F4E4BC', summons: '#9B59B6'
};

function renderExtraStats(stats, compact = false) {
    if (!stats || Object.keys(stats).length === 0) return '';
    const rows = STAT_DISPLAY_ORDER
        .filter(k => stats[k] !== undefined && stats[k] !== 0)
        .map(k => {
            const val = stats[k];
            const label = STAT_LABELS_JS[k] || k;
            const color = STAT_COLORS[k] || '#F4E4BC';
            const prefix = val > 0 ? '+' : '';
            if (compact) {
                return `<div class="istat"><span class="istat-name" style="color:${color};">${label}</span><span class="istat-val" style="color:${color};">${prefix}${val}</span></div>`;
            }
            return `<div class="modal-stat-row"><span style="color:${color};">${label}</span><span style="color:${color};font-weight:600;">${prefix}${val}</span></div>`;
        });
    return rows.join('');
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

            const extraStats = renderExtraStats(item.stats, true);

            return `
                <div class="item-card-full">
                    <div class="item-header">
                        <span class="item-type">${getTypeAbbrev(item.type)}</span>
                        <span class="item-level">Lvl ${item.level}</span>
                    </div>
                    <div class="item-name">${item.name}</div>
                    ${item.set ? `<div class="item-set">${item.set}</div>` : ''}
                    ${weaponHtml}
                    <div class="item-stats-list">${paPm}${elStats}${extraStats}</div>
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
        card.addEventListener('click', () => {
            const idx = parseInt(card.dataset.resultIdx);
            gtag('event', 'view_result', { element: selectedElement, score: results[idx]?.totalElement });
            openModal(results[idx]);
        });
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
            <div class="modal-stat-list">${paPm}${elStats}${renderExtraStats(item.stats)}</div>
        </div>`;
}
