from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    snapshots_topic: str = "funding.snapshots"
    poll_interval_seconds: int = 60
    model_config = SettingsConfigDict(env_file=".env")
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+psycopg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
