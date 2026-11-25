"""Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...errors import SteamException

if TYPE_CHECKING:
    from .protobufs.client_messages import ProfileResponseEResponse

__all__ = (
    "Dota2Exception",
    "GCRequestFailed",
    "MatchNotFound",
    "ProfileUnavailable",
)


class Dota2Exception(SteamException):
    """Base exception for errors raised by ``steam.ext.dota2``.

    Subclass of :exc:`steam.SteamException`.
    """


class GCRequestFailed(Dota2Exception):
    """Exception raised when the Dota 2 Game Coordinator answers a request with an error.

    Subclass of :exc:`Dota2Exception`.
    """

    def __init__(self, response: Any, message: str | None = None) -> None:
        self.response = response
        """The protobuf message the Game Coordinator answered with."""
        super().__init__(message or f"The Game Coordinator answered {type(response).__name__} with an error")


class MatchNotFound(GCRequestFailed):
    """Exception raised when the Game Coordinator has no data about a match.

    This happens for wrong ids, but also for matches that are still live, or practice lobbies that leave no record.

    Subclass of :exc:`GCRequestFailed`.
    """

    def __init__(self, response: Any, *, match_id: int | None = None, lobby_id: int | None = None) -> None:
        self.match_id = match_id
        """The id of the match that wasn't found, if it was looked up by match id."""
        self.lobby_id = lobby_id
        """The lobby id of the live match that wasn't found, if it was looked up by lobby id."""
        what = f"match {match_id}" if match_id is not None else f"live match with lobby id {lobby_id}"
        super().__init__(response, f"The Game Coordinator has no data about the {what}")


class ProfileUnavailable(GCRequestFailed):
    """Exception raised when the Game Coordinator refuses to give a Dota 2 profile.

    Limited Steam accounts get this for every profile but their own.

    Subclass of :exc:`GCRequestFailed`.
    """

    def __init__(self, response: Any, *, account_id: int, reason: ProfileResponseEResponse) -> None:
        self.account_id = account_id
        """The account id of the profile that was requested."""
        self.reason = reason
        """Why the Game Coordinator refused, e.g. ``TooBusy``."""
        super().__init__(response, f"The Game Coordinator refused the profile of {account_id} ({reason.name})")
