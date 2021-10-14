from datetime import datetime
from itertools import product
import unittest

from cronsim import CronSim, CronSimError
import pytz

NOW = datetime(2020, 1, 1)


class TestParse(unittest.TestCase):
    def test_it_parses_stars(self):
        w = CronSim("* * * * *", NOW)
        self.assertEqual(w.minutes, set(range(0, 60)))
        self.assertEqual(w.hours, set(range(0, 24)))
        self.assertEqual(w.days, set(range(1, 32)))
        self.assertEqual(w.months, set(range(1, 13)))
        self.assertEqual(w.weekdays, set(range(0, 8)))

    def test_it_parses_numbers(self):
        w = CronSim("1 * * * *", NOW)
        self.assertEqual(w.minutes, {1})

    def test_it_parses_weekday(self):
        w = CronSim("* * * * 1", NOW)
        self.assertEqual(w.weekdays, {1})

    def test_it_handles_0_sunday(self):
        w = CronSim("* * * * 0", NOW)
        self.assertEqual(w.weekdays, {0})

    def test_it_parses_list(self):
        w = CronSim("1,2,3 * * * *", NOW)
        self.assertEqual(w.minutes, {1, 2, 3})

    def test_it_parses_interval(self):
        w = CronSim("1-3 * * * *", NOW)
        self.assertEqual(w.minutes, {1, 2, 3})

    def test_it_parses_two_intervals(self):
        w = CronSim("1-3,7-9 * * * *", NOW)
        self.assertEqual(w.minutes, {1, 2, 3, 7, 8, 9})

    def test_it_parses_step(self):
        w = CronSim("*/15 * * * *", NOW)
        self.assertEqual(w.minutes, {0, 15, 30, 45})

    def test_it_parses_interval_with_step(self):
        w = CronSim("0-10/2 * * * *", NOW)
        self.assertEqual(w.minutes, {0, 2, 4, 6, 8, 10})

    def test_it_parses_start_with_step(self):
        w = CronSim("5/15 * * * *", NOW)
        self.assertEqual(w.minutes, {5, 20, 35, 50})

    def test_it_parses_day_l(self):
        w = CronSim("* * L * *", NOW)
        self.assertEqual(w.days, {CronSim.LAST})

    def test_it_parses_day_lowercase_l(self):
        w = CronSim("* * l * *", NOW)
        self.assertEqual(w.days, {CronSim.LAST})

    def test_it_parses_unrestricted_day_restricted_dow(self):
        w = CronSim("* * * * 1", NOW)
        self.assertEqual(w.days, set())
        self.assertEqual(w.weekdays, {1})

    def test_it_parses_restricted_day_unrestricted_dow(self):
        w = CronSim("* * 1 * *", NOW)
        self.assertEqual(w.days, {1})
        self.assertEqual(w.weekdays, set())

    def test_it_parses_nth_weekday(self):
        w = CronSim("* * * * 1#2", NOW)
        self.assertEqual(w.weekdays, {(1, 2)})

    def test_it_parses_symbolic_weekday(self):
        w = CronSim("* * * * MON", NOW)
        self.assertEqual(w.weekdays, {1})

    def test_it_parses_lowercase_symbolic_weekday(self):
        w = CronSim("* * * * mon", NOW)
        self.assertEqual(w.weekdays, {1})

    def test_it_parses_symbolic_month(self):
        w = CronSim("* * * JAN *", NOW)
        self.assertEqual(w.months, {1})

    def test_it_parses_weekday_range_from_zero(self):
        w = CronSim("* * * * 0-2", NOW)
        self.assertEqual(w.weekdays, {0, 1, 2})

    def test_it_parses_sun_tue(self):
        w = CronSim("* * * * sun-tue", NOW)
        self.assertEqual(w.weekdays, {0, 1, 2})

    def test_it_starts_weekday_step_from_zero(self):
        w = CronSim("* * * * */2", NOW)
        self.assertEqual(w.weekdays, {0, 2, 4, 6})

    def test_it_accepts_l_with_step(self):
        w = CronSim("* * L/2 * *", NOW)
        self.assertEqual(w.days, [CronSim.LAST])

    def test_it_handles_a_mix_of_ints_and_tuples(self):
        w = CronSim("* * * * 1,2,3#1", NOW)
        self.assertEqual(w.weekdays, {1, 2, (3, 1)})

    def test_it_accepts_weekday_7(self):
        w = CronSim("* * * * 7", NOW)
        self.assertEqual(w.weekdays, {7})


