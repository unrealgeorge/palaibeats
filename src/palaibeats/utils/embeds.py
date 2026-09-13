"""Embed builders shared across cogs and UI views."""

from __future__ import annotations

import discord

from palaibeats.player.guild_player import GuildPlayer
from palaibeats.player.models import PlayerMode
from palaibeats.utils.formatting import format_duration


def build_now_playing_embed(player: GuildPlayer) -> discord.Embed:
    if player.mode == PlayerMode.RADIO and player.current_station is not None:
        embed = discord.Embed(
            title="📻 Now streaming",
            description=f"**{player.current_station.name}**",
            color=discord.Color.green(),
        )
        embed.add_field(name="Volume", value=f"{int(player.volume * 100)}%")
        return embed

    if player.mode == PlayerMode.QUEUE and player.current_track is not None:
        track = player.current_track
        embed = discord.Embed(
            title="🎵 Now playing",
            description=f"**{track.title}**",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Source", value="Local file" if track.is_local else "Link")
        if track.duration:
            embed.add_field(name="Duration", value=format_duration(track.duration))
        embed.add_field(name="Volume", value=f"{int(player.volume * 100)}%")
        embed.add_field(name="Loop", value="On" if player.loop_current else "Off")
        embed.add_field(name="Up next", value=str(len(player.queue)))
        embed.set_footer(text=f"Requested by {track.requested_by}")
        return embed

    return discord.Embed(
        title="⏹ Nothing playing",
        description="Use `/browse`, `/play`, or `/radio play` to start something.",
        color=discord.Color.greyple(),
    )
