import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("india_hotspots.csv")

print("=" * 50)
print("DATASET ANALYSIS")
print("=" * 50)

# 1. Dataset information
print("\nDataset Shape:", df.shape)

print("\nColumn Names:")
print(df.columns.tolist())

# 2. Convert date into datetime format
df["acq_date"] = pd.to_datetime(df["acq_date"])

# 3. Basic statistical analysis
print("\nStatistical Summary:")
print(df[["brightness", "bright_t31", "frp"]].describe())

# 4. Satellite-wise detections
print("\nSatellite-wise Hotspots:")
print(df["satellite"].value_counts())

# 5. Day vs Night detections
print("\nDay/Night Distribution:")
print(df["daynight"].value_counts())

# 6. Daily hotspot count
daily_count = df.groupby("acq_date").size()

print("\nDaily Hotspot Summary:")
print(daily_count.describe())

# 7. High FRP detections
print("\nTop 10 FRP Records:")
print(
    df.nlargest(10, "frp")[
        ["latitude", "longitude", "acq_date", "frp", "satellite"]
    ]
)

# -----------------------------------
# VISUALIZATION 1: FRP Distribution
# -----------------------------------

plt.figure(figsize=(8, 5))

plt.hist(df["frp"], bins=100)

plt.title("Fire Radiative Power Distribution")
plt.xlabel("FRP")
plt.ylabel("Number of Hotspots")

plt.tight_layout()
plt.savefig("frp_distribution.png")
plt.show()

# -----------------------------------
# VISUALIZATION 2: Daily Hotspots
# -----------------------------------

plt.figure(figsize=(12, 5))

daily_count.plot()

plt.title("Daily Satellite Hotspot Detections")
plt.xlabel("Date")
plt.ylabel("Hotspot Count")

plt.tight_layout()
plt.savefig("daily_hotspots.png")
plt.show()

# -----------------------------------
# VISUALIZATION 3: Satellite Comparison
# -----------------------------------

satellite_count = df["satellite"].value_counts()

plt.figure(figsize=(8, 5))

satellite_count.plot(kind="bar")

plt.title("Hotspots by Satellite")
plt.xlabel("Satellite")
plt.ylabel("Number of Hotspots")

plt.tight_layout()
plt.savefig("satellite_comparison.png")
plt.show()

# -----------------------------------
# VISUALIZATION 4: Geographic Hotspots
# -----------------------------------

plt.figure(figsize=(10, 7))

plt.scatter(
    df["longitude"],
    df["latitude"],
    c=df["frp"],
    s=2,
    alpha=0.5
)

plt.colorbar(label="FRP")

plt.title("Geographic Distribution of Hotspots")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.tight_layout()
plt.savefig("hotspot_map.png")
plt.show()

print("\nEDA completed successfully!")
print("Graphs saved in project folder.")