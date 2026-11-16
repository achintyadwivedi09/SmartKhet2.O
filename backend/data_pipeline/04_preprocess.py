"""
SmartKhet 2.0 — Phase 1: Preprocessing
========================================
Script 04 — Preprocess Agricultural Dataset

Run from backend/ directory:
    python data_pipeline/04_preprocess.py

This script:
  1. Loads data/processed/demo_agricultural_data.csv (or any CSV in processed/)
  2. Validates data types and date parsing
  3. Checks for and reports missing values
  4. Applies linear interpolation for gaps ≤ 3 days (documented)
  5. Removes duplicate dates per farm
  6. Calculates derived features:
       - relative_humidity (from dewpoint/temp via Magnus formula)
       - daily_et_estimate (Hargreaves-Samani simplified ETo)
  7. Saves interim files to data/interim/
  8. Logs all operations

PySpark is used if available; falls back to pandas automatically.
"""

import os
import sys
import json
import datetime
import traceback
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).resolve().parent
BACKEND_DIR  = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_PROCESSED  = PROJECT_ROOT / "data" / "processed"
DATA_INTERIM    = PROJECT_ROOT / "data" / "interim"
DATA_METADATA   = PROJECT_ROOT / "data" / "metadata"
AUDIT_LOG       = PROJECT_ROOT / "docs" / "SMARTKHET_PROJECT_AUDIT_LOG.csv"

for d in [DATA_INTERIM, DATA_METADATA]:
    d.mkdir(parents=True, exist_ok=True)

try:
    import numpy as np
    import pandas as pd
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
            f.write(f'{_ts()},04_preprocess,"{action}","{detail}",{status}\n')
    except Exception:
        pass


ops_log = []  # In-memory operation log


def log_op(operation: str, *args, **kwargs):
    """Record an operation to the ops log."""
    msg_parts = list(args)
    if "detail" in kwargs:
        msg_parts.append(str(kwargs.pop("detail")))
    full_detail = " | ".join(str(m) for m in msg_parts)
    entry = {"timestamp": _ts(), "operation": operation, "detail": full_detail}
    if "before" in kwargs:
        entry["before"] = kwargs.pop("before")
    if "after" in kwargs:
        entry["after"] = kwargs.pop("after")
    entry.update(kwargs)
    ops_log.append(entry)
    print(f"  [{operation}] {full_detail}")


# ---------------------------------------------------------------------------
# PySpark loader (optional)
# ---------------------------------------------------------------------------

def try_load_spark(csv_path: Path):
    """Attempt to load with PySpark; return Spark DataFrame or None."""
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F

        print("  [INFO] PySpark found — using Spark for loading.")
        spark = (
            SparkSession.builder
            .appName("SmartKhet2_Preprocess")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.driver.memory", "2g")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")

        sdf = spark.read.csv(str(csv_path), header=True, inferSchema=True)
        # Convert to pandas for downstream processing (small dataset)
        df = sdf.toPandas()
        spark.stop()
        log_op("SPARK_LOAD", f"Loaded {len(df):,} rows via PySpark")
        return df
    except ImportError:
        return None
    except Exception as e:
        print(f"  [WARN] PySpark failed ({e}); falling back to pandas.")
        return None


# ---------------------------------------------------------------------------
# Core preprocessing steps
# ---------------------------------------------------------------------------

def load_data() -> pd.DataFrame:
    """Load the demo agricultural dataset."""
    input_path = DATA_PROCESSED / "demo_agricultural_data.csv"
    if not input_path.exists():
        print(f"\n[ERROR] Input file not found: {input_path.relative_to(PROJECT_ROOT)}")
        print("  Please run 03_generate_demo_dataset.py first.")
        sys.exit(1)

    print(f"  Loading: {input_path.relative_to(PROJECT_ROOT)}")

    # Try PySpark first
    df = try_load_spark(input_path)

    # Fallback to pandas
    if df is None:
        print("  [INFO] Using pandas for loading.")
        df = pd.read_csv(input_path, low_memory=False)
        log_op("PANDAS_LOAD", f"Loaded {len(df):,} rows via pandas")

    return df


