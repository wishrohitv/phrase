import uuid
from enum import Enum

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
    model_validator,
)

from common.pydantic_schema import PhraseOrSentence


class QueryMatchType(str, Enum):
    START = "start"
    WORD = "word"
    EXACT = "exact"


class TitleType(str, Enum):
    MOVIE = "movie"
    EPISODE = "episode"
    TVSHOW = "tvshow"


class OpenSubtitleMovieIdSchema(BaseModel):
    os_id: int


class SearchQuerySchema(BaseModel):
    feature_id: int | None = Field(default=None)
    full_search: bool = Field(default=False)
    imdb_id: str | None = Field(default=None)
    tmdb_id: str | None = Field(
        default=None
    )  # TheMovieDB ID - combine with type to avoid errors
    query: str | None = Field(default=None, min_length=3)
    query_match: QueryMatchType = Field(default=QueryMatchType.START)
    type: TitleType = Field(
        default=None
    )  # empty to list all or movie, tvshow or episode.
    year: int = Field(default=None)

    # Validator to check none value if all value is none
    @model_validator(mode="after")
    def check_none(self) -> SearchQuerySchema:
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


class FeatureDetails(BaseModel):
    feature_id: int
    feature_type: TitleType
    year: int | None
    title: str
    movie_name: str
    imdb_id: int
    tmdb_id: int | None

    # Episode specific fields
    parent_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None
    parent_imdb_id: int | None = None

    # If api sends titletype in upper case then make to lowercase then parse it
    @field_validator("feature_type", mode="before")
    @classmethod
    def normalize_feature_type(cls, value):
        return value.lower()


class ReletedLinks(BaseModel):
    img_url: str


class Files(BaseModel):
    file_id: int
    cd_number: int


class SubtileFileSchema(BaseModel):
    id: str
    type: str
    language: str = Field(validation_alias=AliasPath("attributes", "language"))
    feature_details: FeatureDetails = Field(
        validation_alias=AliasPath("attributes", "feature_details")
    )

    related_links: list[ReletedLinks] = Field(
        validation_alias=AliasPath("attributes", "related_links")
    )

    files: list[Files] = Field(validation_alias=AliasPath("attributes", "files"))


# Search endpoint return type:Feature json model from
# https://api.opensubtitles.com/api/v1/subtitles which contains both movie,tvshow,endpoint
# with contanst field
class Episodes(BaseModel):
    episode_number: int
    title: str | None
    feature_imdb_id: int


class Seasons(BaseModel):
    season_number: int
    episodes: list[Episodes]


class Attributes(BaseModel):
    title: str
    original_title: str | None = None
    year: int | str | None = None
    subtitles_count: int = 0
    seasons_count: int = 0
    subtitles_counts: dict
    parent_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None
    imdb_id: int
    tmdb_id: int | None = None
    parent_imdb_id: int | None = None
    feature_id: str
    title_aka: list[str]
    # feature_type: TitleType  # movie|episode|tvshow
    img_url: str
    seasons: list[Seasons] = []

    # @field_validator("feature_type", mode="before")
    # @classmethod
    # def normalize_feature_type(cls, value):
    #     return value.lower()


class SearchResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    """
    Search Schema contains
    the response from search endpoint
    """

    id: str
    type: str
    attributes: Attributes


class DiscoverReponseSchema(SearchResponseSchema):
    pass


class TranslationsResponseSchema(PhraseOrSentence):
    id: int
    content_uid: uuid.UUID
    language: str
