from src.modules.clubs.schemas import Club
from src.storages.sql.models import Host, HostType


def is_leader_of_club(user_clubs: list[Club], hosts: list[Host]):
    club_ids = [host.name for host in hosts if host.host_type == HostType.CLUB]
    return any([club.id in club_ids for club in user_clubs])
