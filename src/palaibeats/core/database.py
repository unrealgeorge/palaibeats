"""Async SQLite persistence layer (radio stations, guild settings)."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path

import aiosqlite

from palaibeats.core.exceptions import (
    StationAlreadyExistsError,
    StationNotFoundError,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS radio_stations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    url         TEXT NOT NULL,
    added_by    TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id        INTEGER PRIMARY KEY,
    last_volume     REAL,
    last_station    TEXT
);
"""


@dataclass(frozen=True, slots=True)
class RadioStation:
    id: int
    name: str
    url: str
    added_by: str
    created_at: str


class Database:
    """Thin async wrapper around the SQLite file used by PalaiBeats."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def _c(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database.connect() must be called first")
        return self._conn

    # --- radio stations -------------------------------------------------

    async def add_station(self, name: str, url: str, added_by: str) -> RadioStation:
        existing = await self.get_station(name)
        if existing is not None:
            raise StationAlreadyExistsError(name)

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor = await self._c.execute(
            "INSERT INTO radio_stations (name, url, added_by, created_at) "
            "VALUES (?, ?, ?, ?)",
            (name, url, added_by, created_at),
        )
        await self._c.commit()
        station_id = cursor.lastrowid
        assert station_id is not None
        return RadioStation(station_id, name, url, added_by, created_at)

    async def get_station(self, name: str) -> RadioStation | None:
        cursor = await self._c.execute(
            "SELECT id, name, url, added_by, created_at FROM radio_stations "
            "WHERE name = ? COLLATE NOCASE",
            (name,),
        )
        row = await cursor.fetchone()
        return RadioStation(**dict(row)) if row is not None else None

    async def list_stations(self) -> list[RadioStation]:
        cursor = await self._c.execute(
            "SELECT id, name, url, added_by, created_at FROM radio_stations "
            "ORDER BY name COLLATE NOCASE"
        )
        rows = await cursor.fetchall()
        return [RadioStation(**dict(row)) for row in rows]

    async def delete_station(self, name: str) -> None:
        existing = await self.get_station(name)
        if existing is None:
            raise StationNotFoundError(name)
        await self._c.execute(
            "DELETE FROM radio_stations WHERE id = ?", (existing.id,)
        )
        await self._c.commit()

    # --- per-guild settings ---------------------------------------------

    async def get_last_volume(self, guild_id: int) -> float | None:
        cursor = await self._c.execute(
            "SELECT last_volume FROM guild_settings WHERE guild_id = ?",
            (guild_id,),
        )
        row = await cursor.fetchone()
        return row["last_volume"] if row is not None else None

    async def set_last_volume(self, guild_id: int, volume: float) -> None:
        await self._c.execute(
            "INSERT INTO guild_settings (guild_id, last_volume) VALUES (?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET last_volume = excluded.last_volume",
            (guild_id, volume),
        )
        await self._c.commit()
