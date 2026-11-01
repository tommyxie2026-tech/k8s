#!/usr/bin/env python3
"""Offline integration smoke test for the source-tag build and checksum pipeline.

Uses a local disposable Git repository and fake executables. This tests the
harness only; it does not claim real Kubernetes or Go compilation succeeded.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, env=env, capture_output=True, text=True, check=False
    )


class SourceBuildPipelineTests(unittest.TestCase):
    def test_local_source_tag_build_creates_verified_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            source = work / "fake-source"
            source.mkdir()

            for args in (
                ("git", "init", "--quiet"),
                ("git", "config", "user.email", "smoke@example.invalid"),
                ("git", "config", "user.name", "CI Smoke"),
            ):
                result = run(*args, cwd=source)
                self.assertEqual(result.returncode, 0, result.stderr)

            (source / "README.md").write_text("fixture only\n", encoding="utf-8")
            for args in (("git", "add", "README.md"), ("git", "commit", "--quiet", "-m", "fixture"),
                         ("git", "tag", "v0.0.1")):
                result = run(*args, cwd=source)
                self.assertEqual(result.returncode, 0, result.stderr)

            manifest = work / "sources.yml"
            manifest.write_text(
                yaml.safe_dump(
                    {
                        "components": [
                            {
                                "component": "cfssl",
                                "version": "0.0.1",
                                "git": str(source),
                                "tag": "v0.0.1",
                                "build": {
                                    "command": (
                                        "mkdir -p bin && "
                                        "printf '#!/bin/sh\\necho fixture\\n' > bin/cfssl && "
                                        "cp bin/cfssl bin/cfssljson && "
                                        "chmod +x bin/cfssl bin/cfssljson"
                                    )
                                },
                                "outputs": [
                                    {"src": "bin/cfssl", "dest": "cfssl"},
                                    {"src": "bin/cfssljson", "dest": "cfssljson"},
                                ],
                            },
                            {
                                "component": "skip-on-stage1",
                                "version": "0.0.1",
                                "git": "/this/source/must/not/be/cloned",
                                "tag": "v0.0.1",
                                "build": {"command": "exit 99"},
                                "outputs": [{"src": "missing", "dest": "must-not-build"}],
                            },
                        ]
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            output = work / "files" / "amd64"
            env = dict(
                os.environ,
                ARCH="amd64",
                SOURCES_FILE=str(manifest),
                WORK_DIR=str(work / "src"),
                FILES_DIR=str(output),
                BUILD_COMPONENTS="cfssl",
                PACKAGE_DEPLOY_ARCHIVES="true",
                STRICT_PACKAGE="false",
            )
            result = run("bash", "scripts/build-default-binaries.sh", cwd=ROOT, env=env)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            self.assertEqual((output / "cfssl").read_bytes(), (output / "cfssljson").read_bytes())
            self.assertFalse((output / "must-not-build").exists())
            self.assertTrue((output / "SHA256SUMS").is_file())

            checked = run(
                "bash", "scripts/verify-binary-cache.sh", str(output), cwd=ROOT, env=env
            )
            self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)

            checksums_path = work / "checksums.yml"
            generated = run(
                "python3",
                "scripts/generate-download-checksums.py",
                "--arch",
                "amd64",
                "--files-dir",
                str(output),
                "--output",
                str(checksums_path),
                cwd=ROOT,
                env=env,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr + generated.stdout)
            checksums = yaml.safe_load(checksums_path.read_text(encoding="utf-8"))
            self.assertEqual(set(checksums["download_checksums"]), {"cfssl", "cfssljson"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
