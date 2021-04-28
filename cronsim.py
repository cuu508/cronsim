import calendar
from datetime import datetime, timedelta as td, time
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
    list(range(0, 7)),
]

SYMBOLIC_DAYS = "MON TUE WED THU FRI SAT SUN".split()
SYMBOLIC_MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


def _int(field, value):
    if field == Field.MONTH:
        if value.upper() in SYMBOLIC_MONTHS:
            value = SYMBOLIC_MONTHS.index(value.upper()) + 1

    if field == Field.DOW:
        if value.upper() in SYMBOLIC_DAYS:
            value = SYMBOLIC_DAYS.index(value.upper()) + 1

    return int(value)


def _parse(field, value):
    if value == "*":
        return RANGES[field]

    if "," in value:
        result = set()
        for item in value.split(","):
            result.update(_parse(field, item))
        return sorted(result)

    if "#" in value and field == Field.DOW:
        term, nth = value.split("#")
        return [(_int(field, term), int(nth))]

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

    if value == "L" and field == Field.DAY:
        return [CronSim.LAST]

    return [_int(field, value)]


class CronSimError(Exception):
    pass


class CronSim(object):
    LAST = 1000

    def __init__(self, expr, dt):
        self.dt = dt.replace(second=0, microsecond=0)

        parts = expr.split()
        if len(parts) != 5:
            raise CronSimError("Bad expression, wrong number of fields")

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

        self.dt = self.dt.replace(minute=min(self.minutes))
        return True

    def match_day(self, d):
        # Does the day of the month match?
        if d.day in self.days:
            return True

        if CronSim.LAST in self.days:
            _, last = calendar.monthrange(d.year, d.month)
            if d.day == last:
                return True

        # Does the day of the week match?
        dow = d.weekday() + 1
        if dow in self.weekdays or dow % 7 in self.weekdays:
            return True

        idx = (d.day + 6) // 7
        if (dow, idx) in self.weekdays or (dow % 7, idx) in self.weekdays:
            return True

    def advance_day(self):
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

        self.dt = datetime.combine(needle, time(), self.dt.tzinfo)
        return True

    def advance_month(self):
        """Roll forward the month component until it satisfies the constraints. """

        if self.dt.month in self.months:
            return

        needle = self.dt.date()
        while needle.month not in self.months:
            needle += td(days=1)

        self.dt = datetime.combine(needle, time(), self.dt.tzinfo)

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
    a = CronSim("0 1 * * */2", datetime.now())
    for i in range(0, 10):
        print("Here's what we got: ", next(a))
