from __future__ import annotations

from dataclasses import dataclass
from typing import Generator


@dataclass(frozen=True)
class Sequence:
    start: int | None = None
    stop: int | None = None
    step: int = 1
    nth: int | None = None

    def is_star(self) -> bool:
        return self.start is None and self.step == 1

    def is_single(self) -> bool:
        return self.start is not None and self.start == self.stop


def join(l: list[str]) -> str:
    if len(l) == 1:
        return l[0]

    if len(l) == 2:
        return f"{l[0]} and {l[1]}"

    head = ", ".join(l[:-1])
    return f"{head}, and {l[-1]}"


def ordinal(x: int) -> str:
    if x == 1:
        return "1st"
    if x == 2:
        return "2nd"
    if x == 3:
        return "3rd"
    return f"{x}th"


def format_time(h: int, m: int) -> str:
    if h == 0:
        return f"00:{m:02d}"

    return f"{h}:{m:02d}"


class Field(object):
    name = "FIXME"
    symbolic: list[str] = []
    min_value = 0
    max_value = 0

    def __init__(self, value: str):
        self.value = value
        self.parsed: list[Sequence] = []

        for seq in self.parse(value):
            if seq not in self.parsed:
                self.parsed.append(seq)

        # If the field contains a single numeric value,
        # store it in self.single_value
        self.single_value = self.parsed[0].start
        for seq in self.parsed:
            if seq.start != self.single_value or seq.stop != self.single_value:
                self.single_value = None
                break

        # Does the field cover the full range?
        self.star = all(seq.is_star() for seq in self.parsed)
        # Are there any single values?
        self.any_singles = any(seq.is_single() for seq in self.parsed)
        # Are all values single values?
        self.all_singles = all(seq.is_single() for seq in self.parsed)

    def parse(self, value: str) -> Generator[Sequence, None, None]:
        for term in value.split(","):
            if term == "*":
                yield Sequence()
            elif isinstance(self, Weekday) and term.endswith("L"):
                v = self._int(term[:-1])
                yield Sequence(start=v, stop=v, nth=-1)
            elif "#" in term:
                term, nth = term.split("#")
                v = self._int(term)
                yield Sequence(start=v, stop=v, nth=int(nth))
            elif "/" in term:
                term, step_str = term.split("/")
                step = int(step_str)
                if term == "*":
                    yield Sequence(step=step)
                else:
                    if "-" in term:
                        start_str, stop_str = term.split("-")
                        start, stop = self._int(start_str), self._int(stop_str)
                    else:
                        start = self._int(term)
                        stop = self.max_value

                    if start <= self.min_value and stop >= self.max_value:
                        yield Sequence(step=step)
                    else:
                        yield Sequence(start=start, stop=stop, step=step)
            elif "-" in term:
                start_str, stop_str = term.split("-")
                start, stop = self._int(start_str), self._int(stop_str)
                if start + 1 == stop:
                    # treat a 2-long sequence as two single values:
                    yield Sequence(start=start, stop=start)
                    yield Sequence(start=stop, stop=stop)
                elif start <= self.min_value and stop >= self.max_value:
                    yield Sequence()
                else:
                    yield Sequence(start=start, stop=stop)
            elif term == "L":
                yield Sequence(start=-1, stop=-1, nth=-1)
            else:
                v = self._int(term)
                yield Sequence(start=v, stop=v)

    def _int(self, value: str) -> int:
        if value in self.symbolic:
            return self.symbolic.index(value)
        return int(value)

    def singles(self) -> list[int]:
        return [seq.start for seq in self.parsed if isinstance(seq.start, int)]

    def label(self, idx: int) -> str:
        return str(idx)

    def format_single(self, value: int) -> str:
        return f"{self.name} {self.label(value)}"

    def format_nth(self, value: int, nth: int) -> str:
        raise NotImplementedError

    def format_every(self, step: int = 1) -> str:
        if step == 1:
            return f"every {self.name}"
        return f"every {ordinal(step)} {self.name}"

    def format_seq(self, start: int, stop: int, step: int = 1) -> str:
        start_str = self.label(start)
        stop_str = self.label(stop)
        if step == 1:
            return f"every {self.name} from {start_str} through {stop_str}"
        return f"every {ordinal(step)} {self.name} from {start_str} through {stop_str}"

    def format(self) -> str:
        parts = []
        for seq in self.parsed:
            if seq.start is None:
                parts.append(self.format_every(seq.step))
            elif seq.stop != seq.start:
                assert seq.stop is not None
                parts.append(self.format_seq(seq.start, seq.stop, seq.step))
            elif seq.nth is not None:
                parts.append(self.format_nth(seq.start, seq.nth))
            else:
                parts.append(self.format_single(seq.start))

        return join(parts)

    def __str__(self) -> str:
        return self.format()


class Minute(Field):
    name = "minute"
    min_value = 0
    max_value = 59

    def format(self) -> str:
        if self.all_singles and len(self.parsed) > 1:
            labels = [self.label(v) for v in self.singles()]
            return f"minutes {join(labels)}"
        return super().format()

    def __str__(self) -> str:
        result = super().__str__()
        if self.any_singles:
            return "at " + result

        return result


