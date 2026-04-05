# Dofus Retro Optimizer - Version History

## v1.3.5 (2025-04-05)
- Fixed module.exports error in items_retro.js causing "module is not defined"
- Added optimizer_milp.js script to index.html (was missing)
- MILP optimizer now connected to UI

## v1.3.4 (2025-04-05)
- Added Exo PA/PM feature for user-specified base PA/PM
- Fixed mobile layout issues with CSS media queries
- Added version badge and "Fait par Nouaman" credit
- Deployed to GitHub Pages

## v1.3.3 (2025-04-05)
- Fixed element selection visual bug (CSS styling)
- Attempted GLPK WASM - blocked by CORS/MIME type

## v1.3.2 (2025-04-05)
- Attempted external MILP solvers (HiGHS, javascript-lp-solver)
- Both blocked by CORS/MIME type issues

## v1.3.1 (2025-04-05)
- Implemented recursive branch and bound MILP
- Had issues with search space exploration

## v1.3.0 (2025-04-05)
- First MILP implementation with poor exploration
- Only tried 1-2 item swaps

## v1.2.0 (2025-04-05)
- Fixed level filter reading from wrong input
- Changed data source from DofusDB to Dofus Retro 1.29

## v1.1.0 (2025-04-05)
- Downloaded and converted Dofus Retro item/set data
- 1489 items, 108 sets
- Built Greedy optimizer
