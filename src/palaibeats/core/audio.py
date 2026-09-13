"""Everything that turns "a thing the user asked for" into a playable
discord.py `AudioSource`: opus library loading, yt-dlp resolution for
links/searches, and FFmpeg source construction.

Learned the hard way on Raspberry Pi (see README "Notes for Raspberry Pi"):
  * libopus is not always auto-detected on arm64 Debian -> load explicitly.
  * `-reconnect` ffmpeg flags are for network streams only; they break
    local file playback and must not be used there.
"""

from __future__ import annotations

import asyncio
import ctypes.util
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import discord
import yt_dlp

from palaibeats.core.exceptions import TrackResolutionError

logger = logging.getLogger(__name__)

# Paths worth trying explicitly before giving up — arm64 Debian/Ubuntu
# (as shipped on Raspberry Pi OS 64-bit) sometimes doesn't expose libopus
# under a name ctypes.util.find_library() can locate automatically.
_OPUS_CANDIDATES = (
    "opus",
    "libopus.so.0",
    "/usr/lib/aarch64-linux-gnu/libopus.so.0",
    "/usr/lib/arm-linux-gnueabihf/libopus.so.0",
    "/usr/lib/x86_64-linux-gnu/libopus.so.0",
    "/usr/local/lib/libopus.so.0",
)

_STREAM_BEFORE_OPTIONS = (
    "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin"
)
_LOCAL_BEFORE_OPTIONS = "-nostdin"

_YDL_OPTS: dict[str, Any] = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch1",
    "source_address": "0.0.0.0",
}


def ensure_opus_loaded() -> None:
    """Make sure libopus is loaded, trying several known-good paths."""

    if discord.opus.is_loaded():
        return

    found = ctypes.util.find_library("opus")
    candidates = ([found] if found else []) + list(_OPUS_CANDIDATES)

    for candidate in candidates:
        try:
            discord.opus.load_opus(candidate)
            logger.info("Loaded libopus via %r", candidate)
            return
        except (OSError, TypeError):
            continue

    logger.error(
        "Could not load libopus from any known path (%s). "
        "Voice playback will fail. Install libopus0 (Debian/Ubuntu) "
        "or the equivalent package for your platform.",
        ", ".join(c for c in candidates if c),
    )


@dataclass(frozen=True, slots=True)
class ResolvedTrack:
    title: str
    stream_url: str
    webpage_url: str
    duration: float | None
    http_headers: dict[str, str]


async def resolve_track(query_or_url: str) -> ResolvedTrack:
    """Resolve a YouTube/SoundCloud/etc. link, or a plain search query,
    into a direct, streamable audio URL. Runs yt-dlp in a worker thread
    since it performs blocking network I/O.
    """

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, _extract_info, query_or_url)
    except yt_dlp.utils.DownloadError as exc:
        raise TrackResolutionError(str(exc)) from exc

    if info is None:
        raise TrackResolutionError(f"Could not resolve: {query_or_url}")

    # A search (`ytsearch1:...`) returns a playlist-like dict with entries.
    if "entries" in info:
        entries = [e for e in info["entries"] if e]
        if not entries:
            raise TrackResolutionError(f"No results for: {query_or_url}")
        info = entries[0]

    stream_url = info.get("url")
    if not stream_url:
        raise TrackResolutionError(f"No playable stream found for: {query_or_url}")

    return ResolvedTrack(
        title=info.get("title") or query_or_url,
        stream_url=stream_url,
        webpage_url=info.get("webpage_url") or query_or_url,
        duration=info.get("duration"),
        http_headers=info.get("http_headers") or {},
    )


def _extract_info(query_or_url: str) -> dict[str, Any] | None:
    with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
        return ydl.extract_info(query_or_url, download=False)


def build_local_source(
    path: Path, volume: float, ffmpeg_executable: str
) -> discord.PCMVolumeTransformer:
    """Local file playback — no reconnect flags (they break seeking/EOF
    detection on local files)."""

    source = discord.FFmpegPCMAudio(
        str(path),
        executable=ffmpeg_executable,
        before_options=_LOCAL_BEFORE_OPTIONS,
        options="-vn",
    )
    return discord.PCMVolumeTransformer(source, volume=volume)


def build_stream_source(
    url: str,
    volume: float,
    ffmpeg_executable: str,
    http_headers: dict[str, str] | None = None,
) -> discord.PCMVolumeTransformer:
    """Network stream playback (resolved links or direct radio URLs) —
    includes reconnect flags so brief network hiccups don't kill the
    stream outright."""

    before_options = _STREAM_BEFORE_OPTIONS
    if http_headers:
        header_str = "".join(f"{k}: {v}\r\n" for k, v in http_headers.items())
        before_options = f'{before_options} -headers "{header_str}"'

    source = discord.FFmpegPCMAudio(
        url,
        executable=ffmpeg_executable,
        before_options=before_options,
        options="-vn",
    )
    return discord.PCMVolumeTransformer(source, volume=volume)
