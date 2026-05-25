#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
GROUP_VARS = ROOT / "inventories" / "group_vars" / "all.yml"
SOURCES = ROOT / "repo" / "sources.yml"

VERSION_KEYS = {
    "kubernetes": "kubernetes_version",
    "etcd": "etcd_version",
    "containerd": "containerd_version",
    "runc": "runc_version",
    "cni-plugins": "cni_plugins_version",
    "cfssl": "cfssl_version",
    "calico": "calico_version",
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    group_vars = load_yaml(GROUP_VARS)
    sources = load_yaml(SOURCES)

    source_versions = {}
    for item in sources.get("components", []):
        source_versions[item["component"]] = str(item["version"])
    for item in sources.get("manifests", []):
        source_versions[item["component"]] = str(item["version"])

    errors = []
    for component, var_name in VERSION_KEYS.items():
        expected = str(group_vars.get(var_name, ""))
        actual = str(source_versions.get(component, ""))
        if not expected:
            errors.append(f"missing {var_name} in {GROUP_VARS}")
            continue
        if not actual:
            errors.append(f"missing component {component} in {SOURCES}")
            continue
        if actual != expected:
            errors.append(
                f"version mismatch for {component}: repo/sources.yml={actual}, {var_name}={expected}"
            )

    if errors:
        print("Version consistency check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Version consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
