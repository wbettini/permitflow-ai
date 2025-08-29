#!/usr/bin/env bash
set -e

# ====== CONFIG ======
APP_NAME="permitflow-ai-demo"
RESOURCE_GROUP="PermitFlowAI-RG"
LOCATION="eastus2"
SKU="F1"
BASE_URL="https://$APP_NAME.azurewebsites.net"
WS_PATH="/ws/flowbot"

# ====== MAIN ======
run_smoke_tests() {
python3 - <<EOF
import requests, websocket, json, ssl, time

BASE_URL = "$BASE_URL"
WS_PATH = "$WS_PATH"

# ANSI colors
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
        elapsed = (time.perf_counter() - start) * 1000  # ms
        if r.status_code == 200:
            print(f"{fmt('ok')}{path.ljust(PATH_WIDTH)}→ {r.status_code}  ({elapsed:.1f} ms)")
            if path == "/health":
                print(f"{' ' * STATUS_WIDTH}{' ' * PATH_WIDTH}   Payload: {r.json()}")
        else:
            print(f"{fmt('fail')}{path.ljust(PATH_WIDTH)}→ {r.status_code}  ({elapsed:.1f} ms)")
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{fmt('error')}{path.ljust(PATH_WIDTH)}→ {e}  ({elapsed:.1f} ms)")

def check_websocket():
    ws_url = BASE_URL.replace("https", "wss") + WS_PATH
    print(f"{fmt('info')}{'WebSocket connect'.ljust(PATH_WIDTH)}→ {ws_url}")
    start = time.perf_counter()
    try:
        ws = websocket.create_connection(ws_url, sslopt={"cert_reqs": ssl.CERT_NONE}, timeout=10)
        handshake_time = (time.perf_counter() - start) * 1000
        print(f"{fmt('ok')}{'Handshake'.ljust(PATH_WIDTH)}→ {handshake_time:.1f} ms")
        test_message = {"message": "Hello from smoke test!"}
        ws.send(json.dumps(test_message))
        msg_start = time.perf_counter()
        response = ws.recv()
        msg_time = (time.perf_counter() - msg_start) * 1000
        print(f"{fmt('ok')}{'Message roundtrip'.ljust(PATH_WIDTH)}→ {msg_time:.1f} ms | {response}")
        ws.close()
    except Exception as e:
        print(f"{fmt('error')}{'WebSocket test'.ljust(PATH_WIDTH)}→ {e}")

print(f"{YELLOW}Running smoke tests against {BASE_URL}...{NC}\n")
check_http("/")
check_http("/health")
check_http("/docs")
check_websocket()
EOF
}

if [[ "$1" == "--test-only" ]]; then
    echo -e "${YELLOW}🔍 Running smoke tests only (no deploy)...${NC}"
    run_smoke_tests
else
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