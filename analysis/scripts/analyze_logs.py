import os
import re
import pandas as pd
import matplotlib.pyplot as plt

# ==========================
# CONFIGURATION
# ==========================
LOG_DIR = "analysis/logs"        # Folder containing your log files
OUTPUT_CSV = "analysis/output/retry_analysis.csv"
OUTPUT_PLOTS_DIR = "analysis/output/plots"

# Ensure output directory exists
os.makedirs(OUTPUT_PLOTS_DIR, exist_ok=True)

# ==========================
# PARSING LOG FILES
# ==========================
all_logs = []

# Regex to extract info from lines like:
# 2025-08-23 08:18:00,466 INFO  com.retrythesis.tests.RetryAnalyzer - Retrying test 'testRandomFlaky' | Status: FAIL | Attempt: 1/2 | Duration: 23 ms
log_pattern = re.compile(
    r"Retrying test '(?P<test_name>.+?)' \| Status: (?P<status>PASS|FAIL) \| Attempt: (?P<attempt>\d+)/\d+ \| Duration: (?P<duration>[\d.]+) ms"
)

for filename in os.listdir(LOG_DIR):
    if filename.endswith(".log"):
        filepath = os.path.join(LOG_DIR, filename)
        with open(filepath, "r") as f:
            for line in f:
                match = log_pattern.search(line)
                if match:
                    all_logs.append({
                        "test_name": match.group("test_name"),
                        "status": match.group("status"),
                        "retries": int(match.group("attempt")),
                        "duration": float(match.group("duration"))
                    })

if not all_logs:
    print("No log data found.")
    exit()

# Convert to DataFrame
df = pd.DataFrame(all_logs)

# Save CSV
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ CSV saved to {OUTPUT_CSV}")

# ==========================
# FIGURE 1: Retry Distribution
# ==========================
plt.figure(figsize=(8,6))
retry_counts = df['retries'].value_counts().sort_index()
bars = plt.bar(retry_counts.index, retry_counts.values, color='skyblue')
plt.title("Retry Distribution Across Tests")
plt.xlabel("Number of Retries")
plt.ylabel("Number of Tests")
plt.xticks(rotation=0)
for bar in bars:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), str(int(bar.get_height())),
             ha='center', va='bottom')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PLOTS_DIR, "retry_distribution.png"))
plt.close()
print("✅ Retry distribution plot saved.")

# ==========================
# FIGURE 2: Pass/Fail with Retries
# ==========================
plt.figure(figsize=(8,6))
status_retry = df.groupby(['retries', 'status']).size().unstack(fill_value=0)
bars = status_retry.plot(kind='bar', stacked=True, color=['lightgreen', 'salmon'], legend=True)
plt.title("Test Status by Retry Count")
plt.xlabel("Number of Retries")
plt.ylabel("Number of Tests")
plt.xticks(rotation=0)
for i, row in enumerate(status_retry.values):
    bottom = 0
    for val in row:
        plt.text(i, bottom + val/2, str(val), ha='center', va='center', color='black', fontsize=9)
        bottom += val
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PLOTS_DIR, "status_by_retry.png"))
plt.close()
print("✅ Status by retry plot saved.")

# ==========================
# FIGURE 3: Duration vs Retries
# ==========================
plt.figure(figsize=(8,6))
avg_duration = df.groupby('retries')['duration'].mean()
plt.bar(avg_duration.index, avg_duration.values, color='orange')
plt.title("Average Duration vs Retries")
plt.xlabel("Retries")
plt.ylabel("Average Duration (ms)")
plt.xticks(rotation=0)
for i, val in enumerate(avg_duration.values):
    plt.text(avg_duration.index[i], val, f"{val:.3f}", ha='center', va='bottom')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PLOTS_DIR, "duration_by_retry.png"))
plt.close()
print("✅ Duration by retry plot saved.")

# ==========================
# FIGURE 4: Cumulative Pass Rate
# ==========================
plt.figure(figsize=(8,6))
df_sorted = df.sort_values('retries')
df_sorted['cumulative_pass'] = df_sorted['status'].eq('PASS').cumsum()
df_sorted['cumulative_total'] = range(1, len(df_sorted)+1)
df_sorted['cumulative_pass_rate'] = df_sorted['cumulative_pass'] / df_sorted['cumulative_total']

plt.plot(df_sorted['retries'], df_sorted['cumulative_pass_rate'], marker='o', color='blue')
plt.title("Cumulative Pass Rate by Retry")
plt.xlabel("Retries")
plt.ylabel("Cumulative Pass Rate")
plt.ylim(0,1)
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PLOTS_DIR, "cumulative_pass_rate.png"))
plt.close()
print("✅ Cumulative pass rate plot saved.")
