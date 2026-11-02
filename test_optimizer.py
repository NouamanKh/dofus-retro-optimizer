import unittest

import catalog
from catalog import ALL_ELEMENTS, Catalog
from optimizer import optimize


def item(id, type, level=1, set=None, pa=0, pm=0, **elements):
    el = {e: 0 for e in ALL_ELEMENTS}
    el.update(elements)
    return {'id': id, 'name': id, 'type': type, 'level': level, 'elements': el,
            'pa': pa, 'pm': pm, 'stats': {}, 'set': set}


def dmg_item(id, type, stats, set=None, **elements):
    return dict(item(id, type, set=set, **elements), stats=stats)


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

    def test_excluded_item_is_replaced_by_next_best(self):
        cat = Catalog([item('X', 'hat', vitalite=50), item('Y', 'hat', vitalite=10)], [])
        build = optimize(cat, 'vitalite', level=50, total_pa=6, total_pm=3, excluded_ids={'X'})
        self.assertEqual([i['id'] for i in build['items']], ['Y'])

    def test_excluding_covers_copies_with_same_name_and_type_only(self):
        # Real case: 11 identical "Patte d'Ecaflip" weapons, and "Nomoon" is both a weapon and a pet
        cat = Catalog(
            [dict(item('W1', 'weapon', vitalite=50), name='Same'),
             dict(item('W2', 'weapon', vitalite=50), name='Same'),
             dict(item('P', 'pet', vitalite=20), name='Same'),
             item('B', 'weapon', vitalite=10)], [])
        build = optimize(cat, 'vitalite', level=50, total_pa=6, total_pm=3, excluded_ids={'W1'})
        self.assertEqual(sorted(i['id'] for i in build['items']), ['B', 'P'])

    def test_excluded_piece_breaks_set_bonus(self):
        cat = Catalog(
            [item('A', 'hat', set='S', vitalite=10),
             item('B', 'boots', set='S', vitalite=10),
             item('C', 'hat', vitalite=5)],
            [{'name': 'S', 'items': [], 'bonuses': {'2': {'vitalite': 20}}}])
        build = optimize(cat, 'vitalite', level=50, total_pa=6, total_pm=3, excluded_ids={'A'})
        self.assertEqual(sorted(i['id'] for i in build['items']), ['B', 'C'])
        self.assertEqual(build['setBonus'], 0)
        self.assertEqual(build['totalElement'], 15)

    def test_excluding_only_way_to_reach_pa_gives_no_build(self):
        cat = Catalog([item('X', 'hat', pa=1, vitalite=5), item('Y', 'hat', vitalite=50)], [])
        self.assertIsNone(optimize(cat, 'vitalite', level=50, total_pa=7, total_pm=3, excluded_ids={'X'}))


