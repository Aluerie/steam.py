"""Hatch build hook that writes ``steam/__metadata__.py`` with the package version.

Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

RELEASE_LEVELS = {
    "a": "alpha",
    "b": "beta",
    "rc": "candidate",
}

TEMPLATE = """\
from typing import Final, Literal, NamedTuple

__all__ = (
    "__title__",
    "__author__",
    "__license__",
    "__version__",
    "version_info",
)


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]


__title__: Final = "steam"
__author__: Final = "Gobot1234"
__license__: Final = "MIT"
__version__: Final = "{version}"
version_info: Final = VersionInfo(major={major}, minor={minor}, micro={micro}, releaselevel="{release_level}")
"""


def render_metadata(version: str, root: Path) -> str:
    """Return the source of ``steam/__metadata__.py`` for ``version``.

    Pre-release versions get the git commit count and short hash appended when ``root`` is a git checkout.
    """
    try:
        end_char: str = re.findall(r"\d+.\d+.\d+([^\d]+).*", version)[0]
    except IndexError:
        release_level = "final"
        end_char = " "  # if this was empty, str.split would raise a ValueError
    else:
        release_level = RELEASE_LEVELS[end_char]
        try:
            commit_count = subprocess.check_output(["git", "rev-list", "--count", "HEAD"], cwd=root, text=True).strip()
            commit_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            pass
        else:
            if commit_count and commit_hash:
                version = f"{version}{commit_count}+g{commit_hash}"

    major, minor, micro = version.split(".", maxsplit=2)
    micro = micro.split(end_char, maxsplit=1)[0]
    return TEMPLATE.format(version=version, major=major, minor=minor, micro=micro, release_level=release_level)


class CustomBuildHook(BuildHookInterface):  # pyright: ignore[reportMissingTypeArgument]
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        root = Path(self.root)
        project_version: str = self.metadata.version  # pyright: ignore[reportUnknownMemberType]
        (root / "steam" / "__metadata__.py").write_text(
            render_metadata(project_version, root), encoding="utf-8", newline="\n"
        )
