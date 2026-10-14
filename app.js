// Element colours live in styles.css as var(--<element>)
const ELEMENT_NAMES = {
    vitalite: 'Vitalité',
    sagesse: 'Sagesse',
    force: 'Force',
    intelligence: 'Intelligence',
    chance: 'Chance',
    agilite: 'Agilité',
    prospection: 'Prospection'
};

const ALL_ELEMENTS = ['vitalite', 'sagesse', 'force', 'intelligence', 'chance', 'agilite', 'prospection'];
const API_URL = 'https://dofus-retro-optimizer.onrender.com';

let selectedElement = null;

document.addEventListener('DOMContentLoaded', () => {
    setupElementButtons();
    setupModal();
    checkServerStatus();
    // Keep server alive during the session — ping every 10 minutes
    setInterval(() => fetch(`${API_URL}/api/health`).catch(() => {}), 10 * 60 * 1000);

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
                el.textContent = 'Serveur connecté';
                el.className = 'server-status online';
                return;
            }
        } catch {
            if (attempt === 1) {
                el.textContent = 'Réveil du serveur...';
                await new Promise(r => setTimeout(r, 5000));
            }
        }
    }
    el.textContent = 'Serveur hors ligne';
    el.className = 'server-status offline';
}

function setupElementButtons() {
    const buttons = document.querySelectorAll('.element-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => {
                b.classList.toggle('active', b === btn);
                b.setAttribute('aria-pressed', b === btn);
            });
            selectedElement = btn.dataset.element;
            document.getElementById('searchBtn').disabled = false;
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

async function fetchWithRetry(url, options, retries = 2) {
    for (let i = 0; i < retries; i++) {
        try {
            const res = await fetch(url, options);
            if (res.ok) return res;
            throw new Error(`HTTP ${res.status}`);
        } catch (err) {
            if (i < retries - 1) {
                const waitMsg = document.getElementById('searchBtn');
                waitMsg.textContent = 'Nouvelle tentative...';
                await new Promise(r => setTimeout(r, 3000));
            } else {
                throw err;
            }
        }
    }
}

