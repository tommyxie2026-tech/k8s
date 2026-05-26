#!/usr/bin/env bash
set -euo pipefail

INVENTORY="${INVENTORY:-inventories/hosts-container.yml}"
MODE="${MODE:-auto}"

if [[ "${MODE}" == "auto" ]]; then
  case "${INVENTORY}" in
    *hosts-container.yml) MODE="container" ;;
    *hosts-single.yml) MODE="single" ;;
    *hosts-ha-from-single.yml) MODE="single-to-ha" ;;
    *) MODE="ha" ;;
  esac
fi

COMMON_PLAYBOOKS=(
  0000-preflight.yml
  0001-download-binaries.yml
  0000-common-service.yml
  0002-common-kubeconfig.yml
  0003-encryption-config.yml
  0005-install-lb.yml
  0010-create-manager-set.yml
  0012-manager-set-kube.yml
  0030-install-cni.yml
  0040-etcd-snapshot.yml
  0400-cert-expiry-check.yml
  0401-renew-component-certs.yml
  0090-stop-services.yml
  0091-reset-node-runtime.yml
)

case "${MODE}" in
  container)
    PLAYBOOKS=(
      0000-container-infra.yml
      "${COMMON_PLAYBOOKS[@]}"
      0020-create-compute-set.yml
      0099-container-cleanup.yml
    )
    ;;
  single)
    PLAYBOOKS=(
      "${COMMON_PLAYBOOKS[@]}"
      0031-single-node-post.yml
    )
    ;;
  single-to-ha)
    PLAYBOOKS=(
      0050-single-to-ha-preflight.yml
      0051-single-to-ha-backup.yml
      0052-expand-etcd-members-preflight.yml
      0053-expand-etcd-members.yml
      0054-renew-apiserver-cert-for-ha.yml
      0055-expand-control-plane.yml
      0056-enable-ha-lb.yml
      0057-switch-kubeconfigs-to-vip.yml
      0050-single-to-ha.yml
    )
    ;;
  ha)
    PLAYBOOKS=(
      "${COMMON_PLAYBOOKS[@]}"
      0020-create-compute-set.yml
    )
    ;;
  *)
    echo "Unsupported MODE=${MODE}. Expected auto, container, single, single-to-ha, or ha." >&2
    exit 2
    ;;
esac

for playbook in "${PLAYBOOKS[@]}"; do
  if [[ -f "${playbook}" ]]; then
    echo "==> syntax check [${MODE}]: ${playbook}"
    ansible-playbook -i "${INVENTORY}" --syntax-check "${playbook}"
  fi
done

echo "==> All syntax checks passed for mode: ${MODE}"
