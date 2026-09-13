"""Application configuration, loaded from environment variables / .env."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp3", ".flac", ".wav", ".m4a", ".ogg", ".opus", ".aac", ".wma"}
)


class Settings(BaseSettings):
    """Runtime configuration for PalaiBeats.

    Values are read from environment variables (or a `.env` file in the
    working directory). See `.env.example` for the full list and defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    discord_token: str = Field(..., description="Discord bot token")
    guild_id: int = Field(..., description="Target Discord guild (server) ID")

    dj_role_name: str = Field(default="DJ")

    music_root: Path = Field(default=Path("/music"))
    db_path: Path = Field(default=Path("/data/palaibeats.db"))

    default_volume: float = Field(default=0.5, ge=0.0, le=2.0)
    idle_timeout_seconds: int = Field(default=300, ge=0)

    log_level: str = Field(default="INFO")
    health_check_port: int | None = Field(default=None)

    ffmpeg_executable: str = Field(default="ffmpeg")
    opus_bitrate_kbps: int = Field(default=128, ge=32, le=512)

    @field_validator("log_level")
    @classmethod
    def _uppercase_log_level(cls, value: str) -> str:
        return value.upper()


def load_settings() -> Settings:
    """Load and validate settings once at process start."""

    return Settings()  # type: ignore[call-arg]
