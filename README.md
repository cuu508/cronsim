# CronSim

[![Tests](https://github.com/cuu508/cronsim/actions/workflows/pytest.yml/badge.svg)](https://github.com/cuu508/cronsim/actions/workflows/pytest.yml)

Cron Sim(ulator), a cron expression parser and evaluator. Works with Python 3.8+.
CronSim is written for and being used in
[Healthchecks](https://github.com/healthchecks/healthchecks/)
(a cron job monitoring service).

Development priorities:

* Correctness. CronSim tries to match Debian's cron as closely as possible,
  including its quirky behaviour during DST transitions.
* Readability. Prefer simple over clever.
* Minimalism. Don't implement features that Healthchecks will not use
  (for example, iteration in reverse, or the seconds field in cron expressions).

## Installation

```
pip install cronsim
```

## Usage

```python
from datetime import datetime
from cronsim import CronSim

it = CronSim("0 0 * 2 MON#5", datetime.now())
for x in range(0, 10):
    print(next(it))
```

Produces:

```
2044-02-29 00:00:00
2072-02-29 00:00:00
2112-02-29 00:00:00
2140-02-29 00:00:00
2168-02-29 00:00:00
2196-02-29 00:00:00
2208-02-29 00:00:00
2236-02-29 00:00:00
2264-02-29 00:00:00
2292-02-29 00:00:00
```

If CronSim receives an invalid cron expression, it raises `cronsim.CronSimError`:

```python
from datetime import datetime
from cronsim import CronSim

CronSim("123 * * * *", datetime.now())
```

Produces:

```
cronsim.cronsim.CronSimError: Bad minute
```

If CronSim cannot find a matching datetime in the next 50 years from the start
date or from the previous match, it stops iteration by raising `StopIteration`:

```python
from datetime import datetime
from cronsim import CronSim

# Every minute of 1st and 21st of month,
# if it is also the *last Monday* of the month:
it = CronSim("* * */20 * 1L", datetime.now())
print(next(it))
```

Produces:

```
StopIteration
```

## CronSim Works With zoneinfo

CronSim starting from version 2.0 is designed to work with timezones provided by
the zoneinfo module.

A previous version, CronSim 1.0, was designed for pytz and relied on its
following non-standard features:

* the non-standard `is_dst` flag in the `localize()` method
* the `pytz.AmbiguousTimeError` and `pytz.NonExistentTimeError` exceptions
* the `normalize()` method

## Supported Cron Expression Features

CronSim aims to match [Debian's cron implementation](https://salsa.debian.org/debian/cron/-/tree/master/)
(which itself is based on Paul Vixie's cron, with modifications). If CronSim evaluates
an expression differently from Debian's cron, that's a bug.

CronSim is open to adding support for non-standard syntax features, as long as
they don't conflict or interfere with the standard syntax.

## DST Transitions

CronSim handles Daylight Saving Time transitions the same as
Debian's cron. Debian has special handling for jobs with a granularity
greater than one hour:

```
Local time changes of less than three hours, such as  those  caused  by
the  start or end of Daylight Saving Time, are handled specially.  This
only applies to jobs that run at a specific time and jobs that are  run
with  a    granularity  greater  than  one hour.  Jobs that run more fre-
quently are scheduled normally.

If time has moved forward, those jobs that would have run in the inter-
val that has been skipped will be run immediately.  Conversely, if time
has moved backward, care is taken to avoid running jobs twice.
```

See test cases in `test_cronsim.py`, `TestDstTransitions` class
for examples of this special handling.

## Cron Expression Feature Matrix

| Feature                              | Debian | Quartz | croniter | cronsim |
| ------------------------------------ | :----: | :----: | :------: | :-----: |
| Seconds in the 6th field             | No     | Yes    | Yes      | No      |
| "L" as the day-of-month              | No     | Yes    | Yes      | Yes     |
| "LW" as the day-of-month             | No     | Yes    | No       | Yes     |
| "L" in the day-of-week field         | No     | Yes    | No       | Yes     |
| Nth weekday of month                 | No     | Yes    | Yes      | Yes     |


**Seconds in the 6th field**: an optional sixth field specifying seconds.
Supports the same syntax features as the minutes field. Quartz Scheduler
expects seconds in the first field, croniter expects seconds in the last field.

Quartz example: `*/15 * * * * *` (every 15 seconds).

**"L" as the day-of-month**: support for the "L" special character in the
day-of-month field. Interpreted as "the last day of the month".

Example: `0 0 L * *` (at the midnight of the last day of every month).

**"LW" as the day-of-month**: support for the "LW" special value in the
day-of-month field. Interpreted as "the last weekday (Mon-Fri) of the month".

Example: `0 0 LW * *` (at the midnight of the last weekday of every month).

**"L" in the day-of-week field**: support for the "{weekday}L" syntax.
For example, "5L" means "the last Friday of the month".

Example: `0 0 * * 6L` (at the midnight of the last Saturday of every month).

**Nth weekday of month**: support for "{weekday}#{nth}" syntax.
For example, "MON#1" means "first Monday of the month", "MON#2" means "second Monday
of the month".

Example: `0 0 * * MON#1` (at midnight of the first monday of every month).

## The `explain()` Method

Starting from version 2.4, the CronSim objects have an `explain()` method
which generates a text description of the supplied cron expression.

```python
from datetime import datetime
from cronsim import CronSim

expr = CronSim("*/5 9-17 * * *", datetime.now())
print(expr.explain())
```

Outputs:

```
Every fifth minute from 09:00 through 17:59
```

The text descriptions are available in English only. The text descriptions
use the 24-hour time format ("23:00" instead of "11:00 PM").

For examples of generated descriptions see `tests/test_explain.py`.