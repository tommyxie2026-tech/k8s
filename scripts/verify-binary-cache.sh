#!/usr/bin/env bash
set -euo pipefail
FILES_DIR="${1:?Usage: verify-binary-cache.sh FILES_DIR [--strict]}"
MODE="${2:-}"
ARCH="${ARCH:-${FILES_DIR##*/}}"
test -f "${FILES_DIR}/SHA256SUMS" || { echo "Missing SHA256SUMS in ${FILES_DIR}" >&2; exit 1; }
(cd "${FILES_DIR}" && sha256sum -c SHA256SUMS)
if [[ "${MODE}" == "--strict" ]]; then
  MATRIX="inventories/group_vars/all.yml"
  test -f "${MATRIX}" || { echo "Missing version matrix: ${MATRIX}" >&2; exit 1; }
  read_version() {
    sed -nE 's/^'"${1}"': *"([^"]+)".*/\1/p' "${MATRIX}" | head -n1
  }
  etcd_version="$(read_version etcd_version)"
  k8s_version="$(read_version kubernetes_version)"
  containerd_version="$(read_version containerd_version)"
  cni_version="$(read_version cni_plugins_version)"
  test -n "${etcd_version}" && test -n "${k8s_version}" &&
    test -n "${containerd_version}" && test -n "${cni_version}" ||
    { echo "Incomplete component version matrix" >&2; exit 1; }
  # Match roles/download's offline cache requirements for the target version.
  required=(
    cfssl cfssljson kubectl runc containerd.service calico.yaml
    "etcd-v${etcd_version}-linux-${ARCH}.tar.gz"
    "kubernetes-server-linux-${ARCH}.tar.gz"
    "kubernetes-node-linux-${ARCH}.tar.gz"
    "containerd-${containerd_version}-linux-${ARCH}.tar.gz"
    "cni-plugins-linux-${ARCH}-v${cni_version}.tgz"
  )
  for file in "${required[@]}"; do
    test -s "${FILES_DIR}/${file}" || { echo "Missing required deploy artifact: ${file}" >&2; exit 1; }
    grep -Fq "  ./${file}" "${FILES_DIR}/SHA256SUMS" || { echo "Artifact not checksummed: ${file}" >&2; exit 1; }
  done
fi
