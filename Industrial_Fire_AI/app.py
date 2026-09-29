import streamlit as st
import pandas as pd
import folium

from streamlit_folium import st_folium

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Industrial Fire AI Dashboard",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Industrial Fire & Thermal Anomaly Dashboard")

st.caption(
    "Satellite-based thermal anomaly monitoring "
    "| Preliminary investigation support"
)

# ---------------- LOAD DATA ----------------

@st.cache_data
def load_data():
    return pd.read_csv("industrial_risk_classified.csv")

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load dataset: {e}")
    st.stop()

# ---------------- SIDEBAR FILTERS ----------------

st.sidebar.header("Dashboard Filters")

priorities = st.sidebar.multiselect(
    "Select Investigation Priority",
    ["HIGH", "MEDIUM", "LOW"],
    default=["HIGH", "MEDIUM", "LOW"]
)

filtered_df = df[
    df["investigation_priority"].isin(priorities)
].copy()

# ---------------- METRICS ----------------

st.subheader("📊 Alert Summary")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Anomalies", len(filtered_df))

c2.metric(
    "HIGH Priority",
    (filtered_df["investigation_priority"] == "HIGH").sum()
)

c3.metric(
    "MEDIUM Priority",
    (filtered_df["investigation_priority"] == "MEDIUM").sum()
)

c4.metric(
    "LOW Priority",
    (filtered_df["investigation_priority"] == "LOW").sum()
)

st.info(
    "These are AI-flagged thermal anomalies and preliminary "
    "investigation priorities—not confirmed industrial fires."
)

# ---------------- MAP ----------------

st.subheader("🗺️ Interactive Thermal Anomaly Map")

india_map = folium.Map(
    location=[22.5, 79.0],
    zoom_start=5,
    tiles="OpenStreetMap"
)

colors = {
    "HIGH": "red",
    "MEDIUM": "orange",
    "LOW": "blue"
}

for _, row in filtered_df.iterrows():

    priority = row["investigation_priority"]
    color = colors.get(priority, "gray")

    popup = f"""
    <b>Investigation Priority:</b> {priority}<br>
    <b>Date:</b> {row['acq_date']}<br>
    <b>Satellite:</b> {row['satellite']}<br>
    <b>FRP:</b> {row['frp']} MW<br>
    <b>Brightness:</b> {row['brightness']} K<br>
    <b>Nearest Industry:</b> {row['nearest_industry_name']}<br>
    <b>Distance:</b> {row['nearest_industry_distance_km']:.2f} km<br>
    <b>Reason:</b> {row['classification_reason']}
    """

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=6 if priority == "HIGH" else 4,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup, max_width=350)
    ).add_to(india_map)

st_folium(
    india_map,
    width=None,
    height=550,
    use_container_width=True
)

# ---------------- ALERT TABLE ----------------

st.subheader("🚨 Thermal Alert Records")

search = st.text_input("Search industry name")

if search:
    filtered_df = filtered_df[
        filtered_df["nearest_industry_name"]
        .fillna("")
        .str.contains(search, case=False)
    ]

display_columns = [
    "latitude",
    "longitude",
    "acq_date",
    "satellite",
    "frp",
    "nearest_industry_name",
    "nearest_industry_distance_km",
    "investigation_priority",
    "classification_reason"
]

st.dataframe(
    filtered_df[display_columns],
    use_container_width=True
)

# ---------------- DOWNLOAD ----------------

st.download_button(
    label="📥 Download Filtered Alerts CSV",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_industrial_alerts.csv",
    mime="text/csv"
)

st.success("Dashboard loaded successfully!")