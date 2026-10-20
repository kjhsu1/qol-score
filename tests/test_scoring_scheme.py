"""Business examples and invariants for the two-route scoring scheme."""
from datetime import datetime
from itertools import product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'For_new_users' / 'Scripts'))
from core import calculate_qol_score


def day(**changes):
    # Exactly 900 minutes awake, so 9 focused minutes = one percentage point.
    return dict(dict(wake_time='2026-10-20T08:30:00', sleep_time='2026-10-20T23:30:00',
                     todays_date='2026-10-20', exercise='Yes', outside='Yes', talk='Yes',
                     social_media='0', time_focused='540', offday_special_day='No'), **changes)


def missed(count):
    return {field: 'No' if index < count else 'Yes'
            for index, field in enumerate(('exercise', 'outside', 'talk'))}


class TwoRouteScoringTests(unittest.TestCase):
    def test_healthy_examples(self):
        for focused, score in [(405,85), (450,90), (495,95), (540,100)]:
            with self.subTest(focused=focused):
                self.assertAlmostEqual(calculate_qol_score(day(time_focused=str(focused))),score)

    def test_healthy_missed_habit_deductions(self):
        for count, score in [(0,95), (1,85), (2,75), (3,68.5)]:
            # At three missed habits, the productive route overtakes healthy.
            with self.subTest(count=count):
                self.assertAlmostEqual(calculate_qol_score(day(time_focused='495',**missed(count))),score)

    def test_productive_habits_still_matter_at_seventy_percent(self):
        for count, score in [(0,100), (1,97), (2,94), (3,91)]:
            with self.subTest(count=count):
                self.assertAlmostEqual(calculate_qol_score(day(time_focused='630',**missed(count))),score)

    def test_extra_focus_compensates_for_each_missed_habit(self):
        for count, focused in [(1,648), (2,666), (3,684)]:
            with self.subTest(count=count):
                self.assertAlmostEqual(calculate_qol_score(day(time_focused=str(focused),**missed(count))),100)
                self.assertAlmostEqual(calculate_qol_score(day(time_focused=str(focused-9),**missed(count))),98.5)

    def test_better_route_is_selected_below_seventy_percent(self):
        for count, score in [(0,100), (1,90), (2,86.5), (3,83.5)]:
            with self.subTest(count=count):
                self.assertAlmostEqual(calculate_qol_score(day(time_focused='585',**missed(count))),score)

    def test_more_focus_never_lowers_score_or_causes_a_cliff(self):
        for habits in product(('Yes','No'), repeat=3):
            changes=dict(zip(('exercise','outside','talk'),habits))
            previous=calculate_qol_score(day(time_focused='0',**changes))
            for focused in range(1,901):
                current=calculate_qol_score(day(time_focused=str(focused),**changes))
                self.assertGreaterEqual(current + 1e-9,previous,(habits,focused))
                # The steepest allowed rate is 1.5 points per percentage point.
                self.assertLessEqual(current-previous,1.5/9+1e-9,(habits,focused))
                previous=current

    def test_completing_any_habit_never_lowers_score(self):
        for focused in range(0,901,9):
            for habits in product(('Yes','No'),repeat=3):
                changes=dict(zip(('exercise','outside','talk'),habits))
                before=calculate_qol_score(day(time_focused=str(focused),**changes))
                for field in changes:
                    if changes[field]=='No':
                        after=calculate_qol_score(day(time_focused=str(focused),**dict(changes,**{field:'Yes'})))
                        self.assertGreaterEqual(after+1e-9,before,(focused,changes,field))

    def test_ideal_bedtime_is_2330(self):
        for bed, score in [('23:29',99.8),('23:30',100),('23:31',99.8),('23:59',94.2)]:
            with self.subTest(bed=bed):
                self.assertAlmostEqual(calculate_qol_score(day(time_focused='700',sleep_time='2026-10-20T'+bed+':00')),score)

    def test_bedtime_penalty_is_symmetric_and_capped(self):
        for bed, score in [('2026-10-20T23:00:00',94), ('2026-10-21T00:00:00',94),
                           ('2026-10-20T22:15:00',85), ('2026-10-21T00:45:00',85)]:
            with self.subTest(bed=bed):
                self.assertAlmostEqual(calculate_qol_score(day(time_focused='700',sleep_time=bed)),score)

    def test_wake_and_bedtime_caps_are_separate(self):
        self.assertAlmostEqual(calculate_qol_score(day(wake_time='2026-10-20T09:45:00',
            sleep_time='2026-10-20T22:15:00',time_focused='700')),70)
        self.assertAlmostEqual(calculate_qol_score(day(wake_time='2026-10-20T08:00:00',time_focused='700')),100)

    def test_social_media_threshold_and_floor(self):
        for minutes, score in [(45,100),(46,99.8),(90,91),(900,0)]:
            with self.subTest(minutes=minutes):
                self.assertAlmostEqual(calculate_qol_score(day(time_focused='700',social_media=str(minutes))),score)

    def test_extra_productivity_cannot_cancel_common_deductions(self):
        self.assertAlmostEqual(calculate_qol_score(day(wake_time='2026-10-20T09:00:00',
            sleep_time='2026-10-21T00:00:00',time_focused='800',social_media='90',**missed(3))),79)

    def test_users_fifty_percent_and_0130_example(self):
        self.assertAlmostEqual(calculate_qol_score(day(wake_time='2026-10-20T08:00:00',
            sleep_time='2026-10-21T01:30:00',time_focused='525',exercise='No')),65)

    def test_offday_override_still_validates_inputs(self):
        self.assertEqual(calculate_qol_score(day(time_focused='0',social_media='900',
            offday_special_day='Yes',**missed(3))),100)
        with self.assertRaises(ValueError):
            calculate_qol_score(day(time_focused='-1',offday_special_day='Yes'))

    def test_ui_defaults_to_ideal_bedtime(self):
        import UI
        defaults=UI.build_default_datetime_strings(datetime(2026,10,20,12))
        self.assertEqual(defaults['sleep_time'],'2026-10-20T23:30:00')
        self.assertEqual(defaults['todays_date'],'2026-10-20')
