# SmartKhet 2.0: Comprehensive Data Dictionary & Schema Specification

This document details every variable, feature, and database table used across the Big Data pipeline, ML models, and Fog nodes.

---

## 1. Raw & Ingested Variables

| Column Name | Physical Meaning | Source / Instrument | Unit | Valid Range | Missing Treatment |
|---|---|---|---|---|---|
| `date` | Calendar observation timestamp | Timestamp | ISO 8601 YYYY-MM-DD | 2019-01-01 to 2023-12-31 | Drop invalid |
| `farm_id` | Unique farm identifier | Platform Registry | String (TN001-TN003) | TN001, TN002, TN003 | Rejection |
| `rainfall_mm` | Daily accumulated precipitation | IMD 0.25° Gridded NetCDF | mm / day | [0.0, 300.0] | Zero-fill if trace |
| `soil_moisture` | Volumetric water content ($\theta$) | ISRO MOSDAC / ILDAS / In-situ | m³/m³ (dimensionless) | [0.05, 0.55] | Linear interpolation (≤3d) |
| `temperature_c` | 2m surface air temperature | Copernicus ERA5-Land | °C | [10.0, 50.0] | Linear interpolation |
| `dewpoint_c` | 2m surface dewpoint temp | Copernicus ERA5-Land | °C | [5.0, 35.0] | Linear interpolation |
| `humidity_pct` | Relative atmospheric humidity | ERA5-Land / Derived | % | [10.0, 100.0] | Clausius-Clapeyron Magnus |
| `crop` | Dominant crop in field | Agricultural Registry | String | Rice, Cotton, Groundnut | Mandatory |

---

## 2. Engineered ML Feature Matrix (16 Features)

| Feature Name | Category | Mathematical Formulation | Agronomic Purpose |
|---|---|---|---|
| `soil_moisture_lag1` | Inertia | $\text{SM}_{t-1}$ | Captures antecedent ground moisture state |
| `soil_moisture_lag2` | Inertia | $\text{SM}_{t-2}$ | Rate-of-change and memory effect |
| `soil_moisture_ma3` | Rolling Stat | $\frac{1}{3} \sum_{i=1}^3 \text{SM}_{t-i}$ | Short-term moisture smoothing |
| `soil_moisture_ma7` | Rolling Stat | $\frac{1}{7} \sum_{i=1}^7 \text{SM}_{t-i}$ | Weekly root-zone moisture reservoir |
| `rainfall_mm` | Meteorology | $R_t$ | Current daily rainfall contribution |
| `rainfall_lag1` | Lagged Rain | $R_{t-1}$ | Infiltration delay from previous day |
| `rainfall_cum3` | Cumulative | $\sum_{i=1}^3 R_{t-i}$ | 3-day saturated soil moisture buffer |
| `rainfall_cum7` | Cumulative | $\sum_{i=1}^7 R_{t-i}$ | Weekly monsoon recharge |
| `temperature_c` | Meteorology | $T_t$ | Evaporation thermal driver |
| `relative_humidity_pct` | Meteorology | $\text{RH}_t$ | Atmospheric vapor deficit proxy |
| `rh_computed` | Derived | Magnus formula from $T$ and $T_d$ | Rigorous thermodynamic validation |
| `daily_et_estimate_mm` | Agronomic | $0.0023 \cdot (T + 17.8) \cdot \sqrt{R_a}$ | Potential evapotranspiration loss |
| `month` | Temporal | $\text{Month}(t) \in [1, 12]$ | Annual monsoon cycle indicator |
| `day_of_year` | Temporal | $\text{DOY}(t) \in [1, 365]$ | Continuous solar azimuth progression |
| `season` | Seasonal | Winter=1, Summer=2, SW=3, NE=4 | South Indian agricultural seasons |
| **`soil_moisture_next_day`** | **TARGET** | **$\text{SM}_{t+1}$** | **Supervised next-day target (EXCLUDED from X)** |

---

## 3. Database Schema (SQLite ORM Models)

### 3.1 `farms`
- `farm_id` (PK, String): TN001, TN002, TN003.
- `name` (String): e.g. "Cauvery Delta Farm".
- `district` (String): Thanjavur, Coimbatore, Madurai.
- `crop` (String): Rice, Cotton, Groundnut.
- `latitude`, `longitude` (Float): Geographical GPS coordinates.
- `soil_moisture_threshold` (Float): Optimal upper bounds (0.35, 0.25, 0.20).
- `irrigation_trigger_moisture` (Float): Critical minimum threshold (0.28, 0.18, 0.14).

### 3.2 `data_records`
- `id` (PK, Integer).
- `farm_id` (FK to farms).
- `recorded_at` (DateTime): Timestamp of observation.
- `rainfall_mm`, `soil_moisture`, `temperature_c`, `humidity_pct` (Float).
- `is_demo` (Boolean): Explicit flag ensuring academic non-fabrication compliance.

### 3.3 `ml_models`
- `id` (PK, Integer).
- `model_name` (String): "Random Forest Regressor (Soil Moisture)".
- `version` (String): "2.0.0".
- `target_variable` (String): "soil_moisture_next_day".
- `mae`, `rmse`, `r2_score` (Float): Test metrics (0.0040, 0.0082, 0.8722).
- `file_path` (String): Relative path to `.joblib` artifact.

### 3.4 `fog_nodes`
- `node_id` (PK, String): FOG-TN001, FOG-TN002, FOG-TN003.
- `farm_id` (FK to farms).
- `is_online` (Boolean): Operational state.
- `model_loaded` (Boolean): Local artifact status.
- `buffered_event_count` (Integer): Pending offline events.

### 3.5 `audit_logs`
- `id` (PK, Integer).
- `timestamp` (DateTime UTC).
- `actor` (String): Calling agent/service.
- `action` (String): Operation name.
- `resource_type`, `resource_id` (String).
- `details` (JSON): Machine-readable payload.
- `status` (String): 'success' | 'warning' | 'failure'.

