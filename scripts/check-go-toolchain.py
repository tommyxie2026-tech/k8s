#!/usr/bin/env python3
"""Check selected builder Go release against pinned component source requirements."""
from __future__ import annotations
from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "repo/sources.yml"
ACTION = ROOT / ".github/actions/prepare-binaries/action.yml"

def semver(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError(f"Expected Go version x.y.z; got {value!r}")
    return tuple(map(int, value.split(".")))

def main() -> int:
    sources = yaml.safe_load(SOURCES.read_text())
    action = yaml.safe_load(ACTION.read_text())
    builder_versions = [
        x.get("with", {}).get("go-version")
        for x in action["runs"]["steps"]
        if x.get("uses", "").startswith("actions/setup-go@")
    ]
    if len(builder_versions) != 1:
        raise ValueError(f"Expected a single pinned setup-go step; got {builder_versions!r}")
    builder = semver(builder_versions[0])
    for component in sources["components"]:
        name = component["component"]
        minimum = semver(component["go_minimum"])
        if builder < minimum:
            raise ValueError(
                f"{name} requires Go >= {component['go_minimum']} "
                f"but builder is {builder_versions[0]}"
            )
    print(f"Go toolchain validation passed: {builder_versions[0]}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, TypeError) as exc:
        print(f"Go toolchain validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
