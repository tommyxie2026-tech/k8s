#!/usr/bin/env bash
set -euo pipefail

ARCH="${ARCH:-amd64}"
CACHE_BRANCH="${CACHE_BRANCH:-binary-cache/${ARCH}}"
REMOTE="${REMOTE:-origin}"
FILES_DIR="files/${ARCH}"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

echo "==> Fetching ${CACHE_BRANCH} from ${REMOTE}"
git fetch "${REMOTE}" "${CACHE_BRANCH}"

echo "==> Exporting ${FILES_DIR} from ${CACHE_BRANCH}"
git archive "${REMOTE}/${CACHE_BRANCH}" "${FILES_DIR}" | tar -x -C "${TMP_DIR}"

mkdir -p "${FILES_DIR}"
rsync -a --delete "${TMP_DIR}/${FILES_DIR}/" "${FILES_DIR}/"

echo "==> Synced binary cache to ${FILES_DIR}"
if [[ -f "${FILES_DIR}/SHA256SUMS" ]]; then
  echo "==> Verifying SHA256SUMS"
  (cd "${FILES_DIR}" && sha256sum -c SHA256SUMS)
fi
