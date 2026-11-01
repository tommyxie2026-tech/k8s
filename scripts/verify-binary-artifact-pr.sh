#!/usr/bin/env bash
# Verify a generated binary PR against the exact successful source-build run.
# Run after checkout of the PR merge ref, before executing any PR-owned scripts.
set -euo pipefail
: "${GITHUB_REPOSITORY:?}"
: "${PR_NUMBER:?}"
: "${GH_TOKEN:?}"

pr="$(gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}")"
branch="$(jq -r '.head.ref' <<< "${pr}")"
base="$(jq -r '.base.ref' <<< "${pr}")"
base_sha="$(jq -r '.base.sha' <<< "${pr}")"
head_repo="$(jq -r '.head.repo.full_name' <<< "${pr}")"
head_sha="$(jq -r '.head.sha' <<< "${pr}")"

test "${base}" = master && test "${head_repo}" = "${GITHUB_REPOSITORY}" || {
  echo "Only same-repository binary PRs targeting master are eligible" >&2
  exit 1
}
[[ "${branch}" =~ ^artifact-pr/(amd64|arm64)/run-([1-9][0-9]*)-attempt-([1-9][0-9]*)$ ]] || {
  echo "Not a generated artifact PR branch: ${branch}" >&2
  exit 1
}
arch="${BASH_REMATCH[1]}"
run_id="${BASH_REMATCH[2]}"
attempt="${BASH_REMATCH[3]}"

# PR diff allowlist: never check out or execute changes to workflow/scripts
# from a binary submission branch.
changed="$(gh api --paginate "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}/files?per_page=100" --jq '.[].filename')"
test -n "${changed}" || { echo "Empty binary PR" >&2; exit 1; }
while IFS= read -r name; do
  case "${name}" in
    "files/${arch}/"*|"inventories/group_vars/download-checksums-${arch}.yml") ;;
    *) echo "Disallowed file in binary PR: ${name}" >&2; exit 1 ;;
  esac
done <<< "${changed}"

run="$(gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${run_id}")"
read -r source_sha run_number run_attempt < <(
  jq -r '[.head_sha, (.run_number|tostring), (.run_attempt|tostring)] | join(" ")' <<< "${run}"
)
jq -e --arg repo "${GITHUB_REPOSITORY}" \
  '.name == "Build default binaries (read-only validation)" and
   .event == "workflow_dispatch" and .head_branch == "master" and
   .head_repository.full_name == $repo and
   .status == "completed" and .conclusion == "success"' <<< "${run}" >/dev/null || {
  echo "Source run is not a successful trusted build" >&2
  exit 1
}
test "${run_attempt}" = "${attempt}" &&
  test "${source_sha}" = "${base_sha}" || {
  echo "Stale or mismatched build SHA / attempt" >&2
  exit 1
}
test "${head_sha}" = "${PR_HEAD_SHA:?}" || {
  echo "The PR head moved during verification" >&2
  exit 1
}

# Fetch only the immutable, named full-build output from the trusted run.
artifact_name="k8s-source-validation-${arch}-${run_number}-${attempt}"
gh run download "${run_id}" --repo "${GITHUB_REPOSITORY}" \
  --name "${artifact_name}" --dir .binary-source
python3 scripts/validate-binary-promotion.py \
  --root .binary-source --arch "${arch}" \
  --run-id "${run_id}" --run-attempt "${attempt}" \
  --source-sha "${source_sha}"

# Now materialize the submitted LFS objects. No executor or deployment runs.
git lfs install --local
git lfs pull origin --include="files/${arch}/**" --exclude=""
test "$(git check-attr filter -- "files/${arch}/SHA256SUMS" | awk '{print $3}')" = lfs || {
  echo "Missing binary Git LFS tracking" >&2; exit 1;
}

# In addition to checksum verification, reject extra files and symlinks.
python3 - "${arch}" <<'PY'
from pathlib import Path
import sys

arch = sys.argv[1]
directory = Path("files") / arch
sums = directory / "SHA256SUMS"
if not sums.is_file() or sums.is_symlink():
    raise SystemExit("Missing safe SHA256SUMS")
expected = set()
for line in sums.read_text(encoding="utf-8").splitlines():
    digest, sep, name = line.partition("  ./")
    if not sep or len(digest) != 64 or not all(c in "0123456789abcdef" for c in digest):
        raise SystemExit("Malformed binary checksum entry")
    path = Path(name)
    if not name or name.startswith("/") or ".." in path.parts or name in expected:
        raise SystemExit("Unsafe or duplicate binary checksum path")
    expected.add(name)
actual = set()
for path in directory.rglob("*"):
    if path.is_symlink():
        raise SystemExit("Binary PR contains symlink")
    if path.is_file() and path != sums:
        actual.add(path.relative_to(directory).as_posix())
if actual != expected or not actual:
    raise SystemExit("Checksums do not cover exactly the PR binaries")
PY

bash scripts/verify-binary-cache.sh "files/${arch}" --strict
cmp ".binary-source/files/${arch}/SHA256SUMS" "files/${arch}/SHA256SUMS"
cmp ".binary-source/inventories/group_vars/download-checksums-${arch}.yml" \
  "inventories/group_vars/download-checksums-${arch}.yml"

echo "Verified PR #${PR_NUMBER}: ${arch}, build ${run_id} attempt ${attempt}, head ${head_sha}"
