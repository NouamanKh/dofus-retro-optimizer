import unittest

import catalog
from catalog import ALL_ELEMENTS, Catalog
from optimizer import optimize, optimize_tradeoffs


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
        return optimize(cat, element, level=50, total_pa=6, total_pm=3, damage_range=(base, base))

    def test_formula_rounds_multiplied_part_down_then_adds_flat(self):
        cat = Catalog([dmg_item('A', 'hat', {'dmg': 5, 'pct_dmg': 3}, force=7)], [])
        # floor(33 x (100 + 7 + 3) / 100) + 5 = floor(36.3) + 5
        self.assertEqual(self.best(cat, base=33)['totalElement'], 41)

    def test_each_end_of_the_range_is_estimated(self):
        cat = Catalog([dmg_item('A', 'hat', {'dmg': 5, 'pct_dmg': 3}, force=7)], [])
        build = optimize(cat, 'force', level=50, total_pa=6, total_pm=3, damage_range=(33, 50))
        # floor(33 x 1.10) + 5 and floor(50 x 1.10) + 5
        self.assertEqual(build['damageRange'], [41, 60])
        self.assertEqual(list(build['spellRoll']), [33, 50])
        # The average roll, 41.5: floor(41.5 x 1.10) + 5
        self.assertEqual(build['totalElement'], 50)

    def test_average_roll_decides_the_build(self):
        cat = Catalog([item('S', 'hat', force=100), dmg_item('F', 'hat', {'dmg': 40})], [])
        # Both ends sit on either side of the break-even point of 40: only the average matters
        pick = lambda low, high: [i['id'] for i in optimize(
            cat, 'force', level=50, total_pa=6, total_pm=3, damage_range=(low, high))['items']]
        self.assertEqual(pick(10, 90), ['S'])  # average 50
        self.assertEqual(pick(10, 50), ['F'])  # average 30

    def test_stat_search_has_no_damage_range(self):
        build = optimize(Catalog([item('S', 'hat', force=1)], []), 'force', level=50, total_pa=6, total_pm=3)
        self.assertIsNone(build['damageRange'])
        self.assertIsNone(build['spellRoll'])

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


