# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: dota_shared_enums.proto
# plugin: python-betterproto

from __future__ import annotations

from typing import TYPE_CHECKING

from ....enums import IntEnum, classproperty

if TYPE_CHECKING:
    from collections.abc import Mapping

    from typing_extensions import Self


# fmt: off
class DOTAGameMode(IntEnum):
    NONE              = 0
    AP                = 1
    CM                = 2
    RD                = 3
    SD                = 4
    AR                = 5
    INTRO             = 6
    HW                = 7
    REVERSE_CM        = 8
    XMAS              = 9
    TUTORIAL          = 10
    MO                = 11
    LP                = 12
    POOL1             = 13
    FH                = 14
    CUSTOM            = 15
    CD                = 16
    BD                = 17
    ABILITY_DRAFT     = 18
    EVENT             = 19
    ARDM              = 20
    MID1V1            = 21
    ALL_DRAFT         = 22
    TURBO             = 23
    MUTATION          = 24
    COACHES_CHALLENGE = 25

    @classproperty
    def DISPLAY_NAMES(cls: type[Self]) -> Mapping[DOTAGameMode, str]:  # type: ignore
        return {
                cls.NONE             : "None",
                cls.AP               : "All Pick",
                cls.CM               : "Captains Mode",
                cls.RD               : "Random Draft",
                cls.SD               : "Single Draft",
                cls.AR               : "All Random",
                cls.INTRO            : "Intro",
                cls.HW               : "Diretide",
                cls.REVERSE_CM       : "Reverse Captains Mode",
                cls.XMAS             : "Frostivus",
                cls.TUTORIAL         : "Tutorial",
                cls.MO               : "Mid Only",
                cls.LP               : "Least Played",
                cls.POOL1            : "New Player Mode",
                cls.FH               : "Compendium Match",
                cls.CUSTOM           : "Custom Game",
                cls.CD               : "Captains Draft",
                cls.BD               : "Balanced Draft",
                cls.ABILITY_DRAFT    : "Ability Draft",
                cls.EVENT            : "Event Game",
                cls.ARDM             : "All Random DeathMatch",
                cls.MID1V1           : "1v1 Mid Only",
                cls.ALL_DRAFT        : "All Pick",
                cls.TURBO            : "Turbo",
                cls.MUTATION         : "Mutation",
                cls.COACHES_CHALLENGE: "Coaches Challenge",
        }

    @property
    def display_name(self) -> str:
        return self.DISPLAY_NAMES[self]
