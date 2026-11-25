import uuid

from pydantic import TypeAdapter
from sqlalchemy import select

from database import AsyncSessionLocal
from models import Episode, Movie, Title, Translation
from modules.title.pydantic_schema import SubtileFileSchema, TitleType

from .pydantic_schema import PhraseOrSentence

# Pre-compile a TypeAdapter for fast list validation
PhraseListAdapter = TypeAdapter(list[PhraseOrSentence])


async def save_subtile_and_parsed_data(
    imdb_id: str,
    raw_subtitle_data: dict,
    raw_llm_data: list[dict],
) -> uuid.UUID:
    # 1. Validate inputs with Pydantic before opening a DB connection
    subtitle_schema = SubtileFileSchema.model_validate(raw_subtitle_data)
    llm_data: list[PhraseOrSentence] = PhraseListAdapter.validate_python(raw_llm_data)

    async with AsyncSessionLocal() as db:
        try:
            uid = None

            # Check if Movie or Episode already exists (e.g., from another language)
            if subtitle_schema.feature_details.feature_type == TitleType.MOVIE:
                uid = await db.scalar(
                    select(Movie.unique_id).filter(Movie.imdb_id == imdb_id)
                )

                if not uid:
                    uid = uuid.uuid7()

                    title = Title(
                        imdb_id=imdb_id,
                        title=subtitle_schema.feature_details.title,
                        type=subtitle_schema.feature_details.feature_type,
                        img_url=subtitle_schema.related_links[0].img_url,
                        author_id=1,  # TODO: pass user_id if needed
                    )
                    db.add(title)
                    await db.flush()

                    movie = Movie(
                        title_id=title.id,
                        title=subtitle_schema.feature_details.title,
                        imdb_id=imdb_id,
                        unique_id=uid,
                    )
                    db.add(movie)
                    await db.flush()

            elif subtitle_schema.feature_details.feature_type == TitleType.EPISODE:
                uid = await db.scalar(
                    select(Episode.unique_id).filter(Episode.imdb_id == imdb_id)
                )

                if not uid:
                    uid = uuid.uuid7()
                    details = subtitle_schema.feature_details

                    # Reuse parent TV show Title if another episode already created it
                    title_id = await db.scalar(
                        select(Title.id).filter(Title.imdb_id == details.parent_imdb_id)
                    )
                    if not title_id:
                        title = Title(
                            imdb_id=details.parent_imdb_id,
                            title=details.parent_title,
                            type="tvshow",
                            img_url=subtitle_schema.related_links[0].img_url,
                            author_id=1,
                        )
                        db.add(title)
                        await db.flush()
                        title_id = title.id

                    episode = Episode(
                        title_id=title_id,
                        title=details.title,
                        imdb_id=imdb_id,
                        parent_imdb=details.parent_imdb_id,
                        episode_number=details.episode_number,
                        season_number=details.season_number,
                        unique_id=uid,
                    )
                    db.add(episode)
                    await db.flush()

            else:
                raise ValueError(
                    f"Unsupported feature type: {subtitle_schema.feature_details.feature_type}"
                )

            # Insert all validated translations
            objs = [
                Translation(
                    content_uid=uid,
                    language=subtitle_schema.language,
                    **t.model_dump(exclude={"content_uid", "language"}),
                )
                for t in llm_data
            ]
            db.add_all(objs)

            # Single atomic commit for all inserts
            await db.commit()
            return uid

        except Exception as e:
            await db.rollback()
            raise ValueError(f"Failed to save subtitle and parsed data: {e}") from e
