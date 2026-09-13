"""Browse-by-folder UI for the local music library.

Anyone can open and navigate `/browse`. Actually picking a song to play
is a control action and requires the DJ role (see `core.permissions`).
"""

from __future__ import annotations

import logging

import discord

from palaibeats.config import Settings
from palaibeats.core.library import MusicLibrary, Song
from palaibeats.core.permissions import is_dj
from palaibeats.player.manager import PlayerManager
from palaibeats.player.models import Track
from palaibeats.utils.formatting import truncate
from palaibeats.utils.pagination import paginate, page_count

logger = logging.getLogger(__name__)


async def _require_voice_channel(interaction: discord.Interaction) -> discord.VoiceChannel | None:
    member = interaction.user
    if not isinstance(member, discord.Member) or member.voice is None or member.voice.channel is None:
        await interaction.response.send_message(
            ":no_entry: Join a voice channel first.", ephemeral=True
        )
        return None
    return member.voice.channel


def _check_dj(interaction: discord.Interaction, settings: Settings) -> bool:
    return isinstance(interaction.user, discord.Member) and is_dj(interaction.user, settings.dj_role_name)


class FolderBrowseView(discord.ui.View):
    def __init__(
        self,
        library: MusicLibrary,
        player_manager: PlayerManager,
        settings: Settings,
        page: int = 0,
    ) -> None:
        super().__init__(timeout=180)
        self._library = library
        self._player_manager = player_manager
        self._settings = settings
        self._page = page
        self._rebuild()

    def _rebuild(self) -> None:
        self.clear_items()
        folders = self._library.folder_names
        total_pages = page_count(len(folders))
        self._page = max(0, min(self._page, total_pages - 1))
        page_items = paginate(folders, self._page)

        select = discord.ui.Select(
            placeholder=f"Choose a folder… (page {self._page + 1}/{total_pages})",
            options=[
                discord.SelectOption(label=truncate(name), value=name)
                for name in page_items
            ]
            or [discord.SelectOption(label="No music found", value="__none__")],
            disabled=not page_items,
        )
        select.callback = self._on_select  # type: ignore[method-assign]
        self.add_item(select)

        prev_button = discord.ui.Button(
            label="◀ Prev", style=discord.ButtonStyle.secondary, disabled=self._page == 0
        )
        prev_button.callback = self._on_prev  # type: ignore[method-assign]
        self.add_item(prev_button)

        next_button = discord.ui.Button(
            label="Next ▶",
            style=discord.ButtonStyle.secondary,
            disabled=self._page >= total_pages - 1,
        )
        next_button.callback = self._on_next  # type: ignore[method-assign]
        self.add_item(next_button)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        self._page -= 1
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        self._page += 1
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        assert interaction.data is not None
        folder = interaction.data["values"][0]  # type: ignore[index]
        if folder == "__none__":
            await interaction.response.defer()
            return

        songs = self._library.songs_in(folder)
        view = SongBrowseView(
            folder, songs, self._library, self._player_manager, self._settings
        )
        embed = discord.Embed(
            title=f"📁 {folder}",
            description=f"{len(songs)} song(s) — pick one to play.",
            color=discord.Color.blurple(),
        )
        await interaction.response.edit_message(embed=embed, view=view)


class SongBrowseView(discord.ui.View):
    def __init__(
        self,
        folder: str,
        songs: list[Song],
        library: MusicLibrary,
        player_manager: PlayerManager,
        settings: Settings,
        page: int = 0,
    ) -> None:
        super().__init__(timeout=180)
        self._folder = folder
        self._songs = songs
        self._library = library
        self._player_manager = player_manager
        self._settings = settings
        self._page = page
        self._rebuild()

    def _rebuild(self) -> None:
        self.clear_items()
        total_pages = page_count(len(self._songs))
        self._page = max(0, min(self._page, total_pages - 1))
        page_items = paginate(self._songs, self._page)

        select = discord.ui.Select(
            placeholder=f"Choose a song… (page {self._page + 1}/{total_pages})",
            options=[
                discord.SelectOption(label=truncate(song.title), value=str(i))
                for i, song in enumerate(page_items)
            ]
            or [discord.SelectOption(label="No songs in this folder", value="__none__")],
            disabled=not page_items,
        )
        select.callback = self._make_select_callback(page_items)  # type: ignore[method-assign]
        self.add_item(select)

        back_button = discord.ui.Button(label="⬅ Back", style=discord.ButtonStyle.secondary)
        back_button.callback = self._on_back  # type: ignore[method-assign]
        self.add_item(back_button)

        prev_button = discord.ui.Button(
            label="◀ Prev", style=discord.ButtonStyle.secondary, disabled=self._page == 0
        )
        prev_button.callback = self._on_prev  # type: ignore[method-assign]
        self.add_item(prev_button)

        next_button = discord.ui.Button(
            label="Next ▶",
            style=discord.ButtonStyle.secondary,
            disabled=self._page >= total_pages - 1,
        )
        next_button.callback = self._on_next  # type: ignore[method-assign]
        self.add_item(next_button)

    async def _on_back(self, interaction: discord.Interaction) -> None:
        view = FolderBrowseView(self._library, self._player_manager, self._settings)
        embed = discord.Embed(
            title="🎶 Local library",
            description="Pick a folder to see the songs inside.",
            color=discord.Color.blurple(),
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        self._page -= 1
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        self._page += 1
        self._rebuild()
        await interaction.response.edit_message(view=self)

    def _make_select_callback(self, page_items: list[Song]):
        async def _callback(interaction: discord.Interaction) -> None:
            assert interaction.data is not None
            value = interaction.data["values"][0]  # type: ignore[index]
            if value == "__none__":
                await interaction.response.defer()
                return

            if not _check_dj(interaction, self._settings):
                await interaction.response.send_message(
                    f":no_entry: Only members with the **{self._settings.dj_role_name}** role can play music.",
                    ephemeral=True,
                )
                return

            channel = await _require_voice_channel(interaction)
            if channel is None:
                return

            song = page_items[int(value)]
            assert isinstance(interaction.guild, discord.Guild)
            player = self._player_manager.get_or_create(interaction.guild)
            track = Track(
                title=song.title,
                requested_by=str(interaction.user),
                local_path=song.path,
            )
            await interaction.response.send_message(
                f":inbox_tray: Queued **{song.title}**", ephemeral=True
            )
            await player.enqueue(track, channel, interaction.channel)

        return _callback
