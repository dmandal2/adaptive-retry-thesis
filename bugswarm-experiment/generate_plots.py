import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Paths
LOGS_DIR = "logs"
RETRY_SUMMARY_FILE = os.path.join(LOGS_DIR, "retry_summary.csv")
PAIRS_FILE = os.path.join(LOGS_DIR, "pairs.csv")

# Load retry summary
retry_summary = pd.read_csv(RETRY_SUMMARY_FILE)

# Load bug-fix pairs
pairs_df = pd.read_csv(PAIRS_FILE)

# === 1️⃣ Plot Retry Success vs Failures ===
plt.figure(figsize=(6,5))
sns.barplot(x=['Passes', 'Fails'], y=[retry_summary['Total Passes'][0], retry_summary['Total Fails'][0]], palette='viridis')
plt.title("Retry Outcome Summary")
plt.ylabel("Count")
plt.savefig(os.path.join(LOGS_DIR, "retry_outcome_summary.png"), dpi=300)
plt.show()

# === 2️⃣ Retry Success Rate Pie Chart ===
plt.figure(figsize=(6,6))
plt.pie([retry_summary['Total Passes'][0], retry_summary['Total Fails'][0]],
        labels=['Success', 'Fail'], autopct='%1.1f%%', colors=['#4CAF50','#F44336'])
plt.title("Retry Success Rate")
plt.savefig(os.path.join(LOGS_DIR, "retry_success_rate.png"), dpi=300)
plt.show()

# === 3️⃣ Bug Type vs Retry Pass Analysis (Optional) ===
# Create a simple bug type based on code difference length
pairs_df['bug_length'] = pairs_df['fixed_code'].str.len() - pairs_df['buggy_code'].str.len()
# Group by simple bins
pairs_df['bug_size'] = pd.cut(pairs_df['bug_length'], bins=[-1000,0,5,20,1000], labels=['Small','Medium','Large','Huge'])

# If we had per-pair retry result (0/1), we could merge and visualize like below
# For now, just plot bug_size distribution
plt.figure(figsize=(6,5))
sns.countplot(x='bug_size', data=pairs_df, palette='magma')
plt.title("Distribution of Bug Fix Pair Sizes")
plt.xlabel("Bug Size")
plt.ylabel("Count")
plt.savefig(os.path.join(LOGS_DIR, "bug_size_distribution.png"), dpi=300)
plt.show()

print("✅ Plots generated and saved in the logs folder:")
print("- retry_outcome_summary.png")
print("- retry_success_rate.png")
print("- bug_size_distribution.png (optional)")

