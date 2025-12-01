from typing import Annotated

import httpx
from fastapi import Depends

from src.api.dependencies import CurrentUserDep
from src.config import settings
from src.modules.clubs.schemas import Club, ClubType, LinkSchema, LinkType

CLUBS_ENDPOINT = settings.clubs_base_url + "/clubs/"


async def get_user_clubs(
    current_user: CurrentUserDep,
) -> list[Club]:
    async with httpx.AsyncClient() as client:
        response = await client.get(CLUBS_ENDPOINT)
        response.raise_for_status()
        clubs_data = response.json()

    user_id = current_user.innohassle_id
    result = []
    for club in clubs_data:
        if club.get("leader_innohassle_id") != user_id:
            continue
        links = [
            LinkSchema(
                type=LinkType(link["type"]),
                link=link["link"],
                label=link.get("label"),
            )
            for link in club.get("links", [])
        ]
        result.append(
            Club(
                is_active=club["is_active"],
                slug=club["slug"],
                title=club["title"],
                short_description=club["short_description"],
                description=club["description"],
                logo_file_id=club.get("logo_file_id"),
                type=ClubType(club["type"]),
                leader_innohassle_id=club.get("leader_innohassle_id"),
                links=links,
                sport_id=club.get("sport_id"),
            )
        )

    return result


UserClubsDep = Annotated[list[Club], Depends(get_user_clubs)]
"""
Dependency for getting clubs where current user is a leader.
"""
