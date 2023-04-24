# Changelog
All notable changes to this project will be documented in this file.

## 2.4-dev - Unreleased
- Add explain module (WIP) which describes the expression in human language
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