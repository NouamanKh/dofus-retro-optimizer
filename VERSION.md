# Dofus Retro Optimizer - Version History

## v1.14.0 (2026-11-13)
- Every damage search now gives one build per PA total worth stopping at, from the most PA down, since PA are the costly part: you see what each PA less costs in damage. A build is only shown if no other does as much damage on as few PA
- With "Et maximiser la Sagesse", each PA total gets its most damage, its most Sagesse and one build in between (it was 5 builds over all PA totals)
- "PA Min" still applies: no build goes under it
- API: POST /api/optimize with spellClass returns a list of builds, most PA first

## v1.13.0 (2026-11-13)
- Damage mode now knows the spells: pick a class and an element, and the search chooses the gear and the spells to cast together, for the most damage in one round on one target. It can mix spells (e.g. 2 × Pression + 3 × Concentration) and results list each spell cast with its damage per cast
- The manual spell fields (min, max, PA cost, casts) are gone
- Spell data: 99 damaging class spells with their 6 grades in data/spells_retro.json, read from Ankama's Dofus Retro client files (spells_fr_1254.swf, dated 2025-07-23). This is the live Retro data, not a frozen 1.29 copy
- A spell is taken at the highest grade the character's level allows (grade 5, then 6 from its level). Casts per turn and per target are respected, and a spell with a cooldown is cast once
- Not counted: critical hits, poisons, traps, glyphs, a spell's damage in another element, damage based on life (Punition, Roue de la Fortune). An outcome with a chance counts for its share (Bluff, Esprit Félin)
- One solve now picks the round and the gear, instead of one solve per number of casts
- API: POST /api/optimize takes spellClass (one of the 12 class names, with element Force/Intelligence/Chance/Agilité) in place of damageMin, damageMax, spellPA and castsMax; results return spells (name, grade, pa, castsMax, damageMin, damageMax, casts, damageRange) in place of spellRoll, spellPA, casts and damageRange

## v1.12.1 (2026-11-13)
- Fix: item requirements were never checked, so a build could hold items the character can't wear (455 of the 1581 items have one). An item needing "Force > 100" is now worn only if the rest of the build gives more than 100 Force, set bonuses included; its own stats don't count, as it has to be put on first. "PM >" counts the base 3 PM and exo PM
- Stat points are not known to the app, so they count as 0: a requirement has to be met on gear alone
- Items with a requirement the app can't check are left out: class, alignment, sex, job, rank (30 shields), kamas, and a stat under a value (5 items)

## v1.12.0 (2026-11-03)
- Damage mode now searches for the most damage per round. New fields: "Coût en PA" and "Lancers max par tour". Casts per round = total PA / spell cost, rounded down, so gear that gives PA can beat gear that hits harder. Results show the damage per round, the casts and the damage per cast
- "Et maximiser la Sagesse" compares damage per round too
- Faster solves: set-less items beaten on damage, PA, PM and Sagesse by enough others in their slot no longer reach the solver
- Gunicorn worker timeout raised to 120 seconds (gunicorn.conf.py), as a trade-off search takes several solves per cast count
- API: POST /api/optimize accepts spellPA (0-20, requires damageMin and damageMax; 0 counts one cast) and castsMax (1-99, default 99); results return spellPA, casts, roundDamage and roundAverage

## v1.11.0 (2026-11-02)
- New: "Et maximiser la Sagesse" in damage mode shows up to 5 builds from the most damage to the most Sagesse, each with the most damage possible for its Sagesse. Slots that add no damage are filled with Sagesse gear
- API: POST /api/optimize accepts withSagesse (requires damageMin and damageMax) and can then return several builds

## v1.10.1 (2026-11-02)
- Spell damage is now a min and max instead of one base value. Results show the estimated damage from min to max, and the search maximises the average roll
- API: damageBase replaced by damageMin and damageMax (1 <= min <= max <= 999); results return spellRoll and damageRange

## v1.10.0 (2026-11-02)
- New: "Maximiser les dommages d'un sort" searches for the most damage on a spell in one element, given its base damage. Estimate: floor(base x (100 + element + % Dommages) / 100) + Dommages, gear only (source: forums.jeuxonline.info/sujet/801243, not Retro-specific)
- Set bonuses now include Dommages and % Dommages, shown in the build details
- Fix "Renvois de dommages" read as Dommages (3 items, e.g. Sulik)
- Fix set "% Dommages" labels, which would have read as flat Dommages
- Class items: fixed "Dommage" beside spell-specific lines no longer counts as general Dommages (18 items, e.g. Cape Aillé showed +55); assumed to apply to one spell, whose name is missing from the raw data
- API: POST /api/optimize accepts an optional damageBase (0-999, Force/Intelligence/Chance/Agilité only)

## v1.9.0 (2026-11-02)
- New: "Chercher sans cet objet" button on each item re-runs the search without it. Exclusions add up across searches and are listed above the results, where a click puts an item back
- Excluding an item also excludes its copies with the same name and type (the catalog has 11 identical "Patte d'Ecaflip")
- API: POST /api/optimize accepts an optional excludedIds list of item ids

