"""Scans the local music root into folders (top-level = category/artist)
so it can be browsed from Discord without hitting the disk on every click.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from palaibeats.config import AUDIO_EXTENSIONS

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Song:
    path: Path
    title: str
    folder: str

    @property
    def relative_display(self) -> str:
        return f"{self.folder} / {self.title}"


class MusicLibrary:
    """In-memory index of `music_root`, rebuilt on demand via `refresh()`.

    Layout expected on disk:
        MUSIC_ROOT/
            Some Artist/
                song1.mp3
                song2.flac
            Another Folder/
                sub-folder/          <- nested files are included too
                    song3.m4a

    Each *top-level* directory under `music_root` becomes one browsable
    folder; every audio file found anywhere underneath it (recursively)
    belongs to that folder.
    """

    def __init__(self, music_root: Path) -> None:
        self._music_root = music_root
        self._folders: dict[str, list[Song]] = {}

    def refresh(self) -> int:
        """Rescan disk. Returns the number of songs found."""

        self._folders = {}

        if not self._music_root.exists():
            logger.warning("Music root %s does not exist yet", self._music_root)
            return 0

        for entry in sorted(self._music_root.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_dir():
                continue

            songs = [
                Song(path=file, title=file.stem, folder=entry.name)
                for file in sorted(
                    entry.rglob("*"), key=lambda p: p.name.lower()
                )
                if file.is_file() and file.suffix.lower() in AUDIO_EXTENSIONS
            ]
            if songs:
                self._folders[entry.name] = songs

        total = sum(len(songs) for songs in self._folders.values())
        logger.info(
            "Library scan: %d folder(s), %d song(s) under %s",
            len(self._folders),
            total,
            self._music_root,
        )
        return total

    @property
    def folder_names(self) -> list[str]:
        return list(self._folders.keys())

    def songs_in(self, folder: str) -> list[Song]:
        return self._folders.get(folder, [])

    def search(self, query: str, limit: int = 25) -> list[Song]:
        needle = query.strip().lower()
        if not needle:
            return []
        results: list[Song] = []
        for songs in self._folders.values():
            for song in songs:
                if needle in song.title.lower():
                    results.append(song)
                    if len(results) >= limit:
                        return results
        return results

    @property
    def total_songs(self) -> int:
        return sum(len(songs) for songs in self._folders.values())
