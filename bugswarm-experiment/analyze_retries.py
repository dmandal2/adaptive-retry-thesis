import re
import pandas as pd

# Path to your retry log file
LOG_FILE = "logs/test-retry.log"

def parse_retry_log(file_path):
    """
    Parses the retry log file in BugSwarm format:
    Pair X | Attempt Y | PASS/FAIL/MAX RETRIES REACHED
    """
    total_retries = 0
    total_passes = 0
    total_fails = 0

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            # Match attempts
            match = re.search(r"Pair (\d+) \| Attempt (\d+) \| (\w+)", line)
            if match:
                total_retries += 1
                status = match.group(3)
                if status.upper() == "PASS":
                    total_passes += 1
                elif status.upper() == "FAIL":
                    total_fails += 1

    return total_retries, total_passes, total_fails

def summarize_retries(total_retries, total_passes, total_fails):
    summary = {
        "Total Retries": total_retries,
        "Total Passes": total_passes,
        "Total Fails": total_fails,
        "Retry Success Rate (%)": round((total_passes / max(1, (total_passes + total_fails))) * 100, 2)
    }
    return summary

if __name__ == "__main__":
    total_retries, total_passes, total_fails = parse_retry_log(LOG_FILE)
    summary = summarize_retries(total_retries, total_passes, total_fails)

    print("\n=== Retry Log Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    # Save summary as CSV for thesis plots
    df = pd.DataFrame([summary])
    df.to_csv("logs/retry_summary.csv", index=False)
    print("\nSummary saved to logs/retry_summary.csv")