def validate_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and coerce data types."""
    before_rows = len(df)

    # Parse date column
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            log_op("DATE_COERCE", f"Dropped {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=["date"])

    # Numeric columns
    num_cols = [
        "rainfall_mm", "temperature_c", "humidity_pct",
        "relative_humidity_pct", "dewpoint_c", "soil_moisture",
        "latitude", "longitude"
    ]
    for col in num_cols:
        if col in df.columns:
            before = df[col].dtype
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if str(before) != str(df[col].dtype):
                log_op("DTYPE_COERCE", f"{col}: {before} → {df[col].dtype}")

    # String columns
    for col in ["farm_id", "farm_name", "crop", "data_source"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    log_op("VALIDATE_DTYPES", f"Type validation complete. Rows: {before_rows} → {len(df)}")
    return df


def check_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Report and handle missing values."""
    total = len(df)
    missing_report = {}
    for col in df.columns:
        n_miss = int(df[col].isna().sum())
        if n_miss > 0:
            missing_report[col] = {
                "count": n_miss,
                "pct": round(n_miss / total * 100, 2)
            }

    if missing_report:
        log_op("MISSING_VALUES", f"Found NaN in {len(missing_report)} columns: {list(missing_report.keys())}")
        for col, info in missing_report.items():
            print(f"    {col:30s}: {info['count']:5d} NaN  ({info['pct']}%)")
    else:
        log_op("MISSING_VALUES", "No missing values found")

    return df, missing_report


