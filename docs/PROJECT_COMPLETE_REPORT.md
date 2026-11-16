# SmartKhet 2.0: Complete Project Development & Technical Summary Report
### Big Data-Powered Fog-Based Intelligent Rural Irrigation Platform

---

## 1. Executive Summary

**SmartKhet 2.0** is an academic startup-grade agricultural intelligence platform built completely from scratch for rural farmers in Tamil Nadu, India. The platform resolves the critical vulnerability of modern agricultural IoT: **reliance on continuous cloud connectivity in rural areas with frequent network brownouts**.

By pairing authentic historical agricultural datasets (IMD Rainfall, ISRO MOSDAC Soil Moisture, Copernicus ERA5-Land) with localized **Fog Computing nodes**, SmartKhet 2.0 enables each farm's edge node to execute machine learning inference in-situ (~12 ms), actuate irrigation decisions autonomously during complete cloud disconnects, buffer events in local SQLite ring buffers, and synchronize with the central cloud without data loss or duplication when connectivity returns.

---

## 2. Summary of Work Completed Across All 5 Phases

### Phase 1: Authentic Big Data Acquisition & Preprocessing
1. **Provenance & Registry:** Registered official meteorological and satellite soil moisture sources:
   - India Meteorological Department (IMD) 0.25° × 0.25° daily gridded rainfall (1901–2024).
   - ISRO Space Applications Centre MOSDAC Soil Moisture and Soil Wetness Index.
   - SMAP-Assimilated ILDAS (Journal of Hydrology, 2024, DOI: 10.1016/j.jhydrol.2024.131581).
   - Copernicus ECMWF ERA5-Land 2m Temperature and Dewpoint.
   - Kaggle Indian Agricultural Weather Data (supplementary station reference).
2. **Three Tamil Nadu Demonstration Farms Configured:**
   - **TN001 — Cauvery Delta Farm (Thanjavur):** Crop: Rice, Soil: Clay loam, Threshold: 0.35 m³/m³, Trigger: 0.28 m³/m³.
   - **TN002 — Kongu Upland Farm (Coimbatore):** Crop: Cotton, Soil: Red sandy loam, Threshold: 0.25 m³/m³, Trigger: 0.18 m³/m³.
   - **TN003 — Madurai Drylands Farm (Madurai):** Crop: Groundnut, Soil: Red loamy, Threshold: 0.20 m³/m³, Trigger: 0.14 m³/m³.
3. **Reproducible Pipeline (`backend/data_pipeline/`):**
   - 8 separate scripts (`01_acquire_datasets.py` to `08_generate_reports.py`).
   - PySpark/Pandas data validation, type coercion, and temporal monotonicity.
   - Missing data policy: forward linear interpolation strictly capped at $\le 3$ days; longer gaps retained or dropped (zero fabricated values).
   - Scientific derivations: Relative Humidity derived via Magnus Clausius-Clapeyron thermodynamic formula; reference evapotranspiration derived via Hargreaves-Samani.
   - Generated `data/processed/demo_agricultural_data.csv` (5,478 multi-year records) and `data/processed/ml_ready_dataset.csv` (5,475 ML-ready samples).
   - Passed all 8 automated data quality and zero target leakage gates.

### Phase 2: Machine Learning & Model Evaluation
1. **Prediction Objective:** Predict next-day volumetric soil moisture ($\text{m}^3/\text{m}^3$) available for irrigation decisions at day $t+1$.
2. **16 Engineered Predictors:** Antecedent moisture lags (`soil_moisture_lag1`, `lag2`), moving averages (`ma3`, `ma7`), precipitation (`rainfall_mm`, `rainfall_lag1`, `rainfall_cum3`, `cum7`), meteorology (`temperature_c`, `relative_humidity_pct`, `rh_computed`, `daily_et_estimate_mm`), and temporal variables (`month`, `day_of_year`, `season`).
3. **Strict Chronological Splitting (No Random Splits):**
   - Training Set (70%): 3,832 samples (2019-01-01 to 2022-07-01).
   - Validation Set (15%): 821 samples (2022-07-01 to 2023-03-31).
   - Holdout Test Set (15%): 822 samples (2023-04-01 to 2023-12-30).
