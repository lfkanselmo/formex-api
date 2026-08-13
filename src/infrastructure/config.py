from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://formex:formex@localhost:5433/formex"
    cors_origins: list[str] = ["http://localhost:4200"]
    secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 30


settings = Settings()  # type: ignore[call-arg]
