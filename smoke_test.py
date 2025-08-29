import requests
import websocket
import json
import ssl

BASE_URL = "https://permitflow-ai-demo.azurewebsites.net"
WS_PATH = "/ws/flowbot"

# Column widths
STATUS_WIDTH = 8
PATH_WIDTH = 20

def format_status(label, status_type="info"):
    if status_type == "ok":
        return f"[OK]".ljust(STATUS_WIDTH)
    elif status_type == "fail":
        return f"[FAIL]".ljust(STATUS_WIDTH)
    elif status_type == "error":
        return f"[ERROR]".ljust(STATUS_WIDTH)
    else:
        return f"[INFO]".ljust(STATUS_WIDTH)

def check_http(path):
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, timeout=10)
        status = r.status_code
        if status == 200:
            print(f"{format_status('ok','ok')}{path.ljust(PATH_WIDTH)}→ {status}")
            if path == "/health":
                print(f"{' ' * STATUS_WIDTH}{' ' * PATH_WIDTH}   Payload: {r.json()}")
        else:
            print(f"{format_status('fail','fail')}{path.ljust(PATH_WIDTH)}→ {status}")
    except Exception as e:
        print(f"{format_status('error','error')}{path.ljust(PATH_WIDTH)}→ {e}")

def check_websocket():
    ws_url = BASE_URL.replace("https", "wss") + WS_PATH
    print(f"{format_status('info')}{'WebSocket connect'.ljust(PATH_WIDTH)}→ {ws_url}")
    try:
        ws = websocket.create_connection(ws_url, sslopt={"cert_reqs": ssl.CERT_NONE}, timeout=10)
        test_message = {"message": "Hello from smoke test!"}
        ws.send(json.dumps(test_message))
        response = ws.recv()
        print(f"{format_status('ok','ok')}{'WebSocket message'.ljust(PATH_WIDTH)}→ {response}")
        ws.close()
    except Exception as e:
        print(f"{format_status('error','error')}{'WebSocket test'.ljust(PATH_WIDTH)}→ {e}")

if __name__ == "__main__":
    print(f"Running smoke tests against {BASE_URL}...\n")
    check_http("/")         # FlowBot UI
    check_http("/health")   # Health check JSON
    check_http("/docs")     # FastAPI docs
    check_websocket()       # WebSocket handshake + message