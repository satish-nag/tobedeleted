from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "fba-alert-summary"
    env: str = Field(description="Environment name")
    log_level: str = Field(default="INFO")

    # Alert details service url
    alert_details_url: str

    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment: str
    azure_openai_api_version: str

    # Streaming delay only for testing
    stream_chunk_sleep_ms: int = 3000  # set >0 if you want artificial pacing

    # Timeouts
    http_timeout_seconds: float


settings = Settings()