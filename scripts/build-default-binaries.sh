#!/usr/bin/env bash
set -euo pipefail

ARCH="${ARCH:-amd64}"
SOURCES_FILE="${SOURCES_FILE:-repo/sources.yml}"
WORK_DIR="${WORK_DIR:-.build/src}"
FILES_DIR="${FILES_DIR:-files/${ARCH}}"
BUILD_COMPONENTS="${BUILD_COMPONENTS:-all}"

mkdir -p "${WORK_DIR}" "${FILES_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

if ! python3 -c 'import yaml' >/dev/null 2>&1; then
  echo "PyYAML is required. Install with: python3 -m pip install pyyaml" >&2
  exit 1
fi

render_template() {
  local value="$1"
  value="${value//\{\{ arch \}\}/${ARCH}}"
  echo "${value}"
}

component_enabled() {
  local component="$1"
  if [[ "${BUILD_COMPONENTS}" == "all" ]]; then
    return 0
  fi
  IFS=',' read -ra parts <<< "${BUILD_COMPONENTS}"
  for part in "${parts[@]}"; do
    if [[ "${part}" == "${component}" ]]; then
      return 0
    fi
  done
  return 1
}

read_manifest() {
  python3 - "$SOURCES_FILE" <<'PY'
import sys, yaml, json
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)
for item in data.get('components', []):
    print(json.dumps({'kind':'component', **item}, ensure_ascii=False))
for item in data.get('manifests', []):
    print(json.dumps({'kind':'manifest', **item}, ensure_ascii=False))
PY
}

clone_or_update() {
  local component="$1"
  local git_url="$2"
  local tag="$3"
  local dest="${WORK_DIR}/${component}"

  if [[ -d "${dest}/.git" ]]; then
    echo "==> updating ${component}"
    git -C "${dest}" fetch --tags --force
  else
    echo "==> cloning ${component}: ${git_url}"
    git clone --filter=blob:none "${git_url}" "${dest}"
    git -C "${dest}" fetch --tags --force
  fi

  git -C "${dest}" checkout --force "${tag}"
  git -C "${dest}" clean -fdx
}

copy_output() {
  local component="$1"
  local src="$2"
  local dest="$3"
  local archive="${4:-}"
  local component_dir="${WORK_DIR}/${component}"

  src="$(render_template "${src}")"
  dest="$(render_template "${dest}")"
  archive="$(render_template "${archive}")"

  if [[ -n "${archive}" ]]; then
    echo "==> archive ${component}: ${archive}"
    tar -C "${component_dir}/${src}" -czf "${FILES_DIR}/${archive}" .
    return 0
  fi

  if [[ -d "${component_dir}/${src}" ]]; then
    mkdir -p "${FILES_DIR}/${dest}"
    rsync -a --delete "${component_dir}/${src}/" "${FILES_DIR}/${dest}/"
  else
    cp "${component_dir}/${src}" "${FILES_DIR}/${dest}"
    chmod +x "${FILES_DIR}/${dest}" || true
  fi
}

while IFS= read -r line; do
  kind=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["kind"])' "$line")
  component=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["component"])' "$line")

  if ! component_enabled "${component}"; then
    echo "==> skip ${component}"
    continue
  fi

  if [[ "${kind}" == "manifest" ]]; then
    source_url=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["source"])' "$line")
    dest=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["dest"])' "$line")
    echo "==> download manifest ${component}: ${source_url}"
    curl -fL --retry 3 --retry-delay 2 -o "${FILES_DIR}/${dest}" "${source_url}"
    continue
  fi

  git_url=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["git"])' "$line")
  tag=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["tag"])' "$line")
  command=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["build"]["command"])' "$line")

  clone_or_update "${component}" "${git_url}" "${tag}"

  echo "==> build ${component} ${tag}"
  env_args=()
  while IFS= read -r env_line; do
    key="${env_line%%=*}"
    value="${env_line#*=}"
    value="$(render_template "${value}")"
    env_args+=("${key}=${value}")
  done < <(python3 -c 'import json,sys; d=json.loads(sys.argv[1])["build"].get("env",{}); [print(f"{k}={v}") for k,v in d.items()]' "$line")

  (cd "${WORK_DIR}/${component}" && env "${env_args[@]}" bash -lc "${command}")

  outputs_json=$(python3 -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1]).get("outputs", [])))' "$line")
  python3 - "$outputs_json" <<'PY' > "${WORK_DIR}/${component}.outputs"
import sys, json
for out in json.loads(sys.argv[1]):
    src = out.get('src', '')
    dest = out.get('dest', '')
    archive = out.get('archive', '')
    print(src + '\t' + dest + '\t' + archive)
PY
  while IFS=$'\t' read -r src dest archive; do
    copy_output "${component}" "${src}" "${dest}" "${archive}"
  done < "${WORK_DIR}/${component}.outputs"
done < <(read_manifest)

find "${FILES_DIR}" -type f -maxdepth 2 -print0 | sort -z | xargs -0 sha256sum > "${FILES_DIR}/SHA256SUMS"

echo "==> build outputs are ready in ${FILES_DIR}"
echo "==> checksum file: ${FILES_DIR}/SHA256SUMS"
