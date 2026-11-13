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


def spell(low, high, pa=1, casts_max=1, name='SPELL'):
    return {'name': name, 'damageMin': low, 'damageMax': high, 'pa': pa, 'castsMax': casts_max}


def casts(build):
    return [s['casts'] for s in build['spells']]


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


def needs(it, *requirements):
    return dict(it, requirements=[{'type': t, 'value': v} if v is not None else {'type': t} for t, v in requirements])


class RequirementTest(unittest.TestCase):
    def worn(self, items, sets=(), element='vitalite', **args):
        build = optimize(Catalog(items, list(sets)), element, **{'level': 50, 'total_pa': 6, 'total_pm': 3, **args})
        return sorted(i['id'] for i in build['items'])

    def test_unmet_requirement_leaves_the_item_out(self):
        sword = needs(item('SWORD', 'weapon', vitalite=100), ('Force >', 50))
        self.assertEqual(self.worn([sword, item('STICK', 'weapon', vitalite=10), item('HAT', 'hat', vitalite=1, force=50)]), ['HAT', 'STICK'])

    def test_requirement_is_met_by_the_rest_of_the_gear(self):
        sword = needs(item('SWORD', 'weapon', vitalite=100), ('Force >', 50))
        # WEAK gives more of the target, but only STRONG lets the sword be worn
        self.assertEqual(self.worn([sword, item('WEAK', 'hat', vitalite=20), item('STRONG', 'hat', force=51)]), ['STRONG', 'SWORD'])

    def test_own_stats_do_not_meet_its_requirement(self):
        sword = needs(item('SWORD', 'weapon', vitalite=100, force=99), ('Force >', 50))
        self.assertEqual(self.worn([sword, item('STICK', 'weapon', vitalite=10)]), ['STICK'])

    def test_set_bonus_counts_toward_a_requirement(self):
        sword = needs(item('SWORD', 'weapon', vitalite=100), ('Force >', 50))
        pieces = [item('A', 'hat', set='S'), item('B', 'boots', set='S')]
        sets = [{'name': 'S', 'items': [], 'bonuses': {'2': {'force': 51}}}]
        self.assertEqual(self.worn([sword, *pieces], sets), ['A', 'B', 'SWORD'])

    def test_every_requirement_must_be_met(self):
        sword = needs(item('SWORD', 'weapon', vitalite=100), ('Force >', 50), ('Agilité >', 50))
        self.assertEqual(self.worn([sword, item('HAT', 'hat', vitalite=1, force=51)]), ['HAT'])

    def test_requirement_the_search_cannot_check_leaves_the_item_out(self):
        for requirement in [('Classe doit etre Iop', None), ('Alignement doit etre Bonta', None), ('Grace >', 2), ('Force <', 40)]:
            sword = needs(item('SWORD', 'weapon', vitalite=100), requirement)
            self.assertEqual(self.worn([sword, item('STICK', 'weapon', vitalite=10)]), ['STICK'])

    def test_pm_requirement_counts_base_and_exo_pm(self):
        items = [needs(item('SWORD', 'weapon', vitalite=100), ('PM >', 3)), item('STICK', 'weapon', vitalite=10)]
        self.assertEqual(self.worn(items), ['STICK'])
        self.assertEqual(self.worn(items, total_pm=4, exo_pm=1), ['SWORD'])

    def test_real_builds_meet_their_requirements(self):
        cat = catalog.load()
        stat = {'Vitalité >': 'vitalite', 'Sagesse >': 'sagesse', 'Force >': 'force', 'Intelligence >': 'intelligence', 'Chance >': 'chance', 'Agilité >': 'agilite'}
        conditional = 0
        for element, level in itertools.product(['force', 'intelligence', 'chance', 'agilite', 'vitalite', 'sagesse'], [60, 120, 200]):
            build = optimize(cat, element, level, total_pa=6, total_pm=3)
            for worn in build['items']:
                for req in worn.get('requirements') or []:
                    conditional += 1
                    self.assertGreater(build['totalStats'][stat[req['type']]] - worn['elements'][stat[req['type']]], req['value'], worn['name'])
        self.assertGreater(conditional, 0)


