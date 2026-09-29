# 🔥 Industrial Fire & Thermal Source Classification System

> **SIH 2026 Problem Statement SIH26162** — Satellite-based thermal anomaly detection, source classification (gas flares, industrial explosions, crop burning, coal seam fires, wildfires, desert glare false alarms), spatial facility matching, and multi-factor investigation risk triage.

---

## 🌟 Architecture Overview

This repository integrates satellite thermal remote sensing data (NASA FIRMS MODIS & VIIRS), spatial OpenStreetMap (OSM) industrial facility datasets, Machine Learning (Isolation Forest anomaly detection & BallTree spatial joins), a FastAPI REST backend, and a modern React + Leaflet web dashboard.

```
fire-thermal-classifier/
├── backend/                  # FastAPI REST Server + ML & Rule-Based Classifier
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint & router registry
│   │   ├── config.py         # Application configuration & env variables
│   │   ├── database.py       # SQLAlchemy + PostGIS connection (with offline mode)
│   │   ├── routers/          # API endpoints (/api/hotspots, /api/alerts, /api/industrial-ai, etc.)
│   │   ├── services/         # ML models, spatial joins, Isolation Forest, BallTree matcher
│   │   ├── models/           # SQLAlchemy database models
│   │   └── scheduler.py      # APScheduler background tasks for FIRMS & OSM polling
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React 19 + Vite + Leaflet Web Application
│   ├── src/
│   │   ├── App.jsx           # Main application with view switcher (Classifier & AI Dashboard)
│   │   ├── components/       # MapView, IndustrialAIDashboard, AlertsFeed, CategoryLegend
│   │   └── data/             # API client & mock data fallbacks
│   └── package.json          # Frontend Node.js dependencies
└── Industrial_Fire_AI/       # ML Pipeline & Standalone Streamlit Dashboard
    ├── app.py                # Interactive Streamlit Web Dashboard
    ├── anomaly_detection.py  # Isolation Forest anomaly training per satellite
    ├── industrial_matching.py# BallTree spatial join against OSM industrial sites
    ├── risk_classification.py# Multi-factor investigation priority triage engine
    └── *.csv                 # Pre-classified & mapped industrial fire datasets
```

---

## ✨ Features

1. **Multi-Category Thermal Source Classifier**:
   - **Gas Flare (`gas_flare`)**: Steady, recurring thermal signatures inside industrial facility boundaries.
   - **Accident / Explosion (`accident_explosion`)**: Sudden, intense brightness spikes vs. baseline history inside industrial zones.
   - **Crop Burning (`crop_burning`)**: Simultaneous clusters over agricultural land during harvest season (Oct-Nov / Apr-May).
   - **Coal Seam Fire (`coal_seam_fire`)**: Persistent low-level thermal detections over mining/exposed land.
   - **Wildfire (`wildfire`)**: Spreading cluster fronts over forest land boundaries.
   - **Desert Glare / False Alarm (`desert_glare_false_alarm`)**: Low FRP, isolated surface reflection false positives.

2. **Industrial Fire AI Module**:
   - **Isolation Forest Anomaly Scoring**: Trains unsupervised decision trees per satellite instrument (`MODIS`, `VIIRS N20`, `SNPP`, `Aqua`, `Terra`) on `brightness`, `bright_t31`, `frp`, `scan`, and `track`.
   - **BallTree Haversine Spatial Matcher**: Calculates exact distances (`nearest_industry_distance_km`) to mapped OSM industrial locations (`industrial_locations.csv`).
   - **Multi-Factor Priority Triage**: Assigns investigation priorities (`HIGH`, `MEDIUM`, `LOW`) with human-readable rationale (`classification_reason`).

