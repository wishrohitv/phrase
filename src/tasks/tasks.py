import asyncio
import json
import os
import uuid

from celery import Celery
from redis import Redis

from common.db_query import PhraseListAdapter, save_subtile_and_parsed_data
from services.open_router import llm_process_subtitle_data
from services.process_subtitles import OPENSUBTITLE, SUBDL
from settings import settings
from utils.text_splitter import process_large_file

celery_app = Celery(
    "worker",
    broker=f"{settings.REDIS_URL}/0",
    backend=f"{settings.REDIS_URL}/1",
)

redis_client = Redis.from_url(url=f"{settings.REDIS_URL}/2", decode_responses=True)

subtitle_service = (OPENSUBTITLE(), SUBDL())

# Hardcoded to opensubtile
SUBTITLE_SERVICE = subtitle_service[0]


def publish_progress(
    job_id: str, step: str, percent: int, message: str, extra: dict | None = None
) -> None:
    payload = {
        "job_id": job_id,
        "step": step,
        "percent": percent,
        "message": message,
        **(extra or {}),
    }

    serialized = json.dumps(payload)

    redis_client.set(f"progress_state:{job_id}", serialized, ex=3600)
    redis_client.publish(f"progress_channel:{job_id}", serialized)


@celery_app.task(name="fetch_subtile_detail")
def fetch_subtitle_detail(job_id: uuid.UUID, imdb_id: str, language: str):
    try:
        publish_progress(job_id, "search", 10, "Searching for subtitle file...")
        # Run async service inside the sync Celery worker
        res = asyncio.run(
            SUBTITLE_SERVICE.search_subtitle(imdb_id=imdb_id, language_code=language)
        )

        result = res.get("data", [])

        if not result:
            raise ValueError(f"Subtitle file not found for language: {language}")

        subtitle_data = result[0]

        # Publish the progress

        publish_progress(job_id, "search", 25, "Subtitle metadata found.")

        # Return JSON-serializable dict for the next task in the chain

        return {
            "job_id": job_id,
            "imdb_id": imdb_id,
            "language": language,
            "subtitle_data": subtitle_data,
        }

    except Exception as e:
        publish_progress(job_id, "error", -1, str(e))
        raise


@celery_app.task(name="download_subtitle_file")
def download_subtitle_file(payload: dict) -> dict:
    job_id = payload["job_id"]

    try:
        publish_progress(job_id, "download", 35, "Downloading subtitle file...")

        file_id = payload["subtitle_data"]["attributes"]["files"][0]["file_id"]
        imdb_id = payload["imdb_id"]

        file_path = asyncio.run(SUBTITLE_SERVICE.download(file_id, imdb_id))

        if not os.path.exists(file_path):
            raise ValueError("Failed to download subtitle file")
        publish_progress(job_id, "download", 50, "Subtitle file downloaded...")

        payload["file_path"] = file_path
        return payload
    except Exception as e:
        publish_progress(job_id, "error", -1, str(e))
        raise


@celery_app.task(name="process_subtile_file")
def process_subtile_file(payload: dict) -> dict:
    job_id = payload["job_id"]
    try:
        chunks = list(
            process_large_file(payload["file_path"], chunk_size=40000, overlap=50)
        )
        total_chunks = len(chunks)
        llm_data = []

        # Process chunks and emit granular progress from 50% -> 90%
        for idx, chunk in enumerate(chunks, start=1):
            current_pct = 50 + int((idx / total_chunks) * 40)
            publish_progress(
                job_id,
                "llm_processing",
                current_pct,
                f"Translating chunk {idx} of {total_chunks}...",
            )

            context = {
                "subtitle_filename": payload["subtitle_data"]["attributes"]["feature_details"][
                    "title"
                ],
                "learning_language": "English",
                "native_language": "Hindi",
                "subtitle_text": chunk,
            }
            raw_data = asyncio.run(llm_process_subtitle_data(context))
            llm_data.extend(json.loads(raw_data))

        # Save Title, Movie/Episode, and Translation records in a single DB transaction
        # Inside process_subtile_file task:
        validated_chunks: list[dict] = []

        for idx, chunk in enumerate(chunks, start=1):
            # ... publish progress ...
            raw_data = asyncio.run(llm_process_subtitle_data(context))

            # Validate immediately on each chunk so malformed LLM JSON fails fast
            parsed_items = PhraseListAdapter.validate_json(raw_data)
            validated_chunks.extend([item.model_dump() for item in parsed_items])

        publish_progress(job_id, "saving", 95, "Saving translations to database...")

        # Save everything atomically
        uid = asyncio.run(
            save_subtile_and_parsed_data(
                imdb_id=payload["imdb_id"],
                raw_subtitle_data=payload["subtitle_data"],
                raw_llm_data=validated_chunks,
            )
        )

        publish_progress(
            job_id,
            "completed",
            100,
            "Translations ready!",
            extra={"unique_id": str(uid)},
        )
        return {"status": "completed", "unique_id": str(uid)}
    except Exception as e:
        publish_progress(job_id, "error", -1, str(e))
        raise
