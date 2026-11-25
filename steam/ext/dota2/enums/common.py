"""Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ....enums import IntEnum, classproperty

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Self

__all__ = (
    "GameMode",
    "LobbyType",
    "MatchOutcome",
    "RankTier",
)


class GameMode(IntEnum):  # source: dota_shared_enums.proto
    NONE = 0
    AllPick = 1
    CaptainsMode = 2
    RandomDraft = 3
    SingleDraft = 4
    AllRandom = 5
    Intro = 6
    Diretide = 7
    ReverseCaptainsMode = 8
    Frostivus = 9
    Tutorial = 10
    MidOnly = 11
    LeastPlayed = 12
    NewPlayerMode = 13
    CompendiumMatch = 14
    Custom = 15
    CaptainsDraft = 16
    BalancedDraft = 17
    AbilityDraft = 18
    Event = 19
    AllRandomDeathMatch = 20
    Mid1v1 = 21
    AllDraft = 22
    Turbo = 23
    Mutation = 24
    CoachesChallenge = 25

    @classproperty
    def DISPLAY_NAMES(cls: type[Self]) -> Mapping[GameMode, str]:  # type: ignore
        return {
            cls.NONE: "None",
            cls.AllPick: "All Pick",
            cls.CaptainsMode: "Captain's Mode",
            cls.RandomDraft: "Random Draft",
            cls.SingleDraft: "Single Draft",
            cls.AllRandom: "All Random",
            cls.Intro: "Intro",
            cls.Diretide: "Diretide",
            cls.ReverseCaptainsMode: "Reverse Captain's Mode",
            cls.Frostivus: "Frostivus",  # XMAS, The Greeviling
            cls.Tutorial: "Tutorial",
            cls.MidOnly: "Mid Only",
            cls.LeastPlayed: "Least Played",
            cls.NewPlayerMode: "New Player Mode",
            cls.CompendiumMatch: "Compendium Match",
            cls.Custom: "Custom Game",
            cls.CaptainsDraft: "Captain's Draft",
            cls.BalancedDraft: "Balanced Draft",
            cls.AbilityDraft: "Ability Draft",
            cls.Event: "Event Game",
            cls.AllRandomDeathMatch: "All Random DeathMatch",
            cls.Mid1v1: "1v1 Mid Only",
            cls.AllDraft: "All Draft",  # Ranked Matchmaking
            cls.Turbo: "Turbo",
            cls.Mutation: "Mutation",
            cls.CoachesChallenge: "Coaches Challenge",
        }

    @property
    def display_name(self) -> str:
        return self.DISPLAY_NAMES[self]


class LobbyType(IntEnum):  # source: dota_gcmessages_common_lobby.proto
    Invalid = -1
    Unranked = 0
    Practice = 1
    CoopBotMatch = 4
    Ranked = 7
    BattleCup = 9
    LocalBotMatch = 10
    Spectator = 11
    EventGameMode = 12
    NewPlayerMode = 14
    FeaturedGameMode = 15

    @classproperty
    def DISPLAY_NAMES(cls: type[Self]) -> Mapping[LobbyType, str]:  # type: ignore
        return {
            cls.Invalid: "Invalid",
            cls.Unranked: "Unranked",
            cls.Practice: "Practice",
            cls.CoopBotMatch: "Coop Bots",
            cls.Ranked: "Ranked",
            cls.BattleCup: "Battle Cup",
            cls.LocalBotMatch: "Local Bot Match",
            cls.Spectator: "Spectator",
            cls.EventGameMode: "Event",
            cls.NewPlayerMode: "New Player Mode",
            cls.FeaturedGameMode: "Featured Gamemode",
        }

    @property
    def display_name(self) -> str:
        return self.DISPLAY_NAMES[self]


class RankTier(IntEnum):
    """Enum representing Dota 2 Rank Tier.

    Commonly called "ranked medals".
    """

    Uncalibrated = 0
    Herald1 = 11
    Herald2 = 12
    Herald3 = 13
    Herald4 = 14
    Herald5 = 15
    Guardian1 = 21
    Guardian2 = 22
    Guardian3 = 23
    Guardian4 = 24
    Guardian5 = 25
    Crusader1 = 31
    Crusader2 = 32
    Crusader3 = 33
    Crusader4 = 34
    Crusader5 = 35
    Archon1 = 41
    Archon2 = 42
    Archon3 = 43
    Archon4 = 44
    Archon5 = 45
    Legend1 = 51
    Legend2 = 52
    Legend3 = 53
    Legend4 = 54
    Legend5 = 55
    Ancient1 = 61
    Ancient2 = 62
    Ancient3 = 63
    Ancient4 = 64
    Ancient5 = 65
    Divine1 = 71
    Divine2 = 72
    Divine3 = 73
    Divine4 = 74
    Divine5 = 75
    Immortal = 80

    @property
    def division(self) -> str:
        """Medal name without the stars, e.g. ``"Herald"`` for ``Herald3``."""
        return self.name.rstrip("0123456789")

    @property
    def stars(self) -> int:
        """Number of stars on the medal, ``0`` for ``Uncalibrated`` and ``Immortal``."""
        return self.value % 10

    @property
    def display_name(self) -> str:
        """Medal name with the stars, e.g. ``"Herald 3"`` for ``Herald3``."""
        suffix = f" {self.stars}" if self.stars else ""
        return self.division + suffix


class MatchOutcome(IntEnum):  # source: dota_shared_enums.proto
    """Represents Match Outcome."""

    Unknown = 0
    RadiantVictory = 2
    DireVictory = 3
    NeutralVictory = 4
    NoTeamWinner = 5
    Custom1Victory = 6
    Custom2Victory = 7
    Custom3Victory = 8
    Custom4Victory = 9
    Custom5Victory = 10
    Custom6Victory = 11
    Custom7Victory = 12
    Custom8Victory = 13
    NotScoredPoorNetworkConditions = 64
    NotScoredLeaver = 65
    NotScoredServerCrash = 66
    NotScoredNeverStarted = 67
    NotScoredCanceled = 68
    NotScoredSuspicious = 69
