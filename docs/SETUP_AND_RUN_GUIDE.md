# SmartKhet 2.0 — Complete Setup, Installation & Operation Guide

**SmartKhet 2.0: Big Data-Powered Fog-Based Intelligent Rural Irrigation System**  
*Operating Environment: Windows 11 / Modern Linux / macOS*  
*Architecture: FastAPI Backend + React 18 / TypeScript Frontend + Scikit-Learn ML + SQLite Database*

---

## 1. System Requirements & Prerequisites

Ensure the following runtimes and tools are installed on your machine:

| Component | Minimum Version | Recommended / Tested Version | Verification Command |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows 10/11 (64-bit) | Windows 11 Pro 64-bit | `winver` |
| **Python** | 3.10+ | Python 3.11 – 3.13 | `python --version` |
| **Node.js** | v18.0.0+ | Node.js v20+ / v24+ | `node -v` |
| **npm** | 9.0+ | npm 10+ / 11+ | `npm -v` |
| **Git** (optional) | 2.30+ | 2.40+ | `git --version` |

---

## 2. Project Directory Structure

SmartKhet 2.0 strictly adheres to the mandated 5-directory root architecture:

```text
SmartKhet2.O/
├── backend/            # FastAPI REST & WebSocket server, ML & Fog services, SQLite DB
├── data/               # Raw sources, interim data, processed CSVs, trained models & evaluation plots
├── docs/               # Technical specs, architecture, viva guides, and project reports
├── frontend/           # React 18, TypeScript, Vite, Tailwind CSS, Recharts dashboard
├── tests/              # 20 automated unit, integration, and simulation tests
├── .env.example        # Environment configuration template
├── .gitignore          # Git exclusion rules
└── README.md           # Project summary and quickstart
```

---

## 3. Step-by-Step Installation

### Step 3.1: Backend Virtual Environment & Dependencies

Open **PowerShell** or **Command Prompt** in the project root:

```powershell
# Navigate into the project root
cd c:\Users\achin\Desktop\Pitaji\SmartKhet2.O

# (Optional but recommended) Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Or Command Prompt (cmd):
.\venv\Scripts\activate.bat

# Install all backend requirements
pip install -r backend/requirements.txt
```

> **Note on PowerShell Script Execution:** If PowerShell returns an `Execution_Policies` restriction error when activating `venv`, execute:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### Step 3.2: Frontend Node.js Dependencies

Open another terminal or navigate into `frontend/`:

```powershell
cd c:\Users\achin\Desktop\Pitaji\SmartKhet2.O\frontend

# Install dependencies
npm install
```

---

## 4. Big Data Preprocessing & ML Model Training

*Note: All preprocessed datasets and trained model binaries are already generated and present in the repository. If you ever want to re-execute the pipeline from scratch, follow these commands:*

```powershell
# Navigate to project root with Python environment active
cd c:\Users\achin\Desktop\Pitaji\SmartKhet2.O

# Run the complete sequential data pipeline:
python backend/data_pipeline/01_acquire_datasets.py
python backend/data_pipeline/02_inspect_datasets.py
python backend/data_pipeline/03_generate_demo_dataset.py
python backend/data_pipeline/04_preprocess.py
python backend/data_pipeline/05_feature_engineering.py
python backend/data_pipeline/06_validate_pipeline.py
python backend/data_pipeline/07_train_model.py
python backend/data_pipeline/08_generate_reports.py
```

### Verified Artifacts Generated:
- `data/processed/demo_agricultural_data.csv` (5,478 daily agricultural observations across 3 Tamil Nadu farms)
- `data/processed/ml_ready_dataset.csv` (5,475 rows, 16 features ready for ML)
- `data/models/rf_model.joblib` (Random Forest Regressor, $R^2 = 0.8722$)
- `data/models/xgb_model.joblib` (XGBoost Regressor, $R^2 = 0.8582$)
- `data/models/scaler.joblib` (StandardScaler feature transformer)
- `data/reports/plots/` (Actual vs Predicted, Feature Importance, Residual distributions)

---

## 5. Starting the Application

The full application runs locally using two lightweight processes: the Backend API and the Frontend Vite development server.

