import calendar
from datetime import datetime, timedelta as td
from enum import IntEnum


class Field(IntEnum):
    MINUTE = 0
    HOUR = 1
    DAY = 2
    MONTH = 3
    DOW = 4


RANGES = [
    list(range(0, 60)),
    list(range(0, 24)),
    list(range(1, 32)),
    list(range(1, 13)),
    list(range(1, 8)),
]


def _int(field, value):
    return int(value)


def _parse(field, value):
    if value == "*":
        return RANGES[field]

    if "," in value:
        result = set()
        for item in value.split(","):
            result.update(_parse(field, item))
        return sorted(result)

    if "/" in value:
        term, step = value.split("/")
        items = _parse(field, term)
        if len(items) == 1:
            start = items[0]
            items = [v for v in RANGES[field] if v >= start]

        return items[::int(step)]

    if "-" in value:
        start, end = value.split("-")
        start = _int(field, start)
        end = _int(field, end)
        return list(range(start, end + 1))

    if value == "L":
        if field == Field.DAY:
            return [Wat.LAST]
        if field == Field.DOW:
            return [7]

    return [_int(field, value)]


class Wat(object):
    LAST = 1000

    def __init__(self, expr, dt):
        self.dt = dt.replace(second=0, microsecond=0)

        parts = expr.split()
        self.minutes = _parse(Field.MINUTE, parts[0])
        self.hours = _parse(Field.HOUR, parts[1])
        self.days = _parse(Field.DAY, parts[2])
        self.months = _parse(Field.MONTH, parts[3])
        self.weekdays = _parse(Field.DOW, parts[4])

        # If day is unrestricted but dow is restricted then match only with dow:
        if self.days == RANGES[Field.DAY] and self.weekdays != RANGES[Field.DOW]:
            self.days = []

        # If dow is unrestricted but day is restricted then match only with day:
        if self.weekdays == RANGES[Field.DOW] and self.days != RANGES[Field.DAY]:
            self.weekdays = []

        self.min_m = min(self.minutes)
        self.min_h = min(self.hours)

    def advance_minute(self):
        """Roll forward the minute component until it satisfies the constraints.

        Return False if the minute meets contraints without modification.
        Return True if self.dt was rolled forward.

        """

        if self.dt.minute in self.minutes:
            return False

        delta = min((v - self.dt.minute) % 60 for v in self.minutes)
        self.dt += td(minutes=delta)

        return True

    def advance_hour(self):
        """Roll forward the hour component until it satisfies the constraints.

        Return False if the hour meets contraints without modification.
        Return True if self.dt was rolled forward.

        """

        if self.dt.hour in self.hours:
            return False

        delta = min((v - self.dt.hour) % 24 for v in self.hours)
        self.dt += td(hours=delta)

        self.dt = self.dt.replace(minute=self.min_m)
        return True

    def match_day(self):
        if self.dt.day in self.days:
            return True
        if self.dt.weekday() + 1 in self.weekdays:
            return True
        if Wat.LAST in self.days:
            _, last = calendar.monthrange(self.dt.year, self.dt.month)
            return self.dt.day == last

    def advance_day(self):
        """Roll forward the day component until it satisfies the constraints.

        This method advances the date until it matches either the
        day-of-month, or the day-of-week constraint.

        Return False if the day meets contraints without modification.
        Return True if self.dt was rolled forward.

        """

        if self.match_day():
            return False

        while not self.match_day():
            self.dt += td(days=1)

        self.dt = self.dt.replace(minute=self.min_m, hour=self.min_h)
        return True

    def advance_month(self):
        """Roll forward the month component until it satisfies the constraints. """

        if self.dt.month in self.months:
            return

        while self.dt.month not in self.months:
            self.dt += td(days=1)

        self.dt = self.dt.replace(hour=self.min_h, minute=self.min_m)

    def __iter__(self):
        return self

    def __next__(self):
        self.dt += td(minutes=1)

        while True:
            self.advance_month()

            if self.advance_day():
                continue

            if self.advance_hour():
                continue

            if self.advance_minute():
                continue

            # If all constraints are satisfied then we have the result:
            return self.dt


if __name__ == '__main__':
    a = Wat("15,30,45 21 29 2 1", datetime.now())
    for i in range(0, 10):
        print("Here's what we got: ", next(a))
