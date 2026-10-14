import unittest

import catalog
from catalog import ALL_ELEMENTS, Catalog
from optimizer import optimize


def item(id, type, level=1, set=None, pa=0, pm=0, **elements):
    el = {e: 0 for e in ALL_ELEMENTS}
    el.update(elements)
    return {'id': id, 'name': id, 'type': type, 'level': level, 'elements': el,
            'pa': pa, 'pm': pm, 'stats': {}, 'set': set}


class ActiveBonusTest(unittest.TestCase):
    def test_active_bonus_picks_highest_reached_tier(self):
        cat = Catalog([], [{'name': 'S', 'items': [], 'bonuses': {'2': {'vitalite': 10}, '4': {'vitalite': 30}}}])
        self.assertEqual(cat.active_bonus('S', 1), {})
        self.assertEqual(cat.active_bonus('S', 2), {'vitalite': 10})
        self.assertEqual(cat.active_bonus('S', 3), {'vitalite': 10})
        self.assertEqual(cat.active_bonus('S', 4), {'vitalite': 30})
        self.assertEqual(cat.active_bonus('S', 5), {'vitalite': 30})
        self.assertEqual(cat.active_bonus('Inconnu', 4), {})


class OptimizeTest(unittest.TestCase):
    def test_set_bonus_tier_is_two_pieces_not_three(self):
        cat = Catalog(
            [item('A', 'hat', set='S', vitalite=10),
             item('B', 'boots', set='S', vitalite=10),
             item('C', 'hat', vitalite=15),
             item('Z', 'hat', level=200, vitalite=999)],
            [{'name': 'S', 'items': [], 'bonuses': {'2': {'vitalite': 20}}}])
        build = optimize(cat, 'vitalite', level=50, total_pa=6, total_pm=3)
        self.assertEqual(sorted(i['id'] for i in build['items']), ['A', 'B'])
        self.assertEqual(build['totalElement'], 40)
        self.assertEqual(build['setBonus'], 20)

    def test_pa_is_a_minimum(self):
        cat = Catalog([item('X', 'hat', pa=1, vitalite=5), item('Y', 'hat', vitalite=50)], [])
        build = optimize(cat, 'vitalite', level=100, total_pa=8, total_pm=3)
        self.assertEqual([i['id'] for i in build['items']], ['X'])
        self.assertEqual(build['totalPA'], 8)
        self.assertIsNone(optimize(cat, 'vitalite', level=99, total_pa=8, total_pm=3))

    def test_extra_pa_allowed_when_it_scores(self):
        cat = Catalog([item('X', 'hat', pa=1, vitalite=50), item('Y', 'hat', vitalite=10)], [])
        build = optimize(cat, 'vitalite', level=50, total_pa=6, total_pm=3)
        self.assertEqual([i['id'] for i in build['items']], ['X'])
        self.assertEqual(build['totalPA'], 7)

    def test_set_pa_counts_toward_minimum(self):
        cat = Catalog(
            [item('A', 'hat', set='S', vitalite=10),
             item('B', 'boots', set='S', vitalite=10),
             item('C', 'hat', pa=1, vitalite=5)],
            [{'name': 'S', 'items': [], 'bonuses': {'2': {'pa': 1}}}])
        build = optimize(cat, 'vitalite', level=50, total_pa=7, total_pm=3)
        self.assertEqual(sorted(i['id'] for i in build['items']), ['A', 'B'])
        self.assertEqual(build['totalPA'], 7)

    def test_set_bonus_applies_even_when_it_hurts(self):
        cat = Catalog(
            [item('A', 'hat', set='S', vitalite=20),
             item('B', 'boots', set='S', vitalite=20),
             item('D', 'boots', vitalite=15)],
            [{'name': 'S', 'items': [], 'bonuses': {'2': {'vitalite': -30}}}])
        build = optimize(cat, 'vitalite', level=50, total_pa=6, total_pm=3)
        self.assertEqual(sorted(i['id'] for i in build['items']), ['A', 'D'])
        self.assertEqual(build['totalElement'], 35)

    def test_pet_or_mount_never_both(self):
        cat = Catalog(
            [item('P', 'pet', vitalite=100),
             item('M', 'mount', level=60, vitalite=100),
             item('H', 'hat', vitalite=10)], [])
        ids = sorted(i['id'] for i in optimize(cat, 'vitalite', level=100, total_pa=6, total_pm=3)['items'])
        self.assertEqual(len(set(ids) & {'P', 'M'}), 1)
        self.assertIn('H', ids)

    def test_prospection_counts_chance_tenth(self):
        cat = Catalog([item('P', 'hat', prospection=6), item('Q', 'hat', chance=75)], [])
        build = optimize(cat, 'prospection', level=50, total_pa=6, total_pm=3)
        self.assertEqual([i['id'] for i in build['items']], ['Q'])
        self.assertEqual(build['totalElement'], 7)


class RealDataTest(unittest.TestCase):
    def test_real_catalog(self):
        cat = catalog.load()
        self.assertEqual(max(cat.set_bonuses['Panoplie Champchamp']), 4)
        self.assertTrue(any('prospection' in i['elements'] for i in cat.items))
        self.assertFalse(any('prospection' in i['stats'] for i in cat.items))
        pets = {i['name']: i for i in cat.items if i['type'] == 'pet'}
        mounts = {i['name']: i for i in cat.items if i['type'] == 'mount'}
        self.assertEqual(pets['Nomoon']['elements']['prospection'], 80)
        self.assertEqual(mounts['Dragodinde Emeraude/Rousse']['pm'], 1)


class AdapterTest(unittest.TestCase):
    def setUp(self):
        import server
        self.client = server.app.test_client()

    def test_optimize_endpoint(self):
        body = {'element': 'vitalite', 'level': 50, 'totalPA': 6, 'totalPM': 3, 'exoPA': 0, 'exoPM': 0}
        resp = self.client.post('/api/optimize', json=body)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        if data:
            self.assertGreaterEqual(data[0]['totalPA'], 6)

    def test_bad_element_is_400(self):
        resp = self.client.post('/api/optimize', json={'element': 'nope'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.get_json())


if __name__ == '__main__':
    unittest.main()
