# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: dota_gcmessages_common_lobby.proto
# plugin: python-betterproto

from __future__ import annotations

from typing import TYPE_CHECKING

from ....enums import classproperty, IntEnum

if TYPE_CHECKING:
    from collections.abc import Mapping

    from typing_extensions import Self


# fmt: off
class CSODOTALobbyLobbyType(IntEnum):
    INVALID           = -1
    CASUAL_MATCH      = 0
    PRACTICE          = 1
    COOP_BOT_MATCH    = 4
    COMPETITIVE_MATCH = 7
    WEEKEND_TOURNEY   = 9
    LOCAL_BOT_MATCH   = 10
    SPECTATOR         = 11
    EVENT_MATCH       = 12
    NEW_PLAYER_POOL   = 14
    FEATURED_GAMEMODE = 15

    @classproperty
    def DISPLAY_NAMES(cls: type[Self]) -> Mapping[CSODOTALobbyLobbyType, str]:  # type: ignore
        return {
            cls.INVALID           : 'Invalid',
            cls.CASUAL_MATCH      : 'Unranked',
            cls.PRACTICE          : 'Practice',
            cls.COOP_BOT_MATCH    : 'Coop Bots',
            cls.COMPETITIVE_MATCH : 'Ranked',
            cls.WEEKEND_TOURNEY   : 'Battle Cup',
            cls.LOCAL_BOT_MATCH   : 'Local Bot Match',
            cls.SPECTATOR         : 'Spectator',
            cls.EVENT_MATCH       : 'Event',
            cls.NEW_PLAYER_POOL   : 'New Player Mode',
            cls.FEATURED_GAMEMODE : 'Featured Gamemode',
        }

    @property
    def display_name(self) -> str:
        return self.DISPLAY_NAMES[self]
# fmt: on
