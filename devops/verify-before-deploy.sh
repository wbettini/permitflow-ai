#!/usr/bin/env bash
# =============================================================================
# verify-before-deploy.sh — Local import check before Azure deployment
#
# Purpose:
#   Simulate Azure's fresh environment by creating a temporary virtualenv,
#   installing only production dependencies from requirements.txt, and
#   starting uvicorn to ensure there are no ModuleNotFoundError issues.
#
# Usage:
#   ./devops/verify-before-deploy.sh
#
# Notes:
#   - Runs from any location; paths are resolved relative to this script.
#   - Creates a throwaway venv in /tmp and deletes it after the check.
#   - Fails fast if dependencies are missing or app fails to start.
# =============================================================================

set -euo pipefail
clear; 

# ====== PATH SETUP ======
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REQ_FILE="$REPO_ROOT/requirements.txt"
REQ_DEV_FILE="$REPO_ROOT/requirements-dev.txt"

# ====== PRE-FLIGHT CHECKS ======
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not found."; exit 1; }
command -v uvicorn >/dev/null 2>&1 || { echo "❌ uvicorn not found. Install with: pip install uvicorn"; exit 1; }

if [[ ! -f "$REQ_FILE" ]]; then
    echo "❌ requirements.txt not found in repo root: $REQ_FILE"
    exit 1
fi

# ====== CREATE TEMP VENV ======
TMP_VENV=$(mktemp -d /tmp/permitflow_venv_XXXX)
echo "📦 Creating temporary virtual environment at $TMP_VENV..."
python3 -m venv "$TMP_VENV"
# shellcheck disable=SC1090
source "$TMP_VENV/bin/activate"

# ====== INSTALL DEPENDENCIES ======
echo "📥 Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r "$REQ_FILE"

# ====== RUN UVICORN IMPORT CHECK ======
echo "🚀 Starting uvicorn to verify imports..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

UVICORN_PID=$!
sleep 3  # Give it a moment to start

if ps -p $UVICORN_PID > /dev/null; then
    echo "✅ App started successfully — no missing modules detected."
    kill $UVICORN_PID
else
    echo "❌ App failed to start — check logs above for missing imports."
    deactivate || true
    rm -rf "$TMP_VENV"
    exit 1
fi

# ====== CLEANUP ======
echo "🧹 Cleaning up temporary environment..."
deactivate || true
rm -rf "$TMP_VENV"

# ====== RESTORE DEV ENVIRONMENT ======
if [[ -f "$REQ_DEV_FILE" ]]; then
    echo "🔄 Restoring local dev environment from requirements-dev.txt..."
    pip install -r "$REQ_DEV_FILE"
    echo "✅ Dev environment restored."
else
    echo "ℹ️ No requirements-dev.txt found — skipping dev restore."
fi

echo "✅ Verification complete. Safe to deploy."
