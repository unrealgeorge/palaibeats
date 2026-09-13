"""Per-guild playback state machine.

One `GuildPlayer` per Discord server. It owns the voice connection and
switches between two mutually-exclusive modes:

  * QUEUE  — local files and/or resolved links, played in order.
  * RADIO  — a single continuous stream, auto-reconnected on drops.

Mode transitions are guarded by checking `self.mode` from inside the
`after=` callbacks discord.py invokes (on a *different* thread) when a
source finishes or errors — this is what stops a stale radio reconnect
from firing after the user has switched to queue playback, and vice
versa, without needing extra locks.
"""

from __future__ import annotations

import asyncio
import logging

import discord

from palaibeats.config import Settings
from palaibeats.core import audio
from palaibeats.core.database import Database, RadioStation
from palaibeats.core.exceptions import NothingPlayingError
from palaibeats.player.models import PlayerMode, Track
from palaibeats.player.queue import TrackQueue

logger = logging.getLogger(__name__)


class GuildPlayer:
    def __init__(
        self,
        guild: discord.Guild,
        bot: discord.Client,
        settings: Settings,
        db: Database,
    ) -> None:
        self.guild = guild
        self.bot = bot
        self.settings = settings
        self.db = db

        self.queue = TrackQueue()
        self.mode: PlayerMode = PlayerMode.IDLE
        self.voice_client: discord.VoiceClient | None = None
        self.current_track: Track | None = None
        self.current_station: RadioStation | None = None
        self.text_channel: discord.abc.Messageable | None = None
        self.volume: float = settings.default_volume
        self.loop_current: bool = False

        self._idle_disconnect_task: asyncio.Task | None = None

    # ---- connection -------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self.voice_client is not None and self.voice_client.is_connected()

    async def connect(self, channel: discord.VoiceChannel) -> None:
        if self.voice_client is not None and self.voice_client.is_connected():
            if self.voice_client.channel.id != channel.id:
                await self.voice_client.move_to(channel)
            return
        self.voice_client = await channel.connect()

    async def disconnect(self) -> None:
        self._cancel_idle_task()
        self.queue.clear()
        self.mode = PlayerMode.IDLE
        self.current_track = None
        self.current_station = None
        if self.voice_client is not None:
            await self.voice_client.disconnect(force=True)
            self.voice_client = None

    # ---- queue mode ---------------------------------------------------------

    async def enqueue(
        self,
        track: Track,
        channel: discord.VoiceChannel,
        text_channel: discord.abc.Messageable,
    ) -> bool:
        """Adds `track` to the queue and (re)starts playback if the player
        was idle or in radio mode. Returns True if this call caused
        immediate playback to start."""

        await self.connect(channel)
        self.text_channel = text_channel
        self.queue.push(track)

        already_playing_queue = self.mode == PlayerMode.QUEUE and (
            self.voice_client.is_playing() or self.voice_client.is_paused()
        )
        if not already_playing_queue:
            await self._play_next()
            return True
        return False

    async def _play_next(self) -> None:
        assert self.voice_client is not None

        if self.loop_current and self.current_track is not None:
            next_track = self.current_track
        else:
            next_track = self.queue.pop_next()

        if next_track is None:
            self.mode = PlayerMode.IDLE
            self.current_track = None
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()
            self._evaluate_idle()
            return

        self.mode = PlayerMode.QUEUE
        self.current_track = next_track

        try:
            if next_track.is_local:
                assert next_track.local_path is not None
                source = audio.build_local_source(
                    next_track.local_path, self.volume, self.settings.ffmpeg_executable
                )
            else:
                assert next_track.stream_url is not None
                source = audio.build_stream_source(
                    next_track.stream_url,
                    self.volume,
                    self.settings.ffmpeg_executable,
                    next_track.http_headers,
                )
        except Exception:
            logger.exception("Failed to build audio source for %r", next_track.title)
            await self._notify(f":warning: Skipping **{next_track.title}** — could not start playback.")
            await self._play_next()
            return

        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()

        self.voice_client.play(source, after=self._make_queue_after_callback())
        self._evaluate_idle()
        await self._notify(f":arrow_forward: Now playing **{next_track.title}**")

    def _make_queue_after_callback(self):
        loop = self.bot.loop

        def _after(error: Exception | None) -> None:
            if error:
                logger.error("Playback error: %s", error)
            if self.mode != PlayerMode.QUEUE:
                return  # superseded by a mode switch (e.g. /radio, /stop)
            asyncio.run_coroutine_threadsafe(self._play_next(), loop)

        return _after

    async def skip(self) -> None:
        if self.voice_client is None or not (
            self.voice_client.is_playing() or self.voice_client.is_paused()
        ):
            raise NothingPlayingError()
        self.loop_current = False
        self.voice_client.stop()  # the after-callback advances the queue

    async def stop(self) -> None:
        self.queue.clear()
        self.current_track = None
        self.current_station = None
        self.mode = PlayerMode.IDLE
        self.loop_current = False
        if self.voice_client is not None and (
            self.voice_client.is_playing() or self.voice_client.is_paused()
        ):
            self.voice_client.stop()
        self._evaluate_idle()

    async def pause(self) -> None:
        if self.voice_client is None or not self.voice_client.is_playing():
            raise NothingPlayingError()
        self.voice_client.pause()

    async def resume(self) -> None:
        if self.voice_client is None or not self.voice_client.is_paused():
            raise NothingPlayingError()
        self.voice_client.resume()

    async def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(2.0, volume))
        if self.voice_client is not None and isinstance(
            self.voice_client.source, discord.PCMVolumeTransformer
        ):
            self.voice_client.source.volume = self.volume
        await self.db.set_last_volume(self.guild.id, self.volume)

    def toggle_loop(self) -> bool:
        self.loop_current = not self.loop_current
        return self.loop_current

    # ---- radio mode -----------------------------------------------------

    async def play_radio(
        self,
        station: RadioStation,
        channel: discord.VoiceChannel,
        text_channel: discord.abc.Messageable,
    ) -> None:
        await self.connect(channel)
        self.text_channel = text_channel
        self.queue.clear()
        self.current_track = None
        self.loop_current = False
        self.mode = PlayerMode.RADIO
        self.current_station = station
        await self._start_radio_stream()
        self._evaluate_idle()

    async def _start_radio_stream(self) -> None:
        assert self.voice_client is not None
        assert self.current_station is not None

        source = audio.build_stream_source(
            self.current_station.url, self.volume, self.settings.ffmpeg_executable
        )

        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()

        self.voice_client.play(source, after=self._make_radio_after_callback())
        await self._notify(f":radio: Now streaming **{self.current_station.name}**")

    def _make_radio_after_callback(self):
        loop = self.bot.loop

        def _after(error: Exception | None) -> None:
            station_name = self.current_station.name if self.current_station else "?"
            if error:
                logger.warning("Radio stream %r dropped: %s", station_name, error)
            if self.mode != PlayerMode.RADIO:
                return  # superseded by a mode switch (e.g. /play, /stop)
            asyncio.run_coroutine_threadsafe(self._reconnect_radio(), loop)

        return _after

    async def _reconnect_radio(self, delay: float = 3.0) -> None:
        await asyncio.sleep(delay)
        if self.mode != PlayerMode.RADIO or self.current_station is None:
            return
        logger.info("Reconnecting radio stream: %s", self.current_station.name)
        await self._start_radio_stream()

    # ---- idle auto-disconnect ---------------------------------------------

    def _evaluate_idle(self) -> None:
        if not self.is_connected:
            self._cancel_idle_task()
            return
        assert self.voice_client is not None
        humans_present = any(not m.bot for m in self.voice_client.channel.members)
        should_idle = self.mode == PlayerMode.IDLE or not humans_present
        if should_idle:
            self._start_idle_disconnect_countdown()
        else:
            self._cancel_idle_task()

    def _start_idle_disconnect_countdown(self) -> None:
        if self._idle_disconnect_task is not None:
            return
        if self.settings.idle_timeout_seconds <= 0:
            return
        self._idle_disconnect_task = self.bot.loop.create_task(
            self._idle_disconnect_after_delay()
        )

    def _cancel_idle_task(self) -> None:
        if self._idle_disconnect_task is not None:
            self._idle_disconnect_task.cancel()
            self._idle_disconnect_task = None

    async def _idle_disconnect_after_delay(self) -> None:
        try:
            await asyncio.sleep(self.settings.idle_timeout_seconds)
        except asyncio.CancelledError:
            return
        self._idle_disconnect_task = None
        if not self.is_connected:
            return
        assert self.voice_client is not None
        humans_present = any(not m.bot for m in self.voice_client.channel.members)
        if self.mode == PlayerMode.IDLE or not humans_present:
            logger.info("Idle timeout reached for guild %s — disconnecting", self.guild.id)
            await self._notify(":zzz: Leaving the voice channel — idle for a while.")
            await self.disconnect()

    def on_voice_state_update(self) -> None:
        """Called by the bot's global voice-state listener whenever
        someone joins/leaves a channel in this guild."""

        self._evaluate_idle()

    # ---- misc ---------------------------------------------------------------

    async def _notify(self, message: str) -> None:
        if self.text_channel is None:
            return
        try:
            await self.text_channel.send(message)
        except discord.HTTPException:
            logger.debug("Failed to send player notification", exc_info=True)

    def now_playing_label(self) -> str | None:
        if self.mode == PlayerMode.RADIO and self.current_station is not None:
            return f"📻 {self.current_station.name}"
        if self.mode == PlayerMode.QUEUE and self.current_track is not None:
            return f"🎵 {self.current_track.title}"
        return None
