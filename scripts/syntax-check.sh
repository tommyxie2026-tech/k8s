#!/usr/bin/env bash
set -euo pipefail

INVENTORY="${INVENTORY:-inventories/hosts-container.yml}"

PLAYBOOKS=(
  0000-container-infra.yml
  0000-preflight.yml
  0001-download-binaries.yml
  0000-common-service.yml
  0002-common-kubeconfig.yml
  0005-install-lb.yml
  0010-create-manager-set.yml
  0012-manager-set-kube.yml
  0020-create-compute-set.yml
  0030-install-cni.yml
  0040-etcd-snapshot.yml
  0090-stop-services.yml
  0099-container-cleanup.yml
)

for playbook in "${PLAYBOOKS[@]}"; do
  if [[ -f "${playbook}" ]]; then
    echo "==> syntax check: ${playbook}"
    ansible-playbook -i "${INVENTORY}" --syntax-check "${playbook}"
  fi
done

echo "==> All syntax checks passed"
