import hashlib
import re


def normalize_team_name(team_name: str) -> str:
    """Normalize team names for stable invite-code generation and matching."""
    if not team_name:
        return ""
    normalized = re.sub(r"\s+", " ", str(team_name).strip())
    return normalized


def make_team_invite_code(team_name: str, length: int = 8) -> str:
    """Create a deterministic, human-friendly invite code from team name."""
    normalized = normalize_team_name(team_name).lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()
    return digest[:length]


def find_team_by_invite_code(code: str, teams: dict) -> str | None:
    """Return a matching team name for an invite code, or None if no match."""
    cleaned = (code or "").strip().upper()
    if not cleaned:
        return None
    for team_name in teams.keys():
        if make_team_invite_code(team_name) == cleaned:
            return team_name
    return None