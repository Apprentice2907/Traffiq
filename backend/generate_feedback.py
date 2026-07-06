import pandas as pd
import random
import datetime
import os

os.makedirs('../data', exist_ok=True)

texts = [
    "Cars blocking driveway near the junction every evening.",
    "No parking zone ignored by autos.",
    "Bikes parked on the footpath, pedestrians have to walk on the road.",
    "Huge traffic jam caused by illegal parking near the tech park.",
    "Truck unloaded goods during peak hour, total gridlock.",
    "Taxi stand overflowing onto the main road.",
    "People double parking outside the bakery.",
    "Traffic police nowhere to be seen while cars block the intersection.",
    "Delivery boys parking haphazardly on the corner.",
    "Bus stop is completely blocked by parked private vehicles."
]

def generate():
    df = pd.read_csv('../data.csv')
    if 'grid_id' not in df.columns:
        df['grid_id'] = (df['latitude'] // 0.005 * 0.005).astype(str) + '_' + (df['longitude'] // 0.005 * 0.005).astype(str)
        
    top_grids = df['grid_id'].value_counts().head(20).index.tolist()
    
    records = []
    now = datetime.datetime.now()
    for i in range(80):
        records.append({
            "complaint_id": f"C{1000+i}",
            "zone_id": random.choice(top_grids),
            "timestamp": (now - datetime.timedelta(days=random.randint(0, 7), hours=random.randint(0,23))).isoformat(),
            "text": random.choice(texts)
        })
        
    out_df = pd.DataFrame(records)
    out_df.to_csv('../data/citizen_feedback.csv', index=False)
    print("Generated data/citizen_feedback.csv with 80 records.")

if __name__ == "__main__":
    generate()
