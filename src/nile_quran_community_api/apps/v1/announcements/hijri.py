"""Hijri month arithmetic for the monthly leaderboard.

Uses the Umm al-Qura calendar. That is deterministic and testable, but it can differ by
a day from a local moon sighting; the community accepts that trade.

Month boundaries are evaluated in ANNOUNCEMENTS_TIMEZONE rather than the project's UTC,
so a Hijri month turns over at local midnight.
"""

import datetime as dt
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone
from hijridate import Gregorian, Hijri


def _zone() -> ZoneInfo:
    return ZoneInfo(settings.ANNOUNCEMENTS_TIMEZONE)


def today() -> dt.date:
    """The current date as the community experiences it."""

    return timezone.now().astimezone(_zone()).date()


def to_hijri(date: dt.date) -> Hijri:
    return Gregorian(date.year, date.month, date.day).to_hijri()


def previous_month(date: dt.date) -> tuple[int, int]:
    """The (year, month) of the Hijri month before the one `date` falls in."""

    hijri = to_hijri(date)
    if hijri.month == 1:
        return hijri.year - 1, 12
    return hijri.year, hijri.month - 1


def month_name(year: int, month: int) -> str:
    return Hijri(year, month, 1).month_name("ar")


def month_window(year: int, month: int) -> tuple[dt.datetime, dt.datetime]:
    """The half-open [start, end) range of a Hijri month, as aware datetimes."""

    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    zone = _zone()
    return (
        dt.datetime(*Hijri(year, month, 1).to_gregorian().datetuple(), tzinfo=zone),
        dt.datetime(
            *Hijri(next_year, next_month, 1).to_gregorian().datetuple(), tzinfo=zone
        ),
    )
