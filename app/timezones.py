"""Central timestamp helpers standardising all SwapLah times to Singapore time.

Strategy
--------
* New records are stored as naive UTC strings with microseconds
  (``YYYY-MM-DD HH:MM:SS.ffffff``). Legacy second-precision rows are still
  parsed correctly.
* Stored values are always interpreted as UTC.
* Conversion to ``Asia/Singapore`` (UTC+08:00) happens only when serialising to
  an API response or rendering a template, never in the database.
"""

from datetime import datetime, timedelta, timezone

try:  # Prefer the real IANA zone; fall back to a fixed offset when tzdata is absent.
    from zoneinfo import ZoneInfo

    SINGAPORE_TZ = ZoneInfo("Asia/Singapore")
except Exception:  # pragma: no cover - exercised only without tzdata installed
    # Singapore has observed a constant UTC+08:00 with no DST since 1982, so a
    # fixed offset is exact for every timestamp this application handles.
    SINGAPORE_TZ = timezone(timedelta(hours=8), "Asia/Singapore")

DB_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DB_TIMESTAMP_FORMAT_MICRO = "%Y-%m-%d %H:%M:%S.%f"
DISPLAY_DATETIME_FORMAT = "%d %b %Y"
DISPLAY_TIME_FORMAT = "%M %p"


def utc_now():
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def format_db_timestamp(moment=None):
    """Return a naive UTC timestamp string with microseconds for storage."""
    moment = moment or utc_now()
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc)
    return moment.strftime(DB_TIMESTAMP_FORMAT_MICRO)


def _parse_naive(text):
    """Parse a naive database timestamp string, or return None."""
    for fmt in (DB_TIMESTAMP_FORMAT, DB_TIMESTAMP_FORMAT_MICRO):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_db_timestamp(value):
    """Return an aware UTC datetime for a stored value, or None when unparseable."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            parsed = _parse_naive(text)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def to_singapore_time(value):
    """Return a timezone-aware ``Asia/Singapore`` datetime, or None."""
    parsed = parse_db_timestamp(value)
    if parsed is None:
        return None
    return parsed.astimezone(SINGAPORE_TZ)


def to_singapore_iso(value):
    """Return an ISO-8601 Singapore-time string (``...+08:00``), or None."""
    moment = to_singapore_time(value)
    return moment.isoformat() if moment is not None else None


def format_singapore_datetime(value):
    """Return a readable Singapore datetime, e.g. ``24 Jul 2026, 12:46 PM``."""
    moment = to_singapore_time(value)
    if moment is None:
        return ""
    hour12 = moment.strftime("%I").lstrip("0") or "12"
    return f"{moment.strftime(DISPLAY_DATETIME_FORMAT)}, {hour12}:{moment.strftime(DISPLAY_TIME_FORMAT)}"


def format_singapore_date(value):
    """Return a readable Singapore date, e.g. ``24 Jul 2026``."""
    moment = to_singapore_time(value)
    if moment is None:
        return ""
    return moment.strftime(DISPLAY_DATETIME_FORMAT)
