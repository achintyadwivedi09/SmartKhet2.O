"""
SmartKhet 2.0 — Phase 1: Demo Dataset Generation
=================================================
Script 03 — Generate Demo Agricultural Dataset

Run from backend/ directory:
    python data_pipeline/03_generate_demo_dataset.py

THIS SCRIPT GENERATES DEMONSTRATION DATA — NOT REAL SENSOR DATA.
Every record is explicitly labelled with:
    data_source = "demonstration_climatological_pattern"

The data reflects REALISTIC Tamil Nadu climate patterns:
  - Actual temperature ranges for the region
  - SW Monsoon (Jun–Sep) and NE Monsoon (Oct–Dec) seasonality
  - Physically plausible soil moisture dynamics

Outputs:
  data/processed/demo_agricultural_data.csv
  data/metadata/demo_dataset_info.json
"""

import os
import sys
import json
import datetime
import traceback
import random
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).resolve().parent
BACKEND_DIR  = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_PROCESSED  = PROJECT_ROOT / "data" / "processed"
DATA_METADATA   = PROJECT_ROOT / "data" / "metadata"
AUDIT_LOG       = PROJECT_ROOT / "docs" / "SMARTKHET_PROJECT_AUDIT_LOG.csv"

for d in [DATA_PROCESSED, DATA_METADATA]:
    d.mkdir(parents=True, exist_ok=True)

try:
    import numpy as np
    import pandas as pd
    HAS_NP = True
except ImportError:
    print("[ERROR] numpy and pandas are required. Run: pip install numpy pandas")
    sys.exit(1)


def _ts() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _append_audit(action: str, detail: str, status: str = "INFO"):
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        header_needed = not AUDIT_LOG.exists()
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            if header_needed:
                f.write("timestamp,script,action,detail,status\n")
            f.write(f'{_ts()},03_generate_demo_dataset,"{action}","{detail}",{status}\n')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Farm configurations (Tamil Nadu)
# ---------------------------------------------------------------------------
FARMS = {
    "TN001": {
        "name": "Thanjavur Rice Farm",
        "crop": "Rice",
        "lat": 10.787,
        "lon": 79.139,
        "soil_field_capacity": 0.42,   # FC — soil holds up to this fraction
        "soil_wilting_point":  0.14,   # WP — below this, plant stress
        "init_moisture": 0.38,
    },
    "TN002": {
        "name": "Coimbatore Cotton Farm",
        "crop": "Cotton",
        "lat": 11.0168,
        "lon": 76.9558,
        "soil_field_capacity": 0.35,
        "soil_wilting_point":  0.12,
        "init_moisture": 0.28,
    },
    "TN003": {
        "name": "Madurai Groundnut Farm",
        "crop": "Groundnut",
        "lat": 9.9252,
        "lon": 78.1198,
        "soil_field_capacity": 0.30,
        "soil_wilting_point":  0.10,
        "init_moisture": 0.22,
    },
}

# ---------------------------------------------------------------------------
# Climate model for Tamil Nadu
# ---------------------------------------------------------------------------

def get_season(doy: int) -> int:
    """
    Tamil Nadu seasons by day-of-year:
      1 = Winter/Cool-Dry  (Jan–Feb, Dec):         DOY 1-59, 335-365
      2 = Summer/Pre-Monsoon (Mar–May):             DOY 60-151
      3 = SW Monsoon (Jun–Sep):                     DOY 152-273
      4 = NE Monsoon / Retreating Monsoon (Oct–Nov): DOY 274-334
    """
    if doy <= 59 or doy >= 335:
        return 1
    elif doy <= 151:
        return 2
    elif doy <= 273:
        return 3
    else:
        return 4


