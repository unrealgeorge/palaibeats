"""Data types shared by the queue and the guild player."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from pathlib import Path


class PlayerMode(enum.Enum):
    IDLE = "idle"
    QUEUE = "queue"  # local files and/or resolved links, played in order
    RADIO = "radio"  # a single continuous stream, auto-reconnected


@dataclass(slots=True)
class Track:
    """One playable item: either a local file or a resolved stream URL."""

    title: str
    requested_by: str
    local_path: Path | None = None
    stream_url: str | None = None
    http_headers: dict[str, str] | None = None
    webpage_url: str | None = None
    duration: float | None = None

    @property
    def is_local(self) -> bool:
        return self.local_path is not None
