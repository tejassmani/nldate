from __future__ import annotations

import re
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize(s: str) -> str:
    """Lowercase, remove commas, strip extra whitespace."""
    s = s.replace(",", " ").replace(".", " ")
    s = re.sub(r"\bthe day\b", "1 day", s, flags=re.I)
    return re.sub(r"\s+", " ", s.lower().strip())


# ---------------------------------------------------------------------------
# Strategy 1 – keyword anchors
# ---------------------------------------------------------------------------

_KEYWORD_MAP: dict[str, int] = {
    "today": 0,
    "tonight": 0,
    "now": 0,
    "yesterday": -1,
    "tomorrow": 1,
    "tmrw": 1,
    "tmr": 1,
}

WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

_WEEKDAY_RE = re.compile(
    r"^(next|last|this|on|coming)?\s*(" + "|".join(WEEKDAYS) + r")$", re.I
)

MONTHS: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_ORD_RE = re.compile(r"(\d+)(?:st|nd|rd|th)", re.I)

NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "a": 1,
    "an": 1,
}

UNIT_DAYS: dict[str, int] = {
    "day": 1,
    "days": 1,
    "week": 7,
    "weeks": 7,
    "fortnight": 14,
    "fortnights": 14,
}

_FROM_NOW_RE = re.compile(r"\bfrom\s+(now|today|tonight)\b", re.I)
_OFFSET_UNIT_RE = re.compile(
    r"(\w+)\s+(day|days|week|weeks|month|months|year|years|fortnight|fortnights)"
)


def _strip_ordinal(s: str) -> str:
    return _ORD_RE.sub(r"\1", s)


def _try_keyword(s: str, today: date) -> date | None:
    key = _normalize(s)
    if key in _KEYWORD_MAP:
        return today + timedelta(days=_KEYWORD_MAP[key])
    return None


def _next_weekday(anchor: date, wd: int) -> date:
    days_ahead = wd - anchor.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return anchor + timedelta(days=days_ahead)


def _last_weekday(anchor: date, wd: int) -> date:
    days_behind = anchor.weekday() - wd
    if days_behind <= 0:
        days_behind += 7
    return anchor - timedelta(days=days_behind)


def _this_weekday(anchor: date, wd: int) -> date:
    days_ahead = wd - anchor.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return anchor + timedelta(days=days_ahead)


def _try_weekday(s: str, today: date) -> date | None:
    m = _WEEKDAY_RE.match(_normalize(s))
    if not m:
        return None
    modifier = (m.group(1) or "").lower()
    wd = WEEKDAYS[m.group(2).lower()]
    if modifier == "last":
        return _last_weekday(today, wd)
    if modifier in ("next", "coming"):
        return _next_weekday(today, wd)
    return _this_weekday(today, wd)


def _try_iso(s: str, today: date) -> date | None:  # noqa: ARG001
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s.strip())
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def _try_numeric_slash(s: str, today: date) -> date | None:  # noqa: ARG001
    s = s.strip()
    # YYYY/MM/DD
    m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # MM/DD/YYYY or MM/DD/YY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        return date(year, month, day)
    return None


def _try_absolute(s: str, today: date) -> date | None:
    s2 = _normalize(_strip_ordinal(s))
    tokens = s2.split()

    while tokens and tokens[0] in ("on", "the"):
        tokens.pop(0)

    # Must contain a month name
    if not any(t in MONTHS for t in tokens):
        return None

    month: int | None = None
    day: int | None = None
    year: int | None = None

    for tok in tokens:
        if tok in MONTHS:
            month = MONTHS[tok]
        elif tok.isdigit():
            val = int(tok)
            if val > 31:
                year = val
            elif month is None:
                day = val
            elif day is None:
                day = val
            else:
                year = val

    if month is None or day is None:
        return None

    if year is None:
        candidate = date(today.year, month, day)
        if candidate < today:
            candidate = date(today.year + 1, month, day)
        return candidate

    return date(year, month, day)


def _parse_number(token: str) -> int | None:
    token = token.strip()
    if token.isdigit():
        return int(token)
    return NUMBER_WORDS.get(token)


def _add_months(d: date, months: int) -> date:
    import calendar

    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def _extract_offsets(s: str) -> list[tuple[int, str]] | None:
    offsets: list[tuple[int, str]] = []
    for m in _OFFSET_UNIT_RE.finditer(s):
        qty = _parse_number(m.group(1))
        if qty is None:
            return None
        offsets.append((qty, m.group(2).lower()))
    return offsets if offsets else None


def _apply_offsets(
    anchor: date, offsets: list[tuple[int, str]], direction: int
) -> date:
    result = anchor
    for qty, unit in offsets:
        signed = qty * direction
        if unit in ("month", "months"):
            result = _add_months(result, signed)
        elif unit in ("year", "years"):
            result = _add_years(result, signed)
        else:
            result += timedelta(days=UNIT_DAYS[unit] * signed)
    return result


def _try_pure_offset(s: str, today: date) -> date | None:
    norm = _normalize(_strip_ordinal(s))
    words = norm.split()

    direction: int | None = None
    if words and words[0] == "in":
        direction = 1
    elif words and words[-1] == "ago":
        direction = -1
    elif "hence" in words:
        direction = 1
    elif _FROM_NOW_RE.search(norm):
        direction = 1
    else:
        return None

    offsets = _extract_offsets(norm)
    if not offsets:
        return None

    return _apply_offsets(today, offsets, direction)


_SPLIT_FUTURE = re.compile(r"\bafter\b|\bfollowing\b", re.I)
_SPLIT_PAST = re.compile(r"\bbefore\b|\bprior to\b", re.I)
_SPLIT_FROM = re.compile(r"\bfrom\b", re.I)


def _try_offset_anchor(s: str, today: date) -> date | None:
    norm = _normalize(_strip_ordinal(s))

    for pattern, direction in (
        (_SPLIT_PAST, -1),
        (_SPLIT_FUTURE, 1),
        (_SPLIT_FROM, 1),
    ):
        m = pattern.search(norm)
        if not m:
            continue

        offset_part = norm[: m.start()].strip()
        anchor_part = norm[m.end() :].strip()

        # skip if anchor is "now/today" — that's _try_pure_offset's job
        if anchor_part in ("now", "today", "tonight"):
            continue

        offsets = _extract_offsets(offset_part)
        if not offsets:
            continue

        anchor: date | None = None
        for strategy in (
            _try_keyword,
            _try_weekday,
            _try_iso,
            _try_numeric_slash,
            _try_absolute,
        ):
            anchor = strategy(anchor_part, today)
            if anchor is not None:
                break

        if anchor is None:
            continue

        return _apply_offsets(anchor, offsets, direction)

    return None


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------


def parse(s: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()

    s = s.strip()

    for strategy in (
        _try_offset_anchor,
        _try_keyword,
        _try_weekday,
        _try_iso,
        _try_numeric_slash,
        _try_absolute,
        _try_pure_offset,
    ):
        result = strategy(s, today)
        if result is not None:
            return result

    raise ValueError(f"Could not parse date: {s!r}")
