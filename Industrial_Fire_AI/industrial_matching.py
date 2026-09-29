import pandas as pd
from sklearn.neighbors import BallTree
import numpy as np

print("Loading thermal alerts and industrial locations...")

# Load datasets
alerts = pd.read_csv("thermal_alerts.csv")
industries = pd.read_csv("industrial_locations.csv")

# Remove rows with missing coordinates
alerts = alerts.dropna(subset=["latitude", "longitude"])
industries = industries.dropna(subset=["latitude", "longitude"])

# Convert coordinates to radians for Haversine distance
industry_coords = np.radians(
    industries[["latitude", "longitude"]].values
)

alert_coords = np.radians(
    alerts[["latitude", "longitude"]].values
)

# Build spatial search tree
tree = BallTree(industry_coords, metric="haversine")

# Find nearest industry for each alert
distances, indices = tree.query(alert_coords, k=1)

# Convert radians to kilometers
alerts["nearest_industry_distance_km"] = (
    distances.flatten() * 6371
)

# Get nearest industry details
nearest = industries.iloc[indices.flatten()].reset_index(drop=True)

alerts["nearest_industry_name"] = nearest["name"].values
alerts["nearest_industry_type"] = nearest["industrial_type"].values
alerts["nearest_industry_latitude"] = nearest["latitude"].values
alerts["nearest_industry_longitude"] = nearest["longitude"].values

# Preliminary proximity flag (5 km radius)
alerts["industry_proximity"] = np.where(
    alerts["nearest_industry_distance_km"] <= 5,
    "NEAR_INDUSTRY",
    "NOT_NEAR_INDUSTRY"
)

# Save matched dataset
alerts.to_csv("industrial_fire_alerts.csv", index=False)

print("\nIndustrial matching completed!")
print("Total alerts matched:", len(alerts))

print("\nProximity distribution:")
print(alerts["industry_proximity"].value_counts())

print("\nTop 10 nearest-industry alerts:")
print(
    alerts[
        [
            "latitude",
            "longitude",
            "priority",
            "nearest_industry_name",
            "nearest_industry_distance_km",
            "industry_proximity"
        ]
    ].sort_values("nearest_industry_distance_km").head(10)
)

print("\nSaved: industrial_fire_alerts.csv")