class TradeoffTest(unittest.TestCase):
    def builds(self, cat, roll=(100, 100), **kwargs):
        kwargs = {'total_pa': 6, 'total_pm': 3, **kwargs}
        return optimize_tradeoffs(cat, 'force', 50, damage_range=roll, **kwargs)

    def test_goes_from_most_damage_to_most_sagesse(self):
        cat = Catalog([item('D', 'hat', force=100), item('M', 'hat', force=50, sagesse=50), item('W', 'hat', sagesse=100)], [])
        self.assertEqual([[i['id'] for i in b['items']] for b in self.builds(cat)], [['D'], ['M'], ['W']])

    def test_each_build_has_the_most_damage_for_its_sagesse(self):
        cat = Catalog(
            [item('D', 'hat', force=100), item('W', 'hat', sagesse=100),
             item('Worse', 'hat', force=10, sagesse=50), item('Better', 'hat', force=60, sagesse=50)], [])
        ids = [b['items'][0]['id'] for b in self.builds(cat)]
        self.assertEqual(ids, ['D', 'Better', 'W'])

    def test_slots_without_damage_are_filled_with_sagesse(self):
        cat = Catalog([item('F', 'hat', force=100), item('B', 'boots', sagesse=30), item('E', 'boots')], [])
        builds = self.builds(cat)
        self.assertEqual(len(builds), 1)
        self.assertEqual(sorted(i['id'] for i in builds[0]['items']), ['B', 'F'])

    def test_no_conflict_gives_one_build(self):
        cat = Catalog([item('A', 'hat', force=100, sagesse=100), item('C', 'hat', force=1)], [])
        self.assertEqual([i['id'] for i in self.builds(cat)[0]['items']], ['A'])
        self.assertEqual(len(self.builds(cat)), 1)

    def test_set_sagesse_counts(self):
        cat = Catalog(
            [item('A', 'hat', set='S'), item('B', 'boots', set='S'), item('C', 'hat', sagesse=20), item('F', 'hat', force=5)],
            [{'name': 'S', 'items': [], 'bonuses': {'2': {'sagesse': 50}}}])
        last = self.builds(cat)[-1]
        self.assertEqual(sorted(i['id'] for i in last['items']), ['A', 'B'])
        self.assertEqual(last['totalStats']['sagesse'], 50)

    def test_pa_and_exclusions_apply_to_every_build(self):
        cat = Catalog(
            [item('P', 'hat', pa=1, force=5), item('D', 'hat', force=100), item('W', 'boots', sagesse=50, pa=1), item('V', 'boots', sagesse=90)], [])
        builds = self.builds(cat, total_pa=7, excluded_ids={'V'})
        self.assertTrue(builds)
        for build in builds:
            self.assertGreaterEqual(build['totalPA'], 7)
            self.assertNotIn('V', [i['id'] for i in build['items']])

    def test_impossible_requirement_gives_nothing(self):
        self.assertEqual(self.builds(Catalog([item('F', 'hat', force=1)], []), total_pa=7), [])

    def test_nothing_useful_gives_nothing(self):
        self.assertEqual(self.builds(Catalog([item('E', 'hat')], [])), [])


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

    def test_real_tradeoffs_end_on_the_single_objective_optimum(self):
        cat = catalog.load()
        args = {'total_pa': 6, 'total_pm': 3}
        builds = optimize_tradeoffs(cat, 'force', 100, damage_range=(20, 40), **args)
        self.assertGreater(len(builds), 1)
        self.assertEqual(builds[0]['totalElement'], optimize(cat, 'force', 100, damage_range=(20, 40), **args)['totalElement'])
        self.assertEqual(builds[-1]['totalStats']['sagesse'], optimize(cat, 'sagesse', 100, **args)['totalElement'])
        for less, more in zip(builds, builds[1:]):
            self.assertLess(less['totalStats']['sagesse'], more['totalStats']['sagesse'])
            self.assertGreater(less['totalElement'], more['totalElement'])

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
        body = {'element': 'force', 'level': 100, 'totalPA': 6, 'totalPM': 3, 'damageMin': 20, 'damageMax': 40}
        build = self.client.post('/api/optimize', json=body).get_json()[0]
        self.assertEqual(build['spellRoll'], [20, 40])
        multiplier = 100 + build['totalStats']['force'] + build['totalPctDmg']
        self.assertEqual(build['damageRange'], [roll * multiplier // 100 + build['totalDmg'] for roll in (20, 40)])

    def test_bad_damage_requests_are_400(self):
        for body in [{'element': 'vitalite', 'damageMin': 20, 'damageMax': 40},
                     {'element': 'force', 'damageMin': 40, 'damageMax': 20},
                     {'element': 'force', 'damageMin': -1, 'damageMax': 20},
                     {'element': 'force', 'damageMin': 0, 'damageMax': 20},
                     {'element': 'force', 'damageMin': 20},
                     {'element': 'force', 'damageMax': 20},
                     {'element': 'force', 'damageMin': 20, 'damageMax': 1000},
                     {'element': 'force', 'damageMin': 'x', 'damageMax': 20}]:
            self.assertEqual(self.client.post('/api/optimize', json=body).status_code, 400, body)

    def test_with_sagesse_returns_several_builds(self):
        body = {'element': 'force', 'level': 100, 'totalPA': 6, 'totalPM': 3, 'damageMin': 20, 'damageMax': 40, 'withSagesse': True}
        builds = self.client.post('/api/optimize', json=body).get_json()
        self.assertGreater(len(builds), 1)
        self.assertEqual(len(self.client.post('/api/optimize', json={**body, 'withSagesse': False}).get_json()), 1)

    def test_bad_with_sagesse_is_400(self):
        roll = {'element': 'force', 'damageMin': 20, 'damageMax': 40}
        self.assertEqual(self.client.post('/api/optimize', json={**roll, 'withSagesse': 'yes'}).status_code, 400)
        self.assertEqual(self.client.post('/api/optimize', json={'element': 'force', 'withSagesse': True}).status_code, 400)

    def test_bad_excluded_ids_is_400(self):
        for bad in ['retro_1', [1], {'a': 1}, [['retro_1']]]:
            resp = self.client.post('/api/optimize', json={'element': 'force', 'excludedIds': bad})
            self.assertEqual(resp.status_code, 400, bad)


if __name__ == '__main__':
    unittest.main()
