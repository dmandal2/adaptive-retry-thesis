#!/usr/bin/env python3
import re
import json
import glob
import os
from datetime import datetime

# Input candidate log locations
LOG_CANDIDATES = [
    "test-retry.log",
    "logs/*.log",
    "analysis/logs/*.log",
    "logs/test-retry-*.log",
    "analysis/logs/test-retry-*.log"
]
OUTPUT_DIR = "analysis/logs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "tests.json")

# Regex patterns
# 1) "Test 'X' finished | Final Status: FAIL | Total Duration: 1 ms (after 2 attempts)"
finished_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Test '([^']+)' finished \| Final Status: (PASS|FAIL) \| Total Duration: (\d+) ms \(after (\d+) attempts\)"
)
# 2) "Retrying test 'X' | Status: FAIL | Attempt: 1/2 | Duration: 28 ms"
retry_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Retrying test '([^']+)' \| Status: (\S+) \| Attempt: (\d+)/(\d+) \| Duration: (\d+) ms"
)
# 3) AfterMethod "Final Result | Test: X | Status: PASS"
final_result_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*Final Result \| Test: (\S+) \s*\| Status: (PASS|FAIL)"
)

def find_log_files():
    files = []
    for pattern in LOG_CANDIDATES:
        files.extend(glob.glob(pattern))
    # remove duplicates and keep existing ones
    files = sorted(list(set(files)))
    return files

def parse_file(path):
    entries = []
    # we will keep a small state per test for attempt counts
    attempts = {}  # test_name -> max_attempt_seen
    with open(path, "r", errors="ignore") as f:
        for lineno, line in enumerate(f, start=1):
            # finished pattern (authoritative: includes total duration & attempts)
            m = finished_pattern.search(line)
            if m:
                ts_str, test_name, status, dur_ms, attempts_count = m.groups()
                entries.append({
                    "source": path,
                    "line_no": lineno,
                    "timestamp": ts_str,
                    "test_name": test_name,
                    "status": status,
                    "retries": int(attempts_count),
                    "duration_ms": int(dur_ms)
                })
                attempts[test_name] = max(attempts.get(test_name, 0), int(attempts_count))
                continue

            # retry lines give attempt numbers we can use if finished not present
            m = retry_pattern.search(line)
            if m:
                ts_str, test_name, status, attempt_num, attempt_total, dur_ms = m.groups()
                attempts[test_name] = max(attempts.get(test_name, 0), int(attempt_num))
                # keep a lightweight entry for visibility (not final)
                entries.append({
                    "source": path,
                    "line_no": lineno,
                    "timestamp": ts_str,
                    "test_name": test_name,
                    "status": status,
                    "retries": int(attempt_num),
                    "duration_ms": int(dur_ms),
                    "entry_type": "retry_notify"
                })
                continue

            # AfterMethod "Final Result ..." (if 'finished' wasn't emitted)
            m = final_result_pattern.search(line)
            if m:
                ts_str, test_name, status = m.groups()
                entries.append({
                    "source": path,
                    "line_no": lineno,
                    "timestamp": ts_str,
                    "test_name": test_name,
                    "status": status,
                    "retries": attempts.get(test_name, 0),
                    "duration_ms": None
                })
                continue
    return entries

def collect_all():
    files = find_log_files()
    if not files:
        print("No log files found (looked at patterns).")
        return []

    all_entries = []
    for f in files:
        try:
            e = parse_file(f)
            all_entries.extend(e)
        except Exception as ex:
            print(f"Error parsing {f}: {ex}")
    return all_entries

def normalize_and_save(all_entries):
    # We'll keep entries where test_name and status are present.
    output = []
    seen_keys = set()
    for e in all_entries:
        if "test_name" not in e or "status" not in e:
            continue
        # dedupe by (source, line_no)
        key = (e.get("source"), e.get("line_no"), e.get("test_name"), e.get("status"), e.get("retries"))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        # parse timestamp to ISO if present
        ts = e.get("timestamp")
        iso_ts = None
        try:
            if ts:
                iso_ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S,%f").isoformat()
        except:
            iso_ts = ts
        output.append({
            "source": e.get("source"),
            "line_no": e.get("line_no"),
            "timestamp": iso_ts,
            "test_name": e.get("test_name"),
            "status": e.get("status"),
            "retries": int(e.get("retries") or 0),
            "duration_ms": e.get("duration_ms") if e.get("duration_ms") is not None else None,
            "entry_type": e.get("entry_type", "final_or_detected")
        })

    with open(OUTPUT_FILE, "w") as fh:
        json.dump(output, fh, indent=2)

    print(f"✅ Converted {len(output)} entries to JSON at {OUTPUT_FILE}")

if __name__ == "__main__":
    entries = collect_all()
    normalize_and_save(entries)
