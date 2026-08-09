from enum import Enum

from pydantic import BaseModel, Field, model_validator, model_serializer


class QueryMatchType(str, Enum):
    START = "start"
    WORD = "word"
    EXACT = "exact"


class EntityType(str, Enum):
    MOVIE = "movie"
    EPISODE = "episode"
    TVSHOW = "tvshow"


class OpenSubtitleMovieIdSchema(BaseModel):
    os_id: int


class SearchValueSchema(BaseModel):
    feature_id: int | None = Field(default=None)
    full_search: bool = Field(default=False)
    imdb_id: str | None = Field(default=None)
    tmdb_id: str | None = Field(
        default=None
    )  # TheMovieDB ID - combine with type to avoid errors
    query: str | None = Field(default=None, min_length=3)
    query_match: QueryMatchType = Field(default=QueryMatchType.START)
    type: EntityType = Field(
        default=None
    )  # empty to list all or movie, tvshow or episode.
    year: int = Field(default=None)

    # Validator to check none value if all value is none
    @model_validator(mode="after")
    def check_none(self) -> SearchValueSchema:
        if not any(
            [
                self.feature_id,
                self.imdb_id,
                self.tmdb_id,
                self.query,
            ]
        ):
            raise ValueError(
                "You must provide either 'feature_id' or 'imdb_id', 'tmdb_id', 'query' "
            )
        return self

    @model_serializer
    def serialize_model(self) -> dict:
        _query = {}

        if self.feature_id:
            _query["feature_id"] = self.feature_id
            return _query
        if self.imdb_id:
            _query["imdb_id"] = self.imdb_id
            return _query
        if self.tmdb_id:
            _query["tmdb_id"] = self.tmdb_id
            return _query
        if self.query:
            _query["query"] = self.query
            _query["query_match"] = self.query_match.value
            if self.type:
                _query["type"] = self.type.value
            if self.year:
                _query["year"] = self.year

            return _query
