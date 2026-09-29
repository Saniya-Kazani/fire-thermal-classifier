import pandas as pd
import folium

print("Loading thermal alerts...")

# Load AI-generated alerts
df = pd.read_csv("thermal_alerts.csv")

# Create India-centered map
india_map = folium.Map(
    location=[22.5, 79.0],
    zoom_start=5,
    tiles="CartoDB positron"
)

print("Plotting thermal anomalies...")

# Add anomaly markers
for _, row in df.iterrows():

    # Marker color based on priority
    if row["priority"] == "HIGH_REVIEW":
        color = "red"
    else:
        color = "orange"

    # Popup information
    popup_text = f"""
    <b>Priority:</b> {row['priority']}<br>
    <b>Date:</b> {row['acq_date']}<br>
    <b>Satellite:</b> {row['satellite']}<br>
    <b>Brightness:</b> {row['brightness']} K<br>
    <b>FRP:</b> {row['frp']} MW<br>
    <b>Status:</b> {row['anomaly_status']}<br>
    <b>Alert:</b> {row['alert_message']}
    """

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=5 if row["priority"] == "HIGH_REVIEW" else 3,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(india_map)

# Add map legend
legend_html = """
<div style="
position: fixed;
bottom: 30px;
left: 30px;
width: 180px;
background-color: white;
border: 2px solid grey;
z-index: 9999;
padding: 10px;
font-size: 14px;">

<b>Thermal Alert Legend</b><br>
<span style="color:red;">●</span> HIGH_REVIEW<br>
<span style="color:orange;">●</span> REVIEW
</div>
"""

india_map.get_root().html.add_child(
    folium.Element(legend_html)
)

# Save interactive map
india_map.save("thermal_anomaly_map.html")

print("Map generated successfully!")
print("Saved as: thermal_anomaly_map.html")