from __future__ import annotations

import unittest

from cronsim.explain import explain


class TestBase(unittest.TestCase):
    """
    * * * 1 *             | Every minute in January
    """

    def test(self) -> None:
        for line in self.__doc__.split("\n"):
            if "|" not in line:
                continue
            expr, desc = line.split("|")
            expr, desc = expr.strip(), desc.strip()
            with self.subTest():
                self.assertEqual(explain(expr), desc, expr)


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
    */5 * * * *           | Every fifth minute of every hour
    0/5 * * * *           | Every fifth minute of every hour
    */5,*/5 * * * *       | Every fifth minute of every hour
    0-30/5 * * * *        | Every fifth minute from 0 through 30 of every hour
    0-59/5 * * * *        | Every fifth minute of every hour
    1/5 * * * *           | Every fifth minute from 1 through 59 of every hour
    1,*/5 * * * *         | At minute 1 and every fifth minute of every hour
    */5,1 * * * *         | At every fifth minute and minute 1 of every hour
    0-10 * * * *          | Every minute from 0 through 10 of every hour
    0-10,20-30 * * * *    | Every minute from 0 through 10 and every minute from 20 through 30 of every hour
    20-30,*/15 * * * *    | Every minute from 20 through 30 and every 15th minute of every hour
    1,20-30,*/15 * * * *  | At minute 1, every minute from 20 through 30, and every 15th minute of every hour
    """


class TestHourField(TestBase):
    """
    * 0 * * *             | Every minute from 00:00 through 00:59
    0-59 0 * * *          | Every minute from 00:00 through 00:59
    * 2,4 * * *           | Every minute past hours 2 and 4
    * */2 * * *           | Every minute past every second hour
    * 0/2 * * *           | Every minute past every second hour
    * */2,*/2 * * *       | Every minute past every second hour
    * */3 * * *           | Every minute past every third hour
    * */4 * * *           | Every minute past every fourth hour
    * 1/4 * * *           | Every minute past every fourth hour from 1 through 23
    * 1-10/4 * * *        | Every minute past every fourth hour from 1 through 10
    * 1,*/4 * * *         | Every minute past hour 1 and every fourth hour
    * 1-4 * * *           | Every minute from 01:00 through 04:59
    * 0-4,23 * * *        | Every minute past every hour from 0 through 4 and hour 23
    * 0-7,18-23 * * *     | Every minute past every hour from 0 through 7 and every hour from 18 through 23
    * 1,9-12,*/4 * * *    | Every minute past hour 1, every hour from 9 through 12, and every fourth hour
    0 */3 * * *           | At minute 0 past every third hour
    0 * * * *             | At the start of every hour
    0 */1 * * *           | At the start of every hour
    0 0/1 * * *           | At the start of every hour
    10 9-17 * * *         | At minute 10 past every hour from 9 through 17
    """


class TestDayField(TestBase):
    """
    0 0 1 * *             | At 00:00 on the first day of every month
    0 0 1,1 * *           | At 00:00 on the first day of every month
    0 0 1,15 * *          | At 00:00 on the first and the 15th day of month
    0 0 1,3,5 * *         | At 00:00 on the first, the third, and the fifth day of month
    0 0 1,3,10-20 * *     | At 00:00 on the first day of month, the third day of month, and every day of month from 10 through 20
    0 0 1-15 * *          | At 00:00 on every day of month from 1 through 15
    0 0 1-15,30 * *       | At 00:00 on every day of month from 1 through 15 and the 30th day of month
    0 0 */5 * *           | At 00:00 on every fifth day of month
    0 0 0/5 * *           | At 00:00 on every fifth day of month
    0 0 1/5 * *           | At 00:00 on every fifth day of month
    0 0 2/5 * *           | At 00:00 on every fifth day of month from 2 through 31
    0 0 2-10/5 * *        | At 00:00 on every fifth day of month from 2 through 10
    0 0 1-5,*/5 * *       | At 00:00 on every day of month from 1 through 5 and every fifth day of month
    0 0 1,L * *           | At 00:00 on the first and the last day of month
    0 0 1,2,L * *         | At 00:00 on the first, the second, and the last day of month
    0 0 L * *             | At 00:00 on the last day of every month
    0 0 L/2 * *           | At 00:00 on the last day of every month
    0 0 L * MON           | At 00:00 on the last day of the month and on Monday
    0 0 LW * *            | At 00:00 on the last weekday of every month
    0 0 LW/2 * *          | At 00:00 on the last weekday of every month
    0 0 LW * MON          | At 00:00 on the last weekday of the month and on Monday
    0 0 L,LW * *          | At 00:00 on the last day of the month and the last weekday of the month
    """


class TestMonthField(TestBase):
    """
    * * * 1 *             | Every minute in January
    * * 15 JAN-FEB *      | Every minute on the 15th day of January and February
    0 0 * 1 *             | At 00:00 every day in January
    0 0 * 1,1 *           | At 00:00 every day in January
    0 0 * JAN *           | At 00:00 every day in January
    0 0 * 1-2 *           | At 00:00 every day in January and February
    0 0 * JAN-FEB *       | At 00:00 every day in January and February
    0 0 15 JAN-FEB *      | At 00:00 on the 15th day of January and February
    0 0 * 1-3 *           | At 00:00 in every month from January through March
    0 0 * */2 *           | At 00:00 in every second month
    0 0 * 1/1 *           | At 00:00 every day
    0 0 * 1/2 *           | At 00:00 in every second month
    0 0 * 3/2 *           | At 00:00 in every second month from March through December
    0 0 * 1-6/2 *         | At 00:00 in every second month from January through June
    0 0 * 1-2,12 *        | At 00:00 every day in January, February, and December
    0 0 * 1-3,12 *        | At 00:00 in every month from January through March and December
    """


class TestSingleDateInMonth(TestBase):
    """
    0 0 1 1-2 *           | At 00:00 on the first day of January and February
    0 0 1 JAN-FEB *       | At 00:00 on the first day of January and February
    0 0 1 1-3 *           | At 00:00 on the first day of every month from January through March
    0 0 1 */2 *           | At 00:00 on the first day of every second month
    0 0 1 1/2 *           | At 00:00 on the first day of every second month
    0 0 1 3/2 *           | At 00:00 on the first day of every second month from March through December
    0 0 1 1-6/2 *         | At 00:00 on the first day of every second month from January through June
    0 0 1 1-2,12 *        | At 00:00 on the first day of January, February, and December
    0 0 1 1-3,12 *        | At 00:00 on the first day of every month from January through March and December
    0 0 1 1 1             | At 00:00 on the first day of month and on Monday in January
    0 0 1 1 1-5           | At 00:00 on the first day of month and on Monday through Friday in January
    0 0 1-2 1 1-5         | At 00:00 on the first and the second day of month and on Monday through Friday in January
    """


class TestWeekdayField(TestBase):
    """
    * * * * 1#2           | Every minute on the second Monday of the month
    * * * * 1L            | Every minute on the last Monday of the month
    0 0 * * 1             | At 00:00 on Monday
    0 0 * * 1,1           | At 00:00 on Monday
    0 0 * * MON           | At 00:00 on Monday
    0 0 * * 1#2           | At 00:00 on the second Monday of the month
    0 0 * * MON#2         | At 00:00 on the second Monday of the month
    0 0 * * 1L            | At 00:00 on the last Monday of the month
    0 0 * * 1-2           | At 00:00 on Monday and Tuesday
    0 0 * * 1,2           | At 00:00 on Monday and Tuesday
    0 0 * * MON,TUE       | At 00:00 on Monday and Tuesday
    0 0 * * 1-3           | At 00:00 on Monday through Wednesday
    0 0 * * MON-WED       | At 00:00 on Monday through Wednesday
    0 0 * * 1-3,5         | At 00:00 on Monday through Wednesday and Friday
    0 0 * * */2           | At 00:00 on every second day of week
    0 0 * * 0/2           | At 00:00 on every second day of week
    0 0 * * 1/2           | At 00:00 on every second day of week from Monday through Sunday
    0 0 * * 1-7           | At 00:00 on Monday through Sunday
    0 0 * * 1-7/1         | At 00:00 on Monday through Sunday
    0 0 * * 0-6           | At 00:00 on Sunday through Saturday
    0 0 * * 0-6/1         | At 00:00 on Sunday through Saturday
    """


class TestDateCombinations(TestBase):
    """
    0 0 15 * *            | At 00:00 on the 15th day of every month
    0 0 15 1 1            | At 00:00 on the 15th day of month and on Monday in January
    0 0 * 1 1             | At 00:00 on Monday in January
    0 0 * JAN-FEB *       | At 00:00 every day in January and February
    0 0 * JAN-MAR *       | At 00:00 in every month from January through March
    0 0 15 JAN-FEB *      | At 00:00 on the 15th day of January and February
    0 0 1 JAN-FEB *       | At 00:00 on the first day of January and February
    0 0 1,2 JAN-FEB *     | At 00:00 on the first and the second day of month in January and February
    0 0 * * 1-5           | At 00:00 on Monday through Friday
    0 0 L JAN *           | At 00:00 on the last day of January
    0 0 LW JAN *          | At 00:00 on the last weekday of January
    """


class TestSpecificTimes(TestBase):
    """
    0 0 * * *             | At 00:00 every day
    0 2 * * *             | At 02:00 every day
    0,30 13,14 * * *      | At 13:00, 13:30, 14:00, and 14:30 every day
    0,15,30,45 2 * * *    | At 02:00, 02:15, 02:30, and 02:45 every day
    0,15,30,45 2,3 * * *  | At minutes 0, 15, 30, and 45 past hours 2 and 3
    0-10 11 * * *         | Every minute from 11:00 through 11:10
    * 9-17 * * *          | Every minute from 09:00 through 17:59
    */2 9-17 * * *        | Every second minute from 09:00 through 17:59
    """


class TestSpecificDates(TestBase):
    """
    0 0 1 1 *            | At 00:00 on January 1
    0 0 15 1 *           | At 00:00 on January 15
    0 0 L 1 *            | At 00:00 on the last day of January
    0 0 LW 1 *           | At 00:00 on the last weekday of January
    """


class TestFunkySchedules(TestBase):
    """
    0 0 1-7 * */7        | At 00:00 on every day of month from 1 through 7 if it's on every seventh day of week
    0 0 */100,1-7 * MON  | At 00:00 on every 100th day of month and every day of month from 1 through 7 if it's on Monday
    """


class TestSmoke(TestBase):
    """
    30-59/5 2,4,6 1-10 1-3 * | Every fifth minute from 30 through 59 past hours 2, 4, and 6 on every day of month from 1 through 10 in every month from January through March
    0/15 9-17 1,10 * *       | Every 15th minute from 09:00 through 17:59 on the first and the 10th day of month
    * * * * 1,2,3            | Every minute on Monday, Tuesday, and Wednesday
    0 0 1 1/2 * *            | At 00:00 on the first day of every second month
    0 0 1 1/2,12 * *         | At 00:00 on the first day of every second month and December
    """


if __name__ == "__main__":
    unittest.main()
