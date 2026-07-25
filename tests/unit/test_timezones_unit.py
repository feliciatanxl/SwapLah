"""Unit tests for the central Singapore-time helpers."""

from datetime import datetime, timezone

from app.timezones import (
    format_db_timestamp,
    format_singapore_date,
    format_singapore_datetime,
    parse_db_timestamp,
    to_singapore_iso,
    to_singapore_time,
    utc_now,
)


def test_known_utc_timestamp_converts_to_plus_eight():
    """A stored UTC value serialises to the same instant at +08:00."""
    assert to_singapore_iso("2026-07-24 04:46:00") == "2026-07-24T12:46:00+08:00"


def test_conversion_crosses_midnight_into_next_day():
    """A late-evening UTC value rolls over to the next calendar day in Singapore."""
    assert to_singapore_iso("2026-07-24 18:30:00") == "2026-07-25T02:30:00+08:00"
    assert format_singapore_date("2026-07-24 18:30:00") == "25 Jul 2026"


def test_format_singapore_datetime_is_readable():
    """The display format matches '24 Jul 2026, 12:46 PM'."""
    assert format_singapore_datetime("2026-07-24 04:46:00") == "24 Jul 2026, 12:46 PM"


def test_format_singapore_datetime_strips_leading_zero_hour():
    """Single-digit hours have no leading zero."""
    assert format_singapore_datetime("2026-07-24 05:05:00") == "24 Jul 2026, 1:05 PM"


def test_midnight_hour_shows_twelve():
    """Midnight Singapore time is shown as 12:00 AM, not 0:00."""
    # 2026-07-23 16:00 UTC -> 2026-07-24 00:00 SGT
    assert format_singapore_datetime("2026-07-23 16:00:00") == "24 Jul 2026, 12:00 AM"


def test_parse_db_timestamp_treats_naive_as_utc():
    """A naive stored value is interpreted as UTC."""
    parsed = parse_db_timestamp("2026-07-24 04:46:00")
    assert parsed == datetime(2026, 7, 24, 4, 46, tzinfo=timezone.utc)


def test_parse_db_timestamp_accepts_iso_with_offset():
    """An ISO string with an offset is normalised back to UTC."""
    parsed = parse_db_timestamp("2026-07-24T12:46:00+08:00")
    assert parsed == datetime(2026, 7, 24, 4, 46, tzinfo=timezone.utc)


def test_blank_and_none_values_are_handled():
    """Empty inputs yield None or empty strings rather than raising."""
    assert parse_db_timestamp(None) is None
    assert parse_db_timestamp("") is None
    assert to_singapore_time(None) is None
    assert to_singapore_iso(None) is None
    assert format_singapore_datetime(None) == ""
    assert format_singapore_date("") == ""


def test_format_db_timestamp_round_trips_utc_now():
    """format_db_timestamp stores an aware UTC value as a naive UTC string."""
    stored = format_db_timestamp(utc_now())
    assert len(stored) == 26
    assert parse_db_timestamp(stored).tzinfo == timezone.utc


def test_format_db_timestamp_converts_singapore_input_to_utc():
    """An aware Singapore datetime is stored as its UTC equivalent."""
    moment = to_singapore_time("2026-07-24 04:46:00")
    assert format_db_timestamp(moment) == "2026-07-24 04:46:00.000000"
