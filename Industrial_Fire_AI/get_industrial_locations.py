import requests
import pandas as pd

print("Fetching industrial locations from OpenStreetMap...")

# Overpass API query for industrial areas in India
query = """
[out:json][timeout:180];
area["ISO3166-1"="IN"][admin_level=2]->.india;

(
  nwr["landuse"="industrial"](area.india);
  nwr["industrial"](area.india);
  nwr["man_made"="works"](area.india);
);

out center tags;
"""

url = "https://overpass.kumi.systems/api/interpreter"

try:
    headers = {
    "User-Agent": "SIH-Industrial-Fire-Detection/1.0",
    "Accept": "application/json"
}

    response = requests.post(
    url,
    data={"data": query},
    headers=headers,
    timeout=240
)

    response.raise_for_status()
    data = response.json()

    locations = []

    for element in data.get("elements", []):

        tags = element.get("tags", {})

        # Get coordinates
        if "lat" in element and "lon" in element:
            lat = element["lat"]
            lon = element["lon"]

        elif "center" in element:
            lat = element["center"]["lat"]
            lon = element["center"]["lon"]

        else:
            continue

        locations.append({
            "name": tags.get("name", "Unknown"),
            "latitude": lat,
            "longitude": lon,
            "industrial_type": tags.get(
                "industrial",
                tags.get("landuse", tags.get("man_made", "Unknown"))
            ),
            "osm_type": element.get("type"),
            "osm_id": element.get("id")
        })

    df = pd.DataFrame(locations)

    if df.empty:
        print("No industrial locations found.")
    else:
        df.drop_duplicates(
            subset=["osm_type", "osm_id"],
            inplace=True
        )

        df.to_csv("industrial_locations.csv", index=False)

        print("\nIndustrial dataset created!")
        print("Total locations:", len(df))
        print("Saved as: industrial_locations.csv")

        print(df.head(10))

except Exception as e:
    print("Error fetching data:", e)