#!/usr/bin/env bash
set -euo pipefail
ARCH="${ARCH:-amd64}"
CACHE_BRANCH="${CACHE_BRANCH:-binary-cache/${ARCH}}"
test "${ARCH}" = amd64 || test "${ARCH}" = arm64 || { echo "Unsupported architecture" >&2; exit 1; }
test "${CACHE_BRANCH}" = "binary-cache/${ARCH}" || { echo "Cache branch must match architecture" >&2; exit 1; }
VERIFY_SCRIPT="$(pwd)/scripts/verify-binary-cache.sh"
TMP="$(mktemp -d)"
cleanup() {
  git worktree remove --force "${TMP}/worktree" >/dev/null 2>&1 || true
  rm -rf "${TMP}"
}
trap cleanup EXIT
git fetch --no-tags origin "refs/heads/${CACHE_BRANCH}:refs/remotes/origin/${CACHE_BRANCH}"
GIT_LFS_SKIP_SMUDGE=1 git worktree add --detach "${TMP}/worktree" "refs/remotes/origin/${CACHE_BRANCH}"
(
  cd "${TMP}/worktree"
  git lfs pull origin --include="files/${ARCH}/**" --exclude=""
  bash "${VERIFY_SCRIPT}" "files/${ARCH}"
)
mkdir -p "files/${ARCH}"
rsync -a --delete "${TMP}/worktree/files/${ARCH}/" "files/${ARCH}/"
if [[ -f "${TMP}/worktree/inventories/group_vars/download-checksums-${ARCH}.yml" ]]; then
  cp "${TMP}/worktree/inventories/group_vars/download-checksums-${ARCH}.yml" \
     "inventories/group_vars/download-checksums-${ARCH}.yml"
fi
bash scripts/verify-binary-cache.sh "files/${ARCH}"
