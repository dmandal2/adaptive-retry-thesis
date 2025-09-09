import re
import json
import os
from datetime import datetime

# Input log and output directory
LOG_FILE = "test-retry.log"
OUTPUT_DIR = "analysis/logs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Data structure: store all attempts per test
tests = {}

# Regex patterns
retry_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Retrying test '(\S+)' \| Attempt: (\d+)"
)
result_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Final Result \| Test: (\S+) \| Status: (PASS|FAIL)"
)

# Parse timestamp from log
def parse_timestamp(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

# Read log file
with open(LOG_FILE, "r") as f:
    for line in f:
        # Retry attempt
        retry_match = retry_pattern.search(line)
        if retry_match:
            ts, test_name, attempt = retry_match.groups()
            ts = parse_timestamp(ts)
            attempt = int(attempt)
            if test_name not in tests:
                tests[test_name] = []
            # Store retry as failed attempt
            tests[test_name].append({
                "type": "RETRY",
                "attempt": attempt,
                "timestamp": ts,
                "status": "FAIL"
            })
            continue

        # Final result (PASS/FAIL)
        result_match = result_pattern.search(line)
        if result_match:
            ts, test_name, status = result_match.groups()
            ts = parse_timestamp(ts)
            if test_name not in tests:
                tests[test_name] = []
            attempt = len(tests[test_name]) + 1
            tests[test_name].append({
                "type": "FINAL",
                "attempt": attempt,
                "timestamp": ts,
                "status": status
            })
            continue

# Convert to flat list for JSON/CSV
output = []
for test_name, attempts in tests.items():
    start_time = attempts[0]["timestamp"] if attempts else None
    for attempt in attempts:
        duration = (attempt["timestamp"] - start_time).total_seconds() if start_time else 0.0
        output.append({
            "test_name": test_name,
            "status": attempt["status"],
            "retries": attempt["attempt"],
            "duration": round(duration, 2)
        })

# Save JSON
json_file = os.path.join(OUTPUT_DIR, "tests.json")
with open(json_file, "w") as f:
    json.dump(output, f, indent=4)

print(f"✅ Converted {len(output)} test attempts to JSON in {json_file}")
