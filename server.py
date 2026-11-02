"""
Flask server - thin HTTP adapter over optimizer.py
Requires: pip install flask pulp flask-cors
Run: python server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from catalog import ALL_ELEMENTS, DAMAGE_ELEMENTS, load as load_catalog
from optimizer import optimize

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
        level, total_pa, total_pm, exo_pa, exo_pm, damage_base = (
            int(data.get(key, default)) for key, default in
            [('level', 100), ('totalPA', 6), ('totalPM', 3), ('exoPA', 0), ('exoPM', 0), ('damageBase', 0)]
        )
    except (TypeError, ValueError):
        return jsonify({'error': 'level, totalPA, totalPM, exoPA, exoPM, damageBase doivent etre des entiers'}), 400
    if not 0 <= damage_base <= 999:
        return jsonify({'error': 'damageBase doit etre entre 0 et 999'}), 400
    if damage_base and element not in DAMAGE_ELEMENTS:
        return jsonify({'error': f'pas de dommages pour: {element}'}), 400

    excluded_ids = data.get('excludedIds', [])
    if not isinstance(excluded_ids, list) or not all(isinstance(i, str) for i in excluded_ids):
        return jsonify({'error': 'excludedIds doit etre une liste de chaines'}), 400

    build = optimize(CATALOG, element, level, total_pa, total_pm, exo_pa, exo_pm, set(excluded_ids), damage_base)
    return jsonify([build] if build else [])


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'items': len(CATALOG.items), 'sets': len(CATALOG.set_bonuses)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
