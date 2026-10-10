import datetime as dt

from nile_quran_community_api.apps.v1.announcements import hijri

# Umm al-Qura: Sha'ban 1447 runs 2026-01-20 .. 2026-02-17, Ramadan 1447 starts 2026-02-18.
RAMADAN_START = dt.date(2026, 2, 18)


class TestHijri:
    def test_previous_month_is_the_one_that_just_ended(self):
        assert hijri.previous_month(RAMADAN_START) == (1447, 8)

    def test_previous_month_wraps_the_year(self):
        muharram_start = dt.date(2026, 6, 16)
        assert hijri.to_hijri(muharram_start).month == 1
        assert hijri.previous_month(muharram_start) == (1447, 12)

    def test_month_window_is_half_open_and_local(self):
        start, end = hijri.month_window(1447, 8)

        assert start.date() == dt.date(2026, 1, 20)
        assert end.date() == dt.date(2026, 2, 18)
        assert start.tzinfo is not None
        # Cairo, not UTC: the month turns over at local midnight.
        assert start.utcoffset() != dt.timedelta(0)

    def test_month_name_is_arabic(self):
        assert hijri.month_name(1447, 9) == "رمضان"
