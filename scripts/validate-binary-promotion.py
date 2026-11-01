#!/usr/bin/env python3
"""Validate a completed, full and strictly checked build before proposing a binary PR.

This script reads only downloaded artifacts. It does not write to Git, invoke
infrastructure commands, or grant permission to publish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import runpy
import sys
from pathlib import Path

import yaml


HEX_SHA = re.compile(r"^[0-9a-f]{40}$")
HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
ARCHES = {"amd64", "arm64"}


def verify(root: Path, arch: str, run_id: int, attempt: int, sha: str) -> None:
    if arch not in ARCHES:
        raise ValueError(f"unsupported architecture: {arch!r}")
    if not HEX_SHA.fullmatch(sha):
        raise ValueError("invalid build source SHA")
    if run_id < 1 or attempt < 1:
        raise ValueError("invalid workflow run identifier")

    marker_path = root / "metadata" / "binary-promotion.json"
    expected = {
        "schema_version": 1,
        "source_mode": "source",
        "stage": "all",
        "strict_package": True,
        "arch": arch,
        "source_sha": sha,
        "run_id": run_id,
        "run_attempt": attempt,
    }
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if type(marker) is not dict or marker != expected:
        raise ValueError("promotion marker mismatches trusted workflow identity")

    cache = root / "files" / arch
    sums = cache / "SHA256SUMS"
    ansible_checksums = (
        root / "inventories" / "group_vars" / f"download-checksums-{arch}.yml"
    )
    if not cache.is_dir() or not sums.is_file() or not ansible_checksums.is_file():
        raise ValueError("candidate is missing its architecture files or checksums")

    allowed_extra = {
        Path("metadata/binary-promotion.json"),
        Path(f"inventories/group_vars/download-checksums-{arch}.yml"),
    }
    files_prefix = ("files", arch)
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ValueError(f"candidate contains symlink: {item.relative_to(root)}")
        if item.is_file():
            rel = item.relative_to(root)
            if rel not in allowed_extra and rel.parts[:2] != files_prefix:
                raise ValueError(f"unexpected file outside target architecture: {rel}")

    entries: dict[str, str] = {}
    for line in sums.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        if "  ./" not in line:
            raise ValueError("non-relative or malformed SHA256SUMS entry")
        digest, filename = line.split("  ./", maxsplit=1)
        if not HEX_DIGEST.fullmatch(digest):
            raise ValueError("invalid SHA256SUMS digest")
        parts = Path(filename).parts
        if not parts or any(part in {".", ".."} for part in parts):
            raise ValueError("invalid checksummed path")
        if filename in entries:
            raise ValueError(f"duplicate checksummed file: {filename}")
        entries[filename] = digest

    actual_paths = {
        p.relative_to(cache).as_posix()
        for p in cache.rglob("*")
        if p.is_file() and p != sums
    }
    if not entries or set(entries) != actual_paths:
        raise ValueError("SHA256SUMS does not cover exactly the delivered files")

    for name, digest in entries.items():
        hasher = hashlib.sha256()
        with (cache / name).open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                hasher.update(block)
        if hasher.hexdigest() != digest:
            raise ValueError(f"checksum mismatch: {name}")

    # Reuse the project's canonical Ansible checksum mapping rather than
    # silently duplicating file-to-key translation in promotion logic.
    checksum_tool = Path(__file__).with_name("generate-download-checksums.py")
    checksum_functions = runpy.run_path(str(checksum_tool))
    from_sha_file = checksum_functions["parse_sha256sums"](sums)
    provided = yaml.safe_load(ansible_checksums.read_text(encoding="utf-8"))
    if provided != {"download_checksums": dict(sorted(from_sha_file.items()))}:
        raise ValueError("Ansible download-checksums do not match SHA256SUMS")

    print(f"Verified {len(entries)} files for {arch}, run {run_id}, source {sha}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--arch", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--run-attempt", required=True, type=int)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    try:
        verify(
            root=args.root,
            arch=args.arch,
            run_id=args.run_id,
            attempt=args.run_attempt,
            sha=args.source_sha,
        )
    except (ValueError, OSError, KeyError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"Binary promotion rejected: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
