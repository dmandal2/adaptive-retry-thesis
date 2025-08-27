import re
import json
import os
from datetime import datetime

LOG_FILE = "test-retry.log"
OUTPUT_DIR = "analysis/logs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

tests = {}

# Regex patterns
retry_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Retrying test '(\S+)' \| Attempt: (\d+)"
)
pass_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Test '(\S+)' PASSED"
)
fail_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Test '(\S+)' FAILED"
)

def parse_timestamp(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

with open(LOG_FILE, "r") as f:
    for line in f:
        # Retry attempt
        retry_match = retry_pattern.search(line)
        if retry_match:
            ts, test_name, attempt = retry_match.groups()
            ts = parse_timestamp(ts)
            attempt = int(attempt)
            if test_name not in tests:
                tests[test_name] = {"retries": attempt, "start_time": ts, "end_time": ts, "status": "PASS"}
            else:
                tests[test_name]["retries"] = max(tests[test_name]["retries"], attempt)
                tests[test_name]["end_time"] = ts
            continue
        
        # PASS
        pass_match = pass_pattern.search(line)
        if pass_match:
            ts, test_name = pass_match.groups()
            ts = parse_timestamp(ts)
            if test_name in tests:
                tests[test_name]["status"] = "PASS"
                tests[test_name]["end_time"] = ts
            else:
                tests[test_name] = {"retries": 0, "start_time": ts, "end_time": ts, "status": "PASS"}
            continue
        
        # FAIL
        fail_match = fail_pattern.search(line)
        if fail_match:
            ts, test_name = fail_match.groups()
            ts = parse_timestamp(ts)
            if test_name in tests:
                tests[test_name]["status"] = "FAIL"
                tests[test_name]["end_time"] = ts
            else:
                tests[test_name] = {"retries": 0, "start_time": ts, "end_time": ts, "status": "FAIL"}

# Convert to list with duration
output = []
for name, info in tests.items():
    try:
        duration = (info["end_time"] - info["start_time"]).total_seconds()
    except:
        duration = 0.0
    output.append({
        "test_name": name,
        "status": info.get("status", "PASS"),
        "retries": info.get("retries", 0),
        "duration": round(duration, 2)
    })

# Save JSON
with open(os.path.join(OUTPUT_DIR, "tests.json"), "w") as f:
    json.dump(output, f, indent=4)

print(f"✅ Converted {len(output)} tests to JSON in {OUTPUT_DIR}/tests.json")
