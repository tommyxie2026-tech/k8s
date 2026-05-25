#!/usr/bin/env python3
"""Validate repo/sources.yml without cloning or building upstream repositories."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("PyYAML is required", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "repo" / "sources.yml"

REQUIRED_COMPONENTS = {
    "kubernetes",
    "etcd",
    "containerd",
    "runc",
    "cni-plugins",
    "cfssl",
}

REQUIRED_MANIFESTS = {
    "calico",
}

REQUIRED_DEPLOY_OUTPUTS = {
    "cfssl",
    "cfssljson",
    "kubectl",
    "kube-apiserver",
    "kube-controller-manager",
    "kube-scheduler",
    "kubelet",
    "kube-proxy",
    "etcd",
    "etcdctl",
    "containerd",
    "containerd-shim-runc-v2",
    "ctr",
    "runc",
}

COMPONENT_REQUIRED_FIELDS = {
    "component",
    "version",
    "git",
    "tag",
    "build",
    "outputs",
}

BUILD_REQUIRED_FIELDS = {
    "type",
    "command",
}

TAG_PATTERN = re.compile(r"^v?\d+\.\d+\.\d+([-.+][A-Za-z0-9_.-]+)?$")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_component(item: dict[str, Any], errors: list[str], output_names: set[str]) -> None:
    component = item.get("component", "<unknown>")

    missing = COMPONENT_REQUIRED_FIELDS - set(item.keys())
    if missing:
        error(errors, f"component {component}: missing required fields: {sorted(missing)}")

    if not isinstance(item.get("component"), str) or not item.get("component"):
        error(errors, f"component {component}: component must be a non-empty string")

    if not isinstance(item.get("version"), str) or not item.get("version"):
        error(errors, f"component {component}: version must be a non-empty string")

    tag = item.get("tag")
    if not isinstance(tag, str) or not tag:
        error(errors, f"component {component}: tag must be a non-empty string")
    elif not TAG_PATTERN.match(tag):
        error(errors, f"component {component}: tag {tag!r} does not look like a release tag")

    git_url = item.get("git")
    if not isinstance(git_url, str) or not git_url:
        error(errors, f"component {component}: git must be a non-empty string")
    elif not (git_url.startswith("https://") or git_url.startswith("git@") or git_url.startswith("ssh://")):
        error(errors, f"component {component}: git URL should be https://, ssh://, or git@")

    build = item.get("build")
    if not isinstance(build, dict):
        error(errors, f"component {component}: build must be a mapping")
    else:
        build_missing = BUILD_REQUIRED_FIELDS - set(build.keys())
        if build_missing:
            error(errors, f"component {component}: build missing required fields: {sorted(build_missing)}")
        if build.get("type") not in {"make", "shell"}:
            error(errors, f"component {component}: build.type must be make or shell")
        if not isinstance(build.get("command"), str) or not build.get("command"):
            error(errors, f"component {component}: build.command must be a non-empty string")
        env = build.get("env", {})
        if not isinstance(env, dict):
            error(errors, f"component {component}: build.env must be a mapping when present")

    outputs = item.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        error(errors, f"component {component}: outputs must be a non-empty list")
        return

    for index, out in enumerate(outputs):
        if not isinstance(out, dict):
            error(errors, f"component {component}: outputs[{index}] must be a mapping")
            continue
        src = out.get("src")
        dest = out.get("dest")
        if not isinstance(src, str) or not src:
            error(errors, f"component {component}: outputs[{index}].src must be a non-empty string")
        if not isinstance(dest, str) or not dest:
            error(errors, f"component {component}: outputs[{index}].dest must be a non-empty string")
        else:
            output_names.add(dest)
        archive = out.get("archive")
        if archive is not None and not isinstance(archive, str):
            error(errors, f"component {component}: outputs[{index}].archive must be a string when present")


def validate_manifest(item: dict[str, Any], errors: list[str]) -> None:
    component = item.get("component", "<unknown>")
    for field in ["component", "version", "source", "dest"]:
        if not isinstance(item.get(field), str) or not item.get(field):
            error(errors, f"manifest {component}: {field} must be a non-empty string")
    source = item.get("source", "")
    if source and not source.startswith("https://"):
        error(errors, f"manifest {component}: source should be https://")


def main() -> int:
    try:
        data = load_yaml(SOURCES)
    except Exception as exc:  # noqa: BLE001
        print(f"failed to load {SOURCES}: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    components = data.get("components")
    manifests = data.get("manifests", [])

    if not isinstance(components, list) or not components:
        error(errors, "components must be a non-empty list")
        components = []
    if not isinstance(manifests, list):
        error(errors, "manifests must be a list when present")
        manifests = []

    component_names: set[str] = set()
    output_names: set[str] = set()

    for item in components:
        if not isinstance(item, dict):
            error(errors, "each component must be a mapping")
            continue
        name = item.get("component")
        if isinstance(name, str):
            if name in component_names:
                error(errors, f"duplicate component: {name}")
            component_names.add(name)
        validate_component(item, errors, output_names)

    manifest_names: set[str] = set()
    for item in manifests:
        if not isinstance(item, dict):
            error(errors, "each manifest must be a mapping")
            continue
        name = item.get("component")
        if isinstance(name, str):
            if name in manifest_names:
                error(errors, f"duplicate manifest: {name}")
            manifest_names.add(name)
        validate_manifest(item, errors)

    missing_components = REQUIRED_COMPONENTS - component_names
    if missing_components:
        error(errors, f"missing required components: {sorted(missing_components)}")

    missing_manifests = REQUIRED_MANIFESTS - manifest_names
    if missing_manifests:
        error(errors, f"missing required manifests: {sorted(missing_manifests)}")

    missing_outputs = REQUIRED_DEPLOY_OUTPUTS - output_names
    if missing_outputs:
        error(errors, f"missing required deploy outputs: {sorted(missing_outputs)}")

    if errors:
        print("Source manifest validation failed:", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("Source manifest validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
