"""Radio station management and playback (`/radio ...`).

Stations are direct stream URLs stored in SQLite. Note: playlist formats
like `.pls`/`.m3u` are *not* directly playable — use the actual stream
URL inside them (see README).
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from palaibeats.config import Settings
from palaibeats.core.database import Database
from palaibeats.core.exceptions import StationAlreadyExistsError, StationNotFoundError
from palaibeats.core.permissions import is_dj
from palaibeats.player.manager import PlayerManager

logger = logging.getLogger(__name__)


class RadioCog(commands.GroupCog, name="radio"):
    def __init__(
        self,
        bot: commands.Bot,
        settings: Settings,
        db: Database,
        player_manager: PlayerManager,
    ) -> None:
        self.bot = bot
        self.settings = settings
        self.db = db
        self.player_manager = player_manager
        super().__init__()

    async def _ensure_dj(self, interaction: discord.Interaction) -> bool:
        if isinstance(interaction.user, discord.Member) and is_dj(
            interaction.user, self.settings.dj_role_name
        ):
            return True
        await interaction.response.send_message(
            f":no_entry: Only members with the **{self.settings.dj_role_name}** role can do that.",
            ephemeral=True,
        )
        return False

    async def _station_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        stations = await self.db.list_stations()
        current_lower = current.lower()
        return [
            app_commands.Choice(name=s.name, value=s.name)
            for s in stations
            if current_lower in s.name.lower()
        ][:25]

    @app_commands.command(name="add", description="Save a radio station (direct stream URL)")
    @app_commands.describe(name="A short name for the station", url="The direct stream URL")
    async def add(self, interaction: discord.Interaction, name: str, url: str) -> None:
        if not await self._ensure_dj(interaction):
            return
        try:
            await self.db.add_station(name, url, added_by=str(interaction.user))
        except StationAlreadyExistsError:
            await interaction.response.send_message(
                f":warning: A station named **{name}** already exists.", ephemeral=True
            )
            return
        await interaction.response.send_message(f":white_check_mark: Saved station **{name}**.")

    @app_commands.command(name="remove", description="Delete a saved radio station")
    @app_commands.describe(name="The station to delete")
    @app_commands.autocomplete(name=_station_autocomplete)
    async def remove(self, interaction: discord.Interaction, name: str) -> None:
        if not await self._ensure_dj(interaction):
            return
        try:
            await self.db.delete_station(name)
        except StationNotFoundError:
            await interaction.response.send_message(
                f":warning: No station named **{name}**.", ephemeral=True
            )
            return
        await interaction.response.send_message(f":wastebasket: Deleted station **{name}**.")

    @app_commands.command(name="list", description="List saved radio stations")
    async def list_stations(self, interaction: discord.Interaction) -> None:
        stations = await self.db.list_stations()
        if not stations:
            await interaction.response.send_message(
                ":radio: No stations saved yet — add one with `/radio add`.", ephemeral=True
            )
            return
        lines = [f"**{s.name}** — {s.url}" for s in stations]
        embed = discord.Embed(
            title="📻 Saved stations", description="\n".join(lines[:25]), color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play", description="Play a saved radio station")
    @app_commands.describe(name="Which station to play")
    @app_commands.autocomplete(name=_station_autocomplete)
    async def play(self, interaction: discord.Interaction, name: str) -> None:
        if not await self._ensure_dj(interaction):
            return

        member = interaction.user
        if (
            not isinstance(member, discord.Member)
            or member.voice is None
            or member.voice.channel is None
        ):
            await interaction.response.send_message(
                ":no_entry: Join a voice channel first.", ephemeral=True
            )
            return

        station = await self.db.get_station(name)
        if station is None:
            await interaction.response.send_message(
                f":warning: No station named **{name}**. Try `/radio list`.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        assert isinstance(interaction.guild, discord.Guild)
        player = self.player_manager.get_or_create(interaction.guild)
        await player.play_radio(station, member.voice.channel, interaction.channel)
        await interaction.followup.send(f":radio: Streaming **{station.name}**.")

    @app_commands.command(name="stop", description="Stop the radio stream")
    async def stop(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_dj(interaction):
            return
        player = self.player_manager.get(interaction.guild_id)  # type: ignore[arg-type]
        if player is None:
            await interaction.response.send_message(":zzz: Nothing is playing.", ephemeral=True)
            return
        await player.stop()
        await interaction.response.send_message(":stop_button: Radio stopped.")
