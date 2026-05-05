#!/usr/bin/env bash
# publish.sh — Compile, version, and distribute the thesis PDF.
#
# Usage:
#   bash publish.sh              # auto-version with today's date
#   bash publish.sh v1.2         # explicit version tag
#
set -euo pipefail

THESIS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROTEA_DIR="$THESIS_DIR/../repositories/PROTEA"
VERSIONS_DIR="$THESIS_DIR/versions"

# ── 1. Compile LaTeX ────────────────────────────────────────────
cd "$THESIS_DIR"
echo "Compiling thesis..."
latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error thesis.tex 2>&1 | tail -3

if [[ ! -f thesis.pdf ]]; then
    echo "ERROR: compilation failed — thesis.pdf not produced."
    exit 1
fi

# ── 2. Version tag ──────────────────────────────────────────────
if [[ -n "${1:-}" ]]; then
    TAG="$1"
else
    TAG="$(date +%Y-%m-%d)"
    # Append -N suffix if same-day version already exists
    if [[ -f "$VERSIONS_DIR/thesis-${TAG}.pdf" ]]; then
        N=2
        while [[ -f "$VERSIONS_DIR/thesis-${TAG}-${N}.pdf" ]]; do
            ((N++))
        done
        TAG="${TAG}-${N}"
    fi
fi

# ── 3. Archive versioned copy ──────────────────────────────────
mkdir -p "$VERSIONS_DIR"
cp thesis.pdf "$VERSIONS_DIR/thesis-${TAG}.pdf"
echo "Archived: versions/thesis-${TAG}.pdf"

# ── 4. Distribute to serving locations ─────────────────────────
cp thesis.pdf "$PROTEA_DIR/static/thesis.pdf"
cp thesis.pdf "$PROTEA_DIR/apps/web/public/thesis.pdf"
echo "Distributed to static/ and apps/web/public/"

# ── 5. Summary ─────────────────────────────────────────────────
echo ""
echo "Published thesis-${TAG}.pdf"
ls -lh "$VERSIONS_DIR"/thesis-*.pdf | awk '{print "  " $5 "  " $NF}'
