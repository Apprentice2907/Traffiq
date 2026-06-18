# Traffiq 🅿
### AI-Driven Parking Violation Intelligence for Bangalore Traffic
> Built for Gridlock Hackathon 2.0 — Round 2

## Problem Statement
On-street illegal parking near commercial areas, metro stations, and junctions
chokes Bangalore's carriageways. Enforcement is reactive and patrol-based with
no data-driven prioritization.

## Our Solution
Traffiq analyzes 115,350 real police violation records to:
- Detect illegal parking hotspots via spatial grid clustering
- Quantify congestion impact using XGBoost (R² = 0.99)
- Predict zone risk for any location + time combination
- Generate AI enforcement patrol schedules automatically

## Strategic Value
Traffiq enables Bangalore Traffic Police to shift from **reactive, 
patrol-based enforcement** to **predictive, resource-efficient deployment**.

- Targeting only the top 5% of high-impact zones covers 40%+ of all violations
- Night shift reallocation (8 PM–6 AM) addresses 88.3% of violations
- Daytime gap (12 PM–4 PM) allows officer redeployment to admin tasks
- Estimated enforcement overhead reduction: 30–40% with same officer count

> "Don't patrol everywhere. Deploy where the data says violations will happen."

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

## Model Transparency
- Algorithm: XGBoost Regressor | R² = 0.99 | RMSE = 1.76
- High R² reflects strong temporal periodicity in Bangalore violation patterns
- Train/test split 80/20 across spatial grid bins ensures generalization
- Features ranked by importance: location grid > hour > day_of_week > vehicle_type
