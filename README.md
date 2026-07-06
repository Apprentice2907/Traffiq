# Nexus: AI-Powered Decision Intelligence Platform 🏙️
### Built for the Google Cloud Architecture Hackathon

## Introduction
Cities run on data, but government agencies operate in silos. Nexus is a generalized **Decision Intelligence Platform** designed to break these silos by unifying structured IoT/sensor data with unstructured citizen feedback. Architected for the Google Cloud ecosystem and currently prototyped with an equivalent open-source stack for rapid iteration, Nexus transforms raw civic data into explainable, automated, and predictive workflows.

While the architecture is domain-agnostic, we are proud to present **Traffiq** as the first deployed proof-of-concept module—a predictive parking enforcement intelligence tool designed for Bangalore traffic police.

## Platform Architecture
Our generalized pipeline turns raw data into actionable civic intelligence:
1. **Ingest**: Connect both structured datasets (IoT sensors, legacy databases) and unstructured data streams (citizen social media feedback, support tickets).
2. **Detect Patterns**: Spatiotemporal aggregation to identify chronic hotspots and anomalies.
3. **Predict Outcomes**: Train regression/classification models to forecast risk and resource requirements.
4. **Generate Recommendations**: AI-driven synthesis of data to recommend automated workflows (e.g., patrol schedules, maintenance dispatches).
5. **Automate Workflows**: Multi-step AI agents autonomously draft reports and trigger interventions.
6. **Explain Decisions**: Surface feature importance and deterministic rules so human operators trust the AI.

## Google Cloud Production Path
Nexus is designed to scale across the following Google Cloud technologies:
- **BigQuery**: Centralized data warehouse for structured violation logs and historical analytics.
- **Vertex AI**: End-to-end model training, registry, and serving for our XGBoost predictive layers.
- **Gemini**: The core reasoning and conversational layer, parsing unstructured citizen text and summarizing intelligence reports.
- **Agent Development Kit (ADK)**: Orchestrating multi-step automation, allowing natural language queries to trigger backend data pipelines.
- **Cloud Run**: Serverless, autoscaling deployment for the containerized FastAPI backend and frontend.

## Roadmap: Beyond Traffic
The Nexus platform is designed to scale instantly to other civic domains. Our next targeted modules include:
- **Waste Management overflow prediction**: Fusing smart-bin weight sensors (structured) with citizen reports of illegal dumping (unstructured) to optimize garbage truck routes.
- **Energy & Utility anomaly detection**: Analyzing smart grid usage spikes alongside text-based outage reports to predict transformer failures before they happen.
- **Healthcare access gap analysis**: Mapping hospital capacity metrics against patient feedback to optimally position mobile health clinics during outbreaks.

---

## Module 1: Traffiq 🅿 (Proof of Concept)
### AI-Driven Parking Violation Intelligence

Traffiq analyzes over 115,000 real police violation records alongside live citizen feedback to enable predictive, resource-efficient deployment.

### Problem Statement
On-street illegal parking near commercial areas, metro stations, and junctions chokes Bangalore's carriageways. Enforcement is reactive and patrol-based with no data-driven prioritization.

### Strategic Value
Traffiq enables Bangalore Traffic Police to shift from **reactive, patrol-based enforcement** to **predictive, resource-efficient deployment**.
- Targeting only the top 5% of high-impact zones covers 40%+ of all violations
- Night shift reallocation (8 PM–6 AM) addresses 88.3% of violations
- Daytime gap (12 PM–4 PM) allows officer redeployment to admin tasks
- Estimated enforcement overhead reduction: 30–40% with same officer count

> "Don't patrol everywhere. Deploy where the data says violations will happen."

### Traffiq Architecture
- **Backend:** Python, FastAPI, Pandas, Uvicorn
- **Machine Learning:** Scikit-learn, XGBoost Regressor
- **Frontend:** Vanilla HTML/CSS/JS, Leaflet.js (Heatmaps), Chart.js
- **Data Pipeline:** Custom `DataLoader` that bins geospatial coordinates into 500m grids and extracts temporal features.

### Setup Instructions
1. Navigate to the `backend/` directory.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the API server: `python app.py`
4. Open `frontend/index.html` in your web browser.

### Key Features
- **Live Violation Heatmap**: CartoDB map with Leaflet heatmap overlay.
- **AI Prediction Engine**: Predicts congestion risk scores and recommends patrol actions.
- **NLP Querying**: Ask questions like "Which zone is worst at night?" and get instant insights grounded in explainable data.
- **Explainability Panel**: Visualizes feature importances and extracts human-readable primary causes for any zone.
- **Unstructured Data Fusion**: Blends citizen complaints parsed by Gemini directly into the hotspot risk profiles. *(Note: Citizen feedback text is synthetically generated to demonstrate unstructured data fusion capabilities; in a production deployment, this would ingest real support tickets or social media streams.)*
- **Automated Intelligence Reports**: Generates downloadable Markdown reports containing patrol schedules and strategic recommendations.

### Model Transparency
- Algorithm: XGBoost Regressor | R² = 0.99 | RMSE = 1.76
- High R² reflects strong temporal periodicity in Bangalore violation patterns
- Train/test split 80/20 across spatial grid bins ensures generalization
- Features ranked by importance: location grid > hour > day_of_week > vehicle_type
