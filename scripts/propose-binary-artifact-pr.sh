#!/usr/bin/env bash
# Only run after verify-binary-cache.sh --strict and the provenance gate pass.
set -euo pipefail

: "${GITHUB_REPOSITORY:?Repository is required}"
: "${GH_TOKEN:?Configure ARTIFACT_PR_TOKEN in environment binary-artifact-pr}"
: "${ARCH:?Target architecture is required}"
: "${SOURCE_SHA:?Trusted build source SHA is required}"
: "${BUILD_RUN_ID:?Completed build run ID is required}"
: "${BUILD_RUN_ATTEMPT:?Build run attempt is required}"

case "${ARCH}" in
  amd64|arm64) ;;
  *) echo "Unsupported architecture: ${ARCH}" >&2; exit 1 ;;
esac
[[ "${SOURCE_SHA}" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid source SHA" >&2; exit 1; }
[[ "${BUILD_RUN_ID}" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid run ID" >&2; exit 1; }
[[ "${BUILD_RUN_ATTEMPT}" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid run attempt" >&2; exit 1; }
test "$(git branch --show-current)" = master || {
  echo "PR promoter must check out master, not a user-supplied PR branch" >&2
  exit 1
}
test "$(git rev-parse HEAD)" = "${SOURCE_SHA}" || {
  echo "Stale build; master SHA differs from compiled source" >&2
  exit 1
}

candidate=".binary-promotion"
test -f "${candidate}/metadata/binary-promotion.json"
test -f "${candidate}/files/${ARCH}/SHA256SUMS"
test -f "${candidate}/inventories/group_vars/download-checksums-${ARCH}.yml"

branch="artifact-pr/${ARCH}/run-${BUILD_RUN_ID}-attempt-${BUILD_RUN_ATTEMPT}"
# A limited PAT / GitHub App token provides PR write and Git LFS access here.
# Build jobs never receive this credential.
gh auth setup-git

existing="$(gh pr list --repo "${GITHUB_REPOSITORY}" \
  --state all --head "${branch}" --json number --jq 'length')"
if [[ "${existing}" != 0 ]]; then
  echo "Artifact PR already exists for ${branch}; refusing duplicate"
  exit 0
fi
if git ls-remote --exit-code --heads origin "refs/heads/${branch}" >/dev/null; then
  echo "Candidate branch ${branch} exists; refusing overwrite" >&2
  exit 1
fi

git lfs install --local
git switch -c "${branch}"

# Replace only the verified target architecture, never the other architecture.
rm -rf -- "files/${ARCH}"
mkdir -p -- "files/${ARCH}" inventories/group_vars
cp -a -- "${candidate}/files/${ARCH}/." "files/${ARCH}/"
cp -- "${candidate}/inventories/group_vars/download-checksums-${ARCH}.yml" \
  "inventories/group_vars/download-checksums-${ARCH}.yml"

test "$(git check-attr filter -- "files/${ARCH}/SHA256SUMS" | awk '{print $3}')" = lfs || {
  echo "files/${ARCH} is not Git LFS-tracked" >&2
  exit 1
}
git add -A -f -- "files/${ARCH}" "inventories/group_vars/download-checksums-${ARCH}.yml"

while IFS= read -r file; do
  case "${file}" in
    "files/${ARCH}/"*|"inventories/group_vars/download-checksums-${ARCH}.yml") ;;
    *) echo "Out-of-scope staged path: ${file}" >&2; exit 1 ;;
  esac
done < <(git diff --cached --name-only)

if git diff --cached --quiet; then
  echo "No binary or checksum changes for ${ARCH}; PR not necessary"
  exit 0
fi

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git commit -m "build(binary): propose verified ${ARCH} artifacts from run ${BUILD_RUN_ID}"

# Upload LFS objects before making the branch visible.
git lfs push origin HEAD
git push origin "HEAD:refs/heads/${branch}"

body="$(mktemp)"
trap 'rm -f "${body}"' EXIT
cat > "${body}" <<EOF
## Source build evidence
- Architecture: \`${ARCH}\`
- Source commit: \`${SOURCE_SHA}\`
- GitHub Actions run: https://github.com/${GITHUB_REPOSITORY}/actions/runs/${BUILD_RUN_ID}
- Run attempt: \`${BUILD_RUN_ATTEMPT}\`
- Mode: source, \`stage=all\`, \`strict_package=true\`
- Integrity: SHA256SUMS, strict deploy-archive verification, and Ansible checksum mapping rechecked

## Changes
- \`files/${ARCH}/\` (Git LFS binaries and SHA256SUMS)
- \`inventories/group_vars/download-checksums-${ARCH}.yml\`

**Automated merge gate**: this PR is eligible for squash merge only after the standard CI and binary-integrity verification succeed for this exact commit, the source SHA still equals current master, and GitHub branch protections permit it. No deployment or binary-cache publication is performed. Check build logs, versions, provenance and Git LFS quota.
EOF

gh pr create \
  --repo "${GITHUB_REPOSITORY}" \
  --base master \
  --head "${branch}" \
  --title "build(binary): deliver verified ${ARCH} artifacts (run ${BUILD_RUN_ID})" \
  --body-file "${body}"
