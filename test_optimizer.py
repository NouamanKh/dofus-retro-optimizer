import itertools
import random
import unittest

import catalog
from catalog import ALL_ELEMENTS, Catalog
from optimizer import _without_dominated, optimize, optimize_tradeoffs


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

    def test_gear_only_worth_wearing_for_damage_gives_one_build(self):
        builds = self.builds(Catalog([item('A', 'hat', force=10, sagesse=-1000)], []))
        self.assertEqual([i['id'] for b in builds for i in b['items']], ['A'])


class RoundDamageTest(unittest.TestCase):
    # At level 50 (6 PA) with a roll of 100, a point of Force is a point of damage per cast
    STRONG = item('STRONG', 'hat', force=100)  # 200 a cast on 6 PA
    QUICK = item('QUICK', 'hat', pa=2, force=10)  # 110 a cast on 8 PA

    def best(self, spell_pa, items=(STRONG, QUICK), roll=(100, 100), **kwargs):
        kwargs = {'total_pa': 6, 'total_pm': 3, **kwargs}
        return optimize(Catalog(list(items), []), 'force', 50, damage_range=roll, spell_pa=spell_pa, **kwargs)

    def ids(self, build):
        return [i['id'] for i in build['items']]

    def test_extra_cast_can_beat_a_harder_hit(self):
        build = self.best(4)
        self.assertEqual(self.ids(build), ['QUICK'])
        self.assertEqual((build['casts'], build['roundDamage'], build['damageRange']), (2, [220, 220], [110, 110]))

    def test_pa_that_adds_no_cast_is_worth_nothing(self):
        build = self.best(5)
        self.assertEqual((self.ids(build), build['casts']), (['STRONG'], 1))

    def test_cast_limit_caps_the_round(self):
        build = self.best(4, casts_max=1)
        self.assertEqual((self.ids(build), build['casts'], build['roundDamage']), (['STRONG'], 1, [200, 200]))

    def test_cast_limit_caps_a_build_with_spare_pa(self):
        self.assertEqual(self.best(2, casts_max=2)['casts'], 2)

    def test_exo_pa_counts_toward_casts(self):
        build = self.best(4, exo_pa=2)
        self.assertEqual((self.ids(build), build['casts']), (['STRONG'], 2))

    def test_pa_min_still_applies(self):
        build = self.best(6, total_pa=8)
        self.assertEqual((self.ids(build), build['casts']), (['QUICK'], 1))

    def test_gear_is_required_when_the_base_cannot_cast_once(self):
        self.assertEqual(self.ids(self.best(7)), ['QUICK'])

    def test_spell_nothing_can_cast_gives_no_build(self):
        self.assertIsNone(self.best(9))

    def test_each_cast_rounds_on_its_own(self):
        build = self.best(4, items=[dmg_item('A', 'hat', {'dmg': 5, 'pct_dmg': 3}, pa=2, force=7)], roll=(35, 35))
        # floor(35 x 1.10) + 5 = 43, twice; rounding after doubling would give 87
        self.assertEqual(build['roundDamage'], [86, 86])

    def test_range_and_average_cover_the_whole_round(self):
        build = self.best(4, roll=(100, 200))
        self.assertEqual((build['damageRange'], build['roundDamage'], build['roundAverage']), ([110, 220], [220, 440], 330))

    def test_more_pa_than_asked_for_counts_every_cast(self):
        build = self.best(4, items=[item('A', 'hat', pa=6, force=10)])
        self.assertEqual(build['casts'], 3)

    def test_spell_cost_is_optional(self):
        build = self.best(0)
        self.assertEqual((self.ids(build), build['casts'], build['roundDamage']), (['STRONG'], 1, build['damageRange']))

    def test_tradeoffs_compare_damage_per_round(self):
        cat = Catalog([self.QUICK, self.STRONG, item('SAGE', 'hat', pa=2, sagesse=50)], [])
        builds = optimize_tradeoffs(cat, 'force', 50, 6, 3, damage_range=(100, 100), spell_pa=4)
        self.assertEqual([self.ids(b) for b in builds], [['QUICK'], ['SAGE']])
        self.assertEqual([b['roundDamage'] for b in builds], [[220, 220], [200, 200]])


def random_catalog(rng):
    gear = [('hat', 3), ('ring', 4), ('boots', 2)]
    items = [dmg_item(f'{slot}{n}', slot, {'pct_dmg': rng.choice([0, 0, 10]), 'dmg': rng.choice([0, 0, 15])},
                      set=rng.choice([None, None, 'S', 'T']), pa=rng.choice([0, 0, 1, 2]),
                      force=rng.randint(-5, 60), sagesse=rng.randint(0, 40))
             for slot, count in gear for n in range(count)]
    sets = [{'name': name, 'items': [], 'bonuses': {'2': {'force': rng.randint(-20, 30), 'sagesse': rng.randint(0, 30), 'pa': rng.choice([0, 1])}}}
            for name in ('S', 'T')]
    return Catalog(items, sets)


