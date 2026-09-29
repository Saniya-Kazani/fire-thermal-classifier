import pandas as pd

# Load the India hotspot dataset
df = pd.read_csv("india_hotspots.csv")

print("Before removing duplicates:", len(df))

# Remove exact duplicate rows
df = df.drop_duplicates()

print("After removing duplicates:", len(df))

# Save cleaned dataset
df.to_csv("india_hotspots.csv", index=False)

print("\nDuplicate records removed successfully!")
print("Clean dataset saved!")