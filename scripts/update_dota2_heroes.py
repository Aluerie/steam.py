"""
A script to sync the Dota 2 ``Hero`` enum with Valve's datafeed hero list.

New heroes get a member name derived from their English name; existing member names are never changed.
Display names and NPC names of existing heroes are refreshed from the datafeed.
Heroes missing from the datafeed are kept as they are.

Prints a short summary of the changes as Markdown (empty when nothing changed).

Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Final, NamedTuple

ROOT: Final = Path(__file__).parent
ENUMS_FILE: Final = ROOT.parent / "steam" / "ext" / "dota2" / "enums.py"
HERO_LIST_URL: Final = "https://www.dota2.com/datafeed/herolist?language=english"

MEMBER_RE: Final = re.compile(r"^    (\w+) = (\d+)$")
DISPLAY_RE: Final = re.compile(r'^            cls\.(\w+): "(.*?)",(?:  # .*)?$')
NPC_RE: Final = re.compile(r'^            cls\.(\w+): "(npc_dota_hero_\w+)",$')


class HeroInfo(NamedTuple):
    member: str
    display_name: str
    npc_name: str


def fetch_heroes() -> dict[int, tuple[str, str]]:
    """Return ``{hero_id: (english_name, npc_name)}`` from the datafeed."""
    request = urllib.request.Request(HERO_LIST_URL, headers={"User-Agent": "steam.py hero updater"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    heroes = data["result"]["data"]["heroes"]
    if not heroes:
        raise RuntimeError("Datafeed returned an empty hero list")
    return {hero["id"]: (hero["name_english_loc"], hero["name"]) for hero in heroes}


def member_name(display_name: str) -> str:
    """Turn ``"Keeper of the Light"`` into ``"KeeperOfTheLight"``."""
    words = re.split(r"[^0-9A-Za-z]+", display_name.replace("'", ""))
    name = "".join(word[:1].upper() + word[1:] for word in words if word)
    if not name.isidentifier():
        raise ValueError(f"Can't make an enum member name out of {display_name!r}")
    return name


def find_block(lines: list[str], start: int, pattern: re.Pattern[str]) -> tuple[int, int]:
    """Return ``(first, last + 1)`` of the first run of lines matching ``pattern`` at or after ``start``."""
    first = next(i for i in range(start, len(lines)) if pattern.match(lines[i]))
    last = first
    while last < len(lines) and pattern.match(lines[last]):
        last += 1
    return first, last


def main() -> None:
    lines = ENUMS_FILE.read_bytes().decode().split("\n")
    class_start = lines.index("class Hero(IntEnum):")

    members_span = find_block(lines, class_start, MEMBER_RE)
    display_start = lines.index("    def DISPLAY_NAMES(cls: type[Self]) -> Mapping[Hero, str]:  # type: ignore", class_start)
    display_span = find_block(lines, display_start, DISPLAY_RE)
    npc_start = lines.index("    def NPC_NAMES(cls: type[Self]) -> Mapping[Hero, str]:  # type: ignore", class_start)
    npc_span = find_block(lines, npc_start, NPC_RE)

    members = {int(m[2]): m[1] for m in map(MEMBER_RE.match, lines[slice(*members_span)]) if m}
    display_names = {m[1]: m[2] for m in map(DISPLAY_RE.match, lines[slice(*display_span)]) if m and m[1] != "NONE"}
    npc_names = {m[1]: m[2] for m in map(NPC_RE.match, lines[slice(*npc_span)]) if m}
    # keep the special NONE entry (and its comment) as it is
    none_display_line = next(line for line in lines[slice(*display_span)] if line.startswith("            cls.NONE:"))

    heroes = {
        hero_id: HeroInfo(member, display_names[member], npc_names[member])
        for hero_id, member in members.items()
        if hero_id != 0
    }

    changes: list[str] = []
    for hero_id, (english_name, npc_name) in sorted(fetch_heroes().items()):
        old = heroes.get(hero_id)
        if old is None:
            new = HeroInfo(member_name(english_name), english_name, npc_name)
            if any(info.member == new.member for info in heroes.values()):
                raise ValueError(f"Member name {new.member!r} for hero {hero_id} is already taken")
            changes.append(f"- Added `Hero.{new.member} = {hero_id}` ({english_name}, `{npc_name}`)")
        else:
            new = old._replace(display_name=english_name, npc_name=npc_name)
            if old.display_name != new.display_name:
                changes.append(f"- `Hero.{old.member}` display name: {old.display_name!r} -> {new.display_name!r}")
            if old.npc_name != new.npc_name:
                changes.append(f"- `Hero.{old.member}` NPC name: `{old.npc_name}` -> `{new.npc_name}`")
        heroes[hero_id] = new

    if not changes:
        return

    ordered = sorted(heroes.items())
    new_members = ["    NONE = 0", *(f"    {info.member} = {hero_id}" for hero_id, info in ordered)]
    new_display = [
        none_display_line,
        *(f"            cls.{info.member}: {json.dumps(info.display_name, ensure_ascii=False)}," for _, info in ordered),
    ]
    new_npc = [f'            cls.{info.member}: "{info.npc_name}",' for _, info in ordered]

    # replace from the bottom up so earlier spans stay valid
    for span, block in sorted(
        [(members_span, new_members), (display_span, new_display), (npc_span, new_npc)], reverse=True
    ):
        lines[slice(*span)] = block

    source = "\n".join(lines)
    compile(source, str(ENUMS_FILE), "exec")
    ENUMS_FILE.write_bytes(source.encode())
    sys.stdout.write("\n".join(changes) + "\n")


if __name__ == "__main__":
    main()
