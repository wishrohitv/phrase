import json
import uuid
from logging import getLogger
from typing import Annotated

import redis.asyncio as aioredis
from celery import chain
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from redis_fastapi import CacheBackendDep, cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.pydantic_schema import PhraseOrSentence
from database import get_db

# from middlewares.auth_middleware import auth_middleware
from models import DiscoverType, Episode, FeatureType, Movie, Title, Translation, Users  # noqa: F401
from services.process_subtitles import OPENSUBTITLE, SUBDL
from settings import settings
from tasks.tasks import (
    download_subtitle_file,
    fetch_subtitle_detail,
    process_subtile_file,
)
from utils.success import SuccessSchema

from .pydantic_schema import (
    DiscoverReponseSchema,
    SearchQuerySchema,
    SearchResponseSchema,
    SubtileFileSchema,
    TitleType,
    TranslationsResponseSchema,
)

title = APIRouter(prefix="/title", tags=["Title"])

subtitle_service = (OPENSUBTITLE(), SUBDL())

logger = getLogger(__name__)

async_redis = aioredis.from_url(f"{settings.REDIS_URL}/2", decode_responses=True)


@title.get(
    "/discover",
    dependencies=[Depends(cache(ttl=60 * 60 * 24 * 3, eviction_group="discover"))],
    response_model=SuccessSchema[list[DiscoverReponseSchema]],
    status_code=200,
)
async def discover_content(
    discover_type: DiscoverType = DiscoverType.POPULAR,
    feature_type: FeatureType = FeatureType.MOVIE,
    language_code: str = "all",
):
    res = await subtitle_service[0].discover(
        discover_type=discover_type,
        feature_type=feature_type,
        language_code=language_code,
    )

    res_model: list[DiscoverReponseSchema] = []

    for obj in res["data"]:
        try:
            res_model.append(DiscoverReponseSchema.model_validate(obj))
        except ValidationError:
            logger.exception("DiscoverReponseSchema validation error")
            logger.error("Invalid object: %s", json.dumps(obj))
    return SuccessSchema(data=res_model)


@title.get(
    "/search",
    dependencies=[Depends(cache(ttl=60 * 60 * 24 * 3, eviction_group="search"))],
    response_model=SuccessSchema[list[SearchResponseSchema]],
    status_code=200,
)
async def search_content(
    query: Annotated[SearchQuerySchema, Query()],
):

    res: dict = await subtitle_service[0].search(query.model_dump())
    res_model: [SearchResponseSchema] = []
    for obj in res["data"]:
        try:
            res_model.append(SearchResponseSchema.model_validate(obj))
        except ValidationError:
            logger.exception("SearchResponseSchema validation error")
            logger.error("Invalid object: %s", obj)
    return SuccessSchema(data=res_model)


@title.get(
    "/{imdb_id}",
    # response_model=SuccessSchema[list[TranslationsResponseSchema]],
    status_code=200,
)
async def get_translations(
    imdb_id: str,
    language: str,
    redis: CacheBackendDep,
    dependencies=[Depends(cache(ttl=60 * 60 * 24 * 3, eviction_group="translation"))],  # noqa: B006, B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):

    # Data storing workflow
    # if imdb is null then dont store that data
    # If feature_type is movie then store in movie table
    # if feature_type is Episode then store in series

    # 1. Check Movie or Episode table
    unique_id = await db.scalar(
        select(Movie.unique_id).filter(Movie.imdb_id == imdb_id)
    )
    if not unique_id:
        unique_id = await db.scalar(
            select(Episode.unique_id).filter(Episode.imdb_id == imdb_id)
        )

    # 2. Check if translations for this language already exist
    if unique_id:
        translations = (
            await db.scalars(
                select(Translation).filter(
                    Translation.content_uid == unique_id,
                    Translation.language == language,
                )
            )
        ).all()

        if translations:
            return SuccessSchema(
                data=[
                    TranslationsResponseSchema.model_validate(t) for t in translations
                ]
            )
    # Prevent duplicate jobs if two users request the same movie/language simultaneously
    lock_key = f"active_job:{imdb_id}:{language}"
    existing_job_id = await async_redis.get(lock_key)
    if existing_job_id:
        return JSONResponse(
            status_code=202,
            content={"status": "processing", "job_id": existing_job_id},
        )

    # Trigger the Celery pipeline
    job_id = str(uuid.uuid4())
    await async_redis.set(lock_key, job_id, ex=600)  # Lock for 10 mins

    initial_state = json.dumps(
        {
            "job_id": job_id,
            "step": "queued",
            "percent": 0,
            "message": "Queued for processing...",
        }
    )
    await async_redis.set(f"progress_state:{job_id}", initial_state, ex=3600)

    workflow = chain(
        fetch_subtitle_detail.s(job_id, imdb_id, language),
        download_subtitle_file.s(),
        process_subtile_file.s(),
    )
    workflow.apply_async()

    return JSONResponse(
        status_code=202,
        content={"status": "processing", "job_id": job_id},
    )


@title.get("/progress/{job_id}")
async def stream_translation_progress(job_id: str):

    async def event_generator():
        pubsub = async_redis.pubsub()
        await pubsub.subscribe(f"progress_channel:{job_id}")

        try:
            cached = await async_redis.get(f"progress_state:{job_id}")
            if cached:
                yield f"data: {cached}\n\n"
                parsed = json.loads(cached)
                if parsed.get("percent") in (100, -1):
                    return

            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    yield f"data: {data}\n\n"
                    parsed = json.loads(data)
                    if parsed.get("percent") in (100, -1):
                        break
        finally:
            await pubsub.unsubscribe(f"progress_channel:{job_id}")
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )
