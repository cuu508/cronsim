from __future__ import annotations

import calendar
from datetime import date, datetime, time
from datetime import timedelta as td
from datetime import timezone
from enum import IntEnum
from typing import Set, Tuple, Union, cast

UTC = timezone.utc

SpecItem = Union[int, Tuple[int, int]]

RANGES = [
    range(0, 60),
    range(0, 24),
    range(1, 32),
    range(1, 13),
    range(0, 8),
]
SYMBOLIC_DAYS = "SUN MON TUE WED THU FRI SAT".split()
SYMBOLIC_MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
DAYS_IN_MONTH = [-1, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
FIELD_NAMES = ["minute", "hour", "day-of-month", "month", "day-of-week"]


class CronSimError(Exception):
    pass


class Field(IntEnum):
    MINUTE = 0
    HOUR = 1
    DAY = 2
    MONTH = 3
    DOW = 4

    def msg(self) -> str:
        return "Bad %s" % FIELD_NAMES[self]

    def _int(self, value: str) -> int:
        if value == "":
            raise CronSimError(self.msg())
        for ch in value:
            if ch not in "0123456789":
                raise CronSimError(self.msg())

        return int(value)

    def int(self, s: str) -> int:
        if self == Field.MONTH and s in SYMBOLIC_MONTHS:
            return SYMBOLIC_MONTHS.index(s) + 1

        if self == Field.DOW and s in SYMBOLIC_DAYS:
            return SYMBOLIC_DAYS.index(s)

        v = self._int(s)
        if v not in RANGES[self]:
            raise CronSimError(self.msg())

        return v

    def parse(self, s: str) -> Set[SpecItem]:
        if s == "*":
            return set(RANGES[self])

        if "," in s:
            result = set()
            for term in s.split(","):
                result.update(self.parse(term))
            return result

        if self == Field.DOW and "L" in s:
            value = s[:-1]
            if not value.isdigit():
                raise CronSimError(self.msg())

            dow = self.int(s[:-1])
            return {(dow, CronSim.LAST)}

        if "#" in s and self == Field.DOW:
            term, nth_str = s.split("#", maxsplit=1)
            nth = self._int(nth_str)
            if nth < 1 or nth > 5:
                raise CronSimError(self.msg())

            nth_tuple = (self.int(term), nth)
            return {nth_tuple}

        if "/" in s:
            term, step_str = s.split("/", maxsplit=1)
            step = self._int(step_str)
            if step == 0:
                raise CronSimError(self.msg())

            items = self.parse(term)
            if items == {CronSim.LAST} or items == {CronSim.LAST_WEEKDAY}:
                return items

            if len(items) == 1:
                start = items.pop()
                assert isinstance(start, int)
                end = max(RANGES[self])
                tail = range(start, end + 1)
                return set(tail[::step])

            # items is an unordered set, so sort it before taking
            # every step-th item. Then convert it back to set.
            return set(sorted(items)[::step])

        if "-" in s:
            start_str, end_str = s.split("-", maxsplit=1)
            start = self.int(start_str)
            end = self.int(end_str)

            if end < start:
                raise CronSimError(self.msg())

            return set(range(start, end + 1))

        if self == Field.DAY and s == "LW":
            return {CronSim.LAST_WEEKDAY}

        if self == Field.DAY and s == "L":
            return {CronSim.LAST}

        return {self.int(s)}


def is_imaginary(dt: datetime) -> bool:
    return dt != dt.astimezone(UTC).astimezone(dt.tzinfo)


def last_weekday(year: int, month: int) -> int:
    """Return the date of the last weekday of a given year and month."""
    first_dow, last_date = calendar.monthrange(year, month)
    last_dow = (first_dow + last_date - 1) % 7

    if last_dow == 6:
        return last_date - 2
    elif last_dow == 5:
        return last_date - 1

    return last_date


class CronSim(object):
    LAST = -1000
    LAST_WEEKDAY = -1001

    def __init__(self, expr: str, dt: datetime):
        self.dt = dt.replace(second=0, microsecond=0)

        self.parts = expr.upper().split()
        if len(self.parts) != 5:
            raise CronSimError("Wrong number of fields")

        # In Debian cron, if either the day-of-month or the day-of-week field
        # starts with a star, then there is an "AND" relationship between them.
        # Otherwise it's "OR".
        self.day_and = self.parts[2].startswith("*") or self.parts[4].startswith("*")

        self.minutes = cast(Set[int], Field.MINUTE.parse(self.parts[0]))
        self.hours = cast(Set[int], Field.HOUR.parse(self.parts[1]))
        self.days = cast(Set[int], Field.DAY.parse(self.parts[2]))
        self.months = cast(Set[int], Field.MONTH.parse(self.parts[3]))
        self.weekdays = Field.DOW.parse(self.parts[4])

        if len(self.days) and min(self.days) > 29:
            # Check if we have any month with enough days
            if min(self.days) > max(DAYS_IN_MONTH[month] for month in self.months):
                raise CronSimError(Field.DAY.msg())

        self.fixup_tz = None
        if self.dt.tzinfo in (None, UTC):
            # No special DST handling for UTC
            pass
        else:
            if not self.parts[0].startswith("*") and not self.parts[1].startswith("*"):
                # Will use special handling for jobs that run at specific time, or
                # with a granularity greater than one hour (to mimic Debian cron).
                self.fixup_tz = self.dt.tzinfo
                self.dt = self.dt.replace(tzinfo=None)

    def tick(self, minutes: int = 1) -> None:
        """Roll self.dt forward by 1 or more minutes and fix timezone."""

        if self.dt.tzinfo not in (None, UTC):
            as_utc = self.dt.astimezone(UTC)
            as_utc += td(minutes=minutes)
            self.dt = as_utc.astimezone(self.dt.tzinfo)
        else:
            self.dt += td(minutes=minutes)

    def advance_minute(self) -> bool:
        """Roll forward the minute component until it satisfies the constraints.

        Return False if the minute meets contraints without modification.
        Return True if self.dt was rolled forward.

        """

        if self.dt.minute in self.minutes:
            return False

        if len(self.minutes) == 1:
            # An optimization for the special case where self.minutes has exactly
            # one element. Instead of advancing one minute per iteration,
            # make a jump from the current minute to the target minute.
            delta = (next(iter(self.minutes)) - self.dt.minute) % 60
            self.tick(minutes=delta)

        while self.dt.minute not in self.minutes:
            self.tick()
            if self.dt.minute == 0:
                # Break out to re-check month, day and hour
                break

        return True

    def advance_hour(self) -> bool:
        """Roll forward the hour component until it satisfies the constraints.

        Return False if the hour meets contraints without modification.
        Return True if self.dt was rolled forward.

        """

        if self.dt.hour in self.hours:
            return False

        self.dt = self.dt.replace(minute=0)
        while self.dt.hour not in self.hours:
            self.tick(minutes=60)
            if self.dt.hour == 0:
                # break out to re-check month and day
                break

        return True

    def match_dom(self, d: date) -> bool:
        """Return True is day-of-month matches."""
        if d.day in self.days:
            return True

        # Optimization: there are no months with fewer than 28 days.
        # If 28th is Sunday, the last weekday of the month is the 26th.
        # Any date before 26th cannot be the the last weekday of the month.
        if self.LAST_WEEKDAY in self.days and d.day >= 26:
            if d.day == last_weekday(d.year, d.month):
                return True

        # Optimization: there are no months with fewer than 28 days,
        # so any date before 28th cannot be the the last day of the month
        if self.LAST in self.days and d.day >= 28:
            _, last = calendar.monthrange(d.year, d.month)
            if d.day == last:
                return True

        return False

    def match_dow(self, d: date) -> bool:
        """Return True is day-of-week matches."""
        dow = d.weekday() + 1
        if dow in self.weekdays or dow % 7 in self.weekdays:
            return True

        if (dow, self.LAST) in self.weekdays or (dow % 7, self.LAST) in self.weekdays:
            _, last = calendar.monthrange(d.year, d.month)
            if d.day + 7 > last:
                # Same day next week would be outside this month.
                # So this is the last one this month.
                return True

        idx = (d.day + 6) // 7
        if (dow, idx) in self.weekdays or (dow % 7, idx) in self.weekdays:
            return True

        return False

    def match_day(self, d: date) -> bool:
        if self.day_and:
            return self.match_dom(d) and self.match_dow(d)

        return self.match_dom(d) or self.match_dow(d)

    def advance_day(self) -> bool:
        """Roll forward the day component until it satisfies the constraints.

        This method advances the date until it matches either the
        day-of-month, or the day-of-week constraint.

        Return False if the day meets contraints without modification.
        Return True if self.dt was rolled forward.

        """

        needle = self.dt.date()
        if self.match_day(needle):
            return False

        while not self.match_day(needle):
            needle += td(days=1)
            if needle.day == 1:
                # We're in a different month now, break out to re-check month
                # This significantly speeds up the "0 0 * 2 MON#5" case
                break

        self.dt = datetime.combine(needle, time(), tzinfo=self.dt.tzinfo)
        return True

    def advance_month(self) -> None:
        """Roll forward the month component until it satisfies the constraints."""

        if self.dt.month in self.months:
            return

        needle = self.dt.date()
        while needle.month not in self.months:
            needle = (needle.replace(day=1) + td(days=32)).replace(day=1)

        self.dt = datetime.combine(needle, time(), tzinfo=self.dt.tzinfo)

    def __iter__(self) -> "CronSim":
        return self

    def __next__(self) -> datetime:
        self.tick()

        start_year = self.dt.year
        while True:
            self.advance_month()
            if self.dt.year > start_year + 50:
                # Give up if there is no match for 50 years.
                # It would be nice to detect "this will never yield any results"
                # situations in a more intelligent way.
                raise StopIteration

            if self.advance_day():
                continue

            if self.advance_hour():
                continue

            if self.advance_minute():
                continue

            # If all constraints are satisfied then we have the result.
            # The last step is to check if we need to fix up an imaginary
            # or ambiguous date.
            if self.fixup_tz:
                result = self.dt.replace(tzinfo=self.fixup_tz, fold=0)
                while is_imaginary(result):
                    self.dt += td(minutes=1)
                    result = self.dt.replace(tzinfo=self.fixup_tz)

                return result

            return self.dt

    def explain(self) -> str:
        from cronsim.explain import Expression

        return Expression(self.parts).explain()
