import unittest

from explain import explain

# TODO
# 0 0 * * *
# At midnight every day


class Test(unittest.TestCase):
    expr = ["0 0 15 1 1"]
    desc = "At 00:00 on day-of-month 15 and on Monday in January"

    def test(self):
        for expr in self.expr:
            parts = expr.upper().split()
            self.assertEqual(explain(parts), self.desc, f"Failed with {expr}")


class TestEveryEverything(Test):
    expr = [
        "* * * * *",
        "*/1 * * * *",
        "0/1 * * * *",
        "0-59 * * * *",
        "* * 1/1 * *",
    ]
    desc = "Every minute"


class TestSpecificTime(Test):
    expr = ["0 0 15 1 1", "0,0,0 0,0,0 15 1 1"]
    desc = "At 00:00 on day-of-month 15 and on Monday in January"


class TestSpecificTimes(Test):
    expr = ["0,30 13,14 * * *"]
    desc = "At 13:00, 13:30, 14:00, and 14:30 every day"


class TestEveryMinute(Test):
    expr = ["* 0 * * *", "0-59 0 * * *"]
    desc = "Every minute past hour 0"


class TestEveryHour(Test):
    expr = ["0 * 15 1 1"]
    desc = "At the start of every hour on day-of-month 15 and on Monday in January"


class TestEveryDayOfMonth(Test):
    expr = ["0 0 * 1 1"]
    desc = "At 00:00 on Monday in January"


class TestEveryDayOfWeek(Test):
    expr = ["0 0 15 JAN-FEB *"]
    desc = "At 00:00 on day-of-month 15 in January and February"


class TestEveryMonth(Test):
    expr = ["0 0 15 * 1"]
    desc = "At 00:00 on day-of-month 15 and on Monday"


class TestEveryDomEveryMonthEveryDow(Test):
    expr = ["0 3 * * *"]
    desc = "At 3:00 every day"


class TestEveryHourDomMonthDow(Test):
    expr = [
        "15 * * * *",
        "15,15 * * * *",
    ]
    desc = "At minute 15 of every hour"


class TestSpecificMinutesEveryHour(Test):
    expr = ["15,16,17 * * * *"]
    desc = "At minutes 15, 16, and 17 of every hour"


class TestFirstDayOfMonths(Test):
    expr = ["15 3 1 JAN-FEB *", "15 3 1,1 JAN-FEB *"]
    desc = "At 3:15 on the first day of month in January and February"


class TestFirstDayOfMonth(Test):
    expr = ["15 3 1 JAN *"]
    desc = "At 3:15 on January 1st"


class TestMinuteInterval(Test):
    expr = ["1-30 * * * *"]
    desc = "Every minute from 1 through 30 of every hour"


class TestMinuteIntervals(Test):
    expr = ["1-20,40-50 * * * *"]
    desc = "Every minute from 1 through 20 and every minute from 40 through 50 of every hour"


class TestMinuteIntervalWithStep(Test):
    expr = ["*/5 * * * *", "0/5 * * * *"]
    desc = "Every 5th minute of every hour"


class TestMixedMinuteIntervals(Test):
    expr = ["1-5,*/15 * * * *"]
    desc = "Every minute from 1 through 5 and every 15th minute of every hour"


class TestMoreMixedMinuteIntervals(Test):
    expr = ["1,*/15 * * * *"]
    desc = "At minute 1 and every 15th minute of every hour"


class TestHourIntervals(Test):
    expr = ["0 */3 * * *"]
    desc = "At minute 0 past every 3rd hour"


class TestMixedHourIntervals(Test):
    expr = ["0 8-17,23 * * *"]
    desc = "At minute 0 past every hour from 8 through 17 and hour 23"


class TestMoreMixedHourIntervals(Test):
    expr = ["0 8-17,*/8 * * *"]
    desc = "At minute 0 past every hour from 8 through 17 and every 8th hour"


class TestStartOfEveryHourIntervals(Test):
    expr = ["0 * * * *", "0,0 * * * *", "0 */1 * * *", "0 0/1 * * *"]
    desc = "At the start of every hour"


class TestEveryMinuteOfSpecificDate(Test):
    expr = ["* * 1 1 *"]
    desc = "Every minute on January 1st"


class TestEverySixHours(Test):
    expr = ["15 */6 * * *"]
    desc = "At minute 15 past every 6th hour"


class TestEveryTwoHours(Test):
    expr = ["0 */2 * * *"]
    desc = "At minute 0 past every 2nd hour"


class TestEveryTwoHoursWithOffset(Test):
    expr = ["0 1/2 * * *"]
    desc = "At minute 0 past every 2nd hour from 1 through 23"


class TestWeekdayInterval(Test):
    expr = ["0 23 * * MON-FRI"]
    desc = "At 23:00 on Monday through Friday"


class TestWeekdayList(Test):
    expr = ["0 23 * * MON,TUE", "0 23 * * 1,2"]
    desc = "At 23:00 on Monday and Tuesday"


class TestSpecificTimeInterval(Test):
    expr = ["0-10 11 * * *"]
    desc = "Every minute from 11:00 through 11:10 every day"


class TestNthWeekday(Test):
    expr = ["* * * * MON#2"]
    desc = "Every minute on the 2nd Monday of the month"


class TestLastDayOfMonth(Test):
    expr = ["* * L * *"]
    desc = "Every minute on the last day of the month"


class TestLastWeekdayOfMonth(Test):
    expr = ["* * * * 1L"]
    desc = "Every minute on the last Monday of the month"


if __name__ == "__main__":
    unittest.main()
