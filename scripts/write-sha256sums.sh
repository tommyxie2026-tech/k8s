#!/usr/bin/env bash
set -euo pipefail
FILES_DIR="${1:?Usage: write-sha256sums.sh FILES_DIR}"
test -d "${FILES_DIR}" || { echo "Missing directory: ${FILES_DIR}" >&2; exit 1; }
# Use paths relative to FILES_DIR, matching Ansible's sha256sum -c chdir.
TEMP_FILE="$(mktemp)"
trap 'rm -f "${TEMP_FILE}"' EXIT
(
  cd "${FILES_DIR}"
  find . -type f ! -name SHA256SUMS ! -name SHA256SUMS.new -print0 |
    sort -z |
    xargs -0 -r sha256sum
) > "${TEMP_FILE}"
test -s "${TEMP_FILE}" || { echo "No build outputs to checksum" >&2; exit 1; }
mv "${TEMP_FILE}" "${FILES_DIR}/SHA256SUMS"
trap - EXIT
(cd "${FILES_DIR}" && sha256sum -c SHA256SUMS)
