import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Log file path
log_file = "test-retry.log"  # adjust if in another folder

# Regex to capture timestamp, attempt, and test name
pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Retrying test '(.+?)' \| Attempt: (\d+)"

data = []

with open(log_file, "r") as f:
    for line in f:
        match = re.search(pattern, line)
        if match:
            timestamp_str = match.group(1)
            test_name = match.group(2)
            attempt = int(match.group(3))
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            data.append({"test_name": test_name, "attempt": attempt, "timestamp": timestamp})

# Convert to DataFrame
df = pd.DataFrame(data)

# Calculate duration between retries per test
df = df.sort_values(by=["test_name", "attempt"])
df["duration_sec"] = df.groupby("test_name")["timestamp"].diff().dt.total_seconds()
df["duration_sec"].fillna(0, inplace=True)  # first attempt duration = 0

# Plot
plt.figure(figsize=(10, 6))
sns.stripplot(data=df, x="attempt", y="duration_sec", jitter=True)
plt.title("Execution Time vs Retry Attempt (Manual Logs)")
plt.xlabel("Retry Attempt")
plt.ylabel("Duration (seconds)")
plt.tight_layout()

# Save plot
plt.savefig("execution_time_vs_retry_manual.png")
plt.show()

print("Plot saved as execution_time_vs_retry_manual.png")
