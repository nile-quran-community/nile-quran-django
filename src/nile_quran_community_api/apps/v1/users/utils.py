import dataclasses
import re
import unicodedata

from .models import User

# Harakat, tatweel and the like: present or absent depending on who typed the name.
_ARABIC_NOISE = re.compile(r"[ؐ-ًؚ-ٰٟـ]")
# Spelling variants that carry no distinction for matching purposes.
_ARABIC_VARIANTS = str.maketrans(
    {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}
)


@dataclasses.dataclass
class DiscordMatches:
    """The outcome of matching community members against a Discord server."""

    linked: dict[int, str] = dataclasses.field(default_factory=dict)
    unmatched: list[User] = dataclasses.field(default_factory=list)
    ambiguous: list[User] = dataclasses.field(default_factory=list)


def normalize_name(name: str) -> str:
    """Fold a name so that spelling variants of it compare equal."""

    folded = unicodedata.normalize("NFKC", name)
    folded = _ARABIC_NOISE.sub("", folded).translate(_ARABIC_VARIANTS)
    return " ".join(folded.split()).casefold()


def match_discord_members(members: list[dict]) -> DiscordMatches:
    """Pair users who have no Discord ID yet with the server members who share a name.

    Deliberately strict: a user is linked only when their name matches exactly one
    member and that member matches exactly one user. A wrong link would mention, and
    later message, the wrong person, so anything uncertain is reported rather than
    guessed at.
    """

    by_name: dict[str, set[str]] = {}
    for member in members:
        by_name.setdefault(normalize_name(member["name"]), set()).add(member["id"])

    candidates: dict[str, list[User]] = {}
    for user in User.objects.filter(is_active=True, discord_id=""):
        name = normalize_name(f"{user.first_name} {user.last_name}")
        if name:
            candidates.setdefault(name, []).append(user)

    matches = DiscordMatches()
    for name, found in candidates.items():
        discord_ids = by_name.get(name, set())
        if len(found) == 1 and len(discord_ids) == 1:
            matches.linked[found[0].pk] = next(iter(discord_ids))
        elif discord_ids:
            matches.ambiguous.extend(found)
        else:
            matches.unmatched.extend(found)

    return matches
