#!/usr/bin/env python3
"""Offline regression checks for the A09 binary build/publish separation."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

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
        publish = yaml.safe_load((ROOT / ".github/workflows/publish-default-binaries.yml").read_text())
        self.assertEqual(publish["permissions"]["contents"], "read")
        self.assertEqual(publish["jobs"]["publish"]["environment"], "binary-cache-publish")
        self.assertNotIn("BINARY_CACHE_TOKEN", str(publish["jobs"]["build"]))
        self.assertIn("BINARY_CACHE_TOKEN", str(publish["jobs"]["publish"]))
        composite = (ROOT / ".github/actions/prepare-binaries/action.yml").read_text()
        self.assertNotIn("BINARY_CACHE_TOKEN", composite)

    def test_checksum_file_excludes_itself_and_is_relative(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "files" / "amd64"
            folder.mkdir(parents=True)
            (folder / "cfssl").write_bytes(b"example binary")
            subprocess.run(["bash", str(ROOT / "scripts/write-sha256sums.sh"), str(folder)], check=True, capture_output=True)
            checksum = (folder / "SHA256SUMS").read_text()
            self.assertIn("./cfssl", checksum)
            self.assertNotIn("SHA256SUMS", checksum)
            subprocess.run(["bash", str(ROOT / "scripts/verify-binary-cache.sh"), str(folder)], check=True, capture_output=True)
            (folder / "cfssl").write_bytes(b"tampered")
            result = subprocess.run(["bash", str(ROOT / "scripts/verify-binary-cache.sh"), str(folder)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_strict_packaging_detects_missing_cni(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "files" / "amd64"
            folder.mkdir(parents=True)
            env = dict(os.environ, ARCH="amd64", FILES_DIR=str(folder), PKG_WORK_DIR=str(Path(tmp) / "packages"), STRICT_PACKAGE="true")
            result = subprocess.run(["bash", str(ROOT / "scripts/package-built-binaries.sh")], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cni-plugins-linux-amd64-v1.9.1.tgz", result.stderr)

if __name__ == "__main__":
    unittest.main(verbosity=2)
