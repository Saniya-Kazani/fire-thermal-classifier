import pandas as pd
import geopandas as gpd

print("Loading hotspot dataset...")

df = pd.read_csv("india_hotspots.csv")

print("Original records:", len(df))


# Load India boundary
print("Loading India boundary...")

boundary = gpd.read_file("geoBoundaries-IND-ADM0.topojson")
# Ensure same coordinate system
boundary = boundary.set_crs("EPSG:4326")
# Combine boundary geometries
india_polygon = boundary.geometry.union_all()


# Convert hotspot coordinates into geographic points
points = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["longitude"],
        df["latitude"]
    ),
    crs="EPSG:4326"
)


# Keep only points inside India
india_points = points[
    points.geometry.intersects(india_polygon)
].copy()


# Remove geometry column before saving CSV
india_points = pd.DataFrame(
    india_points.drop(columns="geometry")
)


# Save exact India dataset
india_points.to_csv(
    "india_hotspots_exact.csv",
    index=False
)


print("\nBoundary filtering completed!")

print("Before filtering:", len(df))

print("After filtering:", len(india_points))

print("Saved: india_hotspots_exact.csv")