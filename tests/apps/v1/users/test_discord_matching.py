import pytest
from django.contrib.auth.models import Group

from nile_quran_community_api.apps.v1.users.models import User
from nile_quran_community_api.apps.v1.users.services import (
    match_discord_members,
    normalize_name,
)


def member(discord_id: str, *names: str) -> dict:
    return {"id": discord_id, "names": list(names)}


@pytest.fixture
def make_user(db):
    students = Group.objects.get(name="Student")

    def _make(username, first, last, discord_id="", is_active=True):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpass",
            first_name=first,
            last_name=last,
            discord_id=discord_id,
            is_active=is_active,
        )
        user.groups.add(students)
        return user

    return _make


class TestNormalizeName:
    def test_folds_alef_variants(self):
        assert normalize_name("أحمد") == normalize_name("احمد")

    def test_strips_diacritics_and_tatweel(self):
        assert normalize_name("مُحَمَّد") == normalize_name("محمــد")

    def test_collapses_surrounding_whitespace(self):
        assert normalize_name("  محمد   علي ") == "محمد علي"

    def test_folds_taa_marbuta_and_alef_maqsura(self):
        assert normalize_name("عائشة") == normalize_name("عائشه")
        assert normalize_name("يحيى") == normalize_name("يحيي")

    def test_latin_names_fold_case(self):
        assert normalize_name("Ahmed Ali") == normalize_name("ahmed ali")


@pytest.mark.django_db
class TestMatchDiscordMembers:
    def test_links_a_unique_name_match(self, make_user):
        user = make_user("ahmed", "أحمد", "علي")

        matches = match_discord_members([member("111", "احمد علي")])

        assert matches.linked == {user.pk: "111"}
        assert matches.unmatched == matches.ambiguous == []

    def test_matches_against_nickname_global_name_or_username(self, make_user):
        user = make_user("ahmed", "أحمد", "علي")

        matches = match_discord_members([member("111", "Ahmoody", "أحمد علي")])

        assert matches.linked == {user.pk: "111"}

    def test_reports_a_user_with_no_matching_member(self, make_user):
        user = make_user("ahmed", "أحمد", "علي")

        matches = match_discord_members([member("111", "شخص آخر")])

        assert matches.linked == {}
        assert matches.unmatched == [user]

    def test_two_users_sharing_a_name_are_left_for_a_human(self, make_user):
        first = make_user("ahmed1", "أحمد", "علي")
        second = make_user("ahmed2", "أحمد", "علي")

        matches = match_discord_members([member("111", "أحمد علي")])

        assert matches.linked == {}
        assert {u.pk for u in matches.ambiguous} == {first.pk, second.pk}

    def test_two_members_sharing_a_name_are_left_for_a_human(self, make_user):
        user = make_user("ahmed", "أحمد", "علي")

        matches = match_discord_members(
            [member("111", "أحمد علي"), member("222", "احمد علي")]
        )

        assert matches.linked == {}
        assert matches.ambiguous == [user]

    def test_one_account_is_never_claimed_by_two_users(self, make_user):
        """A member whose nickname and username name different people links to neither."""
        first = make_user("ahmed", "أحمد", "علي")
        second = make_user("omar", "عمر", "حسن")

        matches = match_discord_members([member("111", "أحمد علي", "عمر حسن")])

        assert matches.linked == {}
        assert {u.pk for u in matches.ambiguous} == {first.pk, second.pk}

    def test_users_who_already_have_an_id_are_left_alone(self, make_user):
        make_user("ahmed", "أحمد", "علي", discord_id="999")

        matches = match_discord_members([member("111", "أحمد علي")])

        assert matches.linked == {}
        assert matches.unmatched == matches.ambiguous == []

    def test_inactive_users_are_skipped(self, make_user):
        make_user("ahmed", "أحمد", "علي", is_active=False)

        matches = match_discord_members([member("111", "أحمد علي")])

        assert matches.linked == {}

    def test_users_without_a_name_are_skipped(self, make_user):
        make_user("nameless", "", "")

        matches = match_discord_members([member("111", "")])

        assert matches.linked == {}
        assert matches.unmatched == matches.ambiguous == []
