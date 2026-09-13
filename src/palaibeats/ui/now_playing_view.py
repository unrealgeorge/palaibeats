"""Playback control buttons attached to the "now playing" message."""

from __future__ import annotations

import logging

import discord

from palaibeats.config import Settings
from palaibeats.core.exceptions import NothingPlayingError
from palaibeats.core.permissions import is_dj
from palaibeats.player.manager import PlayerManager
from palaibeats.utils.embeds import build_now_playing_embed

logger = logging.getLogger(__name__)


class NowPlayingView(discord.ui.View):
    def __init__(self, player_manager: PlayerManager, settings: Settings, guild_id: int) -> None:
        super().__init__(timeout=None)  # persistent-style controls
        self._player_manager = player_manager
        self._settings = settings
        self._guild_id = guild_id

    def _require_dj(self, interaction: discord.Interaction) -> bool:
        return isinstance(interaction.user, discord.Member) and is_dj(
            interaction.user, self._settings.dj_role_name
        )

    async def _guarded(self, interaction: discord.Interaction, action) -> None:
        if not self._require_dj(interaction):
            await interaction.response.send_message(
                f":no_entry: Only members with the **{self._settings.dj_role_name}** role can control playback.",
                ephemeral=True,
            )
            return

        player = self._player_manager.get(self._guild_id)
        if player is None:
            await interaction.response.send_message(":zzz: Nothing is active.", ephemeral=True)
            return

        try:
            await action(player)
        except NothingPlayingError:
            await interaction.response.send_message(":zzz: Nothing is playing.", ephemeral=True)
            return

        embed = build_now_playing_embed(player)
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⏯ Pause/Resume", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        async def _action(player):
            if player.voice_client is not None and player.voice_client.is_paused():
                await player.resume()
            else:
                await player.pause()

        await self._guarded(interaction, _action)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._guarded(interaction, lambda player: player.skip())

    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._guarded(interaction, lambda player: player.stop())

    @discord.ui.button(label="🔉", style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._guarded(interaction, lambda player: player.set_volume(player.volume - 0.1))

    @discord.ui.button(label="🔊", style=discord.ButtonStyle.secondary)
    async def volume_up(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._guarded(interaction, lambda player: player.set_volume(player.volume + 0.1))

    @discord.ui.button(label="🔁 Loop", style=discord.ButtonStyle.secondary)
    async def loop_toggle(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        async def _action(player):
            player.toggle_loop()

        await self._guarded(interaction, _action)
