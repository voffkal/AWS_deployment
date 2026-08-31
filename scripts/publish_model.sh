#!/bin/bash
#
# Build the model package and publish the wheel as a GitHub Release asset.
#
# The course used a private Gemfury index for this. GitHub Releases does the
# same job for free: the wheel is a versioned, downloadable artifact, and the
# API installs it as an ordinary pinned dependency. What is published is the
# package built from THIS commit, so the release tag, the package version and
# the trained model inside it all line up.
#
# Requires: gh (authenticated via GH_TOKEN), python with build installed.
# Usage:    ./scripts/publish_model.sh ./packages/regression_model/

set -euo pipefail

DIRS="$@"
BASE_DIR=$(pwd)

warn() { echo "$@" 1>&2; }
die()  { warn "$@"; exit 1; }

command -v gh >/dev/null || die "gh CLI is required"
[ -n "${GH_TOKEN:-}" ] || warn "GH_TOKEN is not set - gh must be authenticated another way"

publish() {
    local dir="${1/%\//}"
    cd "$BASE_DIR/$dir"
    [ -e setup.py ] || { warn "No setup.py in $dir, skipping"; return; }

    local version tag
    version=$(python setup.py --version)
    tag="model-v${version}"

    echo "Building $(python setup.py --name) ${version}"
    rm -rf dist
    python -m build --wheel --outdir dist . || die "Building the wheel failed"

    # The wheel must carry the trained pipeline; without it the package
    # imports but blows up on the first prediction.
    python - "$version" <<'PY' || die "the wheel has no trained model in it - run train_pipeline.py first"
import glob, sys, zipfile
whl = glob.glob("dist/*.whl")[0]
names = zipfile.ZipFile(whl).namelist()
sys.exit(0 if any(n.endswith(".pkl") for n in names) else 1)
PY

    cd "$BASE_DIR"
    if gh release view "$tag" >/dev/null 2>&1; then
        echo "Release $tag exists - uploading over it"
        gh release upload "$tag" "$dir"/dist/*.whl --clobber
    else
        gh release create "$tag" "$dir"/dist/*.whl \
            --title "$tag" \
            --notes "Model package ${version}, built from ${GITHUB_SHA:-$(git rev-parse HEAD)}."
    fi
    echo "Published $tag"
}

[ -n "$DIRS" ] || die "usage: $0 <package-dir> [...]"
for d in $DIRS; do publish "$d"; done
