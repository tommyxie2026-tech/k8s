#!/usr/bin/env python3
"""Offline validation of the binary-PR promotion gate (no GitHub writes)."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml


# Script filenames contain hyphens, so load the same validator the workflow runs.
import runpy

CHECK = runpy.run_path(str(Path(__file__).with_name("validate-binary-promotion.py")))
verify = CHECK["verify"]
SHA = "a" * 40


class PromotionWorkflowSafetyTests(unittest.TestCase):
    def test_promotion_workflow_is_read_only_until_scoped_pr_step(self) -> None:
        root = Path(__file__).resolve().parents[1]
        workflow = yaml.safe_load(
            (root / ".github/workflows/propose-verified-binaries-pr.yml").read_text(
                encoding="utf-8"
            )
        )
        events = workflow.get("on", workflow.get(True))
        self.assertEqual(events["workflow_run"]["types"], ["completed"])
        self.assertEqual(workflow["permissions"], {"contents": "read", "actions": "read"})
        inspect = workflow["jobs"]["inspect"]
        requirements = inspect["if"]
        for clause in (
            "workflow_run.conclusion == 'success'",
            "workflow_run.event == 'workflow_dispatch'",
            "workflow_run.event == 'push'",
            "workflow_run.head_branch == 'master'",
            "workflow_run.head_repository.full_name == github.repository",
        ):
            self.assertIn(clause, requirements)
        self.assertNotIn("environment", inspect)
        propose = workflow["jobs"]["propose"]
        self.assertEqual(propose["environment"], "binary-artifact-pr")
        checkout = next(
            step
            for step in propose["steps"]
            if step.get("uses", "").startswith("actions/checkout@")
        )
        self.assertIs(checkout["with"]["persist-credentials"], False)
        scoped = [
            step
            for step in propose["steps"]
            if "ARTIFACT_PR_TOKEN" in str(step.get("env", {}))
        ]
        self.assertEqual(len(scoped), 1)
        self.assertIn("propose-binary-artifact-pr.sh", scoped[0]["run"])


    def test_auto_merge_only_after_binary_integrity_and_ci(self) -> None:
        root = Path(__file__).resolve().parents[1]
        flow = yaml.safe_load(
            (root / ".github/workflows/auto-merge-verified-binaries.yml").read_text(
                encoding="utf-8"
            )
        )
        events = flow.get("on", flow.get(True))
        self.assertEqual(
            set(events["workflow_run"]["workflows"]),
            {"CI", "Verify binary artifact PR"},
        )
        self.assertEqual(flow["permissions"]["contents"], "read")
        self.assertEqual(flow["jobs"]["merge"]["environment"], "binary-artifact-pr")
        inspection = flow["jobs"]["inspect"]["steps"][0]["run"]
        self.assertIn("commits/${EVENT_HEAD_SHA}/pulls", inspection)
        self.assertNotIn("actions/runs/${EVENT_RUN_ID}/pulls", inspection)
        merge_step = flow["jobs"]["merge"]["steps"][-1]
        self.assertIn("ARTIFACT_PR_TOKEN", str(merge_step["env"]))
        self.assertNotIn("pull_request_target", str(events))

        script = (root / "scripts/auto-merge-verified-binary-pr.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('.event == "push"', script)
        for required in (
            "ci.yml",
            "verify-binary-artifact-pr.yml",
            "source_sha",
            "master_sha",
            "EXPECTED_HEAD_SHA",
            "--match-head-commit",
            "--squash",
        ):
            self.assertIn(required, script)
        commands = "\n".join(
            line for line in script.splitlines()
            if not line.lstrip().startswith("#")
        )
        self.assertNotIn("--admin", commands)
        self.assertNotIn("--auto", commands)


class PromotionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.arch = "amd64"
        self.files = self.root / "files" / self.arch
        self.files.mkdir(parents=True)
        self.metadata = self.root / "metadata"
        self.metadata.mkdir()
        self.checksum_file = self.root / "inventories" / "group_vars" / (
            f"download-checksums-{self.arch}.yml"
        )
        self.checksum_file.parent.mkdir(parents=True)
        self.marker = {
            "schema_version": 1,
            "source_mode": "source",
            "stage": "all",
            "strict_package": True,
            "arch": self.arch,
            "source_sha": SHA,
            "run_id": 345,
            "run_attempt": 1,
        }
        (self.metadata / "binary-promotion.json").write_text(
            json.dumps(self.marker), encoding="utf-8"
        )
        artifact = self.files / "cfssl"
        artifact.write_bytes(b"fake fixture binary, not an actual compiled executable")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        (self.files / "SHA256SUMS").write_text(
            f"{digest}  ./cfssl\n", encoding="utf-8"
        )
        self.checksum_file.write_text(
            yaml.safe_dump({"download_checksums": {"cfssl": f"sha256:{digest}"}}),
            encoding="utf-8",
        )

    def validate(self) -> None:
        verify(self.root, self.arch, 345, 1, SHA)

    def test_complete_fixture_passes_metadata_and_integrity_gate(self) -> None:
        self.validate()

    def test_different_architecture_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            verify(self.root, "arm64", 345, 1, SHA)

    def test_different_run_identity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            verify(self.root, self.arch, 346, 1, SHA)

    def test_partial_build_marker_is_rejected(self) -> None:
        self.marker["stage"] = "stage1-light"
        (self.metadata / "binary-promotion.json").write_text(
            json.dumps(self.marker), encoding="utf-8"
        )
        with self.assertRaises(ValueError):
            self.validate()

    def test_tampering_is_rejected(self) -> None:
        (self.files / "cfssl").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.validate()

    def test_unchecksummed_extra_file_is_rejected(self) -> None:
        (self.files / "unexpected").write_bytes(b"not in manifest")
        with self.assertRaises(ValueError):
            self.validate()

    def test_cross_architecture_file_is_rejected(self) -> None:
        (self.root / "files" / "arm64").mkdir()
        (self.root / "files" / "arm64" / "other").write_bytes(b"cross contamination")
        with self.assertRaises(ValueError):
            self.validate()

    def test_another_architecture_symlink_is_rejected(self) -> None:
        (self.files / "link").symlink_to(self.files / "cfssl")
        with self.assertRaises(ValueError):
            self.validate()

    def test_mismatched_ansible_checksum_is_rejected(self) -> None:
        self.checksum_file.write_text(
            yaml.safe_dump({"download_checksums": {"cfssl": "sha256:" + "b" * 64}}),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            self.validate()


if __name__ == "__main__":
    unittest.main(verbosity=2)