class TestValidation(unittest.TestCase):
    def test_it_rejects_4_components(self):
        with self.assertRaises(CronSimError):
            CronSim("* * * *", NOW)

    def test_it_rejects_bad_values(self):
        patterns = (
            "%s * * * *",
            "* %s * * *",
            "* * %s * *",
            "* * * %s * ",
            "* * * * %s",
            "* * * * * %s",
            "1-%s * * * *",
            "%s-60 * * * *",
            "* * * %s-DEC *",
            "* * * JAN-%s *",
            "* * * * %s-SUN",
            "* * * * MON-%s",
        )

        bad_values = ("-1", "61", "ABC", "2/", "/2", "2#", "#2", "1##1", "1//2")

        for pattern, s in product(patterns, bad_values):
            with self.assertRaises(CronSimError):
                CronSim(pattern % s, NOW)

    def test_it_rejects_lopsided_range(self):
        with self.assertRaises(CronSimError):
            CronSim("* * 5-1 * *", NOW)

    def test_it_rejects_underscores(self):
        with self.assertRaises(CronSimError):
            CronSim("1-1_0 * * * *", NOW)

    def test_it_rejects_zero_step(self):
        with self.assertRaises(CronSimError):
            CronSim("*/0 * * * *", NOW)

    def test_it_rejects_zero_nth(self):
        with self.assertRaises(CronSimError):
            CronSim("* * * * 1#0", NOW)

    def test_it_rejects_big_nth(self):
        with self.assertRaises(CronSimError):
            CronSim("* * * * 1#6", NOW)

    def test_it_checks_day_of_month_range(self):
        with self.assertRaises(CronSimError):
            CronSim("* * 30 2 *", NOW)

        with self.assertRaises(CronSimError):
            CronSim("* * 31 4 *", NOW)


class TestIterator(unittest.TestCase):
    def test_it_handles_l(self):
        dt = next(CronSim("1 1 L * *", NOW))
        self.assertEqual(dt.isoformat(), "2020-01-31T01:01:00")

    def test_it_handles_nth_weekday(self):
        dt = next(CronSim("1 1 * * 1#2", NOW))
        self.assertEqual(dt.isoformat(), "2020-01-13T01:01:00")


