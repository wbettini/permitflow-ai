import os
import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = "monitoring/smoketest_results.csv"
IMG_PATH = "monitoring/latency_trends.png"

# Ensure monitoring folder exists
os.makedirs("monitoring", exist_ok=True)

# If CSV doesn't exist, create it with headers
if not os.path.isfile(CSV_PATH):
    print(f"⚠️ No CSV found at {CSV_PATH}. Creating empty file...")
    with open(CSV_PATH, "w") as f:
        f.write("timestamp,endpoint,status,response_time_ms\n")

# Load CSV
df = pd.read_csv(CSV_PATH)

# If no data rows, make an empty chart
if df.empty:
    print("ℹ️ CSV is empty — generating placeholder chart.")
    plt.figure(figsize=(8, 5))
    plt.text(0.5, 0.5, "No data yet", ha="center", va="center", fontsize=16, alpha=0.7)
    plt.axis("off")
    plt.savefig(IMG_PATH, dpi=150)
    print(f"✅ Placeholder chart saved to {IMG_PATH}")
else:
    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("timestamp")

    # Filter OK results for latency plotting
    ok_df = df[df["status"] == "OK"]

    plt.figure(figsize=(10, 6))
    for endpoint in ok_df["endpoint"].unique():
        ep_data = ok_df[ok_df["endpoint"] == endpoint]
        plt.plot(ep_data["timestamp"], ep_data["response_time_ms"],
                 marker="o", label=endpoint)

    plt.title("Azure Smoke Test Latency Trends")
    plt.xlabel("Date/Time (UTC)")
    plt.ylabel("Response Time (ms)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(IMG_PATH, dpi=150)
    print(f"✅ Latency trend chart saved to {IMG_PATH}")