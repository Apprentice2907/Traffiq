from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
import pandas as pd
from data_loader import DataLoader
from model import ParkingCongestionModel
import os
import datetime
from analyzer import CongestionAnalyzer
from fastapi.responses import RedirectResponse

app_state = {}

def format_hour(h):
    if h == 0: return "12 AM"
    elif h == 12: return "12 PM"
    elif h < 12: return f"{h} AM"
    else: return f"{h-12} PM"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading data and model...")
    dl = DataLoader("../data.csv")
    df = dl.load_and_clean()
    df = dl.create_grid_cells(df)
    
    model = ParkingCongestionModel()
    model.load()
    
    app_state['df'] = df
    app_state['dl'] = dl
    app_state['model'] = model
    app_state['analyzer'] = CongestionAnalyzer()
    
    print("Precomputing stats...")
    app_state['hotspots_df'] = model.get_top_enforcement_zones(df, top_n=50)
    app_state['hourly'] = dl.get_hourly_trend(df)
    app_state['violation_types'] = dl.get_violation_type_breakdown(df)
    app_state['vehicle_types'] = dl.get_vehicle_breakdown(df)
    print("Ready!")
    
    yield
    app_state.clear()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "project": "Traffiq",
        "hackathon": "Gridlock Hackathon 2.0",
        "status": "running",
        "endpoints": [
            "/api/stats", "/api/heatmap", "/api/hotspots",
            "/api/trend", "/api/predict", "/api/report", "/api/query"
        ],
        "dashboard": "Open frontend/index.html in browser",
        "docs": "/docs"
    }

@app.get("/api/stats")
def get_stats():
    df = app_state['df']
    hourly = app_state['hourly']
    hotspots_df = app_state['hotspots_df']
    
    total_violations = len(df)
    peak_hour = max(hourly, key=hourly.get)
    
    high_critical = hotspots_df[hotspots_df['risk_level'].isin(['HIGH', 'CRITICAL'])]
    
    top_grid_id = hotspots_df.iloc[0]['grid_id']
    zone_df = df[df['grid_id'] == top_grid_id]
    top_zone = zone_df['junction_name'].mode()[0] if not zone_df.empty and not zone_df['junction_name'].mode().empty else "Unknown Zone"
    
    approved_violations = len(df[df['validation_status'] == 'approved'])
    
    night_v = len(df[(df['hour'] >= 20) | (df['hour'] <= 6)])
    night_violation_pct = round((night_v / total_violations) * 100, 1) if total_violations > 0 else 0.0
    
    return {
        "total_violations": total_violations,
        "peak_hour": int(peak_hour),
        "peak_hour_label": format_hour(int(peak_hour)),
        "hotspot_count": len(high_critical),
        "top_zone": str(top_zone),
        "approved_violations": approved_violations,
        "night_violation_pct": float(night_violation_pct)
    }

@app.get("/api/heatmap")
def get_heatmap():
    df = app_state['df']
    model = app_state['model']
    
    grid_counts = df.groupby(['grid_id', 'lat_bin', 'lon_bin']).size().reset_index(name='violation_count')
    top_cells = grid_counts.sort_values('violation_count', ascending=False).head(200)
    
    features = []
    for _, row in top_cells.iterrows():
        pred = model.predict(row['lat_bin'], row['lon_bin'], hour=19, day_of_week=0)
        
        features.append({
            "type": "Feature",
            "properties": {
                "grid_id": row['grid_id'],
                "violation_count": int(row['violation_count']),
                "congestion_score": pred['congestion_score'],
                "risk_level": pred['risk_level'],
                "risk_color": pred['risk_color']
            },
            "geometry": {
                "type": "Point",
                "coordinates": [row['lon_bin'], row['lat_bin']]
            }
        })
    return {"type": "FeatureCollection", "features": features}

@app.get("/api/hotspots")
def get_hotspots():
    df = app_state['df']
    hotspots_df = app_state['hotspots_df'].head(20).copy()
    
    results = []
    for i, row in enumerate(hotspots_df.itertuples(), 1):
        grid_id = row.grid_id
        zone_df = df[df['grid_id'] == grid_id]
        junction_name = zone_df['junction_name'].mode()[0] if not zone_df.empty and not zone_df['junction_name'].mode().empty else "Unknown Zone"
        
        pred = app_state['model'].predict(row.lat, row.lon, hour=row.peak_hour, day_of_week=0)
        
        results.append({
            "rank": i,
            "grid_id": grid_id,
            "lat": row.lat,
            "lon": row.lon,
            "avg_score": row.avg_score,
            "peak_hour": int(row.peak_hour),
            "peak_hour_label": format_hour(int(row.peak_hour)),
            "risk_level": row.risk_level,
            "risk_color": pred['risk_color'],
            "junction_name": str(junction_name)
        })
    return results

@app.get("/api/trend")
def get_trend():
    hourly = app_state['hourly']
    labels = [format_hour(h) for h in range(24)]
    data = [hourly.get(h, 0) for h in range(24)]
    return {"labels": labels, "data": data}

@app.get("/api/violations/type")
def get_violation_types():
    v_types = app_state['violation_types']
    colors = ["#ef4444","#f97316","#f59e0b","#22c55e","#3b82f6","#8b5cf6","#ec4899","#14b8a6","#84cc16","#6366f1"]
    return {
        "labels": list(v_types.keys()),
        "data": list(v_types.values()),
        "colors": colors[:len(v_types)]
    }

@app.get("/api/violations/vehicle")
def get_vehicle_types():
    v_types = app_state['vehicle_types']
    items = list(v_types.items())[:8]
    colors = ["#ef4444","#f97316","#f59e0b","#22c55e","#3b82f6","#8b5cf6","#ec4899","#14b8a6"]
    return {
        "labels": [item[0] for item in items],
        "data": [item[1] for item in items],
        "colors": colors[:len(items)]
    }

class PredictRequest(BaseModel):
    lat: float
    lon: float
    hour: int
    day_of_week: int

@app.post("/api/predict")
def predict_endpoint(req: PredictRequest):
    return app_state['model'].predict(req.lat, req.lon, req.hour, req.day_of_week)

@app.get("/api/report")
def get_report():
    df = app_state['df']
    hotspots_df = app_state['hotspots_df']
    hourly = app_state['hourly']
    violation_types = app_state['violation_types']
    analyzer = app_state['analyzer']
    
    report_md = analyzer.generate_enforcement_report(hotspots_df, hourly, violation_types, df)
    return {"report": report_md, "generated_at": datetime.datetime.now().isoformat()}

class QueryRequest(BaseModel):
    question: str

@app.post("/api/query")
def post_query(req: QueryRequest):
    analyzer = app_state['analyzer']
    df = app_state['df']
    hourly = app_state['hourly']
    total_violations = len(df)
    peak_hour = max(hourly, key=hourly.get)
    night_v = len(df[(df['hour'] >= 20) | (df['hour'] <= 6)])
    night_violation_pct = round((night_v / total_violations) * 100, 1) if total_violations > 0 else 0.0
    
    top_grid_id = app_state['hotspots_df'].iloc[0]['grid_id']
    zone_df = df[df['grid_id'] == top_grid_id]
    top_zone = zone_df['junction_name'].mode()[0] if not zone_df.empty else "Unknown Zone"
    
    stats = {
        "peak_hour_label": format_hour(int(peak_hour)),
        "night_violation_pct": night_violation_pct,
        "top_zone": str(top_zone)
    }
    return {"question": req.question, "answer": analyzer.answer_query(req.question, stats)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
