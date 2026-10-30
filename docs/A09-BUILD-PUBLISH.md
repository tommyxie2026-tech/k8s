# A09 — build verification and binary-cache publication

## Permission boundary

- `Build default binaries (read-only validation)`: manually dispatched; `contents: read`; never receives `BINARY_CACHE_TOKEN`; uploads temporary Actions artifacts (14 days).
- `Cache default binaries (read-only validation)`: upstream release download, also read-only and without publication credentials.
- `Publish default binary cache (approval required)`: manually dispatched, confirmation input must equal `PUBLISH`. Its build job is read-only. Only its separate `publish` job has `BINARY_CACHE_TOKEN`; the job uses GitHub environment `binary-cache-publish` and writes only `binary-cache/<arch>`.
- **Repository administrator must configure required reviewers and appropriate branch protection on the `binary-cache-publish` environment before any publication.** An environment name alone does not enforce approval. Protect `BINARY_CACHE_TOKEN` as an environment secret, not a repository-wide secret, if possible. Until reviewers and secret scope are verified, do not run the publisher.
- The publisher does not have broad `GITHUB_TOKEN` write permission; the publication step uses the separately authorized PAT and no other job receives it.

## Usage

1. **Read-only smoke build**: Run `Build default binaries` with `stage=stage1-light`, `strict_package=false`. The job does not publish/cache anything remotely.
2. **Read-only complete build**: Run the same workflow with `stage=all`, `strict_package=true`; this can be expensive, prefer an adequately sized runner.
3. **Read-only staged verification**: Set `restore_cache=true` for stages 2–4 only if a *previously published* `binary-cache/<arch>` branch exists. The build job restores real Git LFS contents and checks `SHA256SUMS` before building. `restore_cache` is independent of write permission.
4. **Upstream release cache verification**: Run `Cache default binaries`; this only downloads and uploads temporary Actions artifacts.
5. **Publish cache**: Explicitly run `Publish default binary cache`, select `source_mode`, `arch`, `stage`, type `PUBLISH`, complete required environment review, then inspect the published branch and checksum proof. For staged source builds, publish stage1, stage2, stage3, stage4 in that order. For `source_mode=release`, `stage` is ignored. The branch name is locked to the chosen architecture.

For stages 2–4, the publisher restores `binary-cache/<arch>` in the **read-only build job**, then publishes verified combined outputs in the separate protected job. Stage4 and `all` use strict artifact checking. A fresh stage4 build with no preceding cache is expected to fail; run `all` or publish earlier stages first.

## Artifact integrity and offline scope

`scripts/write-sha256sums.sh` writes checksums for **relative paths**, excluding itself; `sha256sum -c SHA256SUMS` is verified inside `files/<arch>`. In strict mode `scripts/verify-binary-cache.sh` checks all required binary deployment files, including Calico and containerd.service. SHA256 provides integrity checking, not cryptographic proof of upstream origin. Operators must separately verify release provenance and licenses.

The restore helper uses a temporary worktree plus `git lfs pull`, never `git archive` (which would expose LFS pointers). The helper validates checksums before copying files into the working tree. It does not write to remote Git.

Offline *binary* caching is not the same as full air-gapped cluster installation: images, operating-system dependencies, DNS and other services need an independent offline readiness test. No live-cluster acceptance is claimed by these workflows.

## Acceptance / rollback

- `python3 scripts/test-binary-delivery.py` checks workflow permission boundaries, relative SHA256 generation, tamper detection and strict package failures.
- PR checks should pass, including existing shell/source/version/Ansible checks; actual full source builds, Git LFS uploads, environment approval and true offline deployments require separately observed executions.
- A publish failure must leave existing branches usable; publication requires a protected branch and separate approval. Do not silently fall back to PAT-less pushes.
- Roll back by reverting this PR; previously published `binary-cache/<arch>` contents are not removed. Do not rewrite or delete those branches as part of rollback.
- Source reference is pinned by `repo/sources.yml`. Published cache traceability additionally includes the source commit in the commit message and Actions run history.

## Current limitations

- Existing CI failures unrelated to A09 (for example malformed Ansible YAML) remain blocking until explicitly fixed.
- Current workflows do not sign binaries or attest reproducibility. All artifact metadata must be reviewed before production delivery.
- First publication and approval require configuring GitHub environment/secret/branch-protection controls; the PR does not and cannot configure these repository settings.
