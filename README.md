# ParkSense AI 🅿
### AI-Driven Parking Violation Intelligence for Bangalore Traffic
> Built for Gridlock Hackathon 2.0 — Round 2

## Problem Statement
On-street illegal parking near commercial areas, metro stations, and junctions
chokes Bangalore's carriageways. Enforcement is reactive and patrol-based with
no data-driven prioritization.

## Our Solution
ParkSense AI analyzes 115,350 real police violation records to:
- Detect illegal parking hotspots via spatial grid clustering
- Quantify congestion impact using XGBoost (R² = 0.99)
- Predict zone risk for any location + time combination
- Generate AI enforcement patrol schedules automatically

## Architecture
- **Backend:** Python, FastAPI, Pandas, Uvicorn
- **Machine Learning:** Scikit-learn, XGBoost Regressor
- **Frontend:** Vanilla HTML/CSS/JS, Leaflet.js (Heatmaps), Chart.js
- **Data Pipeline:** Custom `DataLoader` that bins geospatial coordinates into 500m grids and extracts temporal features.

## Setup Instructions
1. Navigate to the `backend/` directory.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the API server: `python app.py`
4. Open `frontend/index.html` in your web browser.

## Key Features
- **Live Violation Heatmap**: CartoDB dark map with Leaflet heatmap overlay.
- **AI Prediction Engine**: Predicts congestion risk scores and recommends patrol actions.
- **NLP Querying**: Ask questions like "Which zone is worst at night?" and get instant insights.
- **Automated Intelligence Reports**: Generates downloadable Markdown reports containing patrol schedules and strategic recommendations.
