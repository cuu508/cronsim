# CronSim

Cron Sim(ulator), a cron expression parser and evaluator.

Experimental and work in progress.

## Usage

```python
from datetime import datetime
from cronsim import CronSim

it = CronSim("0 0 * 2 MON#5", datetime.now())
for x in range(0, 10):
    print(next(it))
```

Outputs:

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

## Supported Cron Expression Features

CronSim aims to match [Debian's cron implementation](https://salsa.debian.org/debian/cron/-/tree/master/debian)
(which itself is based on Paul Vixie's cron, with modifications). If CronSim evaluates
an expression differently from Debian's cron, that's a bug.

CronSim is open to adding support for non-standard syntax features, as long as
they don't conflict or interfere with the standard syntax.

## Cron Expression Feature Matrix

| Feature                  | Debian | croniter | cronsim |
| ------------------------ | :----: | :------: | :-----: |
| Seconds in the 6th field | No     | Yes      | Yes     |
| Special character "L"    | No     | Yes      | Yes     |
| N-th weekday of month    | Yes    | Yes      | Yes     |


**Seconds in the 6th field**: an optional sixth field specifying seconds. Supports
same syntax features as the minutes field.

Example: `* * * * * */15` (every 15 seconds).

**Special character "L"**: can be used in the day-of-month field and means
"the last day of the month".

Example: `0 0 L * *` (at the midnight of the last day of every month).

**N-th weekday of month**: support for "{weekday}#{nth}" syntax.
For example, "MON#1" means "first Monday of the month", "MON#2" means "second Monday
of the month".

Example: `0 0 * * MON#1` (at midnight of the first monday of every month).