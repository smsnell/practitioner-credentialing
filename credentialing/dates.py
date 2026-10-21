"""Inclusive office calendar rules, using explicit ISO dates and batch clocks."""

from datetime import date, timedelta


class UnsupportedBoundary(ValueError):
    """A required anniversary falls on an unresolved leap-day boundary (Q10)."""


def _date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError(f"Expected YYYY-MM-DD date, got {value!r}")
    return parsed


def _anniversary(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError as exc:
        if value.month == 2 and value.day == 29:
            raise UnsupportedBoundary(
                f"Q10: no leap-day anniversary policy for {value.isoformat()} "
                f"with year offset {years}"
            ) from exc
        raise


def _interval(start: str, end: str) -> tuple[date, date]:
    first, last = _date(start), _date(end)
    if last < first:
        raise ValueError(f"Interval ends before it starts: {start} through {end}")
    return first, last


def inclusive_days(start: str, end: str) -> int:
    first, last = _interval(start, end)
    return (last - first).days + 1


def uncovered_intervals(
    school_end: str, intervals: list[tuple[str, str | None]], as_of: str
) -> list[dict]:
    """Return uncovered spans of at least 30 days after school through export.

    Coverage uses inclusive endpoints. Open entries run through the supplied
    export date. Entries outside the reporting horizon supply no coverage;
    declared endpoints are never changed or returned as invented evidence.
    """
    completed, exported = _date(school_end), _date(as_of)
    coverage = []
    for start, end in intervals:
        first = _date(start)
        last = exported if end is None else _date(end)
        # An open entry beginning after export has not begun at this clock.
        if end is not None and last < first:
            raise ValueError(f"Interval ends before it starts: {start} through {end}")
        coverage.append((first, last))

    cursor = completed
    gaps = []

    def record(first: date, last: date) -> None:
        days = (last - first).days + 1
        if days >= 30:
            gaps.append({"start": first.isoformat(), "end": last.isoformat(), "days": days})

    # Cursor is the last covered/processed day, avoiding overflow at date.max.
    for first, last in sorted(coverage):
        if first > exported or last <= cursor or last < first:
            continue
        if first > cursor and (first - cursor).days > 1:
            record(cursor + timedelta(days=1), first - timedelta(days=1))
        cursor = max(cursor, min(last, exported))
    if exported > cursor:
        record(cursor + timedelta(days=1), exported)
    return gaps


def first_received_window(first_received: str) -> str:
    """Five calendar years before the original application receipt (B14)."""
    return _anniversary(_date(first_received), -5).isoformat()


def overlaps_window(start: str, end: str | None, window_start: str, as_of: str) -> bool:
    first, lower, upper = _date(start), _date(window_start), _date(as_of)
    if lower > upper:
        raise ValueError("Window starts after export date")
    last = upper if end is None else _date(end)
    if end is not None and last < first:
        raise ValueError(f"Interval ends before it starts: {start} through {end}")
    return first <= upper and last >= lower


def request_deadline(sent: str) -> str:
    return (_date(sent) + timedelta(days=30)).isoformat()


def peer_followups(requested: str) -> list[str]:
    """The two reminder dates and additional-referee escalation date (B09)."""
    initial = _date(requested)
    return [(initial + timedelta(days=days)).isoformat() for days in (21, 42, 64)]


def peer_current(signature: str, at: str) -> bool:
    signed, presented = _date(signature), _date(at)
    if presented < signed:
        return False
    return presented <= _anniversary(signed, 2)


def worked_recently(last_worked_or_None: str | None, signature: str) -> bool:
    signed = _date(signature)
    if last_worked_or_None in (None, ""):
        return True
    last = _date(last_worked_or_None)
    if last > signed:
        return False
    return signed <= _anniversary(last, 2)


def appointment_cycle_end(effective: str) -> str:
    return (_anniversary(_date(effective), 1) - timedelta(days=1)).isoformat()
