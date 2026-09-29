import pandas as pd

df = pd.read_csv("india_hotspots.csv")

print("Dataset Shape:", df.shape)

print("\nFirst 5 rows:")
print(df.head())

print("\nMissing Values:")
print(df.isnull().sum())

print("\nSatellite-wise Records:")
print(df["satellite"].value_counts())

print("\nDate Range:")
print(df["acq_date"].min(), "to", df["acq_date"].max())

print("\nFRP Statistics:")
print(df["frp"].describe())