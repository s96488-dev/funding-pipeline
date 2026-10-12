from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    snapshots_topic: str = "funding.snapshots"
