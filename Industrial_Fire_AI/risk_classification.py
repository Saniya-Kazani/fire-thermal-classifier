import pandas as pd

print("Loading industrial fire alerts...")

# Load matched alerts
df = pd.read_csv("industrial_fire_alerts.csv")

# Check required columns
required_columns = [
    "anomaly_score",
    "frp",
    "nearest_industry_distance_km",
    "priority",
    "industry_proximity"
]

for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"Missing column: {col}")

# Assign preliminary investigation priority
def classify_risk(row):

    # High investigation priority:
    # High FRP review alert near mapped industry
    if (
        row["priority"] == "HIGH_REVIEW"
        and row["nearest_industry_distance_km"] <= 5
    ):
        return "HIGH"

    # Medium investigation priority:
    # Any alert near mapped industry
    elif row["nearest_industry_distance_km"] <= 5:
        return "MEDIUM"

    # Other anomalies
    else:
        return "LOW"


df["investigation_priority"] = df.apply(
    classify_risk,
    axis=1
)

# Add explanation for each classification
def get_reason(row):

    if row["investigation_priority"] == "HIGH":
        return (
            "High FRP review alert within 5 km "
            "of mapped industry; verify"
        )

    elif row["investigation_priority"] == "MEDIUM":
        return (
            "Thermal anomaly within 5 km "
            "of mapped industry; verify"
        )

    else:
        return (
            "Thermal anomaly more than 5 km "
            "from mapped industry"
        )


df["classification_reason"] = df.apply(
    get_reason,
    axis=1
)

# Save results
df.to_csv("industrial_risk_classified.csv", index=False)

# Display results
print("\nClassification completed!")

print("\nInvestigation Priority Distribution:")
print(df["investigation_priority"].value_counts())

print("\nSample classified alerts:")
print(
    df[
        [
            "latitude",
            "longitude",
            "frp",
            "nearest_industry_distance_km",
            "priority",
            "investigation_priority",
            "classification_reason"
        ]
    ].head(10)
)

print("\nSaved: industrial_risk_classified.csv")