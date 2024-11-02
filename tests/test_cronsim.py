from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from itertools import product
from typing import Iterator

if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo

from cronsim import CronSim, CronSimError

NOW = datetime(2020, 1, 1)


class TestParse(unittest.TestCase):
    def test_it_parses_stars(self) -> None:
        w = CronSim("* * * * *", NOW)
        self.assertEqual(w.minutes, set(range(0, 60)))
        self.assertEqual(w.hours, set(range(0, 24)))
        self.assertEqual(w.days, set(range(1, 32)))
        self.assertEqual(w.months, set(range(1, 13)))
        self.assertEqual(w.weekdays, set(range(0, 8)))

    def test_it_parses_numbers(self) -> None:
        w = CronSim("1 * * * *", NOW)
        self.assertEqual(w.minutes, {1})

    def test_it_parses_weekday(self) -> None:
        w = CronSim("* * * * 1", NOW)
        self.assertEqual(w.weekdays, {1})

    def test_it_handles_0_sunday(self) -> None:
        w = CronSim("* * * * 0", NOW)
        self.assertEqual(w.weekdays, {0})

    def test_it_parses_list(self) -> None:
        w = CronSim("1,2,3 * * * *", NOW)
        self.assertEqual(w.minutes, {1, 2, 3})

    def test_it_parses_interval(self) -> None:
        w = CronSim("1-3 * * * *", NOW)
        self.assertEqual(w.minutes, {1, 2, 3})

    def test_it_parses_two_intervals(self) -> None:
        w = CronSim("1-3,7-9 * * * *", NOW)
        self.assertEqual(w.minutes, {1, 2, 3, 7, 8, 9})

    def test_it_parses_step(self) -> None:
        w = CronSim("*/15 * * * *", NOW)
        self.assertEqual(w.minutes, {0, 15, 30, 45})

    def test_it_parses_interval_with_step(self) -> None:
        w = CronSim("0-10/2 * * * *", NOW)
        self.assertEqual(w.minutes, {0, 2, 4, 6, 8, 10})

    def test_it_parses_start_with_step(self) -> None:
        w = CronSim("5/15 * * * *", NOW)
        self.assertEqual(w.minutes, {5, 20, 35, 50})

    def test_it_parses_day_l(self) -> None:
        w = CronSim("* * L * *", NOW)
        self.assertEqual(w.days, {CronSim.LAST})

    def test_it_parses_day_lw(self) -> None:
        w = CronSim("* * LW * *", NOW)
        self.assertEqual(w.days, {CronSim.LAST_WEEKDAY})

    def test_it_parses_day_lowercase_l(self) -> None:
        w = CronSim("* * l * *", NOW)
        self.assertEqual(w.days, {CronSim.LAST})

    def test_it_parses_day_lowercase_lw(self) -> None:
        w = CronSim("* * lw * *", NOW)
        self.assertEqual(w.days, {CronSim.LAST_WEEKDAY})

    def test_it_parses_unrestricted_day_restricted_dow(self) -> None:
        w = CronSim("* * * * 1", NOW)
        self.assertEqual(w.days, set(range(1, 32)))
        self.assertEqual(w.weekdays, {1})
        self.assertTrue(w.day_and)

    def test_it_parses_restricted_day_unrestricted_dow(self) -> None:
        w = CronSim("* * 1 * *", NOW)
        self.assertEqual(w.days, {1})
        self.assertEqual(w.weekdays, {0, 1, 2, 3, 4, 5, 6, 7})
        self.assertTrue(w.day_and)

    def test_it_parses_nth_weekday(self) -> None:
        w = CronSim("* * * * 1#2", NOW)
        self.assertEqual(w.weekdays, {(1, 2)})

    def test_it_parses_symbolic_weekday(self) -> None:
        w = CronSim("* * * * MON", NOW)
        self.assertEqual(w.weekdays, {1})

    def test_it_parses_lowercase_symbolic_weekday(self) -> None:
        w = CronSim("* * * * mon", NOW)
        self.assertEqual(w.weekdays, {1})

    def test_it_parses_symbolic_month(self) -> None:
        w = CronSim("* * * JAN *", NOW)
        self.assertEqual(w.months, {1})

    def test_it_parses_weekday_range_from_zero(self) -> None:
        w = CronSim("* * * * 0-2", NOW)
        self.assertEqual(w.weekdays, {0, 1, 2})

    def test_it_parses_sun_tue(self) -> None:
        w = CronSim("* * * * sun-tue", NOW)
        self.assertEqual(w.weekdays, {0, 1, 2})

    def test_it_starts_weekday_step_from_zero(self) -> None:
        w = CronSim("* * * * */2", NOW)
        self.assertEqual(w.weekdays, {0, 2, 4, 6})

    def test_it_accepts_l_with_step(self) -> None:
        w = CronSim("* * L/2 * *", NOW)
        self.assertEqual(w.days, {CronSim.LAST})

    def test_it_accepts_lw_with_step(self) -> None:
        w = CronSim("* * LW/2 * *", NOW)
        self.assertEqual(w.days, {CronSim.LAST_WEEKDAY})

    def test_it_handles_a_mix_of_ints_and_tuples(self) -> None:
        w = CronSim("* * * * 1,2,3#1", NOW)
        self.assertEqual(w.weekdays, {1, 2, (3, 1)})

    def test_it_accepts_weekday_7(self) -> None:
        w = CronSim("* * * * 7", NOW)
        self.assertEqual(w.weekdays, {7})

    def test_it_accepts_weekday_l(self) -> None:
        w = CronSim("* * * * 5L", NOW)
        self.assertEqual(w.weekdays, {(5, CronSim.LAST)})


