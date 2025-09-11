#!/usr/bin/env python3
import os
import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = "analysis/output"
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
JSON_GLOB = "analysis/logs/*.json"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "retry_analysis.csv")

os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1) Load JSON files
json_files = sorted(glob.glob(JSON_GLOB))
if not json_files:
    print("No JSON log files found in analysis/logs/. Run convert_log_to_json.py first.")
    raise SystemExit(1)

rows = []
for jf in json_files:
    with open(jf, "r") as fh:
        try:
            data = json.load(fh)
        except Exception as e:
            print(f"Error loading {jf}: {e}")
            continue
        if isinstance(data, list):
            rows.extend(data)
        elif isinstance(data, dict):
            rows.append(data)

if not rows:
    print("No parsed entries found in JSON files.")
    raise SystemExit(1)

df = pd.DataFrame(rows)

# Normalize columns: test_name, status, retries, duration_ms, timestamp
expected_cols = ["test_name", "status", "retries", "duration_ms", "timestamp"]
for c in expected_cols:
    if c not in df.columns:
        df[c] = None

# Coerce types
df['retries'] = pd.to_numeric(df['retries'], errors='coerce').fillna(0).astype(int)
df['duration_ms'] = pd.to_numeric(df['duration_ms'], errors='coerce').fillna(0.0)
# parse timestamp if present
if df['timestamp'].notnull().any():
    df['timestamp_parsed'] = pd.to_datetime(df['timestamp'], errors='coerce')
else:
    df['timestamp_parsed'] = pd.NaT

# Save CSV (full dataset)
df_out = df[['test_name', 'status', 'retries', 'duration_ms', 'timestamp_parsed']].copy()
df_out.rename(columns={'duration_ms': 'duration'}, inplace=True)
df_out.to_csv(OUTPUT_CSV, index=False)
print(f"✅ CSV saved to {OUTPUT_CSV}")

# Print debug summary
print("Status counts:\n", df['status'].value_counts())
print("Retries distribution:\n", df['retries'].value_counts().sort_index())

# -------------------------
# FIGURE: Retry distribution
# -------------------------
plt.figure(figsize=(8,6))
retry_counts = df['retries'].value_counts().sort_index()
bars = plt.bar(retry_counts.index.astype(str), retry_counts.values)
plt.title("Retry Distribution Across Tests")
plt.xlabel("Number of Retries")
plt.ylabel("Number of Tests")
for bar in bars:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), str(int(bar.get_height())), ha='center', va='bottom')
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "retry_distribution.png"))
plt.close()
print("✅ Retry distribution plot saved.")

# -------------------------
# FIGURE: Status by retry (stacked)
# -------------------------
status_by_retry = df.groupby(['retries', 'status']).size().unstack(fill_value=0)
ax = status_by_retry.plot(kind='bar', stacked=True, figsize=(8,6))
plt.title("Test Status by Retry Count")
plt.xlabel("Number of Retries")
plt.ylabel("Number of Tests")
plt.xticks(rotation=0)
# annotate
for i, (idx, row) in enumerate(status_by_retry.iterrows()):
    bottom = 0
    for status in status_by_retry.columns:
        val = row[status]
        if val > 0:
            ax.text(i, bottom + val/2, int(val), ha='center', va='center', fontsize=9)
        bottom += val
plt.legend(title="status")
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "status_by_retry.png"))
plt.close()
print("✅ Status by retry plot saved.")

# -------------------------
# FIGURE: Average duration vs retries
# -------------------------
avg_dur = df.groupby('retries')['duration_ms'].mean()
plt.figure(figsize=(8,6))
bars = plt.bar(avg_dur.index.astype(str), avg_dur.values)
plt.title("Average Duration vs Retries")
plt.xlabel("Retries")
plt.ylabel("Average Duration (ms)")
for bar in bars:
    h = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, h, f"{h:.2f}", ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "duration_by_retry.png"))
plt.close()
print("✅ Duration by retry plot saved.")

# -------------------------
# FIGURE: Duration scatter (each data point)
# -------------------------
plt.figure(figsize=(8,6))
plt.scatter(df['retries'], df['duration_ms'], s=30)
plt.title("Test Duration by Retry Count")
plt.xlabel("Retries")
plt.ylabel("Duration (ms)")
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "duration_vs_retry.png"))
plt.close()
print("✅ Duration vs retry plot saved.")

# -------------------------
# FIGURE: Cumulative pass rate over time
# -------------------------
if df['timestamp_parsed'].notnull().any():
    df_sorted = df.sort_values('timestamp_parsed').reset_index(drop=True)
else:
    df_sorted = df.reset_index(drop=True)

df_sorted['cumulative_pass'] = (df_sorted['status'] == 'PASS').cumsum()
df_sorted['cumulative_total'] = np.arange(1, len(df_sorted) + 1)
df_sorted['cumulative_pass_rate'] = df_sorted['cumulative_pass'] / df_sorted['cumulative_total']

plt.figure(figsize=(8,6))
x = df_sorted['timestamp_parsed'] if df_sorted['timestamp_parsed'].notnull().any() else df_sorted.index
plt.plot(x, df_sorted['cumulative_pass_rate'], marker='o')
plt.title("Cumulative Pass Rate over Runs")
plt.xlabel("Run (timestamp or index)")
plt.ylabel("Cumulative Pass Rate")
plt.ylim(0,1)
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "cumulative_pass_rate.png"))
plt.close()
print("✅ Cumulative pass rate plot saved.")
