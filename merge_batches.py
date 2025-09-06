import pandas as pd
import glob
import os

# Path to batch CSVs
batch_files = sorted(glob.glob("analysis/output/retry_analysis-run*.csv"))

if not batch_files:
    print("❌ No batch CSVs found in analysis/output/")
    exit(1)

print("📂 Found batch files:", batch_files)

# Load and combine
dfs = [pd.read_csv(f) for f in batch_files]
merged = pd.concat(dfs, ignore_index=True)

# Save consolidated CSV
output_file = "analysis/output/retry_analysis_all.csv"
merged.to_csv(output_file, index=False)

print(f"✅ Merged {len(batch_files)} batch files into {output_file}")
print("Total rows:", len(merged))
print("Sample:")
print(merged.head())

