"""Small text-formatting helpers shared by cogs and UI views."""

from __future__ import annotations


def truncate(text: str, max_len: int = 100) -> str:
    """Discord select-option labels/values are capped at 100 characters."""

    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def format_duration(seconds: float | None) -> str:
    if not seconds or seconds <= 0:
        return "live"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
