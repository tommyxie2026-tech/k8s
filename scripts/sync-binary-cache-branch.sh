#!/usr/bin/env bash
set -euo pipefail
# Legacy deployment entry point delegates to the LFS-aware, checksummed restore.
ARCH="${ARCH:-amd64}" CACHE_BRANCH="${CACHE_BRANCH:-binary-cache/${ARCH}}" \
  bash scripts/restore-binary-cache-branch.sh
