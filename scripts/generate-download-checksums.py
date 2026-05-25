#!/usr/bin/env python3
"""Generate Ansible download_checksums vars from files/<arch>/SHA256SUMS."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required", file=sys.stderr)
    sys.exit(2)

CHECKSUM_KEY_BY_FILE_PREFIX = {
    "cfssl": "cfssl",
    "cfssljson": "cfssljson",
    "kubectl": "kubectl",
    "runc": "runc",
    "containerd.service": "containerd_service",
    "calico.yaml": "calico_manifest",
}


def key_for_file(filename: str) -> str | None:
    if filename in CHECKSUM_KEY_BY_FILE_PREFIX:
        return CHECKSUM_KEY_BY_FILE_PREFIX[filename]
    if filename.startswith("etcd-v") and filename.endswith(".tar.gz"):
        return "etcd"
    if filename.startswith("kubernetes-server-linux-") and filename.endswith(".tar.gz"):
        return "kubernetes_server"
    if filename.startswith("kubernetes-node-linux-") and filename.endswith(".tar.gz"):
        return "kubernetes_node"
    if filename.startswith("containerd-") and filename.endswith(".tar.gz"):
        return "containerd"
    if filename.startswith("cni-plugins-linux-") and filename.endswith(".tgz"):
        return "cni_plugins"
    return None


def parse_sha256sums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                raise ValueError(f"invalid SHA256SUMS line {line_no}: {raw_line!r}")
            digest, filename = parts
            filename = filename.lstrip("*")
            filename = Path(filename).name
            if len(digest) != 64:
                raise ValueError(f"invalid sha256 digest on line {line_no}: {digest}")
            key = key_for_file(filename)
            if key is None:
                continue
            checksums[key] = f"sha256:{digest}"
    return checksums


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch", default="amd64", help="Target architecture, default: amd64")
    parser.add_argument("--files-dir", default=None, help="Binary cache directory, default: files/<arch>")
    parser.add_argument("--output", default=None, help="Output vars file, default: inventories/group_vars/download-checksums-<arch>.yml")
    args = parser.parse_args()

    files_dir = Path(args.files_dir or f"files/{args.arch}")
    sha_file = files_dir / "SHA256SUMS"
    output = Path(args.output or f"inventories/group_vars/download-checksums-{args.arch}.yml")

    if not sha_file.exists():
        print(f"missing checksum file: {sha_file}", file=sys.stderr)
        return 1

    checksums = parse_sha256sums(sha_file)
    if not checksums:
        print(f"no recognized deploy artifact checksums found in {sha_file}", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "download_checksums": dict(sorted(checksums.items())),
    }
    with output.open("w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.safe_dump(payload, f, sort_keys=False)

    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
