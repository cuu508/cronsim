from __future__ import annotations

import unittest

from cronsim.explain import explain

# TODO
# 0 0 * * *
# At midnight every day


class TestBase(unittest.TestCase):
    """
    * * * * * | Every minute
    """

    def test(self) -> None:
        for line in self.__doc__.split("\n"):
            if "|" not in line:
                continue
            expr, desc = line.split("|")
            expr, desc = expr.strip(), desc.strip()
            self.assertEqual(explain(expr), desc, expr)


class Test(unittest.TestCase):
    expr = ["0 0 15 1 1"]
    desc = "At 00:00 on day-of-month 15 and on Monday in January"

    def test(self) -> None:
        for expr in self.expr:
            self.assertEqual(explain(expr), self.desc, f"Failed with {expr}")


class TestEveryMinute(TestBase):
    """
    * * * * *        | Every minute
    */1 * * * *      | Every minute
    0/1 * * * *      | Every minute
    0-59 * * * *     | Every minute
    * * 1/1 * *      | Every minute
    * * * JAN-DEC *  | Every minute
    """


class TestMinuteField(TestBase):
    """
    0 * * * *             | At the start of every hour
    0,0 * * * *           | At the start of every hour
    0,0 */1 * * *         | At the start of every hour
    0,0 0/1 * * *         | At the start of every hour
    5 * * * *             | At minute 5 of every hour
    5,5 * * * *           | At minute 5 of every hour
    5,10 * * * *          | At minutes 5 and 10 of every hour
    5,7,9 * * * *         | At minutes 5, 7, and 9 of every hour
    */5 * * * *           | Every 5th minute of every hour
    0/5 * * * *           | Every 5th minute of every hour
    */5,*/5 * * * *       | Every 5th minute of every hour
    0-30/5 * * * *        | Every 5th minute from 0 through 30 of every hour
    1/5 * * * *           | Every 5th minute from 1 through 59 of every hour
    1,*/5 * * * *         | At minute 1 and every 5th minute of every hour
    */5,1 * * * *         | At every 5th minute and minute 1 of every hour
    0-10 * * * *          | Every minute from 0 through 10 of every hour
    0-10,20-30 * * * *    | Every minute from 0 through 10 and every minute from 20 through 30 of every hour
    20-30,*/15 * * * *    | Every minute from 20 through 30 and every 15th minute of every hour
    1,20-30,*/15 * * * *  | At minute 1, every minute from 20 through 30, and every 15th minute of every hour
    """


class TestSpecificTimes(TestBase):
    """
    0 0 * * *             | At 00:00 every day
    0 2 * * *             | At 2:00 every day
    0,30 13,14 * * *      | At 13:00, 13:30, 14:00, and 14:30 every day
    0,15,30,45 2 * * *    | At 2:00, 2:15, 2:30, and 2:45 every day
    0,15,30,45 2,3 * * *  | At minutes 0, 15, 30, and 45 past hours 2 and 3
    """


class TestSpecificTimeInterval(TestBase):
    """
    0-10 11 * * *         | Every minute from 11:00 through 11:10 every day
    """


class TestHourField(TestBase):
    """
    * 0 * * *             | Every minute past hour 0
    0-59 0 * * *          | Every minute past hour 0
    * 2,4 * * *           | Every minute past hours 2 and 4
    * */2 * * *           | Every minute past every 2nd hour
    * 0/2 * * *           | Every minute past every 2nd hour
    * */2,*/2 * * *       | Every minute past every 2nd hour
    * */3 * * *           | Every minute past every 3rd hour
    * */4 * * *           | Every minute past every 4th hour
    * 1/4 * * *           | Every minute past every 4th hour from 1 through 23
    * 1-10/4 * * *        | Every minute past every 4th hour from 1 through 10
    * 1,*/4 * * *         | Every minute past hour 1 and every 4th hour
    * 1-4 * * *           | Every minute past every hour from 1 through 4
    * 0-4,23 * * *        | Every minute past every hour from 0 through 4 and hour 23
    * 0-7,18-23 * * *     | Every minute past every hour from 0 through 7 and every hour from 18 through 23
    * 1,9-12,*/4 * * *    | Every minute past hour 1, every hour from 9 through 12, and every 4th hour
    0 */3 * * *           | At minute 0 past every 3rd hour
    """