async function runOptimization() {
    const playerLevel = parseInt(document.getElementById('playerLevel').value) || 100;
    const totalPA     = parseInt(document.getElementById('totalPA').value) || 6;
    const totalPM     = parseInt(document.getElementById('totalPM').value) || 3;
    const exoPA       = parseInt(document.getElementById('exoPA').value) || 0;
    const exoPM       = parseInt(document.getElementById('exoPM').value) || 0;

    setLoading(true);
    try {
        const response = await fetchWithRetry(`${API_URL}/api/optimize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ element: selectedElement, level: playerLevel, totalPA, totalPM, exoPA, exoPM })
        });
        const results = await response.json();

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
        showError('Le serveur ne répond pas. Il est peut-être en train de redémarrer — réessayez dans 30 secondes.');
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
    'initiative', 'pods', 'summons'
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
    pods: 'Pods', summons: 'Invocations'
};

function signed(val) {
    return `${val > 0 ? '+' : ''}${val}`;
}

function statRow(label, val, color = 'var(--muted)') {
    return `<div class="stat"><span style="color:${color};">${label}</span><span class="${val < 0 ? 'neg' : ''}">${signed(val)}</span></div>`;
}

function renderExtraStats(stats) {
    return STAT_DISPLAY_ORDER
        .filter(k => stats?.[k])
        .map(k => statRow(STAT_LABELS_JS[k] || k, stats[k]))
        .join('');
}

function renderItemStats(item) {
    return [
        item.pa ? statRow('PA', item.pa, 'var(--pa)') : '',
        item.pm ? statRow('PM', item.pm, 'var(--pm)') : '',
        ...ALL_ELEMENTS.filter(el => item.elements[el]).map(el => statRow(ELEMENT_NAMES[el], item.elements[el], `var(--${el})`)),
        renderExtraStats(item.stats)
    ].join('');
}

function renderWeaponStats(ws) {
    if (!ws) return '';
    return `
        <div class="tags">
            ${ws.AP        ? `<span class="tag">Coût: ${ws.AP} PA</span>` : ''}
            ${ws.scope     ? `<span class="tag">Portée: ${ws.scope}</span>` : ''}
            ${ws.critical_hit_prob ? `<span class="tag">CC: 1/${ws.critical_hit_prob} (+${ws.critical_hit_bonus || 0})</span>` : ''}
        </div>`;
}

function itemCard(item, showRequirements) {
    const reqHtml = showRequirements && item.requirements?.length > 0 ? `
        <div class="tags">${item.requirements.map(req => `<span class="tag req">${req.type} ${req.value}</span>`).join('')}</div>` : '';

    return `
        <div class="item-card">
            <div class="item-header">
                <span>${getTypeName(item.type)}</span>
                <span>Niv. ${item.level}</span>
            </div>
            <div class="item-name">${item.name}</div>
            ${item.set ? `<div class="item-set">${item.set}</div>` : ''}
            ${reqHtml}
            ${renderWeaponStats(item.weapon_stats)}
            <div class="item-stats">${renderItemStats(item)}</div>
        </div>`;
}

function displayResults(results) {
    const resultsList  = document.getElementById('resultsList');
    const resultsCount = document.getElementById('resultsCount');

    if (!results || results.length === 0 || !results[0]?.items?.length) {
        resultsCount.textContent = '0 combinaisons trouvées';
        resultsList.innerHTML = '<div class="empty-state"><p>Aucune combinaison ne respecte ces PA/PM à ce niveau.</p></div>';
        return;
    }

    resultsCount.textContent = 'Solution optimale (MILP)';
    resultsList.innerHTML = '';

    results.forEach((r, i) => {
        // Total stats summary row — show all elements always
        const summaryHtml = ALL_ELEMENTS.map(el => {
            const total = r.totalStats[el] || 0;
            const setB  = r.setBonuses[el] || 0;
            return `
                <div class="summary-stat${el === selectedElement ? ' is-target' : ''}">
                    <div class="summary-stat-name" style="color:var(--${el});">${ELEMENT_NAMES[el]}</div>
                    <div class="summary-stat-value ${total === 0 ? 'zero' : total < 0 ? 'neg' : ''}">${signed(total)}</div>
                    ${setB !== 0 ? `<div class="summary-set-note">dont ${signed(setB)} panoplie</div>` : ''}
                </div>`;
        }).join('');

        const html = `
            <article class="result">
                <div class="result-header">
                    <div>
                        <span class="stat-name">${ELEMENT_NAMES[selectedElement]} totale</span>
                        <span class="stat-value" style="color:var(--${selectedElement});">${r.totalElement}</span>
                    </div>
                    <div class="result-meta">
                        <span class="meta">PA <b>${r.totalPA}</b></span>
                        <span class="meta">PM <b>${r.totalPM}</b></span>
                        ${r.setBonus > 0 ? `<span class="meta">Panoplie <b>+${r.setBonus}</b></span>` : ''}
                        <button type="button" class="details-btn" data-result-idx="${i}">Voir le détail</button>
                    </div>
                </div>
                <div class="result-summary-grid">${summaryHtml}</div>
                <div class="result-items-grid">${r.items.map(item => itemCard(item, false)).join('')}</div>
            </article>`;

        resultsList.insertAdjacentHTML('beforeend', html);
    });

    resultsList.querySelectorAll('.details-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.resultIdx);
            gtag('event', 'view_result', { element: selectedElement, score: results[idx]?.totalElement });
            openModal(results[idx]);
        });
    });
}

function getTypeName(type) {
    const names = { weapon: 'Arme', hat: 'Chapeau', cloak: 'Cape', amulet: 'Amulette', ring: 'Anneau', belt: 'Ceinture', boots: 'Bottes', shield: 'Bouclier', pet: 'Familier', mount: 'Monture' };
    return names[type] || type;
}

function openModal(result) {
    const content = document.getElementById('modalContent');
    const overlay = document.getElementById('modalOverlay');

    const setDetailsHtml = result.setDetails?.length > 0 ? `
        <h4>Bonus de panoplie</h4>
        ${result.setDetails.map(s => `
            <div class="set-detail-row">
                <span class="set-detail-name">${s.setName} <span class="set-detail-pieces">${s.pieces} pièces</span></span>
                <div class="set-detail-bonuses">
                    ${s.bonus.pa ? `<span style="color:var(--pa);">${signed(s.bonus.pa)} PA</span>` : ''}
                    ${s.bonus.pm ? `<span style="color:var(--pm);">${signed(s.bonus.pm)} PM</span>` : ''}
                    ${ALL_ELEMENTS.filter(el => s.bonus[el]).map(el =>
                        `<span style="color:var(--${el});">${signed(s.bonus[el])} ${ELEMENT_NAMES[el]}</span>`
                    ).join('')}
                </div>
            </div>`).join('')}` : '';

    // Full totals table in modal
    const totalsHtml = `
        <div class="modal-totals">
            <div class="modal-totals-row"><span>PA</span><b style="color:var(--pa);">${result.totalPA}</b></div>
            <div class="modal-totals-row"><span>PM</span><b style="color:var(--pm);">${result.totalPM}</b></div>
            ${ALL_ELEMENTS.filter(el => result.totalStats[el]).map(el => {
                const total = result.totalStats[el];
                const setB  = result.setBonuses[el] || 0;
                const note  = setB !== 0 ? ` <small>(dont ${signed(setB)} panoplie)</small>` : '';
                return `
                    <div class="modal-totals-row">
                        <span style="color:var(--${el});">${ELEMENT_NAMES[el]}</span>
                        <b class="${total < 0 ? 'neg' : ''}">${signed(total)}${note}</b>
                    </div>`;
            }).join('')}
        </div>`;

    content.innerHTML = `
        <h2 class="modal-title" id="modalTitle">Combinaison optimale — ${ELEMENT_NAMES[selectedElement]}</h2>
        ${totalsHtml}
        ${setDetailsHtml}
        <h4>Équipements</h4>
        <div class="result-items-grid">${result.items.map(item => itemCard(item, true)).join('')}</div>`;

    overlay.classList.add('active');
    document.getElementById('modalClose').focus();
}