class TestValidation(unittest.TestCase):
    def test_it_rejects_4_components(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Wrong number of fields"):
            CronSim("* * * *", NOW)

    def test_it_rejects_bad_values(self) -> None:
        patterns = (
            "%s * * * *",
            "* %s * * *",
            "* * %s * *",
            "* * * %s * ",
            "* * * * %s",
            "* * * * * %s",
            "1-%s * * * *",
            "%s-60 * * * *",
            "* * 1-%s * *",
            "* * 1,%s * *",
            "* * %s/1 * *",
            "* * * %s-DEC *",
            "* * * JAN-%s *",
            "* * * * %s-SUN",
            "* * * * MON-%s",
        )

        bad_values = (
            "-1",
            "61",
            "ABC",
            "2/",
            "/2",
            "2#",
            "#2",
            "1##1",
            "1//2",
            "¹",
            "LL",
            "LWX",
        )

        for pattern, s in product(patterns, bad_values):
            with self.assertRaises(CronSimError):
                CronSim(pattern % s, NOW)

    def test_it_rejects_lopsided_range(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad day-of-month"):
            CronSim("* * 5-1 * *", NOW)

    def test_it_rejects_underscores(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad minute"):
            CronSim("1-1_0 * * * *", NOW)

    def test_it_rejects_zero_step(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad minute"):
            CronSim("*/0 * * * *", NOW)

    def test_it_rejects_zero_nth(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad day-of-week"):
            CronSim("* * * * 1#0", NOW)

    def test_it_rejects_big_nth(self) -> None:
        with self.assertRaises(CronSimError):
            CronSim("* * * * 1#6", NOW)

    def test_it_checks_day_of_month_range(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad day-of-month"):
            CronSim("* * 30 2 *", NOW)

        with self.assertRaisesRegex(CronSimError, "Bad day-of-month"):
            CronSim("* * 31 4 *", NOW)

    def test_it_rejects_dow_l_range(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad day-of-week"):
            CronSim("* * * * 5L-6", NOW)

    def test_it_rejects_dow_l_hash(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad day-of-week"):
            CronSim("* * * * 5L#1", NOW)

    def test_it_rejects_dow_l_slash(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad day-of-week"):
            CronSim("* * * * 5L/3", NOW)

    def test_it_rejects_symbolic_dow_l(self) -> None:
        with self.assertRaisesRegex(CronSimError, "Bad day-of-week"):
            CronSim("* * * * MONL", NOW)


class TestIterator(unittest.TestCase):
    def test_it_handles_l(self) -> None:
        dt = next(CronSim("1 1 L * *", NOW))
        self.assertEqual(dt.isoformat(), "2020-01-31T01:01:00")

    def test_it_handles_lw(self) -> None:
        dt = next(CronSim("1 1 LW 5 *", NOW))
        self.assertEqual(dt.isoformat(), "2020-05-29T01:01:00")

    def test_it_handles_last_friday(self) -> None:
        it = CronSim("1 1 * * 5L", NOW)
        self.assertEqual(next(it).isoformat(), "2020-01-31T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-02-28T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-03-27T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-04-24T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-05-29T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-06-26T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-07-31T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-08-28T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-09-25T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-10-30T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-11-27T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-12-25T01:01:00")

    def test_it_handles_last_sunday_two_notations(self) -> None:
        for pattern in ("1 1 * * 0L", "1 1 * * 7L"):
            dt = next(CronSim(pattern, NOW))
            self.assertEqual(dt.isoformat(), "2020-01-26T01:01:00")

    def test_it_handles_nth_weekday(self) -> None:
        dt = next(CronSim("1 1 * * 1#2", NOW))
        self.assertEqual(dt.isoformat(), "2020-01-13T01:01:00")

    def test_it_handles_dow_star(self) -> None:
        # "First Sunday of the month"
        it = CronSim("1 1 1-7 * */7", NOW)
        self.assertEqual(next(it).isoformat(), "2020-01-05T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-02-02T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-03-01T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-04-05T01:01:00")

    def test_it_handles_dom_star(self) -> None:
        # "First Monday of the month"
        it = CronSim("1 1 */100,1-7 * MON", NOW)
        self.assertEqual(next(it).isoformat(), "2020-01-06T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-02-03T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-03-02T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-04-06T01:01:00")

    def test_it_handles_no_matches(self) -> None:
        # The first date of the month *and* the fourth Monday of the month
        # will never yield results:
        it = CronSim("1 1 */100 * MON#4", NOW)
        with self.assertRaises(StopIteration):
            next(it)

    def test_it_handles_every_x_weekdays(self) -> None:
        # "every 3rd weekday" means "every 3rd weekday starting from Sunday"
        it = CronSim("1 1 * * */3", NOW)
        self.assertEqual(next(it).isoformat(), "2020-01-01T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-01-04T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-01-05T01:01:00")
        self.assertEqual(next(it).isoformat(), "2020-01-08T01:01:00")


class TestDstTransitions(unittest.TestCase):
    tz = ZoneInfo("Europe/Riga")
    # For reference, DST changes in Europe/Riga in 2021:
    # DST begins (clock moves 1 hour forward) on March 28, 3AM:
    #   2021-03-28T02:59:00+02:00
    #   2021-03-28T04:00:00+03:00
    #   2021-03-28T04:01:00+03:00
    # DST ends (clock moves 1 hour backward) on October 31, 4AM:
    #   2021-10-31T03:59:00+03:00
    #   2021-10-31T03:00:00+02:00
    #   2021-10-31T03:01:00+02:00

    def assertNextEqual(self, iterator: Iterator[datetime], expected_iso: str) -> None:
        self.assertEqual(next(iterator).isoformat(), expected_iso)

    def test_001_every_hour_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        w = CronSim("0 * * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")

    def test_001_every_hour_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("0 * * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_002_every_30_minutes_mar(self) -> None:
        now = datetime(2021, 3, 28, 2, 10, tzinfo=self.tz)
        w = CronSim("*/30 * * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:30:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T04:30:00+03:00")

    def test_002_every_30_minutes_oct(self) -> None:
        now = datetime(2021, 10, 31, 2, 10, tzinfo=self.tz)
        w = CronSim("*/30 * * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:30:00+02:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_003_every_15_minutes_mar(self) -> None:
        now = datetime(2021, 3, 28, 2, 40, tzinfo=self.tz)
        w = CronSim("*/15 * * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:45:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")

    def test_003_every_15_minutes_oct(self) -> None:
        now = datetime(2021, 10, 31, 2, 40, tzinfo=self.tz)
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

    def test_004_every_2_hours_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        w = CronSim("0 */2 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T06:00:00+03:00")

    def test_004_every_2_hours_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("0 */2 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T06:00:00+02:00")

    def test_005_30_minutes_past_every_2_hours_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        w = CronSim("30 */2 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:30:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:30:00+03:00")

    def test_005_30_minutes_past_every_2_hours_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("30 */2 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:30:00+02:00")

    def test_006_every_3_hours_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("0 */3 * * *", now)
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T06:00:00+02:00")

    def test_008_at_1_2_3_4_5_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        w = CronSim("0 1,2,3,4,5 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T05:00:00+03:00")

    def test_008_at_1_2_3_4_5_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("0 1,2,3,4,5 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_009_30_past_1_2_3_4_5_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        w = CronSim("30 1,2,3,4,5 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:30:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T04:30:00+03:00")

    def test_009_30_past_1_2_3_4_5_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("30 1,2,3,4,5 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:30:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:30:00+02:00")

    def test_010_at_2_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        w = CronSim("0 2 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-29T02:00:00+03:00")

    def test_010_at_2_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("0 2 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-11-01T02:00:00+02:00")

    def test_011_at_3_mar(self) -> None:
        now = datetime(2021, 3, 27, 1, 30, tzinfo=self.tz)
        w = CronSim("0 3 * * *", now)
        self.assertNextEqual(w, "2021-03-27T03:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-29T03:00:00+03:00")

    def test_011_at_3_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("0 3 * * *", now)
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-11-01T03:00:00+02:00")

    def test_012_at_4_mar(self) -> None:
        now = datetime(2021, 3, 27, 1, 30, tzinfo=self.tz)
        w = CronSim("0 4 * * *", now)
        self.assertNextEqual(w, "2021-03-27T04:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-29T04:00:00+03:00")

    def test_012_at_4_oct(self) -> None:
        now = datetime(2021, 10, 30, 1, 30, tzinfo=self.tz)
        w = CronSim("0 4 * * *", now)
        self.assertNextEqual(w, "2021-10-30T04:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")
        self.assertNextEqual(w, "2021-11-01T04:00:00+02:00")

    def test_014_every_hour_enumerated_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        w = CronSim(
            "0 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 * * *", now
        )
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T05:00:00+03:00")

    def test_014_every_hour_enumerated_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim(
            "0 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 * * *", now
        )
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_015_every_other_hour_enumerated_mar(self) -> None:
        now = datetime(2021, 3, 28, 0, 30, tzinfo=self.tz)
        w = CronSim("0 1,3,5,7,9,11,13,15,17,19,21,23 * * *", now)
        self.assertNextEqual(w, "2021-03-28T01:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T05:00:00+03:00")

    def test_015_every_other_hour_enumerated_oct(self) -> None:
        now = datetime(2021, 10, 31, 0, 30, tzinfo=self.tz)
        w = CronSim("0 1,3,5,7,9,11,13,15,17,19,21,23 * * *", now)
        self.assertNextEqual(w, "2021-10-31T01:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T05:00:00+02:00")

    def test_016_at_1_to_5_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        w = CronSim("0 1-5 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:00:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-28T05:00:00+03:00")

    def test_016_at_1_to_5_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        w = CronSim("0 1-5 * * *", now)
        self.assertNextEqual(w, "2021-10-31T02:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+03:00")
        self.assertNextEqual(w, "2021-10-31T04:00:00+02:00")

    def test_at_3_15_mar(self) -> None:
        now = datetime(2021, 3, 27, 0, 0, tzinfo=self.tz)
        w = CronSim("15 3 * * *", now)
        self.assertNextEqual(w, "2021-03-27T03:15:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")
        self.assertNextEqual(w, "2021-03-29T03:15:00+03:00")

    def test_at_3_15_oct(self) -> None:
        now = datetime(2021, 10, 30, 0, 0, tzinfo=self.tz)
        w = CronSim("15 3 * * *", now)
        self.assertNextEqual(w, "2021-10-30T03:15:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:15:00+03:00")
        self.assertNextEqual(w, "2021-11-01T03:15:00+02:00")

    def test_every_minute_mar(self) -> None:
        now = datetime(2021, 3, 28, 2, 58, tzinfo=self.tz)
        w = CronSim("* * * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:59:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")

    def test_every_minute_oct(self) -> None:
        now = datetime(2021, 10, 31, 3, 58, fold=0, tzinfo=self.tz)
        w = CronSim("* * * * *", now)
        self.assertNextEqual(w, "2021-10-31T03:59:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:01:00+02:00")

    def test_every_minute_from_1_to_6_mar(self) -> None:
        now = datetime(2021, 3, 28, 2, 58, tzinfo=self.tz)
        w = CronSim("* 1-6 * * *", now)
        self.assertNextEqual(w, "2021-03-28T02:59:00+02:00")
        self.assertNextEqual(w, "2021-03-28T04:00:00+03:00")

    def test_every_minute_from_1_to_6_oct(self) -> None:
        now = datetime(2021, 10, 31, 3, 58, fold=0, tzinfo=self.tz)
        w = CronSim("* 1-6 * * *", now)
        self.assertNextEqual(w, "2021-10-31T03:59:00+03:00")
        self.assertNextEqual(w, "2021-10-31T03:00:00+02:00")
        self.assertNextEqual(w, "2021-10-31T03:01:00+02:00")


class TestOptimizations(unittest.TestCase):
    def test_it_skips_fixup_for_naive_datetimes(self) -> None:
        w = CronSim("1 1 L * *", NOW)
        self.assertIsNone(w.fixup_tz)

    def test_it_skips_fixup_for_utc_datetimes(self) -> None:
        now = NOW.replace(tzinfo=timezone.utc)
        w = CronSim("1 1 L * *", now)
        self.assertIsNone(w.fixup_tz)


class TestExplain(unittest.TestCase):
    def test_it_works(self) -> None:
        result = CronSim("* * * * *", NOW).explain()
        self.assertEqual(result, "Every minute")


class TestReverse(unittest.TestCase):
    samples = [
        "* * * * *",
        "0 * * * *",
        "*/30 * * * *",
        "*/15 * * * *",
        "0 */2 * * *",
        "30 */2 * * *",
        "0 */3 * * *",
        "0 1,2,3,4,5 * * *",
        "30 1,2,3,4,5 * * *",
        "0 2 * * *",
        "0 3 * * *",
        "0 4 * * *",
        "0 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 * * *",
        "0 1,3,5,7,9,11,13,15,17,19,21,23 * * *",
        "0 1-5 * * *",
        "15 3 * * *",
        "* 1-6 * * *",
        "1 1 L * *",
        "1 1 LW 5 *",
        "1 1 * * 5L",
        "1 1 * * 0L",
        "1 1 * * 7L",
        "1 1 * * 1#2",
        "1 1 1-7 * */7",
        "1 1 */100,1-7 * MON",
        "1 1 * * */3",
    ]
    tz = ZoneInfo("Europe/Riga")

    def _test(self, expr, now):
        it = CronSim(expr, now)
        crumbs = [next(it) for i in range(0, 5)]

        reverse_it = CronSim(expr, crumbs.pop(), reverse=True)
        while crumbs:
            self.assertEqual(next(reverse_it), crumbs.pop())

    def test_it_handles_naive_datetime(self) -> None:
        for sample in self.samples:
            self._test(sample, NOW)

    def test_it_handles_utc(self) -> None:
        now = NOW.replace(tzinfo=timezone.utc)
        for sample in self.samples:
            self._test(sample, now)

    def test_it_handles_dst_mar(self) -> None:
        now = datetime(2021, 3, 28, 1, 30, tzinfo=self.tz)
        for sample in self.samples:
            self._test(sample, now)

    def test_it_handles_dst_oct(self) -> None:
        now = datetime(2021, 10, 31, 1, 30, tzinfo=self.tz)
        for sample in self.samples:
            self._test(sample, now)

    def test_it_handles_no_matches(self) -> None:
        # The first date of the month *and* the fourth Monday of the month
        # will never yield results:
        it = CronSim("1 1 */100 * MON#4", NOW, reverse=True)
        with self.assertRaises(StopIteration):
            next(it)


if __name__ == "__main__":
    unittest.main()
