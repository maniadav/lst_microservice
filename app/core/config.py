from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "lst_service"

    # Feature flags
    SEMANTICS_SOURCE: str = "local"  # "local" or "mongodb"
    SAVE_RESULTS_TO_DB: bool = False

    # HuggingFace (required for Pyannote speaker diarization)
    HF_TOKEN: str = ""

    # WhisperX
    WHISPER_MODEL_NAME: str = "large-v3"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # Security
    API_KEY: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    # Audio
    MAX_UPLOAD_SIZE_MB: int = 50

    # Local semantics file path
    LOCAL_SEMANTICS_PATH: str = "app/data/sample_semantics.json"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_mongodb_required(self) -> bool:
        return self.SEMANTICS_SOURCE == "mongodb" or self.SAVE_RESULTS_TO_DB

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
