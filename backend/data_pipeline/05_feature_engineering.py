"""
SmartKhet 2.0 — Phase 1: Feature Engineering
==============================================
Script 05 — Feature Engineering

Run from backend/ directory:
    python data_pipeline/05_feature_engineering.py

This script:
  1. Loads data/interim/preprocessed_all_farms.csv
  2. Per farm (sorted by date), engineers the following features:
       Lag features   : soil_moisture_lag1, soil_moisture_lag2
       Moving averages: soil_moisture_ma3, soil_moisture_ma7
       Lag rainfall   : rainfall_lag1
       Cumulative rain: rainfall_cum3, rainfall_cum7
       Temporal       : month, day_of_year, season
       Target         : soil_moisture_next_day (1-day ahead, shifted by -1)
  3. Drops rows where target is NaN (last row per farm)
  4. Saves ML-ready dataset to data/processed/ml_ready_dataset.csv
  5. Saves feature list to data/metadata/feature_list.json
"""

import os
import sys
import json
import datetime
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).resolve().parent
BACKEND_DIR  = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_INTERIM    = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED  = PROJECT_ROOT / "data" / "processed"
DATA_METADATA   = PROJECT_ROOT / "data" / "metadata"
AUDIT_LOG       = PROJECT_ROOT / "docs" / "SMARTKHET_PROJECT_AUDIT_LOG.csv"

for d in [DATA_PROCESSED, DATA_METADATA]:
    d.mkdir(parents=True, exist_ok=True)

try:
    import numpy as np
    import pandas as pd
except ImportError:
    print("[ERROR] numpy and pandas required. Run: pip install numpy pandas")
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
            f.write(f'{_ts()},05_feature_engineering,"{action}","{detail}",{status}\n')
    except Exception:
        pass


SEASON_MAP = {1: "Winter", 2: "Summer", 3: "SW_Monsoon", 4: "NE_Monsoon"}


def load_interim_data() -> pd.DataFrame:
    """Load preprocessed combined dataset from interim directory."""
    combined_path = DATA_INTERIM / "preprocessed_all_farms.csv"

    if not combined_path.exists():
        # Try per-farm files
        farm_files = sorted(DATA_INTERIM.glob("preprocessed_TN*.csv"))
        if farm_files:
            print(f"  [INFO] Combined file not found; loading {len(farm_files)} per-farm files.")
            dfs = [pd.read_csv(fp, low_memory=False) for fp in farm_files]
            df = pd.concat(dfs, ignore_index=True)
        else:
            print(f"\n[ERROR] No interim files found in: {DATA_INTERIM.relative_to(PROJECT_ROOT)}")
            print("  Please run 04_preprocess.py first.")
            sys.exit(1)
    else:
        df = pd.read_csv(combined_path, low_memory=False)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values(["farm_id", "date"]).reset_index(drop=True)
    print(f"  Loaded: {len(df):,} rows × {df.shape[1]} columns")
    return df


def get_season_from_doy(doy_series: pd.Series) -> pd.Series:
    """
    Assign season code based on day-of-year (Tamil Nadu seasons).
      1 = Winter       (DOY 1-59, 335-365)
      2 = Summer       (DOY 60-151)
      3 = SW_Monsoon   (DOY 152-273)
      4 = NE_Monsoon   (DOY 274-334)
    """
    season = pd.Series(0, index=doy_series.index, dtype=int)
    season[(doy_series >= 1)   & (doy_series <= 59)]  = 1
    season[(doy_series >= 60)  & (doy_series <= 151)] = 2
    season[(doy_series >= 152) & (doy_series <= 273)] = 3
    season[(doy_series >= 274) & (doy_series <= 334)] = 4
    season[doy_series >= 335]                          = 1
    return season


