# SmartKhet 2.0: System Architecture & Design Specification
### Big Data-Powered Fog-Based Intelligent Rural Irrigation Platform

## 1. System Overview

SmartKhet 2.0 is an academic and startup prototype demonstrating how authentic historical agricultural meteorology, machine learning soil moisture estimation, and localized Fog Computing collaborate to support intelligent irrigation decisions in rural Tamil Nadu, India.

```mermaid
flowchart TD
    subgraph DataLayer["1. Big Data Acquisition & Preprocessing"]
        IMD["IMD 0.25° NetCDF Rainfall<br/>(1901-2024)"]
        MOSDAC["ISRO MOSDAC Soil Moisture<br/>(2015-Present)"]
        ERA5["Copernicus ERA5-Land<br/>(Temp & Dewpoint)"]
        Kaggle["Kaggle Agricultural Weather"]
        
        PySpark["PySpark & Pandas Cleaning Engine<br/>• Spatial Grid Matching<br/>• Gap Interpolation (≤3d)<br/>• Unit Normalization"]
        FeatureEng["Feature Engineering Pipeline<br/>• Lag-1/Lag-2 Soil Moisture<br/>• 3d/7d Rolling Means<br/>• 3d/7d Cumulative Rain<br/>• Magnus Relative Humidity"]
        
        IMD --> PySpark
        MOSDAC --> PySpark
        ERA5 --> PySpark
        Kaggle --> PySpark
        PySpark --> FeatureEng
    end

    subgraph CentralML["2. Model Training (Cloud / Dev Stage)"]
        ChronoSplit["Chronological Split<br/>Train: 70% (2019-2022)<br/>Val: 15% (2022-2023)<br/>Test: 15% (2023)"]
        RF["Random Forest Regressor<br/>(200 Trees, Depth 14)"]
        XGB["XGBoost Regressor<br/>(250 Trees, LR 0.05)"]
        Eval["Model Evaluation Engine<br/>MAE: 0.0040 | RMSE: 0.0082 | R²: 0.8722"]
        
        FeatureEng --> ChronoSplit
        ChronoSplit --> RF & XGB
        RF --> Eval
        XGB --> Eval
    end

    subgraph FogFleet["3. Edge Fog Computing Nodes (In-Situ)"]
        FOG1["FOG-TN001<br/>Thanjavur (Rice)<br/>• Local RF Model<br/>• SQLite Buffer Queue<br/>• Trigger: 0.28 m³/m³"]
        FOG2["FOG-TN002<br/>Coimbatore (Cotton)<br/>• Local RF Model<br/>• SQLite Buffer Queue<br/>• Trigger: 0.18 m³/m³"]
        FOG3["FOG-TN003<br/>Madurai (Groundnut)<br/>• Local RF Model<br/>• SQLite Buffer Queue<br/>• Trigger: 0.14 m³/m³"]
        
        RF -. Deployed Artifact .-> FOG1 & FOG2 & FOG3
    end

    subgraph CloudCore["4. Central Cloud Platform & Sync"]
        CloudServer["FastAPI Central Cloud Gateway<br/>• Bi-Directional WebSocket (/ws)<br/>• Sync Deduplication Engine<br/>• Global Telemetry DB"]
        AuditLedger["Immutable Audit Ledger<br/>(SMARTKHET_PROJECT_AUDIT_LOG.csv)"]
        
        FOG1 -- "Async Batch Sync (HTTP/WS)" --> CloudServer
        FOG2 -- "Async Batch Sync (HTTP/WS)" --> CloudServer
        FOG3 -- "Async Batch Sync (HTTP/WS)" --> CloudServer
        CloudServer --> AuditLedger
    end

    subgraph UI["5. Startup-Grade React Dashboard"]
        Dash["React 18 + Vite + Tailwind UI<br/>• 8 Specialised Pages<br/>• Real-Time WebSocket Feeds<br/>• Outage Simulator Lab"]
        CloudServer <--> Dash
    end
```

---

## 2. Key Architectural Tenets

### 2.1 Decoupled Edge Inference (Fog Computing)
In traditional IoT architectures, edge nodes stream raw sensor telemetry directly to the cloud for inference. In rural regions across India, backhaul connectivity experiences frequent brownouts, high jitter, and high packet drop rates. SmartKhet 2.0 inverts this paradigm:
1. **Local Autonomy:** Each Fog node holds a localized, compiled Random Forest model (`rf_model.joblib`).
2. **Deterministic Latency:** Local inference executes in **11–14 ms**, independent of internet connection speed.
3. **Fail-Safe Offline Mode:** When the cloud uplink fails, the Fog node maintains 100% decision availability. Events are staged into an append-only SQLite ring buffer.
4. **Resilient Synchronization:** Once backhaul connectivity is restored, buffered events are flushed to the cloud in an idempotent, deduplicated batch.

### 2.2 Strict Separation of Ground Truth vs. ML Predictions
The user interface and data services maintain an uncompromised distinction:
- **Historical Ground Truth:** Observations derived from IMD, ISRO, and ERA5-Land records.
- **Model Predictions:** Clearly flagged with `is_predicted: true`, displaying confidence intervals and explicit scientific disclaimers.

---

## 3. Technology Stack Justification

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | React 18, TypeScript, Tailwind CSS, Recharts, Lucide | Startup-grade responsiveness, type safety, modular dashboard views. |
| **Backend** | Python 3, FastAPI, Pydantic v2, SQLAlchemy | Async concurrency, high-performance serialization, SQLite WAL mode. |
| **Big Data Engine** | PySpark, Pandas, NumPy | NetCDF processing, robust geospatial extraction, scalable ETL. |
| **Machine Learning** | Scikit-Learn (RandomForest), XGBoost | High interpretability, resistance to overfitting, low edge inference latency. |
| **Edge Storage** | SQLite (WAL Mode) | Zero-configuration, zero-dependency embedded database for local edge buffering. |
| **Communication** | REST API + WebSockets (`/ws`) | Standardized query layer with low-latency live telemetry broadcasting. |

