import pandas as pd
import numpy as np

from sklearn.ensemble import IsolationForest

# =====================================
# 1. LOAD DATASET
# =====================================

print("Loading satellite dataset...")

df = pd.read_csv("india_hotspots_exact.csv")

print("Dataset loaded:", df.shape)


# =====================================
# 2. SELECT AI FEATURES
# =====================================

features = [
    "brightness",
    "bright_t31",
    "frp",
    "scan",
    "track"
]

# Convert features into numeric format
for col in features:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove records with missing feature values
df = df.dropna(subset=features).copy()

print("Clean dataset:", df.shape)


# =====================================
# 3. INITIALIZE OUTPUT COLUMNS
# =====================================

df["anomaly"] = 0
df["anomaly_score"] = np.nan


# =====================================
# 4. TRAIN MODEL PER SATELLITE
# =====================================

print("\nStarting AI anomaly detection...\n")

for satellite in df["satellite"].unique():

    # Select records for one satellite
    mask = df["satellite"] == satellite

    satellite_data = df.loc[mask, features]

    # Skip very small groups
    if len(satellite_data) < 100:
        print(f"Skipping {satellite}: insufficient records")
        continue

    # Create Isolation Forest model
    model = IsolationForest(
        n_estimators=100,
        contamination=0.01,
        random_state=42,
        n_jobs=-1
    )

    # Train model and predict anomalies
    predictions = model.fit_predict(satellite_data)

    # Calculate anomaly scores
    scores = -model.decision_function(satellite_data)

    # Store results
    df.loc[mask, "anomaly"] = np.where(
        predictions == -1, 1, 0
    )

    df.loc[mask, "anomaly_score"] = scores

    print(f"Satellite: {satellite}")
    print(f"Total records: {len(satellite_data)}")
    print(f"Anomalies detected: {(predictions == -1).sum()}")
    print("-" * 35)


# =====================================
# 5. ADD ANOMALY STATUS
# =====================================

df["anomaly_status"] = np.where(
    df["anomaly"] == 1,
    "Unusual Thermal Detection",
    "Normal Pattern"
)


# =====================================
# 6. SAVE AI RESULTS
# =====================================

output_file = "thermal_anomaly_results.csv"

df.to_csv(output_file, index=False)

print("\nAI anomaly detection completed!")

print("Total records:", len(df))

print("Total anomalies detected:", df["anomaly"].sum())

print("Results saved to:", output_file)


# =====================================
# 7. DISPLAY TOP 10 ANOMALIES
# =====================================

anomalies = df[df["anomaly"] == 1]

top_anomalies = anomalies.sort_values(
    by="anomaly_score",
    ascending=False
)

print("\nTOP 10 UNUSUAL THERMAL DETECTIONS:")

print(
    top_anomalies[
        [
            "latitude",
            "longitude",
            "acq_date",
            "satellite",
            "brightness",
            "frp",
            "anomaly_score",
            "anomaly_status"
        ]
    ].head(10).to_string(index=False)
)