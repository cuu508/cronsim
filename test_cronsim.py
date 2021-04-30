from datetime import datetime
import unittest

from cronsim import CronSim, CronSimError

NOW = datetime(2020, 1, 1)


class TestParse(unittest.TestCase):
    def test_it_parses_stars(self):
        w = CronSim("* * * * *", NOW)
        self.assertEqual(w.minutes, list(range(0, 60)))
        self.assertEqual(w.hours, list(range(0, 24)))
        self.assertEqual(w.days, list(range(1, 32)))
        self.assertEqual(w.months, list(range(1, 13)))
        self.assertEqual(w.weekdays, list(range(0, 7)))

    def test_it_parses_six_components(self):
        w = CronSim("* * * * * *", NOW)
        self.assertEqual(w.seconds, list(range(0, 60)))
        self.assertEqual(w.minutes, list(range(0, 60)))
        self.assertEqual(w.hours, list(range(0, 24)))
        self.assertEqual(w.days, list(range(1, 32)))
        self.assertEqual(w.months, list(range(1, 13)))
        self.assertEqual(w.weekdays, list(range(0, 7)))

    def test_it_parses_numbers(self):
        w = CronSim("1 * * * *", NOW)
        self.assertEqual(w.minutes, [1])

    def test_it_parses_weekday(self):
        w = CronSim("* * * * 1", NOW)
        self.assertEqual(w.weekdays, [1])

    def test_it_handles_0_sunday(self):
        w = CronSim("* * * * 0", NOW)
        self.assertEqual(w.weekdays, [0])

    def test_it_parses_list(self):
        w = CronSim("1,2,3 * * * *", NOW)
        self.assertEqual(w.minutes, [1, 2, 3])

    def test_it_parses_interval(self):
        w = CronSim("1-3 * * * *", NOW)
        self.assertEqual(w.minutes, [1, 2, 3])

    def test_it_parses_two_intervals(self):
        w = CronSim("1-3,7-9 * * * *", NOW)
        self.assertEqual(w.minutes, [1, 2, 3, 7, 8, 9])

    def test_it_parses_step(self):
        w = CronSim("*/15 * * * *", NOW)
        self.assertEqual(w.minutes, [0, 15, 30, 45])

    def test_it_parses_interval_with_step(self):
        w = CronSim("0-10/2 * * * *", NOW)
        self.assertEqual(w.minutes, [0, 2, 4, 6, 8, 10])

    def test_it_parses_start_with_step(self):
        w = CronSim("5/15 * * * *", NOW)
        self.assertEqual(w.minutes, [5, 20, 35, 50])

    def test_it_parses_day_l(self):
        w = CronSim("* * L * *", NOW)
        self.assertEqual(w.days, [CronSim.LAST])

    def test_it_parses_day_lowercase_l(self):
        w = CronSim("* * l * *", NOW)
        self.assertEqual(w.days, [CronSim.LAST])

    def test_it_parses_unrestricted_day_restricted_dow(self):
        w = CronSim("* * * * 1", NOW)
        self.assertEqual(w.days, [])
        self.assertEqual(w.weekdays, [1])

    def test_it_parses_restricted_day_unrestricted_dow(self):
        w = CronSim("* * 1 * *", NOW)
        self.assertEqual(w.days, [1])
        self.assertEqual(w.weekdays, [])

    def test_it_parses_nth_weekday(self):
        w = CronSim("* * * * 1#2", NOW)
        self.assertEqual(w.weekdays, [(1, 2)])

    def test_it_parses_symbolic_weekday(self):
        w = CronSim("* * * * MON", NOW)
        self.assertEqual(w.weekdays, [1])

    def test_it_parses_lowercase_symbolic_weekday(self):
        w = CronSim("* * * * mon", NOW)
        self.assertEqual(w.weekdays, [1])

    def test_it_parses_symbolic_month(self):
        w = CronSim("* * * JAN *", NOW)
        self.assertEqual(w.months, [1])

    def test_it_parses_weekday_range_from_zero(self):
        w = CronSim("* * * * 0-2", NOW)
        self.assertEqual(w.weekdays, [0, 1, 2])

    def test_it_parses_sun_tue(self):
        w = CronSim("* * * * sun-tue", NOW)
        self.assertEqual(w.weekdays, [0, 1, 2])

    def test_it_starts_weekday_step_from_zero(self):
        w = CronSim("* * * * */2", NOW)
        self.assertEqual(w.weekdays, [0, 2, 4, 6])


class TestIterator(unittest.TestCase):
    def test_it_handles_l(self):
        dt = next(CronSim("1 1 L * *", NOW))
        self.assertEqual(dt.isoformat(), "2020-01-31T01:01:00")

    def test_it_handles_nth_weekday(self):
        dt = next(CronSim("1 1 * * 1#2", NOW))
        self.assertEqual(dt.isoformat(), "2020-01-13T01:01:00")


if __name__ == "__main__":
    unittest.main()
