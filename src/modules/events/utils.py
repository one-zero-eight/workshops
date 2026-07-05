from src.modules.clubs.schemas import Club
from src.storages.sql.models import Host, HostType

HostLike = Host | dict


def is_leader_of_club(user_clubs: list[Club], hosts: list[HostLike] | None):
    hosts = hosts or []
    club_ids = [
        h["name"] if isinstance(h, dict) else h.name
        for h in hosts
        if (h.get("host_type") if isinstance(h, dict) else h.host_type) == HostType.CLUB
    ]
    return any(club.id in club_ids for club in user_clubs)