class DamageTest(unittest.TestCase):
    def best(self, cat, element='force', base=30):
        return optimize(cat, element, level=50, total_pa=6, total_pm=3, damage_base=base)

    def test_formula_rounds_multiplied_part_down_then_adds_flat(self):
        cat = Catalog([dmg_item('A', 'hat', {'dmg': 5, 'pct_dmg': 3}, force=7)], [])
        # floor(33 x (100 + 7 + 3) / 100) + 5 = floor(36.3) + 5
        self.assertEqual(self.best(cat, base=33)['totalElement'], 41)

    def test_spell_base_decides_between_stat_and_flat(self):
        cat = Catalog([item('S', 'hat', force=100), dmg_item('F', 'hat', {'dmg': 40})], [])
        self.assertEqual([i['id'] for i in self.best(cat, base=50)['items']], ['S'])
        self.assertEqual([i['id'] for i in self.best(cat, base=30)['items']], ['F'])

    def test_percent_counts_like_the_element_stat(self):
        cat = Catalog([item('S', 'hat', force=10), dmg_item('P', 'hat', {'pct_dmg': 20})], [])
        self.assertEqual([i['id'] for i in self.best(cat)['items']], ['P'])

    def test_only_the_chosen_element_counts(self):
        cat = Catalog([item('C', 'hat', chance=500), item('S', 'hat', force=10)], [])
        self.assertEqual([i['id'] for i in self.best(cat)['items']], ['S'])
        self.assertEqual([i['id'] for i in self.best(cat, element='chance')['items']], ['C'])

    def test_set_damage_bonuses_count(self):
        cat = Catalog(
            [item('A', 'hat', set='S', force=10),
             item('B', 'boots', set='S', force=10),
             item('C', 'hat', force=30)],
            [{'name': 'S', 'items': [], 'bonuses': {'2': {'dmg': 20, 'pct_dmg': 10}}}])
        build = self.best(cat, base=100)
        self.assertEqual(sorted(i['id'] for i in build['items']), ['A', 'B'])
        self.assertEqual((build['totalDmg'], build['totalPctDmg']), (20, 10))
        # floor(100 x (100 + 20 + 10) / 100) + 20
        self.assertEqual(build['totalElement'], 150)

    def test_stat_search_ignores_damage(self):
        cat = Catalog([dmg_item('F', 'hat', {'dmg': 500}), item('S', 'hat', force=1)], [])
        build = optimize(cat, 'force', level=50, total_pa=6, total_pm=3)
        self.assertEqual([i['id'] for i in build['items']], ['S'])
        self.assertEqual(build['totalElement'], 1)


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

    def test_real_damage_data(self):
        cat = catalog.load()
        by_name = {i['name']: i for i in cat.items}
        # Class items: "Dommage" beside spell lines applies to one spell
        self.assertNotIn('dmg', by_name['Cape Aillé']['stats'])
        # "Renvois de dommages" is not damage
        self.assertEqual(by_name['Sulik']['stats'].get('dmg_return'), 11)
        self.assertNotIn('dmg', by_name['Sulik']['stats'])
        # Set bonuses: flat and % stay apart ("% Dommages" used to read as flat)
        tiers = [t for bonuses in cat.set_bonuses.values() for t in bonuses.values()]
        self.assertEqual(sum('dmg' in t for t in tiers), 153)
        self.assertEqual(sum('pct_dmg' in t for t in tiers), 19)


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

    def test_excluded_ids_reach_the_optimizer(self):
        body = {'element': 'force', 'level': 100, 'totalPA': 6, 'totalPM': 3}
        first = self.client.post('/api/optimize', json=body).get_json()[0]
        banned = first['items'][0]
        again = self.client.post('/api/optimize', json={**body, 'excludedIds': [banned['id']]}).get_json()[0]
        self.assertNotIn((banned['name'], banned['type']), [(i['name'], i['type']) for i in again['items']])
        self.assertLessEqual(again['totalElement'], first['totalElement'])

    def test_damage_endpoint_reports_the_estimate(self):
        body = {'element': 'force', 'level': 100, 'totalPA': 6, 'totalPM': 3, 'damageBase': 30}
        build = self.client.post('/api/optimize', json=body).get_json()[0]
        self.assertEqual(build['damageBase'], 30)
        multiplied = 30 * (100 + build['totalStats']['force'] + build['totalPctDmg']) // 100
        self.assertEqual(build['totalElement'], multiplied + build['totalDmg'])

    def test_bad_damage_requests_are_400(self):
        for body in [{'element': 'vitalite', 'damageBase': 30},
                     {'element': 'force', 'damageBase': -1},
                     {'element': 'force', 'damageBase': 1000},
                     {'element': 'force', 'damageBase': 'x'}]:
            self.assertEqual(self.client.post('/api/optimize', json=body).status_code, 400, body)

    def test_bad_excluded_ids_is_400(self):
        for bad in ['retro_1', [1], {'a': 1}, [['retro_1']]]:
            resp = self.client.post('/api/optimize', json={'element': 'force', 'excludedIds': bad})
            self.assertEqual(resp.status_code, 400, bad)


if __name__ == '__main__':
    unittest.main()
