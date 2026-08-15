from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://formex:formex@localhost:5433/formex"
    cors_origins: list[str] = ["http://localhost:4200"]
    secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 30
    gotenberg_url: str = "http://localhost:3000"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "formex"
    s3_secret_key: str = "formex123"
    s3_bucket: str = "formex"
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()  # type: ignore[call-arg]
