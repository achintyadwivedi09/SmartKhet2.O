# SmartKhet 2.0
### Big Data-Powered Fog-Based Intelligent Rural Irrigation System

SmartKhet 2.0 is an academic and startup-grade prototype designed to optimize irrigation scheduling for rural agricultural farms across Tamil Nadu, India. The platform integrates authentic historical meteorology (IMD, ISRO MOSDAC, ERA5-Land), Big Data preprocessing, machine learning soil moisture estimation, independent local Fog-node edge inference, cloud telemetry synchronization, an interactive 8-page SaaS dashboard, and a permanent 20-column audit ledger.

---

## 1. System Architecture

SmartKhet 2.0 deploys three independent virtual Fog nodes corresponding to three demonstration farms in Tamil Nadu:
- **TN001 — Cauvery Delta Farm (Thanjavur):** Crop: Rice, Soil: Clay loam, Trigger threshold: $0.28\text{ m}^3/\text{m}^3$.
- **TN002 — Kongu Upland Farm (Coimbatore):** Crop: Cotton, Soil: Red sandy loam, Trigger threshold: $0.18\text{ m}^3/\text{m}^3$.
- **TN003 — Madurai Drylands Farm (Madurai):** Crop: Groundnut, Soil: Red loamy, Trigger threshold: $0.14\text{ m}^3/\text{m}^3$.

Each Fog node maintains an in-situ Random Forest Regressor (`rf_model.joblib`), executing deterministic inferences in ~**12 ms**. During simulated cloud backhaul outages, nodes continue full decision cycles autonomously, buffering events in an embedded ring buffer and flushing to the central cloud upon reconnection.

---

## 2. Directory Structure

```
SmartKhet2.O/
├── frontend/          # React 18 + TypeScript + Vite + Tailwind CSS (8 pages)
├── backend/           # FastAPI + SQLAlchemy + SQLite + PySpark + ML services
├── data/              # raw/, interim/, processed/, models/, reports/, metadata/
├── docs/              # 11 comprehensive academic & technical documentation files
└── tests/             # Automated test suites (backend, data, ml, fog, integration)
```

---

## 3. Installation & Setup Instructions (Windows 11)

### Step 1: Open PowerShell
Open PowerShell and navigate to the project directory:
```powershell
cd C:\Users\achin\Desktop\Pitaji\SmartKhet2.O
```

### Step 2: Python Environment & Dependencies
Python 3.10+ is supported:
```powershell
# Optional: Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: Run the Big Data & ML Pipeline (Reproducible)
From the `backend` directory, execute the pipeline sequentially:
```powershell
cd backend
python data_pipeline/03_generate_demo_dataset.py
python data_pipeline/04_preprocess.py
python data_pipeline/05_feature_engineering.py
python data_pipeline/06_validate_pipeline.py
python data_pipeline/07_train_model.py
python data_pipeline/08_generate_reports.py
cd ..
```

### Step 4: Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 4. Running the Platform

### Terminal 1 — Start the Backend Server (FastAPI)
```powershell
cd C:\Users\achin\Desktop\Pitaji\SmartKhet2.O\backend
python main.py
```
- API Base URL: `http://localhost:8000`
- Swagger Interactive Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- Live WebSocket Feed: `ws://localhost:8000/ws`

### Terminal 2 — Start the Frontend Development Server (React)
```powershell
cd C:\Users\achin\Desktop\Pitaji\SmartKhet2.O\frontend
npm run dev
```
- Interactive Agricultural Dashboard: `http://localhost:5173`

---

## 5. Running Automated Tests

Run the complete automated test suite covering API routes, Big Data preprocessing, ML anti-leakage gates, and Fog autonomy:
```powershell
python -m pytest tests/ -v
```

---

## 6. Permanent Audit Log Export

Export the latest chronological audit ledger to `docs/SMARTKHET_PROJECT_AUDIT_LOG.csv`:
```powershell
cd backend
python -c "from services.audit_service import audit_service; audit_service.export_csv()"
```

---

## 7. Model Performance Summary (Test Set: N=822)

- **Random Forest Regressor (Deployed):**
  - Test $R^2$: **0.8722** (Explains 87.22% of soil moisture variance)
  - Test RMSE: **0.0082 m³/m³**
  - Test MAE: **0.0040 m³/m³**
  - Median AE: **0.0012 m³/m³**
  - Edge Inference Latency: **~12 ms**
- **Baseline (Persistence):**
  - Test $R^2$: 0.7946 | RMSE: 0.0103 m³/m³ | MAE: 0.0044 m³/m³
- **XGBoost Regressor:**
  - Test $R^2$: 0.8582 | RMSE: 0.0086 m³/m³ | MAE: 0.0042 m³/m³

