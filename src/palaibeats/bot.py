"""The bot itself: wiring config, database, library, player manager and
cogs together."""

from __future__ import annotations

import logging

import discord
from aiohttp import web
from discord.ext import commands

from palaibeats.cogs.music import MusicCog
from palaibeats.cogs.radio import RadioCog
from palaibeats.config import Settings
from palaibeats.core.audio import ensure_opus_loaded
from palaibeats.core.database import Database
from palaibeats.core.library import MusicLibrary
from palaibeats.player.manager import PlayerManager

logger = logging.getLogger(__name__)


class PalaiBeatsBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.voice_states = True  # needed to know who's in a voice channel

        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

        self.settings = settings
        self.db = Database(settings.db_path)
        self.library = MusicLibrary(settings.music_root)
        self.player_manager = PlayerManager(self, settings, self.db)
        self._health_runner: web.AppRunner | None = None

    async def setup_hook(self) -> None:
        ensure_opus_loaded()

        await self.db.connect()

        count = self.library.refresh()
        logger.info("Loaded %d song(s) from %s", count, self.settings.music_root)

        await self.add_cog(MusicCog(self, self.settings, self.library, self.player_manager))
        await self.add_cog(RadioCog(self, self.settings, self.db, self.player_manager))

        guild_obj = discord.Object(id=self.settings.guild_id)
        self.tree.copy_global_to(guild=guild_obj)
        synced = await self.tree.sync(guild=guild_obj)
        logger.info("Synced %d application command(s) to guild %s", len(synced), self.settings.guild_id)

        if self.settings.health_check_port:
            from palaibeats.healthcheck import start_health_server

            self._health_runner = await start_health_server(self.settings.health_check_port)
            logger.info("Health endpoint listening on :%d/healthz", self.settings.health_check_port)

    async def on_ready(self) -> None:
        logger.info("Logged in as %s (id=%s)", self.user, self.user.id if self.user else "?")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="/browse or /radio play"
            )
        )

    async def on_guild_join(self, guild: discord.Guild) -> None:
        # PalaiBeats is designed and permissioned for a single server.
        if guild.id != self.settings.guild_id:
            logger.warning(
                "Joined unexpected guild %s (%s) — leaving, PalaiBeats is configured "
                "for guild %s only.",
                guild.id,
                guild.name,
                self.settings.guild_id,
            )
            await guild.leave()

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        player = self.player_manager.get(member.guild.id)
        if player is not None:
            player.on_voice_state_update()

    async def close(self) -> None:
        logger.info("Shutting down...")
        await self.player_manager.disconnect_all()
        await self.db.close()
        if self._health_runner is not None:
            await self._health_runner.cleanup()
        await super().close()
