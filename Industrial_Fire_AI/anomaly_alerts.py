import pandas as pd

# Load AI anomaly detection results
df = pd.read_csv("thermal_anomaly_results.csv")

print("Loading AI results...")

# Keep only detected anomalies
alerts = df[df["anomaly"] == 1].copy()

# Sort by anomaly score
alerts = alerts.sort_values(
    by="anomaly_score",
    ascending=False
)

# Assign investigation priority
# These are initial triage rules, not validated risk levels

frp_threshold = alerts["frp"].quantile(0.90)

alerts["priority"] = "REVIEW"

alerts.loc[
    (alerts["frp"] >= frp_threshold),
    "priority"
] = "HIGH_REVIEW"

# Add alert description
alerts["alert_message"] = (
    "Unusual thermal detection. "
    "Analyst verification required."
)

# Select useful columns
alert_columns = [
    "latitude",
    "longitude",
    "acq_date",
    "satellite",
    "brightness",
    "frp",
    "anomaly_score",
    "anomaly_status",
    "priority",
    "alert_message"
]

alerts = alerts[alert_columns]

# Save alert report
alerts.to_csv("thermal_alerts.csv", index=False)

print("\nAlert generation completed!")

print("Total alerts:", len(alerts))

print("\nPriority distribution:")
print(alerts["priority"].value_counts())

print("\nTop 10 alerts:")
print(alerts.head(10).to_string(index=False))

print("\nSaved: thermal_alerts.csv")