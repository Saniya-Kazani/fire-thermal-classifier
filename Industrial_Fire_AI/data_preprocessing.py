import pandas as pd
import os

# Input dataset folder
DATA_FOLDER = "dataset"

# Output file
OUTPUT_FILE = "india_hotspots.csv"

# India ke approximate geographic boundaries
LAT_MIN, LAT_MAX = 6, 38
LON_MIN, LON_MAX = 68, 98

files = [
    "fire_nrt_J1V-C2_565335.csv",
    "fire_nrt_M-C61_565334.csv",
    "fire_nrt_SV-C2_565336.csv"
]

total_records = 0
india_records = 0

# Process large files in chunks
for file in files:

    file_path = os.path.join(DATA_FOLDER, file)

    print(f"\nProcessing: {file}")

    for chunk in pd.read_csv(file_path, chunksize=100000):

        total_records += len(chunk)

        # Filter approximate India region
        india_data = chunk[
            chunk["latitude"].between(LAT_MIN, LAT_MAX)
            & chunk["longitude"].between(LON_MIN, LON_MAX)
        ].copy()

        if not india_data.empty:

            # Track original dataset
            india_data["source_file"] = file

            # Save data without loading all records into RAM
            india_data.to_csv(
                OUTPUT_FILE,
                mode="a",
                header=not os.path.exists(OUTPUT_FILE),
                index=False
            )

            india_records += len(india_data)

    print("Completed:", file)
    

print("\nPreprocessing completed!")
print("Total records processed:", total_records)
print("India records extracted:", india_records)
print("Output file:", OUTPUT_FILE)
if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)