.PHONY: syntax-check syntax-check-ha syntax-check-single syntax-check-single-to-ha storage-preflight install-csi install-storageclass storage-health-check storage-migration-check storage-pvc-validate kubevirt-preflight install-kubevirt kubevirt-health-check kubevirt-smoke-test install-kubevirt-cdi kubevirt-datavolume-smoke-test install-virtctl kubevirt-vm-ops node-pool-labels node-pool-health-check storage-pool-health-check scheduling-policy-check preflight-container deploy-container deploy-container-offline deploy-single deploy-single-offline deploy-ha deploy-ha-offline migrate-single-to-ha-preflight migrate-single-to-ha-backup migrate-single-to-ha-etcd-preflight migrate-single-to-ha-expand-etcd migrate-single-to-ha-renew-apiserver-cert migrate-single-to-ha-expand-control-plane migrate-single-to-ha-enable-ha-lb migrate-single-to-ha-switch-kubeconfigs-to-vip migrate-single-to-ha cleanup-container smoke-test

INVENTORY ?= inventories/hosts-container.yml
KUBECONFIG_PATH ?= $(HOME)/.kube/config
CONFIRM_SINGLE_TO_HA ?= false
CONFIRM_EXPAND_ETCD ?= false
CONFIRM_RENEW_APISERVER_CERT ?= false
CONFIRM_EXPAND_CONTROL_PLANE ?= false
CONFIRM_ENABLE_HA_LB ?= false
CONFIRM_SWITCH_KUBECONFIGS_TO_VIP ?= false

KUBEVIRT_ENABLED ?= true
KUBEVIRT_VM_ACTION ?= status
KUBEVIRT_VM_NAMESPACE ?= default
KUBEVIRT_VM_NAME ?=

NODE_POOLS_ENABLED ?= true
NODE_POOLS_APPLY_CONFIRM ?= false
NODE_POOLS_MANAGE_TAINTS ?= false
STORAGE_POOLS_ENABLED ?= true

syntax-check:
	INVENTORY=$(INVENTORY) bash scripts/syntax-check.sh

syntax-check-ha:
	INVENTORY=inventories/hosts-ha.yml MODE=ha bash scripts/syntax-check.sh

syntax-check-single:
	INVENTORY=inventories/hosts-single.yml bash scripts/syntax-check.sh

syntax-check-single-to-ha:
	INVENTORY=inventories/hosts-ha-from-single.yml MODE=single-to-ha bash scripts/syntax-check.sh

storage-preflight:
	ansible-playbook -i $(INVENTORY) 0058-storage-preflight.yml

install-csi:
	ansible-playbook -i $(INVENTORY) 0059-install-csi.yml

install-storageclass:
	ansible-playbook -i $(INVENTORY) 0060-install-storageclass.yml

storage-health-check:
	ansible-playbook -i $(INVENTORY) 0061-storage-health-check.yml

storage-migration-check:
	ansible-playbook -i $(INVENTORY) 0062-storage-migration-check.yml

storage-pvc-validate:
	ansible-playbook -i $(INVENTORY) 0063-storage-pvc-validate.yml

kubevirt-preflight:
	ansible-playbook -i $(INVENTORY) 0063-kubevirt-preflight.yml

install-kubevirt:
	ansible-playbook -i $(INVENTORY) 0064-install-kubevirt.yml

kubevirt-health-check:
	ansible-playbook -i $(INVENTORY) 0065-kubevirt-health-check.yml

kubevirt-smoke-test:
	ansible-playbook -i $(INVENTORY) 0066-kubevirt-smoke-test.yml

install-kubevirt-cdi:
	ansible-playbook -i $(INVENTORY) 0067-install-kubevirt-cdi.yml

kubevirt-datavolume-smoke-test:
	ansible-playbook -i $(INVENTORY) 0068-kubevirt-datavolume-smoke-test.yml

install-virtctl:
	ansible-playbook -i $(INVENTORY) 0069-install-virtctl.yml

kubevirt-vm-ops:
	ansible-playbook -i $(INVENTORY) 0070-kubevirt-vm-ops.yml \
		-e kubevirt_enabled=$(KUBEVIRT_ENABLED) \
		-e kubevirt_vm_action=$(KUBEVIRT_VM_ACTION) \
		-e kubevirt_vm_namespace=$(KUBEVIRT_VM_NAMESPACE) \
		-e kubevirt_vm_name=$(KUBEVIRT_VM_NAME)