class DamageTest(unittest.TestCase):
    def best(self, cat, element='force', base=30):
        return optimize(cat, element, level=50, total_pa=6, total_pm=3, spells=[spell(base, base)])

    def test_formula_rounds_multiplied_part_down_then_adds_flat(self):
        cat = Catalog([dmg_item('A', 'hat', {'dmg': 5, 'pct_dmg': 3}, force=7)], [])
        # floor(33 x (100 + 7 + 3) / 100) + 5 = floor(36.3) + 5
        self.assertEqual(self.best(cat, base=33)['totalElement'], 41)

    def test_each_end_of_the_range_is_estimated(self):
        cat = Catalog([dmg_item('A', 'hat', {'dmg': 5, 'pct_dmg': 3}, force=7)], [])
        build = optimize(cat, 'force', level=50, total_pa=6, total_pm=3, spells=[spell(33, 50)])
        # floor(33 x 1.10) + 5 and floor(50 x 1.10) + 5
        self.assertEqual(build['spells'], [{**spell(33, 50), 'casts': 1, 'damageRange': [41, 60]}])
        # The average roll, 41.5: floor(41.5 x 1.10) + 5
        self.assertEqual(build['totalElement'], 50)

    def test_average_roll_decides_the_build(self):
        cat = Catalog([item('S', 'hat', force=100), dmg_item('F', 'hat', {'dmg': 40})], [])
        # Both ends sit on either side of the break-even point of 40: only the average matters
        pick = lambda low, high: [i['id'] for i in optimize(
            cat, 'force', level=50, total_pa=6, total_pm=3, spells=[spell(low, high)])['items']]
        self.assertEqual(pick(10, 90), ['S'])  # average 50
        self.assertEqual(pick(10, 50), ['F'])  # average 30

    def test_stat_search_has_no_spells(self):
        build = optimize(Catalog([item('S', 'hat', force=1)], []), 'force', level=50, total_pa=6, total_pm=3)
        self.assertEqual(build['spells'], [])
        self.assertIsNone(build['roundDamage'])

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
        return optimize_tradeoffs(cat, 'force', 50, spells=[spell(*roll)], **kwargs)

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

    def best(self, spell_pa, items=(STRONG, QUICK), roll=(100, 100), casts_max=99, **kwargs):
        kwargs = {'total_pa': 6, 'total_pm': 3, **kwargs}
        return optimize(Catalog(list(items), []), 'force', 50, spells=[spell(*roll, spell_pa, casts_max)], **kwargs)

    def ids(self, build):
        return [i['id'] for i in build['items']]

    def test_extra_cast_can_beat_a_harder_hit(self):
        build = self.best(4)
        self.assertEqual(self.ids(build), ['QUICK'])
        self.assertEqual((casts(build), build['roundDamage'], build['spells'][0]['damageRange']), ([2], [220, 220], [110, 110]))

    def test_pa_that_adds_no_cast_is_worth_nothing(self):
        build = self.best(5)
        self.assertEqual((self.ids(build), casts(build)), (['STRONG'], [1]))

    def test_cast_limit_caps_the_round(self):
        build = self.best(4, casts_max=1)
        self.assertEqual((self.ids(build), casts(build), build['roundDamage']), (['STRONG'], [1], [200, 200]))

    def test_cast_limit_caps_a_build_with_spare_pa(self):
        self.assertEqual(casts(self.best(2, casts_max=2)), [2])

    def test_exo_pa_counts_toward_casts(self):
        build = self.best(4, exo_pa=2)
        self.assertEqual((self.ids(build), casts(build)), (['STRONG'], [2]))

    def test_pa_min_still_applies(self):
        build = self.best(6, total_pa=8)
        self.assertEqual((self.ids(build), casts(build)), (['QUICK'], [1]))

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
        self.assertEqual((build['spells'][0]['damageRange'], build['roundDamage'], build['roundAverage']), ([110, 220], [220, 440], 330))

    def test_more_pa_than_asked_for_counts_every_cast(self):
        build = self.best(4, items=[item('A', 'hat', pa=6, force=10)])
        self.assertEqual(casts(build), [3])

    def round(self, spells, items=(STRONG, QUICK), **kwargs):
        return optimize(Catalog(list(items), []), 'force', 50, 6, 3, spells=spells, **kwargs)

    def test_round_mixes_spells_to_use_the_pa(self):
        # 6 PA at 2 damage a point of base: HEAVY and LIGHT do 280, three LIGHT 240, HEAVY alone 200
        build = self.round([spell(100, 100, 4, 99, 'HEAVY'), spell(40, 40, 2, 99, 'LIGHT')], items=[self.STRONG])
        self.assertEqual((casts(build), build['roundDamage']), ([1, 1], [280, 280]))

    def test_cast_limit_sends_spare_pa_to_another_spell(self):
        build = self.round([spell(100, 100, 2, 1, 'ONCE'), spell(10, 10, 2, 99, 'FILLER')], items=[self.STRONG])
        self.assertEqual((casts(build), build['roundDamage']), ([1, 2], [240, 240]))

    def test_spell_not_worth_its_pa_is_not_cast(self):
        build = self.round([spell(100, 100, 3, 99, 'GOOD'), spell(100, 100, 4, 99, 'COSTLY')], items=[self.STRONG])
        self.assertEqual(casts(build), [2, 0])

    def test_gear_and_spells_are_chosen_together(self):
        # STRONG casts BIG once for 400; QUICK's 8 PA cast SMALL twice for 2 x 209
        build = self.round([spell(200, 200, 6, 1, 'BIG'), spell(190, 190, 4, 99, 'SMALL')])
        self.assertEqual((self.ids(build), casts(build)), (['QUICK'], [0, 2]))
        # With SMALL limited to one cast, BIG on STRONG wins again
        build = self.round([spell(200, 200, 6, 1, 'BIG'), spell(190, 190, 4, 1, 'SMALL')])
        self.assertEqual((self.ids(build), casts(build)), (['STRONG'], [1, 0]))

    def test_flat_damage_favours_many_small_casts(self):
        flat = dmg_item('FLAT', 'hat', {'dmg': 50})
        spells = [spell(60, 60, 6, 99, 'BIG'), spell(10, 10, 2, 99, 'SMALL')]
        self.assertEqual(casts(self.round(spells, items=[flat])), [0, 3])  # 3 x 60 against 110
        self.assertEqual(casts(self.round(spells, items=[self.STRONG])), [1, 0])  # 120 against 3 x 20

    def test_tradeoffs_compare_damage_per_round(self):
        cat = Catalog([self.QUICK, self.STRONG, item('SAGE', 'hat', pa=2, sagesse=50)], [])
        builds = optimize_tradeoffs(cat, 'force', 50, 6, 3, spells=[spell(100, 100, 4, 99)])
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