class TestDayField(TestBase):
    """
    0 0 1 * *             | At 00:00 on the first day of month
    0 0 1,1 * *             | At 00:00 on the first day of month
    0 0 1,15 * *          | At 00:00 on day-of-month 1 and 15
    0 0 1-15 * *          | At 00:00 on every day-of-month from 1 through 15
    0 0 1-15,30 * *       | At 00:00 on every day-of-month from 1 through 15 and day-of-month 30
    0 0 */5 * *           | At 00:00 on every 5th day-of-month
    0 0 1/5 * *           | At 00:00 on every 5th day-of-month
    0 0 2/5 * *           | At 00:00 on every 5th day-of-month from 2 through 31
    0 0 2-10/5 * *        | At 00:00 on every 5th day-of-month from 2 through 10
    0 0 1-5,*/5 * *       | At 00:00 on every day-of-month from 1 through 5 and every 5th day-of-month
    0 0 L * *             | At 00:00 on the last day of the month
    """


class TestMonthField(TestBase):
    """
    0 0 * 1 *             | At 00:00 every day in January
    0 0 * 1,1 *             | At 00:00 every day in January
    0 0 * JAN *           | At 00:00 every day in January
    0 0 * 1-2 *           | At 00:00 every day in January and February
    0 0 * JAN-FEB *       | At 00:00 every day in January and February
    0 0 15 JAN-FEB *      | At 00:00 on day-of-month 15 in January and February
    0 0 * 1-3 *           | At 00:00 in every month from January through March
    0 0 * */2 *           | At 00:00 in every 2nd month
    0 0 * 1/2 *           | At 00:00 in every 2nd month
    0 0 * 3/2 *           | At 00:00 in every 2nd month from March through December
    0 0 * 1-6/2 *         | At 00:00 in every 2nd month from January through June
    0 0 * 1-2,12 *        | At 00:00 every day in January, February, and December
    0 0 * 1-3,12 *        | At 00:00 in every month from January through March and December
    """


class TestWeekdayField(TestBase):
    """
    0 0 * * 1             | At 00:00 on Monday
    0 0 * * 1,1             | At 00:00 on Monday
    0 0 * * MON           | At 00:00 on Monday
    0 0 * * 1#2           | At 00:00 on the 2nd Monday of the month
    0 0 * * MON#2         | At 00:00 on the 2nd Monday of the month
    0 0 * * 1L            | At 00:00 on the last Monday of the month
    0 0 * * 1-2           | At 00:00 on Monday and Tuesday
    0 0 * * 1,2           | At 00:00 on Monday and Tuesday
    0 0 * * MON,TUE       | At 00:00 on Monday and Tuesday
    0 0 * * 1-3           | At 00:00 on Monday through Wednesday
    0 0 * * MON-WED       | At 00:00 on Monday through Wednesday
    0 0 * * 1-3,5         | At 00:00 on Monday through Wednesday and Friday
    0 0 * * */2           | At 00:00 on every 2nd day-of-week
    0 0 * * 2/2           | At 00:00 on every 2nd day-of-week from Tuesday through Sunday
    """

    # FIXME: test 0 0 * * 2/2


class TestDateCombinations(TestBase):
    """
    0 0 15 1 1            | At 00:00 on day-of-month 15 and on Monday in January
    0 0 * 1 1             | At 00:00 on Monday in January
    0 0 15 JAN-FEB *      | At 00:00 on day-of-month 15 in January and February
    0 0 1 JAN-FEB *       | At 00:00 on the first day of month in January and February
    """


class TestSpecificDates(TestBase):
    """
    0 0 1 1 *            | At 00:00 on January 1st
    """


if __name__ == "__main__":
    unittest.main()