node-pool-labels:
	ansible-playbook -i $(INVENTORY) 0071-node-pool-labels.yml \
		-e node_pools_enabled=$(NODE_POOLS_ENABLED) \
		-e node_pools_apply_confirm=$(NODE_POOLS_APPLY_CONFIRM) \
		-e node_pools_manage_taints=$(NODE_POOLS_MANAGE_TAINTS)

node-pool-health-check:
	ansible-playbook -i $(INVENTORY) 0072-node-pool-health-check.yml \
		-e node_pools_enabled=$(NODE_POOLS_ENABLED)

storage-pool-health-check:
	ansible-playbook -i $(INVENTORY) 0073-storage-pool-health-check.yml \
		-e storage_pools_enabled=$(STORAGE_POOLS_ENABLED)

scheduling-policy-check:
	ansible-playbook -i $(INVENTORY) 0074-scheduling-policy-check.yml \
		-e node_pools_enabled=$(NODE_POOLS_ENABLED)

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

deploy-ha:
	ansible-playbook -i inventories/hosts-ha.yml 0000-preflight.yml
	ansible-playbook -i inventories/hosts-ha.yml 0001-download-binaries.yml
	ansible-playbook -i inventories/hosts-ha.yml 0000-common-service.yml
	ansible-playbook -i inventories/hosts-ha.yml 0002-common-kubeconfig.yml
	ansible-playbook -i inventories/hosts-ha.yml 0003-encryption-config.yml
	ansible-playbook -i inventories/hosts-ha.yml 0005-install-lb.yml
	ansible-playbook -i inventories/hosts-ha.yml 0010-create-manager-set.yml
	ansible-playbook -i inventories/hosts-ha.yml 0012-manager-set-kube.yml
	ansible-playbook -i inventories/hosts-ha.yml 0020-create-compute-set.yml
	ansible-playbook -i inventories/hosts-ha.yml 0030-install-cni.yml

deploy-ha-offline:
	ansible-playbook -i inventories/hosts-ha.yml 0000-preflight.yml
	ansible-playbook -i inventories/hosts-ha.yml 0001-download-binaries.yml -e offline_binary_cache_only=true
	ansible-playbook -i inventories/hosts-ha.yml 0000-common-service.yml
	ansible-playbook -i inventories/hosts-ha.yml 0002-common-kubeconfig.yml
	ansible-playbook -i inventories/hosts-ha.yml 0003-encryption-config.yml
	ansible-playbook -i inventories/hosts-ha.yml 0005-install-lb.yml
	ansible-playbook -i inventories/hosts-ha.yml 0010-create-manager-set.yml
	ansible-playbook -i inventories/hosts-ha.yml 0012-manager-set-kube.yml
	ansible-playbook -i inventories/hosts-ha.yml 0020-create-compute-set.yml
	ansible-playbook -i inventories/hosts-ha.yml 0030-install-cni.yml

migrate-single-to-ha-preflight:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0050-single-to-ha-preflight.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA)

migrate-single-to-ha-backup:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0051-single-to-ha-backup.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA)

migrate-single-to-ha-etcd-preflight:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0052-expand-etcd-members-preflight.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA)

migrate-single-to-ha-expand-etcd:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0053-expand-etcd-members.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA) -e confirm_expand_etcd_members=$(CONFIRM_EXPAND_ETCD)

migrate-single-to-ha-renew-apiserver-cert:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0054-renew-apiserver-cert-for-ha.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA) -e confirm_renew_apiserver_cert=$(CONFIRM_RENEW_APISERVER_CERT)

migrate-single-to-ha-expand-control-plane:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0055-expand-control-plane.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA) -e confirm_expand_control_plane=$(CONFIRM_EXPAND_CONTROL_PLANE)

migrate-single-to-ha-enable-ha-lb:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0056-enable-ha-lb.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA) -e confirm_enable_ha_lb=$(CONFIRM_ENABLE_HA_LB)

migrate-single-to-ha-switch-kubeconfigs-to-vip:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0057-switch-kubeconfigs-to-vip.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA) -e confirm_switch_kubeconfigs_to_vip=$(CONFIRM_SWITCH_KUBECONFIGS_TO_VIP)

migrate-single-to-ha:
	ansible-playbook -i inventories/hosts-ha-from-single.yml 0050-single-to-ha.yml -e confirm_single_to_ha_migration=$(CONFIRM_SINGLE_TO_HA)

cleanup-container:
	ansible-playbook -i inventories/hosts-container.yml 0099-container-cleanup.yml

smoke-test:
	KUBECONFIG_PATH=$(KUBECONFIG_PATH) bash scripts/smoke-test.sh
