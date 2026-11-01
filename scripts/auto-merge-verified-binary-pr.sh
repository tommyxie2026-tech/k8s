#!/usr/bin/env bash
# Called ONLY from the protected promotion workflow, never on PR-owned scripts.
# Do not bypass GitHub required reviews or status checks.
set -euo pipefail

: "${GITHUB_REPOSITORY:?}"
: "${GH_TOKEN:?Set ARTIFACT_PR_TOKEN only in binary-artifact-pr environment}"
: "${PR_NUMBER:?}"
: "${EXPECTED_HEAD_SHA:?}"

[[ "${PR_NUMBER}" =~ ^[1-9][0-9]*$ ]] || exit 1
[[ "${EXPECTED_HEAD_SHA}" =~ ^[0-9a-f]{40}$ ]] || exit 1

pr="$(gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}")"
head="$(jq -r '.head.sha' <<< "${pr}")"
branch="$(jq -r '.head.ref' <<< "${pr}")"
base="$(jq -r '.base.ref' <<< "${pr}")"
base_sha="$(jq -r '.base.sha' <<< "${pr}")"
repo="$(jq -r '.head.repo.full_name' <<< "${pr}")"
state="$(jq -r '.state' <<< "${pr}")"
draft="$(jq -r '.draft' <<< "${pr}")"

test "${state}" = open && test "${draft}" = false &&
  test "${repo}" = "${GITHUB_REPOSITORY}" &&
  test "${base}" = master && test "${head}" = "${EXPECTED_HEAD_SHA}" || {
  echo "PR state or source identity changed; refusing merge" >&2
  exit 1
}

[[ "${branch}" =~ ^artifact-pr/(amd64|arm64)/run-([1-9][0-9]*)-attempt-([1-9][0-9]*)$ ]] || {
  echo "Not an eligible generated binary PR" >&2
  exit 1
}
arch="${BASH_REMATCH[1]}"
run_id="${BASH_REMATCH[2]}"
attempt="${BASH_REMATCH[3]}"

# Pin the compiled master SHA; no stale binary PR is ever merged.
master_sha="$(gh api "repos/${GITHUB_REPOSITORY}/git/ref/heads/master" --jq '.object.sha')"
source="$(gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${run_id}")"
source_sha="$(jq -r '.head_sha' <<< "${source}")"
source_attempt="$(jq -r '.run_attempt' <<< "${source}")"
if [[ "${base_sha}" != "${master_sha}" ||
      "${source_sha}" != "${master_sha}" ||
      "${source_attempt}" != "${attempt}" ]]; then
  echo "Build and current master are not identical; refusing auto-merge" >&2
  exit 1
fi
jq -e --arg repository "${GITHUB_REPOSITORY}" \
  '.name == "Build default binaries (read-only validation)" and
   .event == "workflow_dispatch" and .head_branch == "master" and
   .head_repository.full_name == $repository and .conclusion == "success" and
   .status == "completed"' <<< "${source}" >/dev/null || {
  echo "Original full build is not trustworthy" >&2
  exit 1
}

# Whitelist exact architecture files, rejecting any changed CI/script/source.
paths="$(gh api --paginate "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}/files?per_page=100" --jq '.[].filename')"
test -n "${paths}" || exit 1
while IFS= read -r file; do
  case "${file}" in
    "files/${arch}/"*|"inventories/group_vars/download-checksums-${arch}.yml") ;;
    *) echo "Refusing non-binary PR path: ${file}" >&2; exit 1 ;;
  esac
done <<< "${paths}"

# Both workflows must have completed *successfully* for the exact current
# candidate SHA. No check skipping or admin bypass.
for workflow in ci.yml verify-binary-artifact-pr.yml; do
  result="$(gh api "repos/${GITHUB_REPOSITORY}/actions/workflows/${workflow}/runs?event=pull_request&head_sha=${head}&per_page=100")"
  jq -e --arg sha "${head}" --arg branch "${branch}" \
    '.workflow_runs |
     any(.head_sha == $sha and .head_branch == $branch and
         .status == "completed" and .conclusion == "success")' \
    <<< "${result}" >/dev/null || {
    echo "Required workflow ${workflow} is not green for exact candidate ${head}" >&2
    exit 1
  }
done

echo "All verified binary PR merge gates passed for PR #${PR_NUMBER}, ${arch}"
# GitHub enforces protected-branch review and required checks; never --admin.
gh pr merge "${PR_NUMBER}" --repo "${GITHUB_REPOSITORY}" \
  --squash --match-head-commit "${head}"