### Terminal 1: Launch Backend API Server

```powershell
cd c:\Users\achin\Desktop\Pitaji\SmartKhet2.O\backend
python main.py
```

*The backend starts at `http://localhost:8000` (or `http://127.0.0.1:8000`).*  
- Auto-initializes the SQLite database (`backend/database/smartkhet.db`).
- Mounts all REST endpoints and the real-time WebSocket channel (`ws://localhost:8000/ws`).
- Loads the trained Random Forest model and starts the 3 local Fog Node daemons (`FOG-TN001`, `FOG-TN002`, `FOG-TN003`).

### Terminal 2: Launch Frontend Dashboard

```powershell
cd c:\Users\achin\Desktop\Pitaji\SmartKhet2.O\frontend
npm run dev
```

*Vite starts the React UI at `http://localhost:5173`.*

---

## 6. Accessing the Web Application

Open your web browser (Chrome, Edge, Firefox, Brave) and navigate to:

| Interface | URL | Description |
| :--- | :--- | :--- |
| **Interactive Dashboard** | [http://localhost:5173](http://localhost:5173) | Main React UI featuring all 8 pages, live charts, farm monitors, fog status, and audit viewer |
| **Interactive Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI / Swagger UI to test and execute API endpoints directly |
| **ReDoc API Documentation** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternative structured reference for all API schemas and endpoints |
| **System Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | JSON status endpoint reporting database and model readiness |
| **Real-Time WebSocket Feed** | `ws://localhost:8000/ws` | Live sensor stream, cloud sync ticks, and fog edge heartbeat broadcast |

---

## 7. Exploring Dashboard Modules

The frontend provides 8 fully functional modules via the left navigation bar:

1. **System Overview (`/`)**: High-level telemetry, active farm status, edge node connectivity, quick recommendation stats, and recent irrigation alerts.
2. **Farm Monitoring (`/farms`)**: Deep-dive into each farm (Thanjavur Paddy, Coimbatore Cotton, Madurai Groundnut) with historical soil moisture trends, live weather metrics, and irrigation controls.
3. **Big Data Analytics (`/analytics`)**: Historical dataset exploration, distribution histograms, correlation matrix, and data lineage tracking.
4. **Machine Learning Lab (`/ml-lab`)**: Model performance scorecard ($R^2$, RMSE, MAE, MedAE), feature importance breakdown, residual distributions, and an interactive **Live Prediction Sandbox** where you can enter soil & weather parameters and trigger local inference.
5. **Fog Computing Node Monitor (`/fog-nodes`)**: Real-time inspection of 3 edge fog nodes (`FOG-TN001`, `FOG-TN002`, `FOG-TN003`), edge memory/CPU utilization, local buffer count, offline simulation, and sync dispatch.
6. **Cloud Monitoring & Outage Lab (`/cloud-monitor`)**: Central cloud storage health, real-time ingestion rate, and an **Interactive Cloud Outage Simulator** where you can toggle cloud down/up to observe edge nodes buffering readings and automatically synchronizing when connectivity restores.
7. **Empirical Experiment Lab (`/experiments`)**: Fog vs. Cloud latency, bandwidth, and energy comparison benchmarks with live execution and graphical trade-off charts.
8. **Permanent Audit & Lineage (`/audit`)**: Cryptographically verifiable audit log displaying every acquisition, preprocessing step, ML training run, edge sync, and irrigation decision with SHA-256 integrity checksums.

---

## 8. Key API Endpoints Reference

All endpoints accept standard JSON payloads and return JSON responses.

### 8.1 Farms & Readings
- `GET /api/farms`: List all registered demonstration farms.
- `GET /api/farms/{farm_id}`: Detailed farm info, current sensors, and recommendations.
- `GET /api/farms/{farm_id}/readings?limit=50`: Historical time-series sensor observations.

### 8.2 Machine Learning
- `GET /api/ml/model-info`: Active model metadata, training metrics, features, and file paths.
- `POST /api/ml/predict`: On-demand next-day soil moisture prediction.
  ```json
  {
    "farm_id": "TN-001",
    "soil_moisture_lag1": 0.28,
    "soil_moisture_lag2": 0.29,
    "soil_moisture_lag3": 0.30,
    "rainfall_mm": 5.0,
    "temperature_c": 29.5,
    "humidity_pct": 75.0,
    "solar_radiation": 18.2,
    "wind_speed_ms": 2.5
  }
  ```

### 8.3 Fog Nodes & Edge Operations
- `GET /api/fog/nodes`: Status, battery, memory, and buffered event count for all fog nodes.
- `POST /api/fog/trigger-reading`: Simulate an edge sensor event and immediate local ML inference.
- `POST /api/fog/sync-cloud`: Trigger edge buffer synchronization to central cloud storage.

### 8.4 Cloud Architecture & Outage Simulator
- `GET /api/cloud/status`: Ingestion metrics, total stored records, and network availability.
- `POST /api/cloud/toggle-outage`: Simulate network loss or restoration (`{"is_offline": true/false}`).

### 8.5 Experiments & Auditing
- `POST /api/experiments/run`: Run latency & bandwidth simulation across varying packet sizes.
- `GET /api/audit/logs?limit=100`: Query the permanent project audit log.
- `GET /api/audit/export`: Export the complete immutable audit trail as a downloadable CSV.

---

## 9. Running the Automated Test Suite

SmartKhet 2.0 includes 20 comprehensive automated unit, integration, and simulation tests covering all system layers:

```powershell
cd c:\Users\achin\Desktop\Pitaji\SmartKhet2.O

# Execute pytest with verbose output
python -m pytest tests/ -v
```

### Expected Output:
```text
tests/backend/test_api_endpoints.py::test_health_endpoint PASSED
tests/backend/test_api_endpoints.py::test_get_farms PASSED
tests/backend/test_api_endpoints.py::test_ml_predict PASSED
tests/backend/test_api_endpoints.py::test_fog_nodes PASSED
tests/backend/test_api_endpoints.py::test_cloud_status PASSED
tests/data/test_data_integrity.py::test_raw_data_exists PASSED
tests/data/test_data_integrity.py::test_processed_data_valid PASSED
tests/data/test_data_integrity.py::test_ml_ready_features PASSED
tests/data/test_data_integrity.py::test_no_negative_rainfall PASSED
tests/data/test_data_integrity.py::test_soil_moisture_range PASSED
tests/fog/test_fog_node.py::test_fog_initialization PASSED
tests/fog/test_fog_node.py::test_local_ml_inference PASSED
tests/fog/test_fog_node.py::test_offline_buffering PASSED
tests/fog/test_fog_node.py::test_cloud_sync PASSED
tests/fog/test_fog_node.py::test_deduplication PASSED
tests/integration/test_end_to_end.py::test_full_pipeline_flow PASSED
tests/integration/test_end_to_end.py::test_outage_resilience PASSED
tests/integration/test_end_to_end.py::test_audit_trail_logging PASSED
tests/ml/test_model.py::test_model_artifacts_exist PASSED
tests/ml/test_model.py::test_model_prediction_accuracy PASSED

============================= 20 passed in 16.87s =============================
```

---

## 10. Building for Production

To build the optimized frontend client bundle:

```powershell
cd c:\Users\achin\Desktop\Pitaji\SmartKhet2.O\frontend
npm run build
```

The compiled static assets will be output to `frontend/dist/`.  
To preview the production bundle locally:
```powershell
npm run preview
```

---

## 11. Troubleshooting Common Windows 11 Issues

1. **Port 8000 or 5173 is already in use:**
   - Find the occupying process: `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess`
   - Or start FastAPI on a different port: `python -m uvicorn app.main:app --port 8001` (update Vite proxy in `frontend/vite.config.ts` accordingly).
2. **Missing Python Modules:**
   - Ensure you are running inside your virtual environment (`.\venv\Scripts\Activate.ps1`).
   - Run `pip install -r backend/requirements.txt`.
3. **Frontend fails to connect to backend:**
   - Confirm backend is running at `http://localhost:8000` by visiting `http://localhost:8000/health`.
   - Ensure the Vite proxy in `frontend/vite.config.ts` points to `http://127.0.0.1:8000` (pre-configured).