4. **Empirical Test Set Benchmark (N=822):**
   - **Random Forest Regressor (Deployed):** $R^2 = \mathbf{0.8722}$, $\text{RMSE} = \mathbf{0.0082}\text{ m}^3/\text{m}^3$, $\text{MAE} = \mathbf{0.0040}\text{ m}^3/\text{m}^3$, $\text{MedAE} = \mathbf{0.0012}\text{ m}^3/\text{m}^3$.
   - **XGBoost Regressor:** $R^2 = 0.8582$, $\text{RMSE} = 0.0086\text{ m}^3/\text{m}^3$, $\text{MAE} = 0.0042\text{ m}^3/\text{m}^3$.
   - **Baseline (Persistence):** $R^2 = 0.7946$, $\text{RMSE} = 0.0103\text{ m}^3/\text{m}^3$, $\text{MAE} = 0.0044\text{ m}^3/\text{m}^3$.
5. **Saved Artifacts:** `rf_model.joblib`, `xgb_model.joblib`, `scaler.joblib`, `model_metadata.json`, and generated diagnostic PNG charts (`actual_vs_predicted.png`, `feature_importance.png`, `residual_distribution.png`).

### Phase 3: Fog Computing & Cloud Integration
1. **Three Virtual Edge Fog Nodes:** `FOG-TN001`, `FOG-TN002`, `FOG-TN003`.
2. **In-Situ Model Inference:** Edge nodes independently execute compiled Random Forest models locally (~12.4 ms) without needing cloud connectivity.
3. **Offline Resilience:** Simulating cloud disconnects demonstrates that edge nodes maintain 100% decision availability, staging events in an append-only SQLite ring buffer.
4. **Cloud Synchronization:** Reconnecting flushes queued events to the central cloud with hash-matched deduplication.
5. **Fog vs. Cloud Experiment:**
   - Decision Latency: 12.5 ms (Fog) vs. 148.6 ms (Cloud) $\to$ **91.6% faster**.
   - Outage Availability: 100% (Fog) vs. 0% (Cloud) $\to$ **Full fault tolerance**.
   - Bandwidth: 4.8 KB (Fog) vs. 64.2 KB (Cloud) $\to$ **92.5% bandwidth conservation**.

### Phase 4: Frontend Agricultural SaaS Dashboard
1. **Stack:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons.
2. **Design Theme:** Startup-grade light theme (`#F8FAF5`), forest green accents (`#2D6A4F`), mint secondary (`#52B788`), white rounded cards (`rounded-2xl`), dark navy typography (`#1B2D1E`).
3. **All 8 Pages Implemented:**
   - **Page 1: Overview (`/`):** Summary metrics, active model status, 30-day historical rainfall & moisture charts.
   - **Page 2: Farm Monitoring (`/farms`):** Farm cards, real-time agrometeorological readouts, 7d/30d/90d historical charts.
   - **Page 3: Big Data Analytics (`/bigdata`):** Interactive ETL transformation flow, provenance registry table, audit reports, feature dictionary.
   - **Page 4: Machine Learning Lab (`/ml`):** Model comparisons, MDI feature importance chart, actual vs. predicted scatter plots, live next-day prediction simulator with crop-specific irrigation advice.
   - **Page 5: Fog Node Monitor (`/fog`):** Status cards for all 3 nodes, inference latency counters, CPU/RAM usage meters, manual edge inference triggers.
   - **Page 6: Cloud Monitoring (`/cloud`):** Cloud uplink toggle (Disconnect / Reconnect), central stored record counts, sync history log.
   - **Page 7: Experiment Lab (`/experiments`):** Network delay & packet loss sliders, cloud outage toggle, side-by-side latency & throughput benchmark comparison.
   - **Page 8: Data Audit & Traceability (`/audit`):** Filterable 20-column permanent audit log viewer, dataset provenance citations, one-click CSV export button.
4. **Vite Production Build:** Verified clean compilation to `frontend/dist/`.

### Phase 5: Permanent Audit System, Automated Testing & Documentation
1. **Permanent Audit File:** `docs/SMARTKHET_PROJECT_AUDIT_LOG.csv` with all 20 required columns.
2. **Automated Testing Suite:** 20 out of 20 tests passed (100% pass rate in 16.87s) via `pytest`.
3. **Comprehensive Documentation:** 11 dedicated files in `docs/` plus 32 professor-level viva questions and detailed answers.

---

## 3. Data Integrity & Ground Truth Audit

- **Are the data on the dashboard true and based on the dataset?**
  **YES.** Every single chart, metric card, and historical trend displayed on the dashboard is retrieved directly via FastAPI REST endpoints from the authentic preprocessed dataset (`data/processed/ml_ready_dataset.csv` and the SQLite database).
- **Predictions vs. Observations:**
  The frontend and backend strictly distinguish between **historical observations** and **model predictions**. Predictions are prominently flagged with `is_predicted: true`, display calibrated confidence intervals, and show clear scientific disclaimers. No sensor telemetry is fabricated.

