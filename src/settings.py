from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Phrase"

    DATABASE_URL: str
    SECRET_KEY: SecretStr
    SALT_ROUNDS: int = 14

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    ACCESS_TOKEN_SECRET_KEY: SecretStr
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 15  # 15 days
    REFRESH_TOKEN_SECRET_KEY: SecretStr

    GEMINI_API_KEY: SecretStr

    # Open router api key
    OPENROUTER_API_KEY: SecretStr

    # Opensubtitle
    OPENSUBTITLE_KEY: SecretStr
    OPENSUBTITLE_USERNAME: str
    OPENSUBTITLE_PASSWORD: SecretStr

    # SubDL key
    SUBDL_KEY: SecretStr
    # FANART_KEY key
    FANART_KEY: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Skips over variables not defined in this class
    )


settings = Settings()
