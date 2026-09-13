"""Local library browsing/queue playback and link playback (YouTube,
SoundCloud, and anything else yt-dlp supports).
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from palaibeats.config import Settings
from palaibeats.core import audio
from palaibeats.core.exceptions import NothingPlayingError, TrackResolutionError
from palaibeats.core.library import MusicLibrary
from palaibeats.core.permissions import is_dj
from palaibeats.player.manager import PlayerManager
from palaibeats.player.models import Track
from palaibeats.ui.browse_views import FolderBrowseView
from palaibeats.ui.now_playing_view import NowPlayingView
from palaibeats.utils.embeds import build_now_playing_embed

logger = logging.getLogger(__name__)


class MusicCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        settings: Settings,
        library: MusicLibrary,
        player_manager: PlayerManager,
    ) -> None:
        self.bot = bot
        self.settings = settings
        self.library = library
        self.player_manager = player_manager

    # ---- shared helpers ---------------------------------------------------

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

    async def _voice_channel_or_error(
        self, interaction: discord.Interaction
    ) -> discord.VoiceChannel | None:
        member = interaction.user
        if (
            not isinstance(member, discord.Member)
            or member.voice is None
            or member.voice.channel is None
        ):
            await interaction.response.send_message(
                ":no_entry: Join a voice channel first.", ephemeral=True
            )
            return None
        return member.voice.channel

    # ---- browsing -----------------------------------------------------------

    @app_commands.command(name="browse", description="Browse the local music library by folder")
    async def browse(self, interaction: discord.Interaction) -> None:
        if self.library.total_songs == 0:
            await interaction.response.send_message(
                ":file_folder: No music found yet. Add files under the music folder "
                "and run `/refresh-library`.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🎶 Local library",
            description="Pick a folder to see the songs inside.",
            color=discord.Color.blurple(),
        )
        view = FolderBrowseView(self.library, self.player_manager, self.settings)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="refresh-library", description="Rescan the local music folder")
    async def refresh_library(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_dj(interaction):
            return
        count = self.library.refresh()
        await interaction.response.send_message(
            f":white_check_mark: Library refreshed — {count} song(s) across "
            f"{len(self.library.folder_names)} folder(s).",
            ephemeral=True,
        )

    # ---- link playback ------------------------------------------------------

    @app_commands.command(
        name="play", description="Play a link (YouTube, SoundCloud, ...) or search text"
    )
    @app_commands.describe(query="A link, or words to search for")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        if not await self._ensure_dj(interaction):
            return
        channel = await self._voice_channel_or_error(interaction)
        if channel is None:
            return

        await interaction.response.defer(thinking=True)
        try:
            resolved = await audio.resolve_track(query)
        except TrackResolutionError as exc:
            await interaction.followup.send(f":warning: {exc}")
            return

        assert isinstance(interaction.guild, discord.Guild)
        player = self.player_manager.get_or_create(interaction.guild)
        track = Track(
            title=resolved.title,
            requested_by=str(interaction.user),
            stream_url=resolved.stream_url,
            http_headers=resolved.http_headers,
            webpage_url=resolved.webpage_url,
            duration=resolved.duration,
        )
        await player.enqueue(track, channel, interaction.channel)
        await interaction.followup.send(f":inbox_tray: Queued **{resolved.title}**")

    # ---- playback controls ---------------------------------------------------

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_dj(interaction):
            return
        player = self.player_manager.get(interaction.guild_id)  # type: ignore[arg-type]
        if player is None:
            await interaction.response.send_message(":zzz: Nothing is playing.", ephemeral=True)
            return
        try:
            await player.skip()
        except NothingPlayingError:
            await interaction.response.send_message(":zzz: Nothing is playing.", ephemeral=True)
            return
        await interaction.response.send_message(":track_next: Skipped.")

    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_dj(interaction):
            return
        player = self.player_manager.get(interaction.guild_id)  # type: ignore[arg-type]
        if player is None:
            await interaction.response.send_message(":zzz: Nothing is playing.", ephemeral=True)
            return
        try:
            await player.pause()
        except NothingPlayingError:
            await interaction.response.send_message(":zzz: Nothing is playing.", ephemeral=True)
            return
        await interaction.response.send_message(":pause_button: Paused.")

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_dj(interaction):
            return
        player = self.player_manager.get(interaction.guild_id)  # type: ignore[arg-type]
        if player is None:
            await interaction.response.send_message(":zzz: Nothing is paused.", ephemeral=True)
            return
        try:
            await player.resume()
        except NothingPlayingError:
            await interaction.response.send_message(":zzz: Nothing is paused.", ephemeral=True)
            return
        await interaction.response.send_message(":arrow_forward: Resumed.")

    @app_commands.command(name="stop", description="Stop playback and clear the queue")
    async def stop(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_dj(interaction):
            return
        player = self.player_manager.get(interaction.guild_id)  # type: ignore[arg-type]
        if player is None:
            await interaction.response.send_message(":zzz: Nothing to stop.", ephemeral=True)
            return
        await player.stop()
        await interaction.response.send_message(":stop_button: Stopped and cleared the queue.")

    @app_commands.command(name="leave", description="Disconnect from the voice channel")
    async def leave(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_dj(interaction):
            return
        player = self.player_manager.get(interaction.guild_id)  # type: ignore[arg-type]
        if player is None or not player.is_connected:
            await interaction.response.send_message(":zzz: Not connected.", ephemeral=True)
            return
        await player.disconnect()
        await interaction.response.send_message(":wave: Disconnected.")

    @app_commands.command(name="volume", description="Set the playback volume (0-200%)")
    @app_commands.describe(percent="0 to 200")
    async def volume(self, interaction: discord.Interaction, percent: app_commands.Range[int, 0, 200]) -> None:
        if not await self._ensure_dj(interaction):
            return
        assert isinstance(interaction.guild, discord.Guild)
        player = self.player_manager.get_or_create(interaction.guild)
        await player.set_volume(percent / 100)
        await interaction.response.send_message(f":loud_sound: Volume set to {percent}%.")

    @app_commands.command(name="loop", description="Toggle looping the current track")
    async def loop(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_dj(interaction):
            return
        player = self.player_manager.get(interaction.guild_id)  # type: ignore[arg-type]
        if player is None:
            await interaction.response.send_message(":zzz: Nothing is playing.", ephemeral=True)
            return
        enabled = player.toggle_loop()
        await interaction.response.send_message(
            f":repeat: Loop {'enabled' if enabled else 'disabled'}."
        )

    @app_commands.command(name="queue", description="Show the upcoming queue")
    async def queue(self, interaction: discord.Interaction) -> None:
        player = self.player_manager.get(interaction.guild_id)  # type: ignore[arg-type]
        if player is None or not player.queue:
            await interaction.response.send_message(":inbox_tray: The queue is empty.", ephemeral=True)
            return
        lines = [f"{i}. {track.title}" for i, track in enumerate(player.queue.as_list(), start=1)]
        embed = discord.Embed(
            title="📜 Up next", description="\n".join(lines[:25]), color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="Show what's playing, with controls")
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        assert interaction.guild_id is not None
        player = self.player_manager.get(interaction.guild_id)
        if player is None:
            await interaction.response.send_message(embed=discord.Embed(
                title="⏹ Nothing playing",
                description="Use `/browse`, `/play`, or `/radio play` to start something.",
                color=discord.Color.greyple(),
            ))
            return
        embed = build_now_playing_embed(player)
        view = NowPlayingView(self.player_manager, self.settings, interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:  # pragma: no cover - wired up in bot.py instead
    raise RuntimeError("MusicCog is added manually in bot.py with extra dependencies")
