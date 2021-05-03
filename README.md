# CronSim

A toy cron expression evaluator.

Experimental and work in progress.

## Cron Expression Feature Matrix

| Feature                  | vixie | croniter | cronsim |
| ------------------------ | :---: | :------: | :-----: |
| Seconds in the 6th field | No    | Yes      | Yes     |
| Special character: L     | No    | Yes      | Yes     |
| N-th weekday of month    | Yes   | Yes      | Yes     |


**Seconds in the 6th field**: an optional sixth field specifying seconds. Supports
same syntax features as the minutes field.
Example: `* * * * * */15` (every 15 seconds).

**Special character: L**: can be used in the day-of-month field and means
"the last day of the month".
Example: `0 0 L * *` (at the midnight of the last day of every month).

**N-th weekday of month**: support for "{weekday}#{nth}" syntax.
For example, "1#1" means "first Monday of the month", "1#2" means "second Monday
of the month".
Example: `0 0 * * 1#1` (at midnight of the first monday of every month).