class TestDstTransitions(unittest.TestCase):
    tz = pytz.timezone("Europe/Riga")
    # For reference, DST changes in Europe/Riga in 2021:
    # DST begins (clock moves 1 hour forward) on March 28, 3AM:
    #   2021-03-28T02:59:00+02:00
    #   2021-03-28T04:00:00+03:00
    #   2021-03-28T04:01:00+03:00
    # DST ends (clock moves 1 hour backward) on October 31, 4AM:
    #   2021-10-31T03:59:00+03:00
    #   2021-10-31T03:00:00+02:00
    #   2021-10-31T03:01:00+02:00

    def assertNextEqual(self, iterator, expected_iso):
        self.assertEqual(next(iterator).isoformat(), expected_iso)

    def test_001_every_hour_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 1, 30))
        w = CronSim("0 * * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")

    def test_001_every_hour_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("0 * * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_002_every_30_minutes_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 2, 10))
        w = CronSim("*/30 * * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:30:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T04:30:00+03:00")

    def test_002_every_30_minutes_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 2, 10))
        w = CronSim("*/30 * * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:30:00+02:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_003_every_15_minutes_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 2, 40))
        w = CronSim("*/15 * * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:45:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")

    def test_003_every_15_minutes_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 2, 40))
        w = CronSim("*/15 * * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:45:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:15:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:45:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:15:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:30:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:45:00+02:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_004_every_2_hours_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 1, 30))
        w = CronSim("0 */2 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T06:00:00+03:00")

    def test_004_every_2_hours_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("0 */2 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T06:00:00+02:00")

    def test_005_30_minutes_past_every_2_hours_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 1, 30))
        w = CronSim("30 */2 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:30:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:30:00+03:00")

    def test_005_30_minutes_past_every_2_hours_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("30 */2 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:30:00+02:00")

    def test_006_every_3_hours_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("0 */3 * * *", now)
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T06:00:00+02:00")

    def test_008_at_1_2_3_4_5_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 1, 30))
        w = CronSim("0 1,2,3,4,5 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T05:00:00+03:00")

    def test_008_at_1_2_3_4_5_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("0 1,2,3,4,5 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_009_30_past_1_2_3_4_5_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 1, 30))
        w = CronSim("30 1,2,3,4,5 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:30:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T04:30:00+03:00")

    def test_009_30_past_1_2_3_4_5_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("30 1,2,3,4,5 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:30:00+02:00")

    def test_010_at_2_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 1, 30))
        w = CronSim("0 2 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-29T02:00:00+03:00")

    def test_010_at_2_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("0 2 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-11-01T02:00:00+02:00")

    def test_011_at_3_mar(self):
        now = self.tz.localize(datetime(2021, 3, 27, 1, 30))
        w = CronSim("0 3 * * *", now)
        self.assertNextEqual(w, "2021-03-27T03:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-29T03:00:00+03:00")

    def test_011_at_3_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("0 3 * * *", now)
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-11-01T03:00:00+02:00")

    def test_012_at_4_mar(self):
        now = self.tz.localize(datetime(2021, 3, 27, 1, 30))
        w = CronSim("0 4 * * *", now)
        self.assertNextEqual(w, "2021-03-27T04:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-29T04:00:00+03:00")

    def test_012_at_4_oct(self):
        now = self.tz.localize(datetime(2021, 10, 30, 1, 30))
        w = CronSim("0 4 * * *", now)
        self.assertNextEqual(w, "2021-10-30T04:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")
        self.assertNextEqual(w, "2021-11-01T04:00:00+02:00")

    def test_014_every_hour_enumerated_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 1, 30))
        w = CronSim(
            "0 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 * * *", now
        )
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T05:00:00+03:00")

    def test_014_every_hour_enumerated_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim(
            "0 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 * * *", now
        )
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_015_every_other_hour_enumerated_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 0, 30))
        w = CronSim("0 1,3,5,7,9,11,13,15,17,19,21,23 * * *", now)
        self.assertNextEqual(w, "2021-03-28T01:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T05:00:00+03:00")

    def test_015_every_other_hour_enumerated_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 0, 30))
        w = CronSim("0 1,3,5,7,9,11,13,15,17,19,21,23 * * *", now)
        self.assertNextEqual(w, "2021-10-31T01:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T05:00:00+02:00")

    def test_016_at_1_to_5_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 1, 30))
        w = CronSim("0 1-5 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T05:00:00+03:00")

    def test_016_at_1_to_5_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 1, 30))
        w = CronSim("0 1-5 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_at_3_15_mar(self):
        now = self.tz.localize(datetime(2021, 3, 27, 0, 0))
        w = CronSim("15 3 * * *", now)
        self.assertNextEqual(w, "2021-03-27T03:15:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-29T03:15:00+03:00")

    def test_at_3_15_oct(self):
        now = self.tz.localize(datetime(2021, 10, 30, 0, 0))
        w = CronSim("15 3 * * *", now)
        self.assertNextEqual(w, "2021-10-30T03:15:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:15:00+03:00")
        self.assertNextEqual(w, "2021-11-01T03:15:00+02:00")

    def test_every_minute_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 2, 58))
        w = CronSim("* * * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:59:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")

    def test_every_minute_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 3, 58), is_dst=True)
        w = CronSim("* * * * *", now)
        self.assertNextEqual(w, "2021-10-31T03:59:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:01:00+02:00")

    def test_every_minute_from_1_to_6_mar(self):
        now = self.tz.localize(datetime(2021, 3, 28, 2, 58))
        w = CronSim("* 1-6 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:59:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")

    def test_every_minute_from_1_to_6_oct(self):
        now = self.tz.localize(datetime(2021, 10, 31, 3, 58), is_dst=True)
        w = CronSim("* 1-6 * * *", now)
        self.assertNextEqual(w, "2021-10-31T03:59:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:01:00+02:00")


class TestOptimizations(unittest.TestCase):
    def test_it_skips_fixup_for_naive_datetimes(self):
        w = CronSim("1 1 L * *", NOW)
        self.assertIsNone(w.fixup_tz)

    def test_it_skips_fixup_for_utc_datetimes(self):
        now = pytz.utc.localize(NOW)
        w = CronSim("1 1 L * *", now)
        self.assertIsNone(w.fixup_tz)


if __name__ == "__main__":
    unittest.main()
