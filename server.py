"""
Flask server - thin HTTP adapter over optimizer.py
Requires: pip install flask pulp flask-cors
Run: python server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from catalog import ALL_ELEMENTS, DAMAGE_ELEMENTS, class_spells, load as load_catalog, load_spells
from optimizer import optimize, optimize_per_pa

app = Flask(__name__)
CORS(app)

CATALOG = load_catalog()
SPELLS = load_spells()
CLASSES = {spell['class'] for spell in SPELLS}


@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}

    element = data.get('element', 'vitalite')
    if element not in ALL_ELEMENTS:
        return jsonify({'error': f'element inconnu: {element}'}), 400
    try:
        level, total_pa, total_pm, exo_pa, exo_pm = (
            int(data.get(key, default)) for key, default in [('level', 100), ('totalPA', 6), ('totalPM', 3), ('exoPA', 0), ('exoPM', 0)]
        )
    except (TypeError, ValueError):
        return jsonify({'error': 'level, totalPA, totalPM, exoPA, exoPM doivent etre des entiers'}), 400
    # With a class, the search is for the damage of that class's spells in the element
    spell_class = data.get('spellClass')
    if spell_class is not None and (not isinstance(spell_class, str) or spell_class not in CLASSES or element not in DAMAGE_ELEMENTS):
        return jsonify({'error': f'spellClass doit etre une classe ({", ".join(sorted(CLASSES))}) et element un de {", ".join(DAMAGE_ELEMENTS)}'}), 400
    spells = class_spells(SPELLS, spell_class, element, level) if spell_class else []
    if spell_class and not spells:
        return jsonify([])

    excluded_ids = data.get('excludedIds', [])
    if not isinstance(excluded_ids, list) or not all(isinstance(i, str) for i in excluded_ids):
        return jsonify({'error': 'excludedIds doit etre une liste de chaines'}), 400

    with_sagesse = data.get('withSagesse', False)
    if not isinstance(with_sagesse, bool) or (with_sagesse and not spell_class):
        return jsonify({'error': 'withSagesse doit etre un booleen et demande spellClass'}), 400
    if spells:
        return jsonify(optimize_per_pa(CATALOG, element, level, total_pa, total_pm, exo_pa, exo_pm, set(excluded_ids), spells, with_sagesse))

    build = optimize(CATALOG, element, level, total_pa, total_pm, exo_pa, exo_pm, set(excluded_ids))
    return jsonify([build] if build else [])


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'items': len(CATALOG.items), 'sets': len(CATALOG.set_bonuses)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
