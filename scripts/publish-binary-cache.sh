#!/usr/bin/env bash
set -euo pipefail
ARCH="${ARCH:-amd64}"
test "${ARCH}" = amd64 || test "${ARCH}" = arm64 || { echo "Unsupported architecture" >&2; exit 1; }
test -n "${BINARY_CACHE_TOKEN:-}" || { echo "BINARY_CACHE_TOKEN is required" >&2; exit 1; }
test -n "${GITHUB_REPOSITORY:-}" || { echo "GITHUB_REPOSITORY is required" >&2; exit 1; }
CACHE_BRANCH="binary-cache/${ARCH}"
bash scripts/verify-binary-cache.sh "files/${ARCH}"
test -f "inventories/group_vars/download-checksums-${ARCH}.yml"
TMP="$(mktemp -d)"
cp "scripts/verify-binary-cache.sh" "${TMP}/verify-binary-cache.sh"
trap 'rm -rf "${TMP}"; git remote set-url origin "https://github.com/${GITHUB_REPOSITORY}.git" >/dev/null 2>&1 || true' EXIT
mkdir -p "${TMP}/files/${ARCH}"
cp -a "files/${ARCH}/." "${TMP}/files/${ARCH}/"
cp "inventories/group_vars/download-checksums-${ARCH}.yml" "${TMP}/download-checksums.yml"
# Uploaded artifacts are untracked on master; remove them before switching branches.
rm -rf "files/${ARCH}"
rm -f "inventories/group_vars/download-checksums-${ARCH}.yml"
git lfs install --local
# The publisher is the only job authorized to use this credential. Its
# checkout deliberately has persist-credentials=false, so authenticate before
# fetching either an existing private cache branch or pushing new LFS objects.
git remote set-url origin "https://x-access-token:${BINARY_CACHE_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
if git ls-remote --exit-code --heads origin "${CACHE_BRANCH}" >/dev/null; then
  git fetch origin "refs/heads/${CACHE_BRANCH}:refs/remotes/origin/${CACHE_BRANCH}"
  GIT_LFS_SKIP_SMUDGE=1 git checkout -B "${CACHE_BRANCH}" "refs/remotes/origin/${CACHE_BRANCH}"
else
  GIT_LFS_SKIP_SMUDGE=1 git checkout --orphan "${CACHE_BRANCH}"
  git rm -rf -q . || true
fi
git lfs track "files/**/*"
mkdir -p "files/${ARCH}" inventories/group_vars
rm -rf "files/${ARCH}"
cp -a "${TMP}/files/${ARCH}" "files/${ARCH}"
cp "${TMP}/download-checksums.yml" "inventories/group_vars/download-checksums-${ARCH}.yml"
bash "${TMP}/verify-binary-cache.sh" "files/${ARCH}"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add .gitattributes
git add -f "files/${ARCH}" "inventories/group_vars/download-checksums-${ARCH}.yml"
if git diff --cached --quiet; then
  echo "Binary cache unchanged"
  exit 0
fi
git commit -m "cache: publish ${ARCH} binaries from ${SOURCE_SHA:-manual}"
# Publishing token is only available in this protected publication job.
git lfs push origin HEAD
git push origin "HEAD:refs/heads/${CACHE_BRANCH}"
