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
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app_state = {}

def format_hour(h):
    if h == 0: return "12 AM"
    elif h == 12: return "12 PM"
    elif h < 12: return f"{h} AM"
    else: return f"{h-12} PM"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading data and model...")
    dl = DataLoader()
    df = dl.load_and_clean()
    df = dl.create_grid_cells(df)
    
    model = ParkingCongestionModel()
    try:
        model.load()
    except Exception as e:
        print(f"Model load/train error: {e}")
        raise
    
    app_state['df'] = df
    app_state['dl'] = dl
    app_state['model'] = model
    app_state['analyzer'] = CongestionAnalyzer()
    
    print("Precomputing stats...")
    app_state['hotspots_df'] = model.get_top_enforcement_zones(df, top_n=50)
    app_state['hourly'] = dl.get_hourly_trend(df)
    app_state['violation_types'] = dl.get_violation_type_breakdown(df)
    app_state['vehicle_types'] = dl.get_vehicle_breakdown(df)
    app_state['feedback_analysis'] = {}
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

@app.get("/api")
def root():
    return {
        "project": "Traffiq",
        "hackathon": "Gridlock Hackathon 2.0",
        "status": "running",
        "endpoints": [
            "/api/stats", "/api/heatmap", "/api/hotspots",
            "/api/trend", "/api/predict", "/api/report", "/api/query"
        ],
        "dashboard": "Served at /",
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

def get_explain_data(zone_id: str):
    df = app_state['df']
    try:
        model_obj = app_state['model'].model
        importances = model_obj.feature_importances_.tolist()
        features_list = ['hour', 'day_of_week', 'is_weekend', 'is_peak_hour', 'month', 'vehicle_type_encoded', 'primary_violation_encoded', 'lat_bin', 'lon_bin']
        raw_imp = dict(zip(features_list, importances))
    except Exception:
        raw_imp = {"lat_bin": 0.2, "lon_bin": 0.2, "hour": 0.3, "day_of_week": 0.2, "vehicle_type_encoded": 0.1}

    grouped_importances = {
        "location_grid": round(raw_imp.get("lat_bin", 0) + raw_imp.get("lon_bin", 0), 4),
        "hour": round(raw_imp.get("hour", 0) + raw_imp.get("is_peak_hour", 0), 4),
        "day_of_week": round(raw_imp.get("day_of_week", 0) + raw_imp.get("is_weekend", 0), 4),
        "vehicle_type": round(raw_imp.get("vehicle_type_encoded", 0), 4)
    }

    grid_counts = df.groupby('grid_id').size()
    zone_count = grid_counts.get(zone_id, 0)
    percentile_75 = grid_counts.quantile(0.75) if not grid_counts.empty else 0
    
    zone_df = df[df['grid_id'] == zone_id]
    peak_hour = zone_df['hour'].mode()[0] if not zone_df.empty else 12
    
    if zone_count > percentile_75 and peak_hour in [17, 18, 19, 20, 21, 22]:
        primary_cause = "illegal parking-induced congestion during peak hours"
    elif zone_count > percentile_75 and peak_hour in [8, 9, 10, 18, 19]:
        primary_cause = "peak commute volume"
    elif zone_count > percentile_75:
        primary_cause = "chronic junction bottleneck"
    else:
        primary_cause = "isolated/low-risk zone"
        
    hotspots_df = app_state['hotspots_df']
    zone_hotspot = hotspots_df[hotspots_df['grid_id'] == zone_id]
    risk_score = float(zone_hotspot.iloc[0]['avg_score']) if not zone_hotspot.empty else 0.0

    citizen_signal = {"complaint_count": 0, "average_urgency": "none"}
    if zone_id in app_state.get('feedback_analysis', {}):
        zone_fb = app_state['feedback_analysis'][zone_id]
        citizen_signal['complaint_count'] = len(zone_fb)
        urgencies = [fb.get('urgency', 'low').lower() for fb in zone_fb]
        if urgencies.count('high') > 0: citizen_signal['average_urgency'] = 'high'
        elif urgencies.count('medium') > 0: citizen_signal['average_urgency'] = 'medium'
        else: citizen_signal['average_urgency'] = 'low'
        
    return {"zone_id": zone_id, "feature_importances": grouped_importances, "primary_cause": primary_cause, "risk_score": risk_score, "citizen_signal": citizen_signal}

@app.get("/api/explain/{zone_id}")
def get_explain(zone_id: str):
    return get_explain_data(zone_id)

@app.post("/api/feedback/analyze")
def analyze_feedback():
    import os, pandas as pd, json
    feedback_path = os.path.join(os.path.dirname(__file__), "../data/citizen_feedback.csv")
    if not os.path.exists(feedback_path):
        return {"error": "citizen_feedback.csv not found"}
        
    fb_df = pd.read_csv(feedback_path)
    results = {}
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    batch_size = 10
    for i in range(0, len(fb_df), batch_size):
        batch = fb_df.iloc[i:i+batch_size]
        prompt = "Analyze the citizen complaints. For each, extract the zone_id, topic, sentiment (negative|neutral|positive), and urgency (high|medium|low). Return a JSON array of objects with exactly these keys.\n\nComplaints:\n" + "\n".join([f"Zone: {row['zone_id']}, Text: {row['text']}" for _, row in batch.iterrows()])
        try:
            res = model.generate_content(prompt)
            text = res.text
            if text.startswith('```json'): text = text[7:]
            if text.endswith('```'): text = text[:-3]
            for item in json.loads(text.strip()):
                z_id = item.get('zone_id')
                if z_id:
                    results.setdefault(z_id, []).append(item)
        except Exception as e:
            print(f"Batch error: {e}")
            
    app_state['feedback_analysis'] = results
    return {"status": "success", "processed_zones": len(results)}

class AskRequest(BaseModel):
    question: str

@app.post("/api/ask")
def ask_question(req: AskRequest):
    df = app_state['df']
    
    # 1. Compute aggregated stats
    violation_counts_by_grid = df.groupby('grid_id').size().to_dict()
    violation_counts_by_hour = df.groupby('hour').size().to_dict()
    violation_counts_by_day = df.groupby('day_of_week').size().to_dict()
    
    hotspots_df = app_state['hotspots_df'].head(10)
    top_10_zones = hotspots_df[['grid_id', 'avg_score', 'peak_hour', 'risk_level']].to_dict(orient='records')
    
    for z in top_10_zones:
        exp = get_explain_data(z['grid_id'])
        z['primary_cause'] = exp['primary_cause']
        z['feature_importances'] = exp['feature_importances']

    
    try:
        model_obj = app_state['model'].model
        importances = model_obj.feature_importances_.tolist()
        features_list = ['hour', 'day_of_week', 'is_weekend', 'is_peak_hour', 'month', 'vehicle_type_encoded', 'primary_violation_encoded', 'lat_bin', 'lon_bin']
        feature_importances = dict(zip(features_list, importances))
    except Exception:
        feature_importances = None
        
    context = {
        "violation_counts_by_grid": violation_counts_by_grid,
        "violation_counts_by_hour": violation_counts_by_hour,
        "violation_counts_by_day": violation_counts_by_day,
        "top_10_highest_risk_zones": top_10_zones,
        "feature_importances": feature_importances
    }
    
    system_instruction = (
        "You are an AI assistant for a traffic violation analytics app. "
        "Use the provided JSON context to answer the user's question. "
        "Return exactly a JSON object (and no other text or markdown) with the following schema: "
        "{\"answer\": string, \"zone_id\": string | null, \"chart_type\": \"risk_by_hour\" | \"risk_by_zone\" | \"risk_by_day\" | null}"
    )
    prompt = f"Context: {json.dumps(context)}\n\nQuestion: {req.question}"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        full_prompt = system_instruction + "\n\n" + prompt
        response = model.generate_content(full_prompt)
        # Parse it safely since response_mime_type is not supported
        text = response.text
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Rule-based fallback
        if "night" in req.question.lower():
            return {"answer": "Rule-based fallback: The worst zones at night usually correspond to peak hours between 19:00 and 23:00.", "zone_id": None, "chart_type": "risk_by_hour"}
        elif "day" in req.question.lower():
            best_day = max(violation_counts_by_day, key=violation_counts_by_day.get)
            return {"answer": f"Rule-based fallback: Day {best_day} has the most violations based on the current dataset.", "zone_id": None, "chart_type": "risk_by_day"}
        else:
            return {"answer": "Rule-based fallback: Please check the dashboard for specific zone details.", "zone_id": top_10_zones[0]['grid_id'] if top_10_zones else None, "chart_type": "risk_by_zone"}

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

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
