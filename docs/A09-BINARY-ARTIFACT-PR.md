# A09 extension — Verified build artifact PR to files/<arch>

**Status: proposed, not yet enabled on master.** This design adds a reviewable
pull-request delivery path alongside the existing binary-cache publication
workflow. It does **not** weaken A09's read-only build/publish separation or
automatically merge anything.

## Intended sequence

1. A trusted operator runs **Build default binaries (read-only validation)**
   on `master` with `stage=all`, `strict_package=true`, `restore_cache=false`,
   `arch=amd64` (repeat separately for `arm64`). The source build must succeed
   and contain all deploy-compatible archives.
2. The read-only build uploads the binary Artifact, Ansible download-checksums
   YAML, and a promotion marker binding the run ID, attempt, source SHA, arch,
   and strict full-build options. **Only a complete strict source build
   generates this marker**. Stage1 PR smoke runs are not eligible.
3. An independent **Propose verified architecture binaries PR** workflow
   observes successful completion via `workflow_run`. It only accepts a
   `workflow_dispatch` on this repository's own `master`. Missing marker
   safely skips, without opening any PR.
4. The second job checks out trusted `master`, rejects stale binaries when
   source SHA no longer equals current `master` HEAD, downloads only the
   attempt-specific Artifact, and validates marker, arch, SHA256 coverage,
   foreign-architecture files, symlinks, Ansible checksum mappings, and
   `verify-binary-cache.sh --strict`.
5. After validation, the scoped writer stages only `files/<arch>/` and
   `inventories/group_vars/download-checksums-<arch>.yml` in a new branch
   `artifact-pr/<arch>/run-<id>-attempt-<n>` using **Git LFS**. It pushes LFS
   objects, pushes the branch, and opens a review PR to `master`. It never
   auto-merges, deploys or pushes to `binary-cache/<arch>`.

## Architecture separation

| Build arch | Permitted PR files |
| --- | --- |
| `amd64` | `files/amd64/**`, `inventories/group_vars/download-checksums-amd64.yml` |
| `arm64` | `files/arm64/**`, `inventories/group_vars/download-checksums-arm64.yml` |

The script refuses unrelated staged paths. The repository's existing
`.gitattributes` rule `files/**/* filter=lfs` remains authoritative. This
delivers source-built binaries in **master only after PR review**, unlike
the separate binary cache branch publication workflow.

## Required GitHub settings

Before enabling actual PR creation, an administrator must create or verify
environment **`binary-artifact-pr`** with environment secret
**`ARTIFACT_PR_TOKEN`**. Use a GitHub App installation token or fine-grained
PAT scoped to this repo, with Contents read/write, Pull requests read/write,
and sufficient Git LFS access. Build and inspect steps keep the read-only
GitHub token and never receive this write credential.

Protect `master` with required reviews and appropriate checks. Environment
approval before *opening* a PR is optional; **review before merge is
mandatory**. Missing credentials must fail closed. Do not fall back to a
repository-wide token or grant write access to the compilation job.

A new `workflow_run` workflow is recognized only after it exists on the
default branch; an unmerged PR cannot activate it. The full-build marker is
part of the separate source smoke PR **#8**, so both changes must be merged
and verified before automatic PR promotion works. If `master` advances
after a build, rerun the full source build on its latest commit.

## Acceptance and limitations

- Run `python3 scripts/test-binary-promotion.py` and existing
  `scripts/test-binary-delivery.py` in base CI.
- Verify actual **source compilation** using the real build job log and
  uploaded checksummed files—not offline fixture tests alone.
- Inspect the generated PR's paths, Git LFS pointers, file sizes, source SHA,
  SHA256SUMS, checksum YAML, LFS quota, and mandatory CI before merging.
- LFS pointers are not standalone executables; downstream consumers need
  actual LFS objects or verified download artifacts.
- SHA256 is an integrity check, not a signature or reproducibility proof.
  This flow does not establish complete air-gapped deployability.
- Rollback uses a normal PR reverting target-architecture files; never force
  rewrite or delete old LFS objects as an implicit rollback.

## Verification status

At this proposal stage, source build PR #8 has no observed completed Actions
build. The promotion workflow is not merged into `master`, so no automatic
binary candidate PR can be claimed yet. Confirm each stage using the build
run, promotion run, generated PR, and eventual reviewed merge.
