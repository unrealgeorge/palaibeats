"""Keeps track of one `GuildPlayer` per Discord server."""

from __future__ import annotations

import discord

from palaibeats.config import Settings
from palaibeats.core.database import Database
from palaibeats.player.guild_player import GuildPlayer


class PlayerManager:
    def __init__(self, bot: discord.Client, settings: Settings, db: Database) -> None:
        self._bot = bot
        self._settings = settings
        self._db = db
        self._players: dict[int, GuildPlayer] = {}

    def get(self, guild_id: int) -> GuildPlayer | None:
        return self._players.get(guild_id)

    def get_or_create(self, guild: discord.Guild) -> GuildPlayer:
        player = self._players.get(guild.id)
        if player is None:
            player = GuildPlayer(guild, self._bot, self._settings, self._db)
            self._players[guild.id] = player
        return player

    async def disconnect_all(self) -> None:
        for player in list(self._players.values()):
            await player.disconnect()
