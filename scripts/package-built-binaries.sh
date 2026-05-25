#!/usr/bin/env bash
set -euo pipefail

ARCH="${ARCH:-amd64}"
FILES_DIR="${FILES_DIR:-files/${ARCH}}"
PKG_WORK_DIR="${PKG_WORK_DIR:-.build/package/${ARCH}}"
KUBERNETES_VERSION="${KUBERNETES_VERSION:-1.36.1}"
ETCD_VERSION="${ETCD_VERSION:-3.6.11}"
CONTAINERD_VERSION="${CONTAINERD_VERSION:-2.3.0}"
CNI_PLUGINS_VERSION="${CNI_PLUGINS_VERSION:-1.9.1}"

require_file() {
  local file="$1"
  if [[ ! -f "${file}" ]]; then
    echo "missing required file: ${file}" >&2
    return 1
  fi
}

package_kubernetes_server() {
  local root="${PKG_WORK_DIR}/kubernetes-server"
  rm -rf "${root}"
  mkdir -p "${root}/kubernetes/server/bin"

  for bin in kube-apiserver kube-controller-manager kube-scheduler kubectl; do
    require_file "${FILES_DIR}/${bin}"
    cp "${FILES_DIR}/${bin}" "${root}/kubernetes/server/bin/${bin}"
    chmod +x "${root}/kubernetes/server/bin/${bin}"
  done

  tar -C "${root}" -czf "${FILES_DIR}/kubernetes-server-linux-${ARCH}.tar.gz" kubernetes
}

package_kubernetes_node() {
  local root="${PKG_WORK_DIR}/kubernetes-node"
  rm -rf "${root}"
  mkdir -p "${root}/kubernetes/node/bin"

  for bin in kubelet kube-proxy kubectl; do
    require_file "${FILES_DIR}/${bin}"
    cp "${FILES_DIR}/${bin}" "${root}/kubernetes/node/bin/${bin}"
    chmod +x "${root}/kubernetes/node/bin/${bin}"
  done

  tar -C "${root}" -czf "${FILES_DIR}/kubernetes-node-linux-${ARCH}.tar.gz" kubernetes
}

package_etcd() {
  local root="${PKG_WORK_DIR}/etcd"
  local dir="etcd-v${ETCD_VERSION}-linux-${ARCH}"
  rm -rf "${root}"
  mkdir -p "${root}/${dir}"

  for bin in etcd etcdctl; do
    require_file "${FILES_DIR}/${bin}"
    cp "${FILES_DIR}/${bin}" "${root}/${dir}/${bin}"
    chmod +x "${root}/${dir}/${bin}"
  done

  tar -C "${root}" -czf "${FILES_DIR}/${dir}.tar.gz" "${dir}"
}

package_containerd() {
  local root="${PKG_WORK_DIR}/containerd"
  rm -rf "${root}"
  mkdir -p "${root}/bin"

  for bin in containerd containerd-shim-runc-v2 ctr; do
    require_file "${FILES_DIR}/${bin}"
    cp "${FILES_DIR}/${bin}" "${root}/bin/${bin}"
    chmod +x "${root}/bin/${bin}"
  done

  tar -C "${root}" -czf "${FILES_DIR}/containerd-${CONTAINERD_VERSION}-linux-${ARCH}.tar.gz" bin
}

package_cni_plugins() {
  if [[ -f "${FILES_DIR}/cni-plugins-linux-${ARCH}-v${CNI_PLUGINS_VERSION}.tgz" ]]; then
    return 0
  fi

  if [[ ! -d "${FILES_DIR}/cni-plugins" ]]; then
    echo "skip cni packaging: ${FILES_DIR}/cni-plugins not found and archive already absent" >&2
    return 0
  fi

  tar -C "${FILES_DIR}/cni-plugins" -czf "${FILES_DIR}/cni-plugins-linux-${ARCH}-v${CNI_PLUGINS_VERSION}.tgz" .
}

mkdir -p "${PKG_WORK_DIR}"

package_kubernetes_server
package_kubernetes_node
package_etcd
package_containerd
package_cni_plugins

find "${FILES_DIR}" -type f -maxdepth 2 -print0 | sort -z | xargs -0 sha256sum > "${FILES_DIR}/SHA256SUMS"

echo "==> packaged deploy-compatible archives in ${FILES_DIR}"
