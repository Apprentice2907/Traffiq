import pandas as pd
import numpy as np
import os
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score

MODELS_DIR = os.environ.get("MODELS_DIR", "models")

class ParkingCongestionModel:
    def __init__(self, model_dir=MODELS_DIR):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_dir = os.path.join(base_dir, model_dir)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.model = None
        self.vehicle_encoder = LabelEncoder()
        self.violation_encoder = LabelEncoder()
        self.scaler = MinMaxScaler(feature_range=(0, 100))
        
        self._load_models_if_exist()

    def load(self):
        model_path = os.path.join(self.model_dir, "model.pkl")
        if os.path.exists(model_path):
            # Load existing model
            self.model = joblib.load(model_path)
            self.vehicle_encoder = joblib.load(os.path.join(self.model_dir, "vehicle_encoder.pkl"))
            self.violation_encoder = joblib.load(os.path.join(self.model_dir, "violation_encoder.pkl"))
            self.scaler = joblib.load(os.path.join(self.model_dir, "scaler.pkl"))
        else:
            # No saved model found — train from scratch
            print("No saved model found. Training from scratch...")
            from data_loader import DataLoader
            DATA_PATH = os.environ.get("DATA_PATH", "data.csv")
            dl = DataLoader(DATA_PATH)
            df = dl.load_and_clean()
            df = dl.create_grid_cells(df)
            self.train(df)
            print("Training complete.")

    def _load_models_if_exist(self):
        try:
            self.load()
        except Exception as e:
            pass

    def prepare_features(self, df):
        df = df.copy()
        
        # Target: congestion_impact_score
        counts = df.groupby(['grid_id', 'hour']).size().reset_index(name='violations_per_grid_hour')
        df = df.merge(counts, on=['grid_id', 'hour'], how='left')
        df['congestion_impact_score'] = self.scaler.fit_transform(df[['violations_per_grid_hour']])
        
        # Encoders
        df['vehicle_type_encoded'] = self.vehicle_encoder.fit_transform(df['vehicle_type'].astype(str))
        df['primary_violation_encoded'] = self.violation_encoder.fit_transform(df['primary_violation'].astype(str))
        
        # Grid splits
        df['lat_bin'] = df['grid_id'].apply(lambda x: float(x.split('_')[0]))
        df['lon_bin'] = df['grid_id'].apply(lambda x: float(x.split('_')[1]))
        
        # Ensure correct types
        df['is_weekend'] = df['is_weekend'].astype(int)
        df['is_peak_hour'] = df['is_peak_hour'].astype(int)
        
        features = [
            'hour', 'day_of_week', 'is_weekend', 'is_peak_hour', 'month',
            'vehicle_type_encoded', 'primary_violation_encoded',
            'lat_bin', 'lon_bin'
        ]
        
        return df, features

    def train(self, df):
        print("Preparing features...")
        df_prepared, features = self.prepare_features(df)
        
        X = df_prepared[features]
        y = df_prepared['congestion_impact_score']
        
        print("Splitting data...")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print("Training XGBoost Regressor...")
        IS_CLOUD = os.environ.get("HF_SPACE") or os.environ.get("RENDER")

        params = dict(
            n_estimators=100 if IS_CLOUD else 200,
            max_depth=4 if IS_CLOUD else 6,
            learning_rate=0.1,
            subsample=0.8,
            tree_method='hist',
            random_state=42
        ) if True else {}
        
        self.model = XGBRegressor(**params)
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        print(f"RMSE: {rmse:.4f}")
        print(f"R²: {r2:.4f}")
        
        # Feature importance
        importances = self.model.feature_importances_
        feature_imp = pd.DataFrame({'Feature': features, 'Importance': importances})
        feature_imp = feature_imp.sort_values('Importance', ascending=False)
        print("\nFeature Importances:")
        print(feature_imp)
        
        # Save models
        joblib.dump(self.model, os.path.join(self.model_dir, "model.pkl"))
        joblib.dump(self.vehicle_encoder, os.path.join(self.model_dir, "vehicle_encoder.pkl"))
        joblib.dump(self.violation_encoder, os.path.join(self.model_dir, "violation_encoder.pkl"))
        joblib.dump(self.scaler, os.path.join(self.model_dir, "scaler.pkl"))
        print(f"Models saved to {self.model_dir}")

    def _safe_encode(self, encoder, value):
        classes = encoder.classes_
        if value in classes:
            return encoder.transform([value])[0]
        else:
            return 0  # Default to 0 if unseen

    def predict(self, lat, lon, hour, day_of_week, vehicle_type='CAR', violation_type='WRONG PARKING'):
        if self.model is None:
            raise ValueError("Model not trained yet.")
            
        lat_bin = (lat // 0.005) * 0.005
        lon_bin = (lon // 0.005) * 0.005
        
        is_weekend = int(day_of_week >= 5)
        is_peak_hour = int(hour in [7, 8, 9, 17, 18, 19])
        month = 5 # default month
        
        vehicle_enc = self._safe_encode(self.vehicle_encoder, vehicle_type)
        violation_enc = self._safe_encode(self.violation_encoder, violation_type)
        
        input_data = pd.DataFrame([{
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'is_peak_hour': is_peak_hour,
            'month': month,
            'vehicle_type_encoded': vehicle_enc,
            'primary_violation_encoded': violation_enc,
            'lat_bin': lat_bin,
            'lon_bin': lon_bin
        }])
        
        score = float(self.model.predict(input_data)[0])
        score_rounded = round(max(0.0, min(100.0, score)), 1)
        
        if score_rounded < 25:
            risk_level, risk_color, action = "LOW", "#22c55e", "Monitor via CCTV."
        elif score_rounded < 50:
            risk_level, risk_color, action = "MEDIUM", "#f59e0b", "Add to next patrol route."
        elif score_rounded < 75:
            risk_level, risk_color, action = "HIGH", "#f97316", "Schedule patrol within 1 hour."
        else:
            risk_level, risk_color, action = "CRITICAL", "#ef4444", "Deploy 3+ officers immediately. Tow vehicles."
            
        return {
            "congestion_score": score_rounded,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "recommended_action": action,
            "peak_window": "Worst between 0-6am and 7pm-11pm in this zone"
        }

    def get_top_enforcement_zones(self, df, top_n=20):
        unique_cells = df[['grid_id', 'lat_bin', 'lon_bin']].drop_duplicates()
        hours_to_check = [0, 2, 4, 19, 20, 21, 22, 23]
        
        rows = []
        # Batch preparation for speed
        v_enc = self._safe_encode(self.vehicle_encoder, 'CAR')
        p_enc = self._safe_encode(self.violation_encoder, 'WRONG PARKING')
        
        for _, row in unique_cells.iterrows():
            for h in hours_to_check:
                rows.append({
                    'grid_id': row['grid_id'],
                    'lat_bin': row['lat_bin'],
                    'lon_bin': row['lon_bin'],
                    'hour': h,
                    'day_of_week': 0,
                    'is_weekend': 0,
                    'is_peak_hour': int(h in [7, 8, 9, 17, 18, 19]),
                    'month': 5,
                    'vehicle_type_encoded': v_enc,
                    'primary_violation_encoded': p_enc
                })
                
        batch_df = pd.DataFrame(rows)
        features = [
            'hour', 'day_of_week', 'is_weekend', 'is_peak_hour', 'month',
            'vehicle_type_encoded', 'primary_violation_encoded',
            'lat_bin', 'lon_bin'
        ]
        
        scores = self.model.predict(batch_df[features])
        batch_df['score'] = np.clip(scores, 0.0, 100.0)
        
        results = []
        for grid_id, group in batch_df.groupby('grid_id'):
            avg_score = group['score'].mean()
            peak_hour = group.loc[group['score'].idxmax()]['hour']
            lat_bin = group['lat_bin'].iloc[0]
            lon_bin = group['lon_bin'].iloc[0]
            
            if avg_score < 25: risk_level = "LOW"
            elif avg_score < 50: risk_level = "MEDIUM"
            elif avg_score < 75: risk_level = "HIGH"
            else: risk_level = "CRITICAL"
            
            results.append({
                'grid_id': grid_id,
                'lat': lat_bin,
                'lon': lon_bin,
                'avg_score': round(float(avg_score), 1),
                'peak_hour': int(peak_hour),
                'risk_level': risk_level
            })
            
        results_df = pd.DataFrame(results)
        return results_df.sort_values('avg_score', ascending=False).head(top_n)


if __name__ == "__main__":
    from data_loader import DataLoader
    
    dl = DataLoader()
    df = dl.load_and_clean()
    df = dl.create_grid_cells(df)
    
    m = ParkingCongestionModel()
    m.train(df)
    
    print("\n--- TOP ENFORCEMENT ZONES ---")
    zones = m.get_top_enforcement_zones(df)
    print(zones.head(10))
    
    print("\n--- SAMPLE PREDICTION ---")
    print(m.predict(12.975, 77.575, hour=2, day_of_week=1))