def daily_climate(doy: int, year: int, farm_id: str, rng: np.random.Generator) -> dict:
    """
    Generate plausible daily climate variables for Tamil Nadu.

    Temperature model:
      - Annual mean ~27°C, range 20–38°C
      - SW Monsoon: cooler (25–32°C), NE Monsoon: warm-moist (25–34°C)
      - Summer: hottest (30–40°C), Winter: mild (20–28°C)

    Rainfall model (mm/day):
      - Based on seasonal probabilities derived from IMD climatology
      - SW Monsoon: moderate rain, more frequent
      - NE Monsoon: heavy rain events (Tamil Nadu gets most rain Oct-Nov)
      - Summer/Winter: sporadic light rain
    """
    season = get_season(doy)

    # --- Temperature ---
    if season == 1:    # Winter
        t_mean, t_amp = 23.0, 5.0
    elif season == 2:  # Summer
        t_mean, t_amp = 33.5, 5.5
    elif season == 3:  # SW Monsoon
        t_mean, t_amp = 28.0, 3.5
    else:              # NE Monsoon
        t_mean, t_amp = 27.5, 4.0

    # Slight farm-specific offset (latitude effect)
    lat_offset = {"TN001": 0.0, "TN002": 0.5, "TN003": -0.5}.get(farm_id, 0)
    temperature_c = t_mean + lat_offset + rng.normal(0, t_amp * 0.3)

    # Daily cycle noise
    temperature_c += 0.5 * math.sin(2 * math.pi * doy / 365)
    temperature_c = float(np.clip(temperature_c, 18.0, 42.0))

    # --- Humidity ---
    if season == 3:
        hum_mean = 78.0
    elif season == 4:
        hum_mean = 82.0
    elif season == 1:
        hum_mean = 65.0
    else:
        hum_mean = 55.0

    humidity_pct = float(np.clip(rng.normal(hum_mean, 8.0), 30.0, 98.0))

    # --- Rainfall ---
    # Probability of rain per day
    rain_prob = {1: 0.08, 2: 0.12, 3: 0.35, 4: 0.42}.get(season, 0.1)

    if rng.random() < rain_prob:
        # Rainfall amount: Gamma distribution tuned per season
        if season == 4:    # NE Monsoon — heavy events possible
            rain_shape, rain_scale = 1.5, 12.0
        elif season == 3:  # SW Monsoon
            rain_shape, rain_scale = 1.2, 8.0
        else:
            rain_shape, rain_scale = 0.9, 5.0

        rainfall_mm = float(rng.gamma(rain_shape, rain_scale))
        rainfall_mm = min(rainfall_mm, 180.0)  # cap at plausible daily max
    else:
        rainfall_mm = 0.0

    # Relative humidity (approximate formula from temperature and dewpoint)
    # Using Magnus formula: RH = 100 * exp(17.625*Td/(243.04+Td)) / exp(17.625*T/(243.04+T))
    # Back-calculate dewpoint from humidity
    rh_frac = humidity_pct / 100.0
    alpha = (17.625 * temperature_c) / (243.04 + temperature_c)
    dewpoint_c = 243.04 * (math.log(rh_frac) + alpha) / (17.625 - math.log(rh_frac) - alpha)
    relative_humidity_pct = humidity_pct  # same variable, kept for schema clarity

    return {
        "temperature_c": round(temperature_c, 2),
        "humidity_pct":  round(humidity_pct, 2),
        "relative_humidity_pct": round(relative_humidity_pct, 2),
        "rainfall_mm":   round(rainfall_mm, 2),
        "dewpoint_c":    round(dewpoint_c, 2),
        "season":        season,
    }


# ---------------------------------------------------------------------------
# Soil moisture model
# ---------------------------------------------------------------------------

def compute_soil_moisture(
    prev_sm: float,
    rainfall_mm: float,
    temperature_c: float,
    humidity_pct: float,
    fc: float,
    wp: float,
    rng: np.random.Generator,
) -> float:
    """
    Simplified soil moisture model (NOT a real physics model — demonstration only).

    SM[t] = SM[t-1] * evaporation_factor + rainfall_effect - et_demand

    Parameters derived from Hargreaves-Samani ETo concept (simplified):
      - evaporation_factor: fraction of moisture retained (depends on T & humidity)
      - rainfall_effect: fraction of rainfall that enters soil (after runoff)
      - et_demand: evapotranspiration loss (temperature-driven)

    All values are clipped to [wp, fc] physical limits.
    """
    # Evaporation factor: higher temp + lower humidity → more evaporation
    temp_factor = (temperature_c - 18.0) / 25.0  # 0 at 18°C, 1 at 43°C
    hum_factor  = (100.0 - humidity_pct) / 100.0  # 0 at 100% RH, 1 at 0% RH
    evaporation_rate = 0.012 + 0.018 * temp_factor + 0.008 * hum_factor
    evaporation_factor = max(0.85, 1.0 - evaporation_rate)

    # ET demand (mm equivalent as fraction of SM capacity)
    sm_range = fc - wp
    # Hargreaves approximation: ETo ≈ 0.0023 * Ra * sqrt(T_range) * (Tmean + 17.8)
    # Simplified to daily ETo in mm/day based on temperature
    eto_mm = 0.0023 * (temperature_c + 17.8) * math.sqrt(max(1, temperature_c * 0.4))
    eto_mm = min(eto_mm, 8.0)  # cap at 8 mm/day
    et_demand = (eto_mm / 100.0) * (1.0 / sm_range)

    # Rainfall effect: infiltration fraction (sandy/loamy Tamil Nadu soils)
    # Assumes 30-50% runoff on days with heavy rain
    if rainfall_mm > 50:
        infiltration_frac = 0.50
    elif rainfall_mm > 20:
        infiltration_frac = 0.65
    elif rainfall_mm > 5:
        infiltration_frac = 0.80
    else:
        infiltration_frac = 0.95

    # Rain contribution to soil moisture
    rainfall_effect = (rainfall_mm * infiltration_frac) / 500.0  # normalise

    # Update moisture
    new_sm = prev_sm * evaporation_factor + rainfall_effect - et_demand

    # Physical constraints + small noise for realism
    new_sm += rng.normal(0, 0.003)
    new_sm = float(np.clip(new_sm, wp, fc))

    return round(new_sm, 4)