def engineer_features_per_farm(group: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all feature engineering to a single farm's time-ordered DataFrame.
    """
    g = group.sort_values("date").copy()

    # Temporal features
    g["month"]       = g["date"].dt.month.astype(int)
    g["day_of_year"] = g["date"].dt.dayofyear.astype(int)

    # Season: use pre-existing column if valid, else recompute
    if "season" not in g.columns or g["season"].isna().any():
        g["season"] = get_season_from_doy(g["day_of_year"])
    else:
        g["season"] = pd.to_numeric(g["season"], errors="coerce").fillna(0).astype(int)
        # Fix any zeros
        mask = g["season"] == 0
        if mask.any():
            g.loc[mask, "season"] = get_season_from_doy(g.loc[mask, "day_of_year"])

    # --- Soil moisture lag and rolling features ---
    sm = g["soil_moisture"]
    g["soil_moisture_lag1"] = sm.shift(1)
    g["soil_moisture_lag2"] = sm.shift(2)
    g["soil_moisture_ma3"]  = sm.shift(1).rolling(window=3, min_periods=1).mean().round(5)
    g["soil_moisture_ma7"]  = sm.shift(1).rolling(window=7, min_periods=1).mean().round(5)

    # --- Rainfall lag and cumulative features ---
    rain = g["rainfall_mm"]
    g["rainfall_lag1"] = rain.shift(1)
    g["rainfall_cum3"] = rain.shift(1).rolling(window=3, min_periods=1).sum().round(3)
    g["rainfall_cum7"] = rain.shift(1).rolling(window=7, min_periods=1).sum().round(3)

    # --- Target: next-day soil moisture ---
    g["soil_moisture_next_day"] = sm.shift(-1)

    return g


def engineer_all_farms(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering to all farms."""
    print("  Engineering features per farm…")
    frames = []
    for farm_id, group in df.groupby("farm_id"):
        engineered = engineer_features_per_farm(group)
        frames.append(engineered)
        print(f"    {farm_id}: {len(engineered):,} rows engineered")

    df_all = pd.concat(frames, ignore_index=True)
    df_all.sort_values(["farm_id", "date"], inplace=True)
    df_all.reset_index(drop=True, inplace=True)
    return df_all


def drop_target_nans(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where target (soil_moisture_next_day) is NaN (last row per farm)."""
    before = len(df)
    df = df.dropna(subset=["soil_moisture_next_day"])
    dropped = before - len(df)
    print(f"  Dropped {dropped} rows with NaN target (last row per farm)")
    return df.reset_index(drop=True)


def fill_feature_nans(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """
    Fill NaN in engineered features (first rows lack lag history).
    Strategy: fill with median per farm for lag columns.
    """
    lag_cols = [c for c in feature_cols if "lag" in c or "ma" in c or "cum" in c]
    for col in lag_cols:
        # Fill with farm-level median
        df[col] = df.groupby("farm_id")[col].transform(lambda x: x.fillna(x.median()))
    return df


def define_feature_set(df: pd.DataFrame) -> tuple:
    """
    Define the feature list for ML training.
    Returns (feature_cols, target_col, metadata_cols).
    """
    # Columns NOT to include as features
    exclude = {
        "date", "farm_id", "farm_name", "crop",
        "data_source", "data_note",
        "soil_moisture_next_day",   # target
        "soil_moisture",            # don't leak current-day SM (use lags instead)
        "latitude", "longitude",    # constant per farm
    }

    # Desired feature columns in order
    desired_features = [
        "rainfall_mm",
        "temperature_c",
        "humidity_pct",
        "relative_humidity_pct",
        "rh_computed",
        "daily_et_estimate_mm",
        "soil_moisture_lag1",
        "soil_moisture_lag2",
        "soil_moisture_ma3",
        "soil_moisture_ma7",
        "rainfall_lag1",
        "rainfall_cum3",
        "rainfall_cum7",
        "month",
        "day_of_year",
        "season",
    ]

    feature_cols = [c for c in desired_features if c in df.columns and c not in exclude]
    target_col = "soil_moisture_next_day"

    metadata_cols = ["date", "farm_id", "crop"]

    return feature_cols, target_col, metadata_cols


def save_feature_list(feature_cols: list, target_col: str, metadata: dict):
    """Save feature list JSON."""
    fl_path = DATA_METADATA / "feature_list.json"
    payload = {
        "generated_at": _ts(),
        "script": "05_feature_engineering.py",
        "target": target_col,
        "features": feature_cols,
        "n_features": len(feature_cols),
        "feature_descriptions": {
            "rainfall_mm":              "Daily rainfall in mm (current day)",
            "temperature_c":            "Daily mean temperature °C",
            "humidity_pct":             "Relative humidity % (original)",
            "relative_humidity_pct":    "Relative humidity % (may equal humidity_pct)",
            "rh_computed":              "RH recomputed from dewpoint via Magnus formula",
            "daily_et_estimate_mm":     "Hargreaves-Samani simplified ETo (mm/day)",
            "soil_moisture_lag1":       "Soil moisture at t-1 (previous day)",
            "soil_moisture_lag2":       "Soil moisture at t-2 (two days ago)",
            "soil_moisture_ma3":        "3-day moving average of soil moisture (ending t-1)",
            "soil_moisture_ma7":        "7-day moving average of soil moisture (ending t-1)",
            "rainfall_lag1":            "Rainfall at t-1 (previous day) mm",
            "rainfall_cum3":            "3-day cumulative rainfall (ending t-1) mm",
            "rainfall_cum7":            "7-day cumulative rainfall (ending t-1) mm",
            "month":                    "Calendar month (1-12)",
            "day_of_year":              "Day of year (1-365)",
            "season":                   "Season code (1=Winter, 2=Summer, 3=SW_Monsoon, 4=NE_Monsoon)",
        },
        "target_description": "soil_moisture (0-1 fraction) at t+1 (next day)",
        "data_note": (
            "All features are computed from demonstration data only. "
            "Lag features use t-1 or earlier values only — no data leakage from t+1."
        ),
        "metadata": metadata,
    }
    with open(fl_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"  [OK] Feature list saved → {fl_path.relative_to(PROJECT_ROOT)}")
    return fl_path


def save_ml_ready_dataset(df: pd.DataFrame, feature_cols: list, target_col: str, metadata_cols: list):
    """Save ML-ready CSV."""
    keep_cols = metadata_cols + feature_cols + [target_col]
    keep_cols = [c for c in keep_cols if c in df.columns]
    ml_df = df[keep_cols].copy()

    out_path = DATA_PROCESSED / "ml_ready_dataset.csv"
    ml_df.to_csv(out_path, index=False)
    print(f"  [OK] ML-ready dataset → {out_path.relative_to(PROJECT_ROOT)}")
    print(f"       Shape: {ml_df.shape[0]:,} rows × {ml_df.shape[1]} columns")
    return out_path


def print_feature_stats(df: pd.DataFrame, feature_cols: list):
    """Print quick stats for all engineered features."""
    print(f"\n  {'─'*62}")
    print(f"  {'Feature':<30} {'Mean':>8} {'Std':>8} {'NaN%':>6}")
    print(f"  {'─'*62}")
    for col in feature_cols:
        if col in df.columns:
            mean_v = df[col].mean()
            std_v  = df[col].std()
            nan_p  = df[col].isna().mean() * 100
            print(f"  {col:<30} {mean_v:>8.4f} {std_v:>8.4f} {nan_p:>5.1f}%")
    print(f"  {'─'*62}")


def main():
    print("\n" + "█" * 70)
    print("  SmartKhet 2.0 — 05_feature_engineering.py")
    print("  Phase 1: Feature Engineering")
    print("█" * 70)
    print(f"  Timestamp : {_ts()}")

    _append_audit("script_started", "05_feature_engineering.py started")

    try:
        # 1. Load preprocessed data
        df = load_interim_data()

        # 2. Engineer features per farm
        df = engineer_all_farms(df)

        # 3. Drop rows with NaN target
        df = drop_target_nans(df)

        # 4. Define feature set
        feature_cols, target_col, metadata_cols = define_feature_set(df)
        print(f"\n  Feature columns ({len(feature_cols)}): {feature_cols}")
        print(f"  Target: {target_col}")

        # 5. Fill feature NaNs (first rows lacking lag history)
        df = fill_feature_nans(df, feature_cols)

        # 6. Print stats
        print_feature_stats(df, feature_cols)

        # 7. Save feature list
        meta = {
            "total_rows": int(len(df)),
            "farms": df["farm_id"].unique().tolist(),
            "date_range": {
                "start": str(df["date"].min().date()),
                "end":   str(df["date"].max().date()),
            }
        }
        save_feature_list(feature_cols, target_col, meta)

        # 8. Save ML-ready dataset
        save_ml_ready_dataset(df, feature_cols, target_col, metadata_cols)

        print(f"\n  ✅ Feature engineering complete: {len(df):,} ML-ready rows")
        print("  Next step: python data_pipeline/06_validate_pipeline.py")

    except SystemExit:
        raise
    except Exception as e:
        print(f"\n[ERROR] Feature engineering failed:\n{traceback.format_exc()}")
        _append_audit("script_error", str(e)[:300], "ERROR")
        sys.exit(1)

    print("=" * 70 + "\n")
    _append_audit("script_completed", f"05_feature_engineering.py finished. {len(df):,} ML-ready rows.", "OK")


if __name__ == "__main__":
    main()
