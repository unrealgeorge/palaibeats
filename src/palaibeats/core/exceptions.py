"""Domain-specific exceptions, raised by the core/player layer and turned
into user-facing error messages by the cogs.
"""

from __future__ import annotations


class PalaiBeatsError(Exception):
    """Base class for all expected, user-facing errors."""


class NotInVoiceChannelError(PalaiBeatsError):
    """Raised when the invoking member is not in a voice channel."""


class NoActivePlayerError(PalaiBeatsError):
    """Raised when an action requires an active player but none exists."""


class NothingPlayingError(PalaiBeatsError):
    """Raised when a control action is used but nothing is playing."""


class FolderNotFoundError(PalaiBeatsError):
    """Raised when a requested local-library folder does not exist."""


class TrackResolutionError(PalaiBeatsError):
    """Raised when a link/query could not be resolved to a playable source."""


class StationNotFoundError(PalaiBeatsError):
    """Raised when a radio station name is not in the database."""


class StationAlreadyExistsError(PalaiBeatsError):
    """Raised when adding a radio station whose name is already taken."""


class PermissionDeniedError(PalaiBeatsError):
    """Raised when a member without the DJ role attempts a control action."""
