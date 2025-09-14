import csv
import os
import subprocess
from datetime import datetime

LOG_FILE = "logs/test-retry.log"
PAIRS_FILE = "logs/pairs.csv"
TEMP_FILE = "temp_test.py"

# Clear previous log
with open(LOG_FILE, "w") as f:
    f.write(f"=== Test Retry Log Started at {datetime.now()} ===\n")

def run_retry_test(code_snippet, pair_id):
    # Write buggy code to temp file
    with open(TEMP_FILE, "w") as f:
        f.write(code_snippet)

    # Run the code and simulate retry logic
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(["python3", TEMP_FILE], capture_output=True, text=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as log:
            if result.returncode == 0:
                log.write(f"{timestamp} INFO Pair {pair_id} | Attempt {attempt} | PASS\n")
                break
            else:
                log.write(f"{timestamp} INFO Pair {pair_id} | Attempt {attempt} | FAIL\n")
                log.write(f"{timestamp} INFO Error: {result.stderr}\n")
        if attempt == max_attempts:
            with open(LOG_FILE, "a") as log:
                log.write(f"{timestamp} INFO Pair {pair_id} | MAX RETRIES REACHED\n")

# Read pairs.csv
with open(PAIRS_FILE, "r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        pair_id = row["id"]
        buggy_code = row["buggy_code"]
        run_retry_test(buggy_code, pair_id)

# Cleanup
os.remove(TEMP_FILE)
print(f"All BugSwarm pairs executed. Logs saved in {LOG_FILE}")