## v1.8.0 (2026-10-14)
- New slots: Familier (pet) and Monture (mount); a build gets at most one of the two, as in game
- Pets: every feeding option at its max bonus is a separate choice, so the solver picks the best feeding for the target (source: millenium.org guide 345339)
- Mounts: Dragodindes at mount level 100, ridable from character level 60; mount PM counts toward PM (source: tofus.fr/fiches/dinde)
- Pet/mount data lives in dofus-retro-companions.json (hand-curated, sources inside) and is merged by convert_retro_data.py
- Fix every search after the first failing with "Le serveur ne répond pas": displayResults cleared the results list, deleting #emptyState, then crashed on it next time (the error was reported as a server failure). The no-result message is now rendered directly
- Fix search button staying disabled after an update: browsers could pair the new index.html with a cached old app.js that never enables it. styles.css and app.js are now loaded with ?v=<version> (bump it with each release)

## v1.7.0 (2026-10-14)
- New target: Prospection (score = prospection + Chance ÷ 10, rounded down, from items and set bonuses)
- Fix set bonus tiers: a 2-piece bonus now applies at 2 pieces and full-set bonuses can activate (were shifted up one piece)
- Set bonuses now apply exactly as in game (highest tier reached, even when it lowers the score)
- Set bonus PA/PM now count toward the build's PA/PM
- PA/PM inputs are now minimums ("PA Min" / "PM Min"); builds may exceed them when it scores better
- Backend split: catalog.py (data), optimizer.py (MILP + PA/PM budget + totals), server.py (HTTP only)
- API: POST /api/optimize now takes raw player inputs {element, level, totalPA, totalPM, exoPA, exoPM}; returned totalPA/totalPM are final totals
- Data: convert_retro_data.py now writes data/items_retro.json + data/sets_retro.json (set bonuses pre-decoded)
- Added test_optimizer.py (python -m unittest)
- Pinned pulp<4 (4.x removed the bundled CBC solver)
- Removed unused optimizers, debug/check scripts and old API data (~1,900 lines)

## v1.5.3 (2026-04-06)
- Show all item stats: damages, % damages, resistances (% and flat), steal, crit, heals, range, initiative, prospection, pods, etc.
- Updated convert_retro_data.py to extract all stat types from raw data (was only extracting 6 elements + PA/PM)
- Regenerated items_retro.js with full stats field per item
- Stats displayed in logical groups with color coding on item cards and in modal


- Show all 6 element stats in result card summary grid (always visible, even zeros)
- Item cards now show all non-zero stats with proper +/- coloring
- Weapon stats (AP cost, range, crit) shown on weapon items
- Modal: full totals table with set bonus breakdown per element, item requirements, weapon stats
- Set detail bonuses now show all elements (not just the optimized one)


- MILP now returns only the single optimal solution (removed multi-result re-solve logic — suboptimal alternatives don't make sense for an exact solver)


- Replace all JS optimizers (greedy + JS branch-and-bound) with Python PuLP MILP via server.py
- Frontend now calls server.py API — exact optimal solution guaranteed, no level filter bugs possible
- server.py: added shield slot, max PA/PM constraints, full set bonus logic for all elements, multiple diverse results via exclusion re-solve
- Added server health check indicator in UI
- Added error state when server is unreachable
- Removed data/items_retro.js, sets_retro.js, optimizer.js, optimizer_milp.js from frontend (no longer needed)
- Requires: pip install flask flask-cors pulp


- Fix greedy level filter more robustly: removed spread copies in itemsBySlot (eliminated elementValue mutation), added hard safety filter on all output combos to guarantee no over-level items slip through


- Fix greedy returning items above the character's level (enforcePAPMLimit and ensurePAPMConstraint were using the unfiltered item list)


- Add shield slot to optimizer (was excluded from all optimization)
- Fix MILP: tighter upper bound (no more hardcoded +50), significantly faster
- Fix MILP: now returns up to 10 diverse results (was always 1)
- Fix modal: result cards are now clickable and open item detail modal
- Fix duplicate createItemChip function (second definition silently overrode first)
- Add loading spinner and disable search button during optimization
- Add Escape key to close modal
- Remove all debug console.log statements from production code
- Remove dead code: createResultCard, calculateAllStats, unused createItemChip variant
- PA/PM now shown in modal item details
- Consistent template literal usage throughout app.js

## v1.3.8 (2025-04-05)
- Add debug logging for PA items in MILP

## v1.3.7 (2025-04-05)
- Fix MILP PA/PM constraints (use >= instead of exact match)

## v1.3.6 (2025-04-05)
- Replace external solver with custom branch-and-bound implementation

## v1.3.5 (2025-04-05)
- Fixed module.exports error in items_retro.js causing "module is not defined"
- Added optimizer_milp.js script to index.html (was missing)
- MILP optimizer now connected to UI

## v1.3.4
- Fix MILP with js-lp-solver

## v1.3.3
- Debug element selection

## v1.3.2
- Debug element selection visual bug

## v1.3.1
- Fix MIN constraints

## v1.3.0
- Add MILP with HiGHS solver

## v1.2.0
- Clean up and simplify

## v1.1.4
- Debug items with PA

## v1.1.3
- Show all results

## v1.1.2
- Search for more PA then filter

## v1.1.1
- More debug

## v1.1.0
- Fix syntax error

## v1.0.9
- Debug items PA

## v1.0.8
- More debug

## v1.0.7
- Debug display

## v1.0.6
- Total PA/PM includes exo

## v1.0.5
- Fix exo PA/PM to use max only

## v1.0.4
- Debug exo PA/PM

## v1.0.3
- Fix exo PA/PM constraints

## v1.0.2
- Add exo PA/PM feature

## v1.0.1
- Add version badge and "Fait par Nouaman" credit
- Mobile layout fixes

## v1.0.0
- Initial commit - Dofus Retro Equipment Optimizer
