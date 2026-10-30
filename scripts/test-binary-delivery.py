#!/usr/bin/env python3
"""Offline regression checks for binary build/publish isolation and artifact integrity."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ARCH = "amd64"


def run_bash(script: str, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPTS / script), *map(str, args)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def populate_fixture(folder: Path, *, with_cni: bool = True) -> None:
    """Fake offline binaries are enough to exercise packaging and verification."""
    folder.mkdir(parents=True)
    names = (
        "cfssl", "cfssljson", "kubectl", "runc", "containerd.service", "calico.yaml",
        "kube-apiserver", "kube-controller-manager", "kube-scheduler",
        "kubelet", "kube-proxy", "etcd", "etcdctl",
        "containerd", "containerd-shim-runc-v2", "ctr",
    )
    for name in names:
        (folder / name).write_bytes(("fixture:" + name).encode())
    if with_cni:
        (folder / "cni-plugins-linux-amd64-v1.9.1.tgz").write_bytes(b"fake archive")


class DeliveryTests(unittest.TestCase):
    def test_read_only_workflows_and_secret_isolation(self):
        for name in ("build-default-binaries.yml", "cache-default-binaries.yml"):
            raw = (ROOT / ".github/workflows" / name).read_text()
            flow = yaml.safe_load(raw)
            self.assertEqual(flow["permissions"]["contents"], "read")
            self.assertNotIn("BINARY_CACHE_TOKEN", raw)
            self.assertNotIn("git push", raw)
            for job in flow["jobs"].values():
                self.assertEqual(job["permissions"]["contents"], "read")
        publish = yaml.safe_load(
            (ROOT / ".github/workflows/publish-default-binaries.yml").read_text()
        )
        self.assertEqual(publish["permissions"]["contents"], "read")
        self.assertEqual(publish["jobs"]["publish"]["environment"], "binary-cache-publish")
        self.assertNotIn("BINARY_CACHE_TOKEN", str(publish["jobs"]["build"]))
        self.assertIn("BINARY_CACHE_TOKEN", str(publish["jobs"]["publish"]))
        composite = (ROOT / ".github/actions/prepare-binaries/action.yml").read_text()
        self.assertNotIn("BINARY_CACHE_TOKEN", composite)

    def test_checksum_file_excludes_itself_and_is_relative(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "files" / ARCH
            folder.mkdir(parents=True)
            (folder / "cfssl").write_bytes(b"example binary")
            result = run_bash("write-sha256sums.sh", str(folder))
            self.assertEqual(result.returncode, 0, result.stderr)
            checksum = (folder / "SHA256SUMS").read_text()
            self.assertIn("./cfssl", checksum)
            self.assertNotIn("SHA256SUMS", checksum)
            self.assertEqual(run_bash("verify-binary-cache.sh", str(folder)).returncode, 0)
            (folder / "cfssl").write_bytes(b"tampered")
            self.assertNotEqual(
                run_bash("verify-binary-cache.sh", str(folder)).returncode, 0
            )

    def test_unresolved_lfs_pointer_and_symlink_fail_even_with_matching_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "files" / ARCH
            folder.mkdir(parents=True)
            item = folder / "kubectl"
            item.write_text(
                "version https://git-lfs.github.com/spec/v1\n"
                "oid sha256:" + ("f" * 64) + "\nsize 123\n"
            )
            self.assertEqual(run_bash("write-sha256sums.sh", str(folder)).returncode, 0)
            result = run_bash("verify-binary-cache.sh", str(folder))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unresolved Git LFS pointer", result.stderr)

            item.unlink()
            item.symlink_to(folder / "missing-target")
            result = run_bash("verify-binary-cache.sh", str(folder))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)

    def test_strict_packaging_detects_only_missing_cni(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "files" / ARCH
            populate_fixture(folder, with_cni=False)
            env = dict(
                os.environ,
                ARCH=ARCH,
                FILES_DIR=str(folder),
                PKG_WORK_DIR=str(Path(tmp) / "packages"),
                STRICT_PACKAGE="true",
            )
            result = run_bash("package-built-binaries.sh", env=env)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("cni-plugins-linux-amd64-v1.9.1.tgz", result.stderr)
            self.assertNotIn("cfssl", result.stderr)
            self.assertNotIn("etcd-v3.6.11-linux-amd64.tar.gz", result.stderr)

    def test_strict_packaging_success_and_checksum_manifest_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "files" / ARCH
            populate_fixture(folder)
            env = dict(
                os.environ,
                ARCH=ARCH,
                FILES_DIR=str(folder),
                PKG_WORK_DIR=str(Path(tmp) / "packages"),
                STRICT_PACKAGE="true",
            )
            package = run_bash("package-built-binaries.sh", env=env)
            self.assertEqual(package.returncode, 0, package.stderr)
            verify = run_bash("verify-binary-cache.sh", str(folder), "--strict")
            self.assertEqual(verify.returncode, 0, verify.stderr)
            expected = "cni-plugins-linux-amd64-v1.9.1.tgz"
            checksums = (folder / "SHA256SUMS").read_text()
            (folder / "SHA256SUMS").write_text(
                "\n".join(line for line in checksums.splitlines() if expected not in line)
                + "\n"
            )
            verify = run_bash("verify-binary-cache.sh", str(folder), "--strict")
            self.assertNotEqual(verify.returncode, 0)
            self.assertIn("Artifact not checksummed", verify.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
