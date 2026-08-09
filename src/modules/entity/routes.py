from typing import Annotated

from fastapi import APIRouter, Depends, Query

from middlewares.auth_middleware import auth_middleware
from models.entity import Entity
from models.enums import DiscoverType
from models.translations import Translation
from services.fetch_subtitles import OPENSUBTITLE, SUBDL

from .pydantic_shcema import SearchValueSchema

entity = APIRouter(prefix="/entity")

subtitle_service = (OPENSUBTITLE(), SUBDL())

@entity.get("/discover")
async def discover_content(
    discover_type: DiscoverType = DiscoverType.MOST_DOWNLOADED,
    user: dict = Depends(auth_middleware),  # noqa: B008
):
    print(discover_type)
    return {}


# @entity.get("/search")
# async def search_content(
#     query : Annotated[SearchValueSchema, Query()],
#     user: dict = Depends(auth_middleware),  # noqa: B008
# ):
#     print(query.model_dump())
#     return search(query.model_dump())
@entity.get("/search")
async def search_content(
    q : str,
    user: dict = Depends(auth_middleware),  # noqa: B008
):
    return subtitle_service[1].search(query={"q": q})


@entity.get("/{entity_id}")
async def get_entity(entity_id: int):
    pass
