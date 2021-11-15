import calendar
from datetime import date, datetime, timedelta as td, time, timezone
from enum import IntEnum

UTC = timezone.utc

RANGES = [
    frozenset(range(0, 60)),
    frozenset(range(0, 24)),
    frozenset(range(1, 32)),
    frozenset(range(1, 13)),
    frozenset(range(0, 8)),
    frozenset(range(0, 60)),
]

SYMBOLIC_DAYS = "SUN MON TUE WED THU FRI SAT".split()
SYMBOLIC_MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
DAYS_IN_MONTH = [None, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class CronSimError(Exception):
    pass


def _int(value):
    if not value.isdigit():
        raise CronSimError("Bad value: %s" % value)

    return int(value)


class Field(IntEnum):
    MINUTE = 0
    HOUR = 1
    DAY = 2
    MONTH = 3
    DOW = 4

    def int(self, s):
        if self == Field.MONTH and s.upper() in SYMBOLIC_MONTHS:
            return SYMBOLIC_MONTHS.index(s.upper()) + 1

        if self == Field.DOW and s.upper() in SYMBOLIC_DAYS:
            return SYMBOLIC_DAYS.index(s.upper())

        v = _int(s)
        if v not in RANGES[self]:
            raise CronSimError("Bad value: %s" % s)

        return v

    def parse(self, s):
        if s == "*":
            return RANGES[self]

        if "," in s:
            result = set()
            for term in s.split(","):
                result.update(self.parse(term))
            return result

        if "#" in s and self == Field.DOW:
            term, nth = s.split("#", maxsplit=1)
            nth = _int(nth)
            if nth < 1 or nth > 5:
                raise CronSimError("Bad value: %s" % s)

            spec = (self.int(term), nth)
            return {spec}

        if "/" in s:
            term, step = s.split("/", maxsplit=1)
            step = _int(step)
            if step == 0:
                raise CronSimError("Step cannot be zero")

            items = sorted(self.parse(term))
            if items == [CronSim.LAST]:
                return items

            if len(items) == 1:
                start = items[0]
                end = max(RANGES[self])
                items = range(start, end + 1)
            return set(items[::step])

        if "-" in s:
            start, end = s.split("-", maxsplit=1)
            start = self.int(start)
            end = self.int(end)

            if end < start:
                raise CronSimError("Range end cannot be smaller than start")

            return set(range(start, end + 1))

        if self == Field.DAY and s in ("L", "l"):
            return {CronSim.LAST}

        return {self.int(s)}


def is_imaginary(dt):
    return dt != dt.astimezone(UTC).astimezone(dt.tzinfo)


class CronSim(object):
    LAST = -1000

    def __init__(self, expr: str, dt: datetime):
        self.dt = dt.replace(second=0, microsecond=0)

        parts = expr.split()
        if len(parts) != 5:
            raise CronSimError("Wrong number of fields")

        self.minutes = Field.MINUTE.parse(parts[0])
        self.hours = Field.HOUR.parse(parts[1])
        self.days = Field.DAY.parse(parts[2])
        self.months = Field.MONTH.parse(parts[3])
        self.weekdays = Field.DOW.parse(parts[4])

        # If day is unrestricted but dow is restricted then match only with dow:
        if self.days == RANGES[Field.DAY] and self.weekdays != RANGES[Field.DOW]:
            self.days = set()

        # If dow is unrestricted but day is restricted then match only with day:
        if self.weekdays == RANGES[Field.DOW] and self.days != RANGES[Field.DAY]:
            self.weekdays = set()

        if len(self.days) and min(self.days) > 29:
            # Check if we have any month with enough days
            if min(self.days) > max(DAYS_IN_MONTH[month] for month in self.months):
                raise CronSimError("Bad day-of-month")

        self.fixup_tz = None
        if self.dt.tzinfo in (None, UTC):
            # No special DST handling for UTC
            pass
        else:
            if not parts[0].startswith("*") and not parts[1].startswith("*"):
                # Will use special handling for jobs that run at specific time, or
                # with a granularity greater than one hour (to mimic Debian cron).
                self.fixup_tz = self.dt.tzinfo
                self.dt = self.dt.replace(tzinfo=None)

    def tick(self, minutes: int = 1) -> None:
        """ Roll self.dt forward by 1 or more minutes and fix timezone. """

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

    def match_day(self, d: date) -> bool:
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

        return False

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
        """Roll forward the month component until it satisfies the constraints. """

        if self.dt.month in self.months:
            return

        needle = self.dt.date()
        while needle.month not in self.months:
            needle = (needle.replace(day=1) + td(days=32)).replace(day=1)

        self.dt = datetime.combine(needle, time(), tzinfo=self.dt.tzinfo)

    def __iter__(self):
        return self

    def __next__(self) -> datetime:
        self.tick()

        while True:
            self.advance_month()

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
