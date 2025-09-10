#!/usr/bin/env bash
# =============================================================================
# deploy_and_test.sh — Deploy PermitFlow-AI to Azure and run smoke tests.
#
# Responsibilities:
# - Deploy the FastAPI app to Azure App Service.
# - Run HTTP and WebSocket smoke tests against the deployed app.
# - Provide clear, color-coded output for quick status checks.
#
# Usage:
#   ./devops/deploy_and_test.sh              # Deploy + test
#   ./devops/deploy_and_test.sh --test-only  # Test only, no deploy
#
# Prerequisites:
# - Azure CLI logged in (`az login`)
# - Python 3.12+ (script will auto-install requests + websocket-client if missing)
# =============================================================================

clear
set -euo pipefail

# ====== CONFIG ======
APP_NAME="permitflow-ai-demo"
RESOURCE_GROUP="PermitFlowAI-RG"
LOCATION="eastus2"
SKU="F1"
BASE_URL="https://${APP_NAME}.azurewebsites.net"
WS_PATH="/ws/flowbot"
TOLLGATE_PROMPTS_FILE="app/permitFlowDb/tollgate_prompts.json"

# ANSI colors
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m"

# ====== PRE-FLIGHT CHECKS ======
command -v az >/dev/null 2>&1 || { echo -e "${RED}Azure CLI not found. Install Azure CLI first.${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python 3 not found.${NC}"; exit 1; }

# Confirm importlib.util is importable
python3 - <<'EOF'
import sys
try:
    import importlib.util
except ImportError:
    sys.exit("❌ 'importlib.util' not available — possible shadowing.")
EOF

# Ensure Python deps for smoke tests
python3 - <<'EOF'
import importlib.util, subprocess, sys
missing = []
for pkg, import_name in [("requests", "requests"), ("websocket-client", "websocket")]:
    if importlib.util.find_spec(import_name) is None:
        missing.append(pkg)
if missing:
    print(f"📥 Installing missing packages: {', '.join(missing)}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
EOF

# Validate prompts file
if [[ ! -s "$TOLLGATE_PROMPTS_FILE" ]]; then
    echo -e "${RED}❌ Prompts file missing or empty: $TOLLGATE_PROMPTS_FILE${NC}"
    exit 1
fi

# ====== FUNCTIONS ======
run_smoke_tests() {
python3 - <<EOF
"""
Smoke tests for PermitFlow-AI deployment.
"""
import requests, websocket, ssl, time, uuid

BASE_URL = "$BASE_URL"
WS_PATH = "$WS_PATH"
SESSION_ID = str(uuid.uuid4())

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

STATUS_WIDTH = 8
PATH_WIDTH = 20

def fmt(tag):
    colors = {
        "ok": GREEN + "[OK]" + NC,
        "fail": RED + "[FAIL]" + NC,
        "error": RED + "[ERROR]" + NC,
        "info": YELLOW + "[INFO]" + NC
    }
    return colors[tag].ljust(STATUS_WIDTH + len(colors[tag]) - 4)

def check_http(path):
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()
    try:
        r = requests.get(url, timeout=10)
        elapsed = (time.perf_counter() - start) * 1000
        if r.status_code == 200:
            print(f"{fmt('ok')}{path.ljust(PATH_WIDTH)}→ {r.status_code}  ({elapsed:.1f} ms)")
            if path == "/health":
                print(f"{' ' * STATUS_WIDTH}{' ' * PATH_WIDTH}   Payload: {r.json()}")
        else:
            print(f"{fmt('fail')}{path.ljust(PATH_WIDTH)}→ {r.status_code}  ({elapsed:.1f} ms)")
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{fmt('error')}{path.ljust(PATH_WIDTH)}→ {e}  ({elapsed:.1f} ms)")

def check_websocket_full_flow():
    ws_url = BASE_URL.replace("https", "wss") + f"{WS_PATH}?avatar=FlowBot&session={SESSION_ID}"
    print(f"{fmt('info')}{'WebSocket connect'.ljust(PATH_WIDTH)}→ {ws_url}")
    start = time.perf_counter()
    try:
        ws = websocket.create_connection(ws_url, sslopt={"cert_reqs": ssl.CERT_NONE}, timeout=10)
        handshake_time = (time.perf_counter() - start) * 1000
        print(f"{fmt('ok')}{'Handshake'.ljust(PATH_WIDTH)}→ {handshake_time:.1f} ms")

        steps = [
            ("Permit to Design", "TG1 start"),
            ("The purpose is to expedite tollgate approvals for project managers", "Purpose reply"),
            ("The service name is PermitFlow", "Service name reply"),
            ("The owner is Bill Bettini", "Owner reply"),
            ("The data classification is non private", "Data class reply"),
        ]

        for msg, label in steps:
            ws.send(msg)
            reply = ws.recv()
            print(f"{fmt('ok')}{label.ljust(PATH_WIDTH)}→ {reply}")

        for label in ("TG2 SME review", "TG3 final"):
            reply = ws.recv()
            print(f"{fmt('ok')}{label.ljust(PATH_WIDTH)}→ {reply}")

        ws.close()
    except Exception as e:
        print(f"{fmt('error')}{'WebSocket test'.ljust(PATH_WIDTH)}→ {e}")

print(f"{YELLOW}Running smoke tests against {BASE_URL}...{NC}\n")
check_http("/")
check_http("/health")
check_http("/docs")
check_websocket_full_flow()
EOF
}

# ====== MAIN FLOW ======
if [[ "${1:-}" == "--test-only" ]]; then
    echo -e "${YELLOW}🔍 Running smoke tests only (no deploy)...${NC}"
    run_smoke_tests
else
    echo -e "${YELLOW}⚙️  Setting Azure startup command to app.main:app...${NC}"
    az webapp config set \
      --name "$APP_NAME" \
      --resource-group "$RESOURCE_GROUP" \
      --startup-file "gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0:\$PORT --timeout 600"

    echo -e "${YELLOW}🚀 Deploying $APP_NAME to Azure Web App ($LOCATION, $SKU)...${NC}"
    az webapp up \
      --name "$APP_NAME" \
      --resource-group "$RESOURCE_GROUP" \
      --runtime "PYTHON:3.12" \
      --sku "$SKU" \
      --location "$LOCATION"

    echo ""
    echo -e "${GREEN}✅ Deploy complete. Running smoke tests...${NC}"
    run_smoke_tests
fi