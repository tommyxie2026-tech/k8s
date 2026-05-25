.PHONY: syntax-check syntax-check-single preflight-container deploy-container deploy-single cleanup-container smoke-test

INVENTORY ?= inventories/hosts-container.yml
KUBECONFIG_PATH ?= $(HOME)/.kube/config

syntax-check:
	INVENTORY=$(INVENTORY) bash scripts/syntax-check.sh

syntax-check-single:
	INVENTORY=inventories/hosts-single.yml bash scripts/syntax-check.sh

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

cleanup-container:
	ansible-playbook -i inventories/hosts-container.yml 0099-container-cleanup.yml

smoke-test:
	KUBECONFIG_PATH=$(KUBECONFIG_PATH) bash scripts/smoke-test.sh
