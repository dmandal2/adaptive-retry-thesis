import pandas as pd

# Load dataset
df = pd.read_csv("logs/pairs.csv")

# Show basic info
print("Total bug-fix pairs:", len(df))
print("\nSample columns:", df.columns.tolist())

# Show first 3 samples
print("\nExample entries:")
print(df.head(3)[["id", "commit_message", "date"]])
