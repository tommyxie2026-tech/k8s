.PHONY: syntax-check syntax-check-single syntax-check-single-to-ha preflight-container deploy-container deploy-container-offline deploy-single deploy-single-offline migrate-single-to-ha-preflight migrate-single-to-ha-backup migrate-single-to-ha-etcd-preflight migrate-single-to-ha-expand-etcd migrate-single-to-ha cleanup-container smoke-test

INVENTORY ?= inventories/hosts-container.yml
KUBECONFIG_PATH ?= $(HOME)/.kube/config
CONFIRM_SINGLE_TO_HA ?= false
CONFIRM_EXPAND_ETCD ?= false

syntax-check:
	INVENTORY=$(INVENTORY) bash scripts/syntax-check.sh

syntax-check-single:
	INVENTORY=inventories/hosts-single.yml bash scripts/syntax-check.sh

syntax-check-single-to-ha:
	INVENTORY=inventories/hosts-ha-from-single.yml MODE=single-to-ha bash scripts/syntax-check.sh

preflight-container:
	ansible-playbook -i inventories/hosts-container.yml 0000-container-infra.yml
	ansible-playbook -i inventories/hosts-container.yml 0000-preflight.yml

deploy-container:
	ansible-playbook -i inventories/hosts-container.yml 0000-container-infra.yml
	ansible-playbook -i inventories/hosts-container.yml 0000-preflight.yml
	ansible-playbook -i inventories/hosts-container.yml 0001-download-binaries.yml
	ansible-playbook -i inventories/hosts-container.yml 0000-common-service.yml
	ansible-playbook -i inventories/hosts-container.yml 0002-common-kubeconfig.yml
	ansible-playbook -i inventories/hosts-container.yml 0003-encryption-config.yml
	ansible-playbook -i inventories/hosts-container.yml 0005-install-lb.yml
	ansible-playbook -i inventories/hosts-container.yml 0010-create-manager-set.yml
	ansible-playbook -i inventories/hosts-container.yml 0012-manager-set-kube.yml
	ansible-playbook -i inventories/hosts-container.yml 0020-create-compute-set.yml
	ansible-playbook -i inventories/hosts-container.yml 0030-install-cni.yml

deploy-container-offline:
	ansible-playbook -i inventories/hosts-container.yml 0000-container-infra.yml
	ansible-playbook -i inventories/hosts-container.yml 0000-preflight.yml
	ansible-playbook -i inventories/hosts-container.yml 0001-download-binaries.yml -e offline_binary_cache_only=true
	ansible-playbook -i inventories/hosts-container.yml 0000-common-service.yml
	ansible-playbook -i inventories/hosts-container.yml 0002-common-kubeconfig.yml
	ansible-playbook -i inventories/hosts-container.yml 0003-encryption-config.yml
	ansible-playbook -i inventories/hosts-container.yml 0005-install-lb.yml
	ansible-playbook -i inventories/hosts-container.yml 0010-create-manager-set.yml
	ansible-playbook -i inventories/hosts-container.yml 0012-manager-set-kube.yml
	ansible-playbook -i inventories/hosts-container.yml 0020-create-compute-set.yml
	ansible-playbook -i inventories/hosts-container.yml 0030-install-cni.yml

deploy-single:
	ansible-playbook -i inventories/hosts-single.yml 0000-preflight.yml
	ansible-playbook -i inventories/hosts-single.yml 0001-download-binaries.yml
	ansible-playbook -i inventories/hosts-single.yml 0000-common-service.yml
	ansible-playbook -i inventories/hosts-single.yml 0002-common-kubeconfig.yml
	ansible-playbook -i inventories/hosts-single.yml 0003-encryption-config.yml
	ansible-playbook -i inventories/hosts-single.yml 0005-install-lb.yml
	ansible-playbook -i inventories/hosts-single.yml 0010-create-manager-set.yml
	ansible-playbook -i inventories/hosts-single.yml 0012-manager-set-kube.yml
	ansible-playbook -i inventories/hosts-single.yml 0030-install-cni.yml
	ansible-playbook -i inventories/hosts-single.yml 0031-single-node-post.yml

deploy-single-offline:
	ansible-playbook -i inventories/hosts-single.yml 0000-preflight.yml
	ansible-playbook -i inventories/hosts-single.yml 0001-download-binaries.yml -e offline_binary_cache_only=true
	ansible-playbook -i inventories/hosts-single.yml 0000-common-service.yml
	ansible-playbook -i inventories/hosts-single.yml 0002-common-kubeconfig.yml
	ansible-playbook -i inventories/hosts-single.yml 0003-encryption-config.yml
	ansible-playbook -i inventories/hosts-single.yml 0005-install-lb.yml
	ansible-playbook -i inventories/hosts-single.yml 0010-create-manager-set.yml
	ansible-playbook -i inventories/hosts-single.yml 0012-manager-set-kube.yml
	ansible-playbook -i inventories/hosts-single.yml 0030-install-cni.yml
	ansible-playbook -i inventories/hosts-single.yml 0031-single-node-post.yml

migrate-single-to-ha-preflight:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0050-single-to-ha-preflight.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA)

migrate-single-to-ha-backup:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0051-single-to-ha-backup.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA)

migrate-single-to-ha-etcd-preflight:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0052-expand-etcd-members-preflight.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA)

migrate-single-to-ha-expand-etcd:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0053-expand-etcd-members.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA) -e confirm_expand_etcd_members=$(CONFIRM_EXPAND_ETCD)

migrate-single-to-ha:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0050-single-to-ha.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA)

cleanup-container:
	ansible-playbook -i inventories/hosts-container.yml 0099-container-cleanup.yml

smoke-test:
	KUBECONFIG_PATH=$(KUBECONFIG_PATH) bash scripts/smoke-test.sh
