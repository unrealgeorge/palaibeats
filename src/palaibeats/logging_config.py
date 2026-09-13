"""Structured, readable logging setup."""

from __future__ import annotations

import logging
import sys


class _LevelColorFormatter(logging.Formatter):
    """A minimal formatter that colorizes the level name on TTYs."""

    _COLORS = {
        logging.DEBUG: "\033[36m",  # cyan
        logging.INFO: "\033[32m",  # green
        logging.WARNING: "\033[33m",  # yellow
        logging.ERROR: "\033[31m",  # red
        logging.CRITICAL: "\033[41m",  # red background
    }
    _RESET = "\033[0m"

    def __init__(self, use_color: bool) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        if self._use_color:
            color = self._COLORS.get(record.levelno, "")
            record.levelname = f"{color}{record.levelname}{self._RESET}"
        return super().format(record)


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger for the whole process."""

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(_LevelColorFormatter(use_color=sys.stdout.isatty()))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Noisy third-party loggers: keep them at WARNING unless we're in DEBUG.
    if level != "DEBUG":
        logging.getLogger("discord").setLevel(logging.WARNING)
        logging.getLogger("discord.http").setLevel(logging.WARNING)
        logging.getLogger("yt_dlp").setLevel(logging.WARNING)
