from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Sequence:
    start: int | None
    stop: int | None
    step: int

    def is_star(self):
        return self.start is None and self.step == 1

    def is_single(self):
        return self.start is not None and self.start == self.stop


def join(l):
    if len(l) == 1:
        return l[0]

    if len(l) == 2:
        return f"{l[0]} and {l[1]}"

    head = ", ".join(map(str, l[:-1]))
    return f"{head}, and {l[-1]}"


def ordinal(x: int) -> str:
    if x == 1:
        return "1st"
    if x == 2:
        return "2nd"
    if x == 3:
        return "3rd"
    return f"{x}th"


def format_time(h: int, m: int):
    if h == 0:
        return f"00:{m:02d}"

    return f"{h}:{m:02d}"


class Field(object):
    name = "FIXME"
    symbolic = []

    def __init__(self, value: str):
        self.value = value
        self.parsed = []

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

    def terms(self):
        return self.value.split(",")

    def parse(self, value):
        for term in value.split(","):
            if term == "*":
                yield Sequence(None, None, 1)
            elif "/" in term:
                term, step = term.split("/")
                step = int(step)
                if term == "*":
                    yield Sequence(None, None, step)
                else:
                    if "-" in term:
                        start_str, stop_str = term.split("-")
                        start, stop = self.int(start_str), self.int(stop_str)
                    else:
                        start = self.int(term)
                        stop = self.max_value

                    if start <= self.min_value and stop >= self.max_value:
                        yield Sequence(None, None, step)
                    else:
                        yield Sequence(start, stop, step)
            elif "-" in term:
                start_str, stop_str = term.split("-")
                start, stop = self.int(start_str), self.int(stop_str)
                if start + 1 == stop:
                    # treat a 2-long sequence as two single values:
                    yield Sequence(start, start, 1)
                    yield Sequence(stop, stop, 1)
                elif start <= self.min_value and stop >= self.max_value:
                    yield Sequence(None, None, 1)
                else:
                    yield Sequence(start, stop, 1)
            else:
                v = self.int(term)
                yield Sequence(v, v, 1)

    def int(self, value: str):
        if value in self.symbolic:
            return self.symbolic.index(value)
        return int(value)

    def label(self, idx: int):
        return str(idx)

    def format_single(self, value: int):
        value = self.label(value)
        return f"{self.name} {value}"

    def format_every(self, step: int = 1):
        if step == 1:
            return f"every {self.name}"
        return f"every {ordinal(step)} {self.name}"

    def format_seq(self, start: int, stop: int, step: int = 1):
        start = self.label(start)
        stop = self.label(stop)
        if step == 1:
            return f"every {self.name} from {start} through {stop}"
        return f"every {ordinal(step)} {self.name} from {start} through {stop}"

    def format(self):
        parts = []
        for seq in self.parsed:
            if seq.start is None:
                parts.append(self.format_every(seq.step))
            elif seq.stop != seq.start:
                parts.append(self.format_seq(seq.start, seq.stop, seq.step))
            else:
                parts.append(self.format_single(seq.start))

        return join(parts)

    def __str__(self):
        return self.format()


class Minute(Field):
    name = "minute"
    min_value = 0
    max_value = 59

    def format(self):
        if self.all_singles and len(self.parsed) > 1:
            labels = [self.label(seq.start) for seq in self.parsed]
            return f"minutes {join(labels)}"
        return super().format()

    def __str__(self):
        result = super().__str__()
        if self.any_singles:
            return "at " + result

        return result


class Hour(Field):
    name = "hour"
    min_value = 0
    max_value = 23

    def __str__(self):
        if self.star:
            return "every hour"
        return "past " + super().__str__()


class Day(Field):
    name = "day-of-month"
    min_value = 1
    max_value = 31

    def format(self):
        if self.single_value == 1:
            return "the first day of month"
        return super().format()

    def __str__(self):
        return "on " + super().__str__()


class Month(Field):
    name = "month"
    min_value = 1
    max_value = 12
    symbolic = "_ JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
    labels = "_ January February March April May June July August September October November December".split()

    def label(self, idx: int):
        return self.labels[idx]

    def format_single(self, value):
        # "January" instead of "month January"
        return self.label(value)

    def __str__(self):
        return "in " + super().__str__()


class Weekday(Field):
    name = "day-of-week"
    min_value = 0
    max_value = 7
    symbolic = "SUN MON TUE WED THU FRI SAT SUN".split()
    labels = "Sunday Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()

    def label(self, idx: int):
        return self.labels[idx]

    def format_single(self, value):
        # "Monday" instead of "day-of-week Monday"
        return self.label(value)

    def format_seq(self, start: int, stop: int, step: int = 1):
        if step == 1:
            # "January through July" instead of "every month from January through July"
            return f"{self.label(start)} through {self.label(stop)}"

        return super().format_seq(start, stop, step)

    def __str__(self):
        return "on " + super().__str__()


class Translator(object):
    def __init__(self, csobj):
        self.minute = Minute(csobj.parts[0])
        self.hour = Hour(csobj.parts[1])
        self.day = Day(csobj.parts[2])
        self.month = Month(csobj.parts[3])
        self.dow = Weekday(csobj.parts[4])

    def times(self):
        # at 11:00, 11:30, ...
        if self.hour.all_singles and self.minute.all_singles:
            minute_terms = [seq.start for seq in self.minute.parsed]
            hour_terms = [seq.start for seq in self.hour.parsed]

            if len(minute_terms) * len(hour_terms) <= 4:
                times = []
                for h in sorted(hour_terms):
                    for m in sorted(minute_terms):
                        times.append(format_time(h, m))

                return "at " + join(times)

        # every minute from 11:00 through 11:10
        if self.hour.single_value and len(self.minute.parsed) == 1:
            seq = self.minute.parsed[0]
            if seq.start is not None and seq.step == 1:
                start = format_time(self.hour.single_value, seq.start)
                stop = format_time(self.hour.single_value, seq.stop)
                return f"Every minute from {start} through {stop}"

    def single_date(self):
        if self.day.single_value and self.month.single_value and self.dow.star:
            date_ord = ordinal(self.day.int(self.day.single_value))
            return f"on {self.month.format()} {date_ord}"

    def translate_time(self):
        if self.hour.star:
            if self.minute.star:
                return "every minute", False
            if self.minute.single_value == 0:
                return "at the start of every hour", False
            return f"{self.minute} of every hour", False

        if times := self.times():
            return times, True

        return f"{self.minute} {self.hour}", False

    def translate_date(self):
        if single_date := self.single_date():
            return single_date

        parts = []
        if not self.day.star:
            parts.append(self.day)
        if not self.dow.star:
            if not self.day.star:
                parts.append("and")
            parts.append(self.dow)
        if not self.month.star:
            parts.append(self.month)

        return " ".join(str(part) for part in parts)

    def translate(self):
        time, allow_every_day = self.translate_time()
        if date := self.translate_date():
            return f"{time} {date}"
        elif allow_every_day:
            return f"{time} every day"

        return f"{time}"


def explain(csobj):
    result = Translator(csobj).translate()
    result = result[0].upper() + result[1:]
    return result
