from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "news_dashboard"
    redis_url: str = "redis://localhost:6379/0"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b-instruct-q4_K_M"
    scrape_interval_hours: int = 6
    breaking_check_minutes: int = 60
    run_on_start: bool = True
    user_agent: str = "NewsDashboardBot/0.1 (+local; personal use)"
    staging_ttl_seconds: int = 86400
    dedup_ttl_seconds: int = 7 * 86400
    request_delay_seconds: float = 1.0
    log_level: str = "INFO"
    topics_file: str = "/app/topics.txt"
    sources_per_cycle: int = 30
    rss_items_per_source: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
