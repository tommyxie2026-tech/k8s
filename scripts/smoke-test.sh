#!/usr/bin/env bash
set -euo pipefail

KUBECONFIG_PATH="${KUBECONFIG_PATH:-${HOME}/.kube/config}"
NAMESPACE="${SMOKE_NAMESPACE:-default}"
APP_NAME="${SMOKE_APP_NAME:-smoke-nginx}"
CLIENT_NAME="${SMOKE_CLIENT_NAME:-smoke-client}"
TIMEOUT="${SMOKE_TIMEOUT:-180s}"

export KUBECONFIG="${KUBECONFIG_PATH}"

echo "==> Checking cluster nodes"
kubectl get nodes -o wide

echo "==> Checking system pods"
kubectl get pods -A

echo "==> Creating smoke deployment"
kubectl -n "${NAMESPACE}" create deployment "${APP_NAME}" --image=nginx:alpine --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "${NAMESPACE}" rollout status deployment/"${APP_NAME}" --timeout="${TIMEOUT}"

if ! kubectl -n "${NAMESPACE}" get service "${APP_NAME}" >/dev/null 2>&1; then
  kubectl -n "${NAMESPACE}" expose deployment "${APP_NAME}" --port=80 --target-port=80
fi

echo "==> Verifying DNS and service connectivity"
kubectl -n "${NAMESPACE}" run "${CLIENT_NAME}" \
  --rm \
  --restart=Never \
  --image=curlimages/curl:latest \
  --command -- curl -fsS "http://${APP_NAME}.${NAMESPACE}.svc.cluster.local"

echo "==> Cleaning smoke resources"
kubectl -n "${NAMESPACE}" delete service "${APP_NAME}" --ignore-not-found=true
kubectl -n "${NAMESPACE}" delete deployment "${APP_NAME}" --ignore-not-found=true

echo "==> Smoke test passed"
