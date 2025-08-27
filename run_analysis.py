import os
import subprocess

# Step 1: Convert logs to JSON
print("🔹 Converting log to JSON...")
convert_script = "convert_log_to_json.py"
subprocess.run(["python3", convert_script])

# Step 2: Run analysis
print("🔹 Running analysis script...")
analyze_script = "analysis/scripts/analyze_logs.py"
subprocess.run(["python3", analyze_script])

# Step 3: Summary
csv_file = "analysis/output/retry_analysis.csv"
plots_dir = "analysis/output/plots/"

if os.path.exists(csv_file):
    print(f"✅ CSV saved: {csv_file}")
else:
    print(f"⚠️ CSV not found!")

if os.path.exists(plots_dir):
    plots = os.listdir(plots_dir)
    print(f"✅ Plots saved: {', '.join(plots)}")
else:
    print(f"⚠️ Plots directory not found!")
