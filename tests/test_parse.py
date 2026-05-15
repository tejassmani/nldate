from datetime import date
import pytest
from nldate import parse

TODAY = date(2025, 3, 15)  # Saturday


def p(s: str) -> date:
    return parse(s, today=TODAY)


# Keywords
def test_today() -> None:
    assert p("today") == date(2025, 3, 15)


def test_yesterday() -> None:
    assert p("yesterday") == date(2025, 3, 14)


def test_tomorrow() -> None:
    assert p("tomorrow") == date(2025, 3, 16)


def test_now() -> None:
    assert p("now") == date(2025, 3, 15)


# Weekdays
def test_next_monday() -> None:
    assert p("next Monday") == date(2025, 3, 17)


def test_last_monday() -> None:
    assert p("last Monday") == date(2025, 3, 10)


def test_this_wednesday() -> None:
    assert p("this Wednesday") == date(2025, 3, 19)


def test_bare_tuesday() -> None:
    assert p("Tuesday") == date(2025, 3, 18)


def test_last_sunday() -> None:
    assert p("last Sunday") == date(2025, 3, 9)


# ISO and numeric
def test_iso() -> None:
    assert p("2025-12-01") == date(2025, 12, 1)


def test_slash() -> None:
    assert p("12/01/2025") == date(2025, 12, 1)


def test_slash_two_digit_year() -> None:
    assert p("6/15/26") == date(2026, 6, 15)


# Absolute dates
def test_month_day_year_ordinal() -> None:
    assert p("December 1st, 2025") == date(2025, 12, 1)


def test_day_month_year() -> None:
    assert p("1 January 2026") == date(2026, 1, 1)


def test_no_year_future() -> None:
    assert p("April 10") == date(2025, 4, 10)


def test_no_year_rolls_forward() -> None:
    assert p("February 1") == date(2026, 2, 1)


# Pure offsets
def test_in_3_days() -> None:
    assert p("in 3 days") == date(2025, 3, 18)


def test_2_weeks_ago() -> None:
    assert p("2 weeks ago") == date(2025, 3, 1)


def test_a_month_from_now() -> None:
    assert p("a month from now") == date(2025, 4, 15)


def test_1_year_from_now() -> None:
    assert p("1 year from now") == date(2026, 3, 15)


def test_three_days_from_now() -> None:
    assert p("three days from now") == date(2025, 3, 18)


# Offset + anchor
def test_days_before_absolute() -> None:
    assert p("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_year_and_months_after_yesterday() -> None:
    assert p("1 year and 2 months after yesterday") == date(2026, 5, 14)


def test_weeks_before_next_monday() -> None:
    assert p("2 weeks before next Monday") == date(2025, 3, 3)


def test_days_after_tomorrow() -> None:
    assert p("10 days after tomorrow") == date(2025, 3, 26)


def test_weeks_from_tomorrow() -> None:
    assert p("two weeks from tomorrow") == date(2025, 3, 30)


# Edge cases
def test_invalid_raises() -> None:
    with pytest.raises(ValueError):
        p("not a date at all")


def test_default_today() -> None:
    assert parse("today") == date.today()


def test_comma_in_date() -> None:
    assert p("January 1, 2026") == date(2026, 1, 1)


def test_case_insensitive() -> None:
    assert p("DECEMBER 25 2025") == date(2025, 12, 25)
