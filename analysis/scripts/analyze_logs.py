import json
import os
import matplotlib.pyplot as plt
import pandas as pd

# ==========================
# CONFIGURATION
# ==========================
LOG_DIR = "analysis/logs"        # Folder containing your JSON log files
OUTPUT_CSV = "analysis/output/retry_analysis.csv"
OUTPUT_PLOTS_DIR = "analysis/output/plots"

# Ensure output directory exists
os.makedirs(OUTPUT_PLOTS_DIR, exist_ok=True)

# ==========================
# PARSING LOG FILES
# ==========================
def parse_log_file(file_path):
    """
    Parses a single JSON log file for retry analysis.
    Expects JSON array of test results:
    [
        {"test_name": "test_1", "status": "PASS", "retries": 1, "duration": 2.5},
        ...
    ]
    """
    with open(file_path, "r") as f:
        data = json.load(f)
    parsed = []
    for entry in data:
        parsed.append({
            "test_name": entry.get("test_name"),
            "status": entry.get("status"),
            "retries": entry.get("retries", 0),
            "duration": entry.get("duration", 0.0)
        })
    return parsed

# Aggregate all logs
all_logs = []
for filename in os.listdir(LOG_DIR):
    if filename.endswith(".json"):
        filepath = os.path.join(LOG_DIR, filename)
        parsed = parse_log_file(filepath)
        all_logs.extend(parsed)

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
# Add counts on top of bars
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
# Annotate stacked bars
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
box = df.boxplot(column='duration', by='retries', grid=False, patch_artist=True,
                 boxprops=dict(facecolor='lightblue'))
plt.title("Test Duration by Retry Count")
plt.suptitle("")  # Remove default pandas title
plt.xlabel("Number of Retries")
plt.ylabel("Duration (s)")
# Annotate median on each box
medians = df.groupby('retries')['duration'].median()
for i, median in enumerate(medians):
    plt.text(i+1, median, f'{median:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PLOTS_DIR, "duration_by_retry.png"))
plt.close()
print("✅ Duration by retry plot saved.")

# ==========================
# FIGURE 4: Cumulative Pass Rate
# ==========================
cumulative_df = df.groupby('retries')['status'].apply(lambda x: (x=='PASS').sum()/len(x)).reset_index()
plt.figure(figsize=(8,6))
plt.plot(cumulative_df['retries'], cumulative_df['status'], marker='o', color='purple')
plt.title("Cumulative Pass Rate by Retry Count")
plt.xlabel("Number of Retries")
plt.ylabel("Pass Rate")
plt.ylim(0,1.05)
plt.grid(True)
# Annotate each point
for x, y in zip(cumulative_df['retries'], cumulative_df['status']):
    plt.text(x, y+0.02, f"{y:.2f}", ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PLOTS_DIR, "cumulative_pass_rate.png"))
plt.close()
print("✅ Cumulative pass rate plot saved.")
