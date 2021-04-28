from datetime import datetime
import unittest

from wat import Wat, WatError

NOW = datetime(2020, 1, 1)

class TestParse(unittest.TestCase):

    def test_it_parses_stars(self):
        w = Wat("* * * * *", NOW)
        self.assertEqual(w.minutes, list(range(0, 60)))
        self.assertEqual(w.hours, list(range(0, 24)))
        self.assertEqual(w.days, list(range(1, 32)))
        self.assertEqual(w.months, list(range(1, 13)))
        self.assertEqual(w.weekdays, list(range(1, 8)))

    def test_it_parses_numbers(self):
        w = Wat("1 * * * *", NOW)
        self.assertEqual(w.minutes, [1])

    def test_it_parses_weekday(self):
        w = Wat("* * * * 1", NOW)
        self.assertEqual(w.weekdays, [0])

    def test_it_handles_0_sunday(self):
        w = Wat("* * * * 0", NOW)
        self.assertEqual(w.weekdays, [6])

    def test_it_parses_list(self):
        w = Wat("1,2,3 * * * *", NOW)
        self.assertEqual(w.minutes, [1, 2, 3])

    def test_it_parses_interval(self):
        w = Wat("1-3 * * * *", NOW)
        self.assertEqual(w.minutes, [1, 2, 3])

    def test_it_parses_two_intervals(self):
        w = Wat("1-3,7-9 * * * *", NOW)
        self.assertEqual(w.minutes, [1, 2, 3, 7, 8, 9])

    def test_it_parses_step(self):
        w = Wat("*/15 * * * *", NOW)
        self.assertEqual(w.minutes, [0, 15, 30, 45])

    def test_it_parses_interval_with_step(self):
        w = Wat("0-10/2 * * * *", NOW)
        self.assertEqual(w.minutes, [0, 2, 4, 6, 8, 10])

    def test_it_parses_start_with_step(self):
        w = Wat("5/15 * * * *", NOW)
        self.assertEqual(w.minutes, [5, 20, 35, 50])

    def test_it_parses_day_l(self):
        w = Wat("* * L * *", NOW)
        self.assertEqual(w.days, [Wat.LAST])

    def test_it_parses_unrestricted_day_restricted_dow(self):
        w = Wat("* * * * 1", NOW)
        self.assertEqual(w.days, [])
        self.assertEqual(w.weekdays, [0])

    def test_it_parses_restricted_day_unrestricted_dow(self):
        w = Wat("* * 1 * *", NOW)
        self.assertEqual(w.days, [1])
        self.assertEqual(w.weekdays, [])

    def test_it_parses_nth_weekday(self):
        w = Wat("* * * * 1#2", NOW)
        self.assertEqual(w.weekdays, [(0, 2)])

    def test_it_parses_symbolic_weekday(self):
        w = Wat("* * * * MON", NOW)
        self.assertEqual(w.weekdays, [0])

    def test_it_parses_lowercase_symbolic_weekday(self):
        w = Wat("* * * * mon", NOW)
        self.assertEqual(w.weekdays, [0])

    def test_it_parses_symbolic_month(self):
        w = Wat("* * * JAN *", NOW)
        self.assertEqual(w.months, [1])


class TestValidation(unittest.TestCase):
    def test_it_rejects_six_components(self):
        with self.assertRaises(WatError):
            Wat("* * * * * *", NOW)


class TestIterator(unittest.TestCase):
    def test_it_handles_l(self):
        dt = next(Wat("1 1 L * *", NOW))
        self.assertEqual(dt.isoformat(), "2020-01-31T01:01:00")

    def test_it_handles_nth_weekday(self):
        dt = next(Wat("1 1 * * 1#2", NOW))
        self.assertEqual(dt.isoformat(), "2020-01-13T01:01:00")


if __name__ == '__main__':
    unittest.main()
