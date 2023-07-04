"""Functions to help with timestamp manipulation"""

from datetime import datetime

import pytz


def now() -> datetime:
    """Get the current time as a tz-aware dt."""

    return pytz.UTC.localize(datetime.utcnow())  # pylint: disable=no-value-for-parameter


def parse_db_timestamp(ts: str) -> datetime:
    """Parse a SQLite TIMESTAMP into a tz-aware dt."""

    # strip the ts data
    ts = ts.split("+")[0]

    # auto generated timestamps in the db are second precision
    # datetime objects have ms precision
    fstr = "%Y-%m-%d %H:%M:%S"
    if "." in ts:
        fstr += ".%f"

    return pytz.UTC.localize(datetime.strptime(ts, fstr))  # pylint: disable=no-value-for-parameter


def _convert_to_utc(dt: datetime) -> datetime:
    """Convert a tz-aware or -naive dt to a tz-aware UTC dt."""

    # check if tz naive
    if getattr(dt, "tzinfo") is None:
        # put the UTC tzinfo into the datetime
        dt = pytz.UTC.localize(dt)  # pylint: disable=no-value-for-parameter
    else:
        # have tzinfo, error if its not UTC since it should be and converting timezones sucks
        if dt.tzinfo != pytz.UTC:
            raise ValueError(f"datetime is not in UTC! {dt}")

    return dt


# pylint: disable-next=redefined-builtin
def repr(dt: datetime, as_utc=True) -> str:
    """
    Convert a datetime object to a string.
    Example return: "Aug 23, 2013 at 15:57:31 PDT"

    TODO: this logic is unreasonable since the convert private func requires naive or UTC. but idc

    If as_utc is True, the datetime is converted to UTC.
    If the datetime object is naive, it is assumed to be in UTC
    """

    if getattr(dt, "tzinfo") is None:
        # put the UTC tzinfo into the datetime
        dt = dt.replace(tzinfo=pytz.UTC)

    if as_utc:
        dt = _convert_to_utc(dt)

    return dt.strftime("%b %-d, %Y at %H:%M:%S %Z").strip()


def iso8601(dt: datetime) -> str:
    """
    Convert a datetime object to an ISO8601 timestamp string.

    If the dt is tz-naive, it's assumed to be UTC. If it's tz-aware
    and not UTC, it is converted to UTC.
    """

    dt = _convert_to_utc(dt)

    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