3. **Interactive React + Leaflet Web Dashboard**:
   - Real-time navigation between **Classifier View** and **Industrial AI Dashboard**.
   - Interactive OpenStreetMap view with color-coded markers (`HIGH` = Red, `MEDIUM` = Orange, `LOW` = Blue).
   - Rich anomaly popups detailing FRP (MW), Brightness (K), Anomaly Score, Nearest Industry, and Distance.
   - Live Search, Priority Filters, CSV Alert Export, and On-Demand AI Pipeline Re-Execution.

4. **Standalone Streamlit Dashboard**:
   - Standalone Python visualization dashboard for thermal anomaly mapping and analysis.

---

## 🚀 How to Setup and Run the Project

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher (with `npm`)

---

### Step 1: Backend Setup (FastAPI)

1. Open a terminal and navigate to the `backend` directory:
   ```powershell
   cd backend
   ```

2. Install Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Launch the FastAPI server:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
   *The backend will start at `http://127.0.0.1:8000` (works with PostgreSQL or in automatic offline CSV fallback mode).*

---

### Step 2: Frontend Setup (React + Vite)

1. Open a second terminal and navigate to the `frontend` directory:
   ```powershell
   cd frontend
   ```

2. Install Node dependencies:
   ```powershell
   npm install
   ```

3. Launch the Vite development server:
   ```powershell
   npm run dev
   ```
   *The frontend web dashboard will open at `http://localhost:5173` (or port indicated in the terminal).*

---

### Step 3: Standalone Streamlit App (Optional)

To run the standalone Streamlit dashboard from `Industrial_Fire_AI`:
```powershell
cd Industrial_Fire_AI
streamlit run app.py
```
*The Streamlit dashboard will launch at `http://localhost:8501`.*

---

## 🧪 Testing the Application

### 1. Web Interface Testing
1. Open `http://localhost:5173` in your web browser.
2. **Classifier View**:
   - View thermal hotspots plotted over Panipat / Haryana region.
   - Toggle categories in the legend panel to filter markers dynamically.
   - Click any hotspot dot or alert card to view detailed historical FRP time-series.
3. **Industrial AI Dashboard**:
   - Click the **🤖 Industrial AI Dashboard** tab in the top navigation bar.
   - View total anomalies, HIGH (52), MEDIUM (818), and LOW (1561) priority cards.
   - Click priority filter buttons to toggle visibility.
   - Use the search bar to search for mapped industrial facilities (e.g., *"depot"*, *"saw mill"*, *"refinery"*).
   - Click **📥 Export CSV** to download the filtered alert report.
   - Click **⚡ Re-run AI Pipeline** to trigger on-demand Isolation Forest + BallTree spatial matching.

### 2. API Endpoint Testing

You can test the FastAPI backend endpoints via `curl`, Python, or browser:

- **Health Check**:
  ```http
  GET http://127.0.0.1:8000/api/health
  ```
- **Industrial AI Summary Metrics**:
  ```http
  GET http://127.0.0.1:8000/api/industrial-ai/summary
  ```
- **Industrial AI Alerts List** (with filters):
  ```http
  GET http://127.0.0.1:8000/api/industrial-ai/alerts?priority=HIGH,MEDIUM&limit=10
  ```
- **CSV Export**:
  ```http
  GET http://127.0.0.1:8000/api/industrial-ai/export-csv?priority=HIGH
  ```
- **Re-run AI Pipeline**:
  ```http
  POST http://127.0.0.1:8000/api/industrial-ai/run-pipeline
  ```
- **Interactive OpenAPI Documentation**:
  Visit `http://127.0.0.1:8000/docs` in your browser for Swagger UI testing.

---

## 🛠️ Technology Stack

- **Frontend**: React 19, Vite, Leaflet, React-Leaflet, TailwindCSS, Recharts
- **Backend**: FastAPI, Uvicorn, SQLAlchemy, GeoAlchemy2, Pydantic, APScheduler
- **Machine Learning & Spatial**: scikit-learn (Isolation Forest), BallTree, Pandas, NumPy
- **Standalone**: Streamlit, Folium