def best_round(spells, total_pa, percent, flat):
    """Most damage a round of these spells does on total_pa, trying every number of casts of each; None if none can be cast."""
    best = None
    for counts in itertools.product(*(range(min(s['castsMax'], total_pa // s['pa']) + 1) for s in spells)):
        if any(counts) and sum(n * s['pa'] for n, s in zip(counts, spells)) <= total_pa:
            damage = sum(n * ((s['damageMin'] + s['damageMax']) / 2 * (100 + percent) / 100 + flat) for n, s in zip(counts, spells))
            best = damage if best is None else max(best, damage)
    return best


def every_round(cat, spells):
    """(damage per round, Sagesse) of every legal build that can cast a spell, worked out without the optimizer."""
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
        damage = best_round(spells, total_pa, force + sum(i['stats']['pct_dmg'] for i in worn), sum(i['stats']['dmg'] for i in worn))
        if damage is not None:
            rounds.append((damage, sagesse))
    return rounds


class RoundDamageAgainstBruteForceTest(unittest.TestCase):
    def cases(self):
        for seed in range(12):
            rng = random.Random(seed)
            # Rolls of whole hundreds give whole damage, so the small Sagesse tie-break can't change which build wins
            spells = [spell(roll, roll, rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 99]), n)
                      for n, roll in enumerate(rng.sample([100, 200, 300], rng.choice([1, 2, 3])))]
            yield seed, random_catalog(rng), spells

    def test_single_search_finds_the_most_damage_per_round(self):
        for seed, cat, spells in self.cases():
            rounds = every_round(cat, spells)
            build = optimize(cat, 'force', 50, 6, 3, spells=spells)
            self.assertAlmostEqual(build['roundAverage'], max(d for d, _ in rounds), msg=seed)
            self.assertLessEqual(sum(s['casts'] * s['pa'] for s in build['spells']), build['totalPA'], seed)

    def test_tradeoffs_are_never_beaten_on_both_objectives(self):
        for seed, cat, spells in self.cases():
            rounds = every_round(cat, spells)
            builds = optimize_tradeoffs(cat, 'force', 50, 6, 3, spells=spells)
            points = [(b['roundAverage'], b['totalStats']['sagesse']) for b in builds]
            self.assertAlmostEqual(points[0][0], max(d for d, _ in rounds), msg=seed)
            self.assertEqual(points[-1][1], max(s for _, s in rounds), seed)
            for (d1, s1), (d2, s2) in zip(points, points[1:]):
                self.assertTrue(d1 > d2 and s1 < s2, (seed, points))
            for damage, sagesse in points:
                best = max(d for d, s in rounds if s >= sagesse)
                self.assertAlmostEqual(damage, best, msg=(seed, points))


class ClassSpellsTest(unittest.TestCase):
    def grade(self, level, pa=3, per_turn=0, per_target=0, cooldown=0, damage=({'element': 'terre', 'min': 10, 'max': 20},)):
        return {'level': level, 'pa': pa, 'castsPerTurn': per_turn, 'castsPerTarget': per_target, 'cooldown': cooldown, 'damage': list(damage)}

    def found(self, grades, element='force', level=50, class_name='Iop'):
        return catalog.class_spells([{'class': 'Iop', 'name': 'S', 'grades': grades}], class_name, element, level)

    def test_takes_the_highest_grade_the_level_allows(self):
        grades = [self.grade(10, pa=5), self.grade(10, pa=4), self.grade(110, pa=3)]
        self.assertEqual(self.found(grades, level=9), [])
        self.assertEqual([(s['grade'], s['pa']) for s in self.found(grades, level=109)], [(2, 4)])
        self.assertEqual([(s['grade'], s['pa']) for s in self.found(grades, level=110)], [(3, 3)])

    def test_only_the_class_and_the_stat_s_elements(self):
        lines = [{'element': 'terre', 'min': 10, 'max': 20}, {'element': 'neutre', 'min': 1, 'max': 2}, {'element': 'feu', 'min': 5, 'max': 6}]
        grades = [self.grade(1, damage=lines)]
        self.assertEqual([(s['damageMin'], s['damageMax']) for s in self.found(grades)], [(11, 22)])
        self.assertEqual([(s['damageMin'], s['damageMax']) for s in self.found(grades, element='intelligence')], [(5, 6)])
        self.assertEqual(self.found(grades, element='chance'), [])
        self.assertEqual(self.found(grades, class_name='Sram'), [])

    def test_poisons_traps_and_glyphs_are_left_out_and_a_chance_counts_for_its_share(self):
        lines = [{'element': 'terre', 'min': 10, 'max': 20, 'chance': 50}, {'element': 'terre', 'min': 99, 'max': 99, 'duration': 2},
                 {'element': 'terre', 'min': 99, 'max': 99, 'via': 'piege'}]
        self.assertEqual([(s['damageMin'], s['damageMax']) for s in self.found([self.grade(1, damage=lines)])], [(5, 10)])

    def test_casts_are_limited_for_one_round_on_one_target(self):
        limit = lambda **limits: self.found([self.grade(1, **limits)])[0]['castsMax']
        self.assertEqual(limit(), 99)
        self.assertEqual(limit(per_turn=3, per_target=2), 2)
        self.assertEqual(limit(per_turn=3, cooldown=4), 1)

    def test_real_spells(self):
        spells = catalog.load_spells()
        self.assertEqual(len({s['class'] for s in spells}), 12)
        pression = lambda level: next(s for s in catalog.class_spells(spells, 'Iop', 'force', level) if s['name'] == 'Pression')
        # Checked against wiki-dofus.eu's Pression page
        self.assertEqual(pression(100), {'name': 'Pression', 'grade': 5, 'pa': 3, 'castsMax': 99, 'damageMin': 8, 'damageMax': 12})
        self.assertEqual(pression(101), {'name': 'Pression', 'grade': 6, 'pa': 2, 'castsMax': 99, 'damageMin': 9, 'damageMax': 13})


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

    def test_items_with_requirements_never_drop_another(self):
        sword = needs(item('SWORD', 'weapon', force=50), ('Agilité >', 10))
        self.assertEqual(self.kept(sword, item('STICK', 'weapon', force=10)), ['STICK', 'SWORD'])
        self.assertEqual(self.kept(sword, item('AXE', 'weapon', force=50)), ['AXE'])

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
        builds = optimize_tradeoffs(cat, 'force', 100, spells=[spell(20, 40)], **args)
        self.assertGreater(len(builds), 1)
        self.assertEqual(builds[0]['totalElement'], optimize(cat, 'force', 100, spells=[spell(20, 40)], **args)['totalElement'])
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

    def test_damage_endpoint_casts_the_class_spells(self):
        body = {'element': 'force', 'level': 101, 'totalPA': 6, 'totalPM': 3, 'spellClass': 'Iop'}
        build = self.client.post('/api/optimize', json=body).get_json()[0]
        self.assertEqual([s['name'] for s in build['spells']], ['Pression', 'Intimidation', 'Concentration', 'Epée de Iop', 'Colère de Iop'])
        multiplier = 100 + build['totalStats']['force'] + build['totalPctDmg']
        for cast in build['spells']:
            self.assertEqual(cast['damageRange'], [roll * multiplier // 100 + build['totalDmg'] for roll in (cast['damageMin'], cast['damageMax'])])
            self.assertLessEqual(cast['casts'], cast['castsMax'])
        self.assertLessEqual(sum(s['casts'] * s['pa'] for s in build['spells']), build['totalPA'])
        self.assertEqual(build['roundDamage'], [sum(s['casts'] * s['damageRange'][end] for s in build['spells']) for end in (0, 1)])

    def test_class_without_a_spell_in_the_element_gives_nothing(self):
        body = {'element': 'chance', 'level': 1, 'spellClass': 'Sram'}
        self.assertEqual(self.client.post('/api/optimize', json=body).get_json(), [])

    def test_bad_damage_requests_are_400(self):
        for body in [{'element': 'vitalite', 'spellClass': 'Iop'}, {'element': 'force', 'spellClass': 'Nope'}, {'element': 'force', 'spellClass': 3},
                     {'element': 'force', 'spellClass': ['Iop']}]:
            self.assertEqual(self.client.post('/api/optimize', json=body).status_code, 400, body)

    def test_with_sagesse_returns_several_builds(self):
        body = {'element': 'force', 'level': 100, 'totalPA': 6, 'totalPM': 3, 'spellClass': 'Iop', 'withSagesse': True}
        builds = self.client.post('/api/optimize', json=body).get_json()
        self.assertGreater(len(builds), 1)
        self.assertEqual(len(self.client.post('/api/optimize', json={**body, 'withSagesse': False}).get_json()), 1)

    def test_bad_with_sagesse_is_400(self):
        self.assertEqual(self.client.post('/api/optimize', json={'element': 'force', 'spellClass': 'Iop', 'withSagesse': 'yes'}).status_code, 400)
        self.assertEqual(self.client.post('/api/optimize', json={'element': 'force', 'withSagesse': True}).status_code, 400)

    def test_bad_excluded_ids_is_400(self):
        for bad in ['retro_1', [1], {'a': 1}, [['retro_1']]]:
            resp = self.client.post('/api/optimize', json={'element': 'force', 'excludedIds': bad})
            self.assertEqual(resp.status_code, 400, bad)


if __name__ == '__main__':
    unittest.main()
