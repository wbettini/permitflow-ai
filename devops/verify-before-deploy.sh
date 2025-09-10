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

clear
set -euo pipefail

# ====== CONFIG / PATHS ======
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REQ_FILE="$REPO_ROOT/requirements.txt"
REQ_DEV_FILE="$REPO_ROOT/requirements-dev.txt"
TEXT_UTILS="$REPO_ROOT/app/utils/text_utils.py"

# ANSI colors
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m"

# ====== PRE-FLIGHT CHECKS ======
command -v python3 >/dev/null 2>&1 || {
    echo -e "${RED}❌ Python 3 not found.${NC}"
    exit 1
}

# Confirm importlib.util is actually importable (no false positives)
python3 - <<'EOF'
import sys
try:
    import importlib.util
except ImportError:
    sys.exit("❌ 'importlib.util' not available — possible shadowing.")
EOF

# Ensure uvicorn is installed globally (for the check)
if ! python3 -c "import uvicorn" >/dev/null 2>&1; then
    echo -e "${YELLOW}📥 Installing uvicorn for verification...${NC}"
    pip install uvicorn
fi

# Confirm requirements.txt exists
if [[ ! -f "$REQ_FILE" ]]; then
    echo -e "${RED}❌ requirements.txt not found in repo root: $REQ_FILE${NC}"
    exit 1
fi

# Confirm text_utils.py exists
if [[ ! -f "$TEXT_UTILS" ]]; then
    echo -e "${RED}❌ Missing expected module: app/utils/text_utils.py${NC}"
    exit 1
fi

# Confirm app.main:app is importable
echo -e "${YELLOW}🔍 Verifying app.main:app import path...${NC}"
python3 -c "from app.main import app" || {
    echo -e "${RED}❌ Could not import 'app.main:app'. Check your module structure.${NC}"
    exit 1
}

# ====== CREATE TEMP VENV ======
TMP_VENV=$(mktemp -d /tmp/permitflow_venv_XXXX)
echo -e "${YELLOW}📦 Creating temporary virtual environment at $TMP_VENV...${NC}"
python3 -m venv "$TMP_VENV"
# shellcheck disable=SC1090
source "$TMP_VENV/bin/activate"

# ====== INSTALL DEPENDENCIES ======
echo -e "${YELLOW}📥 Installing dependencies from requirements.txt...${NC}"
pip install --upgrade pip
pip install -r "$REQ_FILE"

# ====== RUN UVICORN IMPORT CHECK ======
echo -e "${YELLOW}🚀 Starting uvicorn to verify imports...${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level warning &

UVICORN_PID=$!
sleep 3  # Give it a moment to start

if ps -p $UVICORN_PID > /dev/null; then
    echo -e "${GREEN}✅ App started successfully — no missing modules detected.${NC}"
    kill $UVICORN_PID
else
    echo -e "${RED}❌ App failed to start — check logs above for missing imports.${NC}"
    deactivate || true
    rm -rf "$TMP_VENV"
    exit 1
fi

# ====== CLEANUP ======
echo -e "${YELLOW}🧹 Cleaning up temporary environment...${NC}"
deactivate || true
rm -rf "$TMP_VENV"

# ====== RESTORE DEV ENVIRONMENT ======
if [[ -f "$REQ_DEV_FILE" ]]; then
    echo -e "${YELLOW}🔄 Restoring local dev environment from requirements-dev.txt...${NC}"
    pip install -r "$REQ_DEV_FILE"
    echo -e "${GREEN}✅ Dev environment restored.${NC}"
else
    echo -e "${YELLOW}ℹ️ No requirements-dev.txt found — skipping dev restore.${NC}"
fi

echo -e "${GREEN}✅ Verification complete. Safe to deploy.${NC}"