def every_round(cat, roll, spell_pa, casts_max):
    """(damage per round, Sagesse) of every legal build that can cast the spell, worked out without the optimizer."""
    of_type = lambda slot: [i for i in cat.items if i['type'] == slot]
    choices = [[(), *((i,) for i in of_type('hat'))],
               [pair for n in range(3) for pair in itertools.combinations(of_type('ring'), n)],
               [(), *((i,) for i in of_type('boots'))]]
    rounds = []
    for parts in itertools.product(*choices):
        worn = [i for part in parts for i in part]
        pieces = {}
        for i in worn:
            if i['set']:
                pieces[i['set']] = pieces.get(i['set'], 0) + 1
        bonuses = [cat.active_bonus(name, count) for name, count in pieces.items()]
        force = sum(i['elements']['force'] for i in worn) + sum(b.get('force', 0) for b in bonuses)
        sagesse = sum(i['elements']['sagesse'] for i in worn) + sum(b.get('sagesse', 0) for b in bonuses)
        total_pa = 6 + sum(i['pa'] for i in worn) + sum(b.get('pa', 0) for b in bonuses)
        casts = min(total_pa // spell_pa, casts_max)
        if casts:
            percent = force + sum(i['stats']['pct_dmg'] for i in worn)
            rounds.append((casts * (roll * (100 + percent) / 100 + sum(i['stats']['dmg'] for i in worn)), sagesse))
    return rounds


class RoundDamageAgainstBruteForceTest(unittest.TestCase):
    ROLL = 100  # Whole damage, so the small Sagesse tie-break can't change which build wins

    def cases(self):
        for seed in range(12):
            rng = random.Random(seed)
            yield seed, random_catalog(rng), rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 99])

    def test_single_search_finds_the_most_damage_per_round(self):
        for seed, cat, spell_pa, casts_max in self.cases():
            rounds = every_round(cat, self.ROLL, spell_pa, casts_max)
            build = optimize(cat, 'force', 50, 6, 3, damage_range=(self.ROLL, self.ROLL), spell_pa=spell_pa, casts_max=casts_max)
            self.assertAlmostEqual(build['roundAverage'], max(d for d, _ in rounds), msg=seed)

    def test_tradeoffs_are_never_beaten_on_both_objectives(self):
        for seed, cat, spell_pa, casts_max in self.cases():
            rounds = every_round(cat, self.ROLL, spell_pa, casts_max)
            builds = optimize_tradeoffs(cat, 'force', 50, 6, 3, damage_range=(self.ROLL, self.ROLL), spell_pa=spell_pa, casts_max=casts_max)
            points = [(b['roundAverage'], b['totalStats']['sagesse']) for b in builds]
            self.assertAlmostEqual(points[0][0], max(d for d, _ in rounds), msg=seed)
            self.assertEqual(points[-1][1], max(s for _, s in rounds), seed)
            for (d1, s1), (d2, s2) in zip(points, points[1:]):
                self.assertTrue(d1 > d2 and s1 < s2, (seed, points))
            for damage, sagesse in points:
                best = max(d for d, s in rounds if s >= sagesse)
                self.assertAlmostEqual(damage, best, msg=(seed, points))


class WithoutDominatedTest(unittest.TestCase):
    def kept(self, *items):
        force = lambda i: (i['elements']['force'],)
        return sorted(i['id'] for i in _without_dominated(list(items), force))

    def test_drops_an_item_the_slot_has_no_room_for(self):
        self.assertEqual(self.kept(item('A', 'hat', force=9), item('B', 'hat', force=5)), ['A'])
        self.assertEqual(self.kept(item('A', 'ring', force=9), item('B', 'ring', force=5), item('C', 'ring', force=2)), ['A', 'B'])

    def test_keeps_one_of_identical_items_per_place_in_the_slot(self):
        self.assertEqual(len(self.kept(item('A', 'ring', force=9), item('B', 'ring', force=9), item('C', 'ring', force=9))), 2)

    def test_keeps_items_better_on_something_else(self):
        value = lambda i: (i['elements']['force'], i['pa'])
        items = [item('A', 'hat', force=9), item('B', 'hat', force=5, pa=1)]
        self.assertEqual(len(_without_dominated(items, value)), 2)

    def test_set_pieces_never_compete(self):
        # Wearing a set piece can change a bonus, so neither side of the comparison can be one
        self.assertEqual(self.kept(item('A', 'hat', force=9, set='S'), item('B', 'hat', force=5)), ['A', 'B'])
        self.assertEqual(self.kept(item('A', 'hat', force=9), item('B', 'hat', force=5, set='S')), ['A', 'B'])


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

    def test_round_damage_endpoint(self):
        body = {'element': 'force', 'level': 100, 'totalPA': 6, 'totalPM': 3, 'damageMin': 20, 'damageMax': 40, 'spellPA': 4}
        build = self.client.post('/api/optimize', json=body).get_json()[0]
        self.assertEqual(build['casts'], build['totalPA'] // 4)
        self.assertEqual(build['roundDamage'], [build['casts'] * d for d in build['damageRange']])
        limited = self.client.post('/api/optimize', json={**body, 'castsMax': 1}).get_json()[0]
        self.assertEqual(limited['casts'], 1)

    def test_bad_round_damage_requests_are_400(self):
        roll = {'element': 'force', 'damageMin': 20, 'damageMax': 40}
        for extra in [{'spellPA': -1}, {'spellPA': 21}, {'spellPA': 'x'}, {'castsMax': 0}, {'castsMax': 100}, {'castsMax': 'x'}]:
            self.assertEqual(self.client.post('/api/optimize', json={**roll, **extra}).status_code, 400, extra)
        self.assertEqual(self.client.post('/api/optimize', json={'element': 'force', 'spellPA': 4}).status_code, 400)

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
