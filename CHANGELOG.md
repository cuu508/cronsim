# Changelog
All notable changes to this project will be documented in this file.

# Unreleased
- Make validation error messages similar to Debian cron error messages

# 2.1 - 2022-04-30
- Add support for "L" in the day-of-week field
- Fix crash when "¹" passed in the input

# 2.0 - 2021-11-15
- Rewrite to use zoneinfo (or backports.zoneinfo) instead of pytz
- Add minimal type hints
- Make CronSimError importable from the top level

## 1.0 - 2021-10-15

- Initial release