# ---------------------------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------------------------

def generate_dataset() -> pd.DataFrame:
    """Generate 5 years of daily records for 3 Tamil Nadu farms."""
    print("\n  Generating demonstration dataset…")
    print("  ⚠️  DATA DISCLAIMER: All records use data_source='demonstration_climatological_pattern'")
    print("      This is NOT real sensor data. Patterns reflect regional climatology.\n")

    rng = np.random.default_rng(seed=42)  # Reproducible seed

    all_records = []
    start_date = datetime.date(2019, 1, 1)
    end_date   = datetime.date(2023, 12, 31)

    total_days = (end_date - start_date).days + 1

    for farm_id, farm_cfg in FARMS.items():
        print(f"  Generating {farm_id} ({farm_cfg['name']})…", end="", flush=True)

        fc  = farm_cfg["soil_field_capacity"]
        wp  = farm_cfg["soil_wilting_point"]
        sm  = farm_cfg["init_moisture"]  # Starting soil moisture

        current_date = start_date
        day_count = 0

        while current_date <= end_date:
            doy  = current_date.timetuple().tm_yday
            year = current_date.year

            climate = daily_climate(doy, year, farm_id, rng)

            sm = compute_soil_moisture(
                prev_sm=sm,
                rainfall_mm=climate["rainfall_mm"],
                temperature_c=climate["temperature_c"],
                humidity_pct=climate["humidity_pct"],
                fc=fc, wp=wp, rng=rng
            )

            record = {
                "date":                      str(current_date),
                "farm_id":                   farm_id,
                "farm_name":                 farm_cfg["name"],
                "crop":                      farm_cfg["crop"],
                "latitude":                  farm_cfg["lat"],
                "longitude":                 farm_cfg["lon"],
                "rainfall_mm":               climate["rainfall_mm"],
                "temperature_c":             climate["temperature_c"],
                "humidity_pct":              climate["humidity_pct"],
                "relative_humidity_pct":     climate["relative_humidity_pct"],
                "dewpoint_c":                climate["dewpoint_c"],
                "soil_moisture":             sm,
                "season":                    climate["season"],
                "data_source":               "demonstration_climatological_pattern",
                "data_note":                 "DEMO DATA — not real sensor measurements",
            }
            all_records.append(record)
            current_date += datetime.timedelta(days=1)
            day_count += 1

        print(f" {day_count:,} records ✓")

    df = pd.DataFrame(all_records)
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(["farm_id", "date"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(f"\n  Total records generated: {len(df):,}")
    return df


def save_dataset(df: pd.DataFrame):
    """Save to CSV and generate metadata JSON."""
    out_path = DATA_PROCESSED / "demo_agricultural_data.csv"
    df.to_csv(out_path, index=False)
    print(f"  [OK] Dataset saved → {out_path.relative_to(PROJECT_ROOT)}")
    _append_audit("demo_dataset_saved", f"{len(df)} records → {out_path.name}", "OK")

    # Metadata
    meta = {
        "generated_at": _ts(),
        "script": "03_generate_demo_dataset.py",
        "data_type": "DEMONSTRATION",
        "disclaimer": (
            "This dataset is generated using climatological patterns for Tamil Nadu. "
            "It is NOT real sensor data and must NOT be presented as such. "
            "Every record carries data_source='demonstration_climatological_pattern'."
        ),
        "geographic_coverage": "Tamil Nadu, India (3 farms)",
        "temporal_coverage": {
            "start": str(df["date"].min().date()),
            "end":   str(df["date"].max().date()),
            "years": 5
        },
        "farms": list(FARMS.keys()),
        "farm_details": FARMS,
        "total_records": int(len(df)),
        "records_per_farm": {
            fid: int((df["farm_id"] == fid).sum())
            for fid in FARMS
        },
        "columns": list(df.columns),
        "soil_moisture_range": {
            "min": round(float(df["soil_moisture"].min()), 4),
            "max": round(float(df["soil_moisture"].max()), 4),
            "mean": round(float(df["soil_moisture"].mean()), 4),
        },
        "rainfall_stats": {
            "mean_mm_day": round(float(df["rainfall_mm"].mean()), 2),
            "max_mm_day":  round(float(df["rainfall_mm"].max()), 2),
            "rain_days_pct": round(float((df["rainfall_mm"] > 0).mean() * 100), 1),
        },
        "output_file": "data/processed/demo_agricultural_data.csv",
        "next_step": "Run 04_preprocess.py to validate and preprocess this dataset.",
        "soil_moisture_model": (
            "SM[t] = SM[t-1] * evaporation_factor + rainfall_effect - et_demand. "
            "evaporation_factor depends on temperature and humidity. "
            "This is a simplified demonstration model, not a validated physics model."
        ),
        "monsoon_pattern": {
            "SW_Monsoon": "June–September (DOY 152-273), moderate rainfall",
            "NE_Monsoon": "October–November (DOY 274-334), heaviest rainfall for Tamil Nadu",
            "Winter": "December–February (DOY 1-59, 335-365), low rainfall",
            "Summer": "March–May (DOY 60-151), sparse rainfall, high evapotranspiration"
        }
    }

    meta_path = DATA_METADATA / "demo_dataset_info.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"  [OK] Metadata saved → {meta_path.relative_to(PROJECT_ROOT)}")
    _append_audit("demo_dataset_metadata_saved", str(meta_path.name), "OK")

    return out_path


def print_summary(df: pd.DataFrame):
    """Print a summary of the generated dataset."""
    print("\n  " + "─" * 60)
    print("  DATASET SUMMARY")
    print("  " + "─" * 60)
    print(f"  Total records  : {len(df):,}")
    print(f"  Farms          : {df['farm_id'].nunique()}")
    print(f"  Date range     : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"  Columns        : {list(df.columns)}")
    print(f"\n  Soil Moisture Stats:")
    for fid in FARMS:
        sub = df[df["farm_id"] == fid]["soil_moisture"]
        print(f"    {fid}: min={sub.min():.3f}, max={sub.max():.3f}, mean={sub.mean():.3f}")
    print(f"\n  Rainfall Stats:")
    print(f"    Mean rain days: {(df['rainfall_mm'] > 0).mean() * 100:.1f}%")
    print(f"    Mean rainfall : {df['rainfall_mm'].mean():.2f} mm/day")
    print(f"    Max rainfall  : {df['rainfall_mm'].max():.2f} mm/day")
    print(f"\n  Season Distribution:")
    season_names = {1: "Winter", 2: "Summer", 3: "SW_Monsoon", 4: "NE_Monsoon"}
    for s, name in season_names.items():
        pct = (df["season"] == s).mean() * 100
        print(f"    {name:12s}: {pct:.1f}%")
    print("  " + "─" * 60)


def main():
    print("\n" + "█" * 70)
    print("  SmartKhet 2.0 — 03_generate_demo_dataset.py")
    print("  Phase 1: Demonstration Dataset Generation")
    print("█" * 70)
    print(f"  Timestamp : {_ts()}")
    print(f"  Project   : {PROJECT_ROOT}")

    _append_audit("script_started", "03_generate_demo_dataset.py started")

    try:
        df = generate_dataset()
        print_summary(df)
        out_path = save_dataset(df)
        print(f"\n  ✅ Demo dataset ready: {out_path.relative_to(PROJECT_ROOT)}")
        print("  Next step: python data_pipeline/04_preprocess.py")
    except Exception as e:
        print(f"\n[ERROR] {e}\n{traceback.format_exc()}")
        _append_audit("script_error", str(e)[:300], "ERROR")
        sys.exit(1)

    print("=" * 70 + "\n")
    _append_audit("script_completed", "03_generate_demo_dataset.py finished successfully", "OK")


if __name__ == "__main__":
    main()
