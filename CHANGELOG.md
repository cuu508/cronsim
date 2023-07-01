# Changelog
All notable changes to this project will be documented in this file.

## 2.5 - 2023-07-01
- Add support for "LW" in the day-of-month field (#1)

## 2.4.1 - 2023-04-27
- [explain] Fix month-day formatting ("January 1st" -> "January 1")
- [explain] Change ordinal formatting to use words instead of numerals for 1-9
- [explain] Fix digital time formatting (use HH:MM instead H:MM)

## 2.4 - 2023-04-26
- Add explain() method which describes the expression in human language
- Remove python 3.7 support

## 2.3 - 2022-09-28
- Add type hints
- Remove python 3.6 support (EOL)

## 2.2 - 2022-09-22
- Make validation error messages similar to Debian cron error messages
- Change day-of-month and day-of-week handling to mimic Debian cron more closely

## 2.1 - 2022-04-30
- Add support for "L" in the day-of-week field
- Fix crash when "¹" passed in the input

## 2.0 - 2021-11-15
- Rewrite to use zoneinfo (or backports.zoneinfo) instead of pytz
- Add minimal type hints
- Make CronSimError importable from the top level

## 1.0 - 2021-10-15

- Initial release