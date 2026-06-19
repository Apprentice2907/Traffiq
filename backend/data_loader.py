import pandas as pd
import numpy as np
import json
import os

DATA_PATH = os.environ.get("DATA_PATH", "data.csv")

class DataLoader:
    def __init__(self, file_path=DATA_PATH):
        self.file_path = file_path

    def load_and_clean(self):
        # Load data.csv
        df = pd.read_csv(self.file_path, low_memory=False)
        
        # Filter: keep only validation_status == 'approved' rows
        df = df[df['validation_status'] == 'approved'].copy()
        
        # Parse created_datetime to datetime
        df['created_datetime'] = pd.to_datetime(df['created_datetime'], errors='coerce')
        df = df.dropna(subset=['created_datetime'])
        
        # Extract time features
        df['hour'] = df['created_datetime'].dt.hour
        df['day_of_week'] = df['created_datetime'].dt.dayofweek
        df['month'] = df['created_datetime'].dt.month
        df['is_weekend'] = df['day_of_week'] >= 5
        df['is_peak_hour'] = df['hour'].isin([7, 8, 9, 17, 18, 19])
        
        # Parse violation_type
        def get_primary_violation(v):
            if pd.isna(v):
                return 'UNKNOWN'
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[0]
            except:
                pass
            return str(v).strip('[]"\'').split(',')[0].strip(' "')

        df['primary_violation'] = df['violation_type'].apply(get_primary_violation)
        
        # Drop rows where latitude/longitude are outside Bangalore bounds
        # lat between 12.8 and 13.2, lon between 77.4 and 77.8
        df = df[
            (df['latitude'] >= 12.8) & (df['latitude'] <= 13.2) &
            (df['longitude'] >= 77.4) & (df['longitude'] <= 77.8)
        ]
        
        IS_HF = os.environ.get("HF_SPACE", False)
        IS_RENDER = os.environ.get("RENDER", False)
        
        if IS_HF or IS_RENDER:
            df = df.sample(n=min(50000, len(df)), random_state=42)
            print(f"Cloud mode: sampled to {len(df)} rows")
        
        return df

    def create_grid_cells(self, df):
        # Bin lat/lon into 0.005 degree grid cells (~500m)
        df['lat_bin'] = (df['latitude'] // 0.005) * 0.005
        df['lon_bin'] = (df['longitude'] // 0.005) * 0.005
        # Create grid_id column as "lat_bin_lon_bin" string
        df['grid_id'] = df['lat_bin'].round(3).astype(str) + "_" + df['lon_bin'].round(3).astype(str)
        return df

    def get_hotspot_summary(self, df):
        # Group by grid_id + junction_name
        grouped = df.groupby(['grid_id', 'junction_name']).agg(
            violation_count=('id', 'count'),
            peak_hour=('hour', lambda x: x.mode()[0] if not x.mode().empty else -1)
        ).reset_index()
        
        # Return top 50 hotspot zones sorted by violation count
        return grouped.sort_values('violation_count', ascending=False).head(50)

    def get_hourly_trend(self, df):
        # Group by hour -> count violations
        return df.groupby('hour').size().to_dict()

    def get_violation_type_breakdown(self, df):
        # Return top 10 types with counts
        return df['primary_violation'].value_counts().head(10).to_dict()

    def get_vehicle_breakdown(self, df):
        # Group by vehicle_type -> count
        return df['vehicle_type'].value_counts().to_dict()

if __name__ == "__main__":
    # Adjust path safely to allow running from Gridlock root or backend dir
    dl = DataLoader()
    df = dl.load_and_clean()
    df = dl.create_grid_cells(df)
    
    print("Clean shape:", df.shape)
    print("\nTop hotspots:")
    print(dl.get_hotspot_summary(df).head(10))
    print("\nHourly trend:", dl.get_hourly_trend(df))
    print("\nViolation types:", dl.get_violation_type_breakdown(df))
