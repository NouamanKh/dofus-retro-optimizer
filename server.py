"""
Flask server - thin HTTP adapter over optimizer.py
Requires: pip install flask pulp flask-cors
Run: python server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from catalog import ALL_ELEMENTS, DAMAGE_ELEMENTS, load as load_catalog
from optimizer import optimize, optimize_tradeoffs

app = Flask(__name__)
CORS(app)

CATALOG = load_catalog()


@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}

    element = data.get('element', 'vitalite')
    if element not in ALL_ELEMENTS:
        return jsonify({'error': f'element inconnu: {element}'}), 400
    try:
        level, total_pa, total_pm, exo_pa, exo_pm, damage_min, damage_max = (
            int(data.get(key, default)) for key, default in
            [('level', 100), ('totalPA', 6), ('totalPM', 3), ('exoPA', 0), ('exoPM', 0), ('damageMin', 0), ('damageMax', 0)]
        )
    except (TypeError, ValueError):
        return jsonify({'error': 'level, totalPA, totalPM, exoPA, exoPM, damageMin, damageMax doivent etre des entiers'}), 400
    damage_range = None
    if damage_min or damage_max:
        if not 1 <= damage_min <= damage_max <= 999:
            return jsonify({'error': 'il faut 1 <= damageMin <= damageMax <= 999'}), 400
        if element not in DAMAGE_ELEMENTS:
            return jsonify({'error': f'pas de dommages pour: {element}'}), 400
        damage_range = (damage_min, damage_max)

    excluded_ids = data.get('excludedIds', [])
    if not isinstance(excluded_ids, list) or not all(isinstance(i, str) for i in excluded_ids):
        return jsonify({'error': 'excludedIds doit etre une liste de chaines'}), 400

    with_sagesse = data.get('withSagesse', False)
    if not isinstance(with_sagesse, bool) or (with_sagesse and not damage_range):
        return jsonify({'error': 'withSagesse doit etre un booleen et demande damageMin et damageMax'}), 400
    if with_sagesse:
        return jsonify(optimize_tradeoffs(CATALOG, element, level, total_pa, total_pm, exo_pa, exo_pm, set(excluded_ids), damage_range))

    build = optimize(CATALOG, element, level, total_pa, total_pm, exo_pa, exo_pm, set(excluded_ids), damage_range)
    return jsonify([build] if build else [])


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'items': len(CATALOG.items), 'sets': len(CATALOG.set_bonuses)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
