#!/usr/bin/env bash
set -euo pipefail
FILES_DIR="${1:?Usage: verify-binary-cache.sh FILES_DIR [--strict]}"
MODE="${2:-}"
ARCH="${ARCH:-${FILES_DIR##*/}}"
test -f "${FILES_DIR}/SHA256SUMS" || { echo "Missing SHA256SUMS in ${FILES_DIR}" >&2; exit 1; }
(cd "${FILES_DIR}" && sha256sum -c SHA256SUMS)
if [[ "${MODE}" == "--strict" ]]; then
  # Identical required file set to roles/download's offline binary cache.
  required=(
    cfssl cfssljson kubectl runc containerd.service calico.yaml
    "etcd-v3.6.11-linux-${ARCH}.tar.gz"
    "kubernetes-server-linux-${ARCH}.tar.gz"
    "kubernetes-node-linux-${ARCH}.tar.gz"
    "containerd-2.3.0-linux-${ARCH}.tar.gz"
    "cni-plugins-linux-${ARCH}-v1.9.1.tgz"
  )
  for file in "${required[@]}"; do
    test -s "${FILES_DIR}/${file}" || { echo "Missing required deploy artifact: ${file}" >&2; exit 1; }
    grep -Fq "  ./${file}" "${FILES_DIR}/SHA256SUMS" || { echo "Artifact not checksummed: ${file}" >&2; exit 1; }
  done
fi
