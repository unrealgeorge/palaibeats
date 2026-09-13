"""A tiny FIFO track queue. Not asyncio-locked on purpose — all mutation
happens from the event loop thread; the only cross-thread entry point
(discord.py's `after=` playback callback) hands off via
`loop.call_soon_threadsafe` / `run_coroutine_threadsafe` before touching it.
"""

from __future__ import annotations

from collections import deque

from palaibeats.player.models import Track


class TrackQueue:
    def __init__(self) -> None:
        self._items: deque[Track] = deque()

    def push(self, track: Track) -> None:
        self._items.append(track)

    def pop_next(self) -> Track | None:
        return self._items.popleft() if self._items else None

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)

    def as_list(self) -> list[Track]:
        return list(self._items)
