#!/usr/bin/env bash
set -euo pipefail

ARCH="${ARCH:-amd64}"
FILES_DIR="${FILES_DIR:-files/${ARCH}}"
CFSSL_VERSION="${CFSSL_VERSION:-1.6.5}"
ETCD_VERSION="${ETCD_VERSION:-3.6.11}"
KUBERNETES_VERSION="${KUBERNETES_VERSION:-1.36.1}"
CONTAINERD_VERSION="${CONTAINERD_VERSION:-2.3.0}"
RUNC_VERSION="${RUNC_VERSION:-1.3.5}"
CNI_PLUGINS_VERSION="${CNI_PLUGINS_VERSION:-1.9.1}"
CALICO_VERSION="${CALICO_VERSION:-3.32.0}"
CONTROLLER_OS="${CONTROLLER_OS:-linux}"
CONTROLLER_ARCH="${CONTROLLER_ARCH:-${ARCH}}"
DOWNLOAD_RETRIES="${DOWNLOAD_RETRIES:-3}"
DOWNLOAD_RETRY_DELAY="${DOWNLOAD_RETRY_DELAY:-5}"

mkdir -p "${FILES_DIR}"

download() {
  local url="$1"
  local dest="$2"
  local tmp="${dest}.tmp"

  if [[ -s "${dest}" ]]; then
    echo "==> exists: ${dest}"
    return 0
  fi

  echo "==> downloading: ${url}"
  for attempt in $(seq 1 "${DOWNLOAD_RETRIES}"); do
    if curl -fL --retry 3 --retry-delay 2 --connect-timeout 20 --max-time 1800 -o "${tmp}" "${url}"; then
      mv "${tmp}" "${dest}"
      return 0
    fi
    echo "download failed, attempt ${attempt}/${DOWNLOAD_RETRIES}: ${url}" >&2
    sleep "${DOWNLOAD_RETRY_DELAY}"
  done

  rm -f "${tmp}"
  echo "failed to download after ${DOWNLOAD_RETRIES} attempts: ${url}" >&2
  return 1
}

download "https://github.com/cloudflare/cfssl/releases/download/v${CFSSL_VERSION}/cfssl_${CFSSL_VERSION}_${CONTROLLER_OS}_${CONTROLLER_ARCH}" \
  "${FILES_DIR}/cfssl"
chmod +x "${FILES_DIR}/cfssl"

download "https://github.com/cloudflare/cfssl/releases/download/v${CFSSL_VERSION}/cfssljson_${CFSSL_VERSION}_${CONTROLLER_OS}_${CONTROLLER_ARCH}" \
  "${FILES_DIR}/cfssljson"
chmod +x "${FILES_DIR}/cfssljson"

download "https://dl.k8s.io/release/v${KUBERNETES_VERSION}/bin/${CONTROLLER_OS}/${CONTROLLER_ARCH}/kubectl" \
  "${FILES_DIR}/kubectl"
chmod +x "${FILES_DIR}/kubectl"

download "https://github.com/etcd-io/etcd/releases/download/v${ETCD_VERSION}/etcd-v${ETCD_VERSION}-linux-${ARCH}.tar.gz" \
  "${FILES_DIR}/etcd-v${ETCD_VERSION}-linux-${ARCH}.tar.gz"

download "https://dl.k8s.io/v${KUBERNETES_VERSION}/kubernetes-server-linux-${ARCH}.tar.gz" \
  "${FILES_DIR}/kubernetes-server-linux-${ARCH}.tar.gz"

download "https://dl.k8s.io/v${KUBERNETES_VERSION}/kubernetes-node-linux-${ARCH}.tar.gz" \
  "${FILES_DIR}/kubernetes-node-linux-${ARCH}.tar.gz"

download "https://github.com/containerd/containerd/releases/download/v${CONTAINERD_VERSION}/containerd-${CONTAINERD_VERSION}-linux-${ARCH}.tar.gz" \
  "${FILES_DIR}/containerd-${CONTAINERD_VERSION}-linux-${ARCH}.tar.gz"

download "https://github.com/opencontainers/runc/releases/download/v${RUNC_VERSION}/runc.${ARCH}" \
  "${FILES_DIR}/runc"
chmod +x "${FILES_DIR}/runc"

download "https://raw.githubusercontent.com/containerd/containerd/v${CONTAINERD_VERSION}/containerd.service" \
  "${FILES_DIR}/containerd.service"

download "https://github.com/containernetworking/plugins/releases/download/v${CNI_PLUGINS_VERSION}/cni-plugins-linux-${ARCH}-v${CNI_PLUGINS_VERSION}.tgz" \
  "${FILES_DIR}/cni-plugins-linux-${ARCH}-v${CNI_PLUGINS_VERSION}.tgz"

download "https://raw.githubusercontent.com/projectcalico/calico/v${CALICO_VERSION}/manifests/calico.yaml" \
  "${FILES_DIR}/calico.yaml"

find "${FILES_DIR}" -type f -maxdepth 1 -print0 | sort -z | xargs -0 sha256sum > "${FILES_DIR}/SHA256SUMS"

echo "==> downloaded default binaries to ${FILES_DIR}"
echo "==> checksum file: ${FILES_DIR}/SHA256SUMS"