class Hour(Field):
    name = "hour"
    min_value = 0
    max_value = 23

    def format(self) -> str:
        if self.all_singles and len(self.parsed) > 1:
            labels = [self.label(v) for v in self.singles()]
            return f"hours {join(labels)}"
        return super().format()

    def __str__(self) -> str:
        if self.star:
            return "every hour"
        return "past " + super().__str__()


class Day(Field):
    name = "day of month"
    min_value = 1
    max_value = 31

    def format_single(self, value: int) -> str:
        return f"the {ordinal(value)} day of month"

    def format_nth(self, value: int, nth: int) -> str:
        if nth == -1:
            return "the last day of the month"
        return super().format_nth(value, nth)

    def format(self) -> str:
        if self.single_value == 1:
            return "the first day of month"
        if self.all_singles and len(self.parsed) > 1:
            labels = [ordinal(v) for v in self.singles()]
            return f"the {join(labels)} day of month"
        return super().format()

    def __str__(self) -> str:
        return "on " + super().__str__()


class Month(Field):
    name = "month"
    min_value = 1
    max_value = 12
    symbolic = "_ JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
    labels = "_ January February March April May June July August September October November December".split()

    def label(self, idx: int) -> str:
        return self.labels[idx]

    def format_single(self, value: int) -> str:
        # "January" instead of "month January"
        return self.label(value)

    def __str__(self) -> str:
        return "in " + super().__str__()


class Weekday(Field):
    name = "day of week"
    min_value = 0
    max_value = 7
    symbolic = "SUN MON TUE WED THU FRI SAT SUN".split()
    labels = "Sunday Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()

    def label(self, idx: int) -> str:
        return self.labels[idx]

    def format_single(self, value: int) -> str:
        # "Monday" instead of "day-of-week Monday"
        return self.label(value)

    def format_nth(self, value: int, nth: int) -> str:
        label = self.label(value)
        if nth == -1:
            return f"the last {label} of the month"

        return f"the {ordinal(nth)} {label} of the month"

    def format_seq(self, start: int, stop: int, step: int = 1) -> str:
        if step == 1:
            # "Monday through Friday"
            # instead of "every day of week from Monday through Friday"
            return f"{self.label(start)} through {self.label(stop)}"

        return super().format_seq(start, stop, step)

    def __str__(self) -> str:
        return "on " + super().__str__()


class Expression(object):
    def __init__(self, parts: list[str]):
        self.minute = Minute(parts[0])
        self.hour = Hour(parts[1])
        self.day = Day(parts[2])
        self.month = Month(parts[3])
        self.dow = Weekday(parts[4])

    def times(self) -> str | None:
        # at 11:00, 11:30, ...
        if self.hour.all_singles and self.minute.all_singles:
            minute_terms, hour_terms = self.minute.singles(), self.hour.singles()

            if len(minute_terms) * len(hour_terms) <= 4:
                times = []
                for h in sorted(hour_terms):
                    for m in sorted(minute_terms):
                        times.append(format_time(h, m))

                return "at " + join(times)

        # every minute from 11:00 through 11:10
        if self.hour.single_value and len(self.minute.parsed) == 1:
            seq = self.minute.parsed[0]
            if seq.start is not None and seq.stop is not None and seq.step == 1:
                start = format_time(self.hour.single_value, seq.start)
                stop = format_time(self.hour.single_value, seq.stop)
                return f"Every minute from {start} through {stop}"

        return None

    def single_date(self) -> str | None:
        if self.month.single_value and self.dow.star:
            if self.day.single_value == -1:
                return f"on the last day of {self.month.format()}"
            if self.day.single_value:
                date_ord = ordinal(self.day.single_value)
                return f"on {self.month.format()} {date_ord}"

        return None

    def translate_time(self) -> tuple[str, bool]:
        if self.hour.star:
            if self.minute.star:
                return "every minute", False
            if self.minute.single_value == 0:
                return "at the start of every hour", False
            return f"{self.minute} of every hour", False

        if times := self.times():
            return times, True

        return f"{self.minute} {self.hour}", False

    def translate_date(self) -> str:
        if single_date := self.single_date():
            return single_date

        if self.day.star and self.dow.star and self.month.all_singles:
            # At ... every day in January
            return f"every day {self.month}"

        parts: list[Field | str] = []
        if not self.day.star:
            parts.append(self.day)
        if not self.dow.star:
            if not self.day.star:
                parts.append("and")
            parts.append(self.dow)
        if not self.month.star:
            parts.append(self.month)

        return " ".join(str(part) for part in parts)

    def explain(self) -> str:
        time, allow_every_day = self.translate_time()
        if date := self.translate_date():
            result = f"{time} {date}"
        elif allow_every_day:
            result = f"{time} every day"
        else:
            result = f"{time}"

        return result[0].upper() + result[1:]


def explain(expr: str) -> str:
    parts = expr.upper().split()
    return Expression(parts).explain()


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        print(explain(sys.argv[1]))
