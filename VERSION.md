# Dofus Retro Optimizer - Version History

## v1.5.2 (2026-04-06)
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