def interpolate_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply linear interpolation for time gaps ≤ 3 consecutive days per farm.

    DOCUMENTED APPROACH:
    - Sort each farm's data by date
    - Identify consecutive NaN runs of length ≤ 3
    - Apply pandas linear interpolation (limit=3)
    - Longer gaps are left as NaN (will be flagged)
    """
    num_cols = ["rainfall_mm", "temperature_c", "humidity_pct",
                "relative_humidity_pct", "soil_moisture", "dewpoint_c"]

    interpolated_total = 0
    frames = []

    for farm_id, group in df.groupby("farm_id"):
        g = group.sort_values("date").copy()
        for col in num_cols:
            if col not in g.columns:
                continue
            n_before = g[col].isna().sum()
            # limit=3: only interpolate runs of ≤3 consecutive NaN
            g[col] = g[col].interpolate(method="linear", limit=3, limit_direction="forward")
            n_after = g[col].isna().sum()
            interpolated_total += (n_before - n_after)
        frames.append(g)

    df_out = pd.concat(frames, ignore_index=True)
    log_op(
        "INTERPOLATE_GAPS",
        f"Linear interpolation applied (limit=3 days). Filled {interpolated_total} values.",
        detail=f"Method: pandas linear, max gap = 3 days. Longer gaps left as NaN."
    )
    return df_out


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate (farm_id, date) rows, keeping first occurrence."""
    before = len(df)
    df = df.drop_duplicates(subset=["farm_id", "date"], keep="first")
    removed = before - len(df)
    log_op("REMOVE_DUPLICATES", f"Removed {removed} duplicate (farm_id, date) rows. Rows: {before} → {len(df)}")
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate derived features.

    1. relative_humidity (re-computed from temperature and dewpoint via Magnus formula)
       RH = 100 * exp(17.625 * Td / (243.04 + Td)) / exp(17.625 * T / (243.04 + T))

    2. daily_et_estimate — Hargreaves-Samani simplified ETo (mm/day)
       ETo ≈ 0.0023 * Ra * sqrt(T_max - T_min) * (Tmean + 17.8)
       We approximate Ra = 15 MJ/m²/day (mean for Tamil Nadu),
       and T_range ≈ 8°C constant (simplified, no diurnal data).
       Result in mm/day using 0.408 conversion factor.
    """

    # 1. Relative humidity from Magnus formula
    if "dewpoint_c" in df.columns and "temperature_c" in df.columns:
        def magnus_rh(row):
            try:
                td = float(row["dewpoint_c"])
                t  = float(row["temperature_c"])
                # exp terms
                e_td = math.exp(17.625 * td / (243.04 + td))
                e_t  = math.exp(17.625 * t  / (243.04 + t ))
                rh   = 100.0 * (e_td / e_t)
                return round(min(100.0, max(0.0, rh)), 2)
            except Exception:
                return float("nan")

        df["rh_computed"] = df.apply(magnus_rh, axis=1)
        log_op("DERIVED_RH", "Computed relative_humidity via Magnus formula from dewpoint and temperature")
    else:
        df["rh_computed"] = df.get("relative_humidity_pct", float("nan"))
        log_op("DERIVED_RH", "dewpoint_c or temperature_c missing; rh_computed set from relative_humidity_pct")

    # 2. Hargreaves-Samani ETo (simplified)
    # ETo = 0.408 * Ra * 0.0023 * (Tmean + 17.8) * sqrt(T_range)
    # Ra (extraterrestrial radiation) for Tamil Nadu centre (~10°N), annual mean ≈ 15 MJ/m²/day
    # T_range approximated as 8°C (simplified; real calculation needs Tmax/Tmin)
    Ra_mean = 15.0  # MJ/m²/day
    T_range_approx = 8.0  # °C (simplified)
    sqrt_tr = math.sqrt(T_range_approx)

    if "temperature_c" in df.columns:
        df["daily_et_estimate_mm"] = (
            0.408 * Ra_mean * 0.0023 * (df["temperature_c"] + 17.8) * sqrt_tr
        ).round(3)
        # Clip to realistic range 2-10 mm/day
        df["daily_et_estimate_mm"] = df["daily_et_estimate_mm"].clip(lower=2.0, upper=10.0)
        log_op("DERIVED_ET", "Computed daily_et_estimate_mm via Hargreaves-Samani simplified ETo")
    else:
        df["daily_et_estimate_mm"] = float("nan")
        log_op("DERIVED_ET", "temperature_c missing; daily_et_estimate_mm set to NaN")

    return df


def save_interim(df: pd.DataFrame):
    """Save interim preprocessed file per farm."""
    for farm_id, group in df.groupby("farm_id"):
        out_path = DATA_INTERIM / f"preprocessed_{farm_id}.csv"
        group.to_csv(out_path, index=False)
        log_op("SAVE_INTERIM", f"Saved {len(group):,} rows → {out_path.relative_to(PROJECT_ROOT)}", status="OK")

    # Also save combined
    combined_path = DATA_INTERIM / "preprocessed_all_farms.csv"
    df.to_csv(combined_path, index=False)
    log_op("SAVE_INTERIM_COMBINED", f"Saved {len(df):,} rows → {combined_path.relative_to(PROJECT_ROOT)}", status="OK")
    return combined_path


def save_ops_log():
    """Save operation log to metadata."""
    log_path = DATA_METADATA / "preprocessing_ops_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": _ts(),
            "script": "04_preprocess.py",
            "total_operations": len(ops_log),
            "operations": ops_log
        }, f, indent=2)
    print(f"  [OK] Operations log → {log_path.relative_to(PROJECT_ROOT)}")


def print_dataframe_summary(df: pd.DataFrame, label: str = ""):
    """Print a quick DataFrame summary."""
    print(f"\n  {'─'*50}")
    print(f"  {label} DataFrame Summary")
    print(f"  {'─'*50}")
    print(f"  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")
    if "farm_id" in df.columns:
        for fid, grp in df.groupby("farm_id"):
            print(f"  {fid}  : {len(grp):,} rows")
    nan_total = int(df.isna().sum().sum())
    print(f"  NaN total : {nan_total}")
    print(f"  {'─'*50}")


def main():
    print("\n" + "█" * 70)
    print("  SmartKhet 2.0 — 04_preprocess.py")
    print("  Phase 1: Data Preprocessing")
    print("█" * 70)
    print(f"  Timestamp : {_ts()}")

    _append_audit("script_started", "04_preprocess.py started")

    try:
        # Step 1: Load
        df = load_data()
        print_dataframe_summary(df, "Raw")

        # Step 2: Validate dtypes
        df = validate_dtypes(df)

        # Step 3: Check missing values
        df, missing_report = check_missing_values(df)

        # Step 4: Interpolate small gaps
        df = interpolate_gaps(df)

        # Step 5: Remove duplicates
        df = remove_duplicates(df)

        # Step 6: Derived features
        df = add_derived_features(df)

        print_dataframe_summary(df, "Preprocessed")

        # Step 7: Save interim files
        combined_path = save_interim(df)

        # Step 8: Save ops log
        save_ops_log()

        print(f"\n  ✅ Preprocessing complete.")
        print(f"  Interim data → {DATA_INTERIM.relative_to(PROJECT_ROOT)}")
        print("  Next step: python data_pipeline/05_feature_engineering.py")

    except SystemExit:
        raise
    except Exception as e:
        print(f"\n[ERROR] Preprocessing failed:\n{traceback.format_exc()}")
        _append_audit("script_error", str(e)[:300], "ERROR")
        sys.exit(1)

    print("=" * 70 + "\n")
    _append_audit("script_completed", f"04_preprocess.py finished. {len(df):,} rows in interim.", "OK")


if __name__ == "__main__":
    main()
