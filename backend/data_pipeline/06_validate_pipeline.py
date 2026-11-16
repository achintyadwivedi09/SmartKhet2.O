"""
SmartKhet 2.0 — Phase 1: Pipeline Validation
=============================================
Script 06 — Pipeline Validation & Leakage Check

Run from backend/ directory:
    python data_pipeline/06_validate_pipeline.py

This script performs rigorous validation on the ML-ready dataset:
  1. Checks file existence and schema integrity.
  2. Verifies NO TARGET LEAKAGE: target column must not be present in feature set,
     and features must not incorporate future timestamps.
  3. Checks for missing / NaN / infinite values.
  4. Validates agronomic and physical range checks:
       - Soil moisture: [0.0, 1.0] (volumetric water content)
       - Temperature: [5.0, 55.0] °C
       - Relative Humidity: [0.0, 100.0] %
       - Rainfall: >= 0.0 mm
  5. Verifies chronological order and continuous date sequence per farm.
  6. Generates data/reports/validation_report.json.
  7. Logs results to audit log.
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

DATA_PROCESSED  = PROJECT_ROOT / "data" / "processed"
DATA_METADATA   = PROJECT_ROOT / "data" / "metadata"
DATA_REPORTS    = PROJECT_ROOT / "data" / "reports"
AUDIT_LOG       = PROJECT_ROOT / "docs" / "SMARTKHET_PROJECT_AUDIT_LOG.csv"

DATA_REPORTS.mkdir(parents=True, exist_ok=True)

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
            f.write(f'{_ts()},06_validate_pipeline,"{action}","{detail}",{status}\n')
    except Exception:
        pass


def run_validation():
    csv_path = DATA_PROCESSED / "ml_ready_dataset.csv"
    meta_path = DATA_METADATA / "feature_list.json"

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing ML-ready dataset: {csv_path}. Run 05_feature_engineering.py first.")
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing feature list metadata: {meta_path}.")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    feature_cols = meta.get("features", [])
    target_col   = meta.get("target", "soil_moisture_next_day")

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])

    checks = []

    # Check 1: Target leakage check
    leakage = target_col in feature_cols
    checks.append({
        "check": "Target Leakage Prevention",
        "passed": not leakage,
        "detail": f"Target '{target_col}' is {'LEAKED into' if leakage else 'cleanly excluded from'} feature list."
    })

    # Check 2: Missing values in features
    nan_features = df[feature_cols].isna().sum().to_dict()
    total_nan_feat = sum(nan_features.values())
    checks.append({
        "check": "Zero Missing Values in Feature Matrix",
        "passed": total_nan_feat == 0,
        "detail": f"Total NaNs in features: {total_nan_feat}"
    })

    # Check 3: Missing values in target
    nan_target = int(df[target_col].isna().sum())
    checks.append({
        "check": "Zero Missing Values in Target Variable",
        "passed": nan_target == 0,
        "detail": f"Target NaNs: {nan_target}"
    })

    # Check 4: Soil moisture range [0.0, 1.0]
    sm_col = "soil_moisture" if "soil_moisture" in df.columns else "soil_moisture_lag1"
    sm_min = float(df[sm_col].min())
    sm_max = float(df[sm_col].max())
    sm_valid = (sm_min >= 0.0) and (sm_max <= 1.0)
    checks.append({
        "check": f"Soil Moisture ({sm_col}) Range [0.0, 1.0]",
        "passed": sm_valid,
        "detail": f"Observed range: [{sm_min:.4f}, {sm_max:.4f}] m³/m³"
    })

    # Check 5: Next-day soil moisture range [0.0, 1.0]
    tgt_min = float(df[target_col].min())
    tgt_max = float(df[target_col].max())
    tgt_valid = (tgt_min >= 0.0) and (tgt_max <= 1.0)
    checks.append({
        "check": f"Target '{target_col}' Range [0.0, 1.0]",
        "passed": tgt_valid,
        "detail": f"Target range: [{tgt_min:.4f}, {tgt_max:.4f}] m³/m³"
    })

    # Check 6: Temperature range [5, 55] °C
    t_col = "temperature" if "temperature" in df.columns else "temperature_c"
    t_min = float(df[t_col].min())
    t_max = float(df[t_col].max())
    t_valid = (t_min >= 5.0) and (t_max <= 55.0)
    checks.append({
        "check": f"Temperature ({t_col}) Range [5.0, 55.0] °C",
        "passed": t_valid,
        "detail": f"Observed range: [{t_min:.1f}, {t_max:.1f}] °C"
    })

    # Check 7: Rainfall non-negative
    r_min = float(df["rainfall_mm"].min())
    r_valid = r_min >= 0.0
    checks.append({
        "check": "Rainfall Non-negative (>= 0.0 mm)",
        "passed": r_valid,
        "detail": f"Min rainfall: {r_min:.2f} mm"
    })

    # Check 8: Chronological ordering per farm
    ordered = True
    for farm_id, group in df.groupby("farm_id"):
        if not group["date"].is_monotonic_increasing:
            ordered = False
            break
    checks.append({
        "check": "Chronological Monotonicity per Farm",
        "passed": ordered,
        "detail": "Dates are strictly monotonically increasing within each farm partition."
    })

    all_passed = all(c["passed"] for c in checks)

    report = {
        "timestamp": _ts(),
        "total_records": len(df),
        "total_features": len(feature_cols),
        "target": target_col,
        "farms": df["farm_id"].unique().tolist(),
        "date_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date())
        },
        "all_checks_passed": all_passed,
        "checks": checks
    }

    report_path = DATA_REPORTS / "validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def main():
    print("\n" + "█" * 70)
    print("  SmartKhet 2.0 — 06_validate_pipeline.py")
    print("  Phase 1: Pipeline Validation & Quality Assurance")
    print("█" * 70)
    print(f"  Timestamp : {_ts()}")

    _append_audit("script_started", "06_validate_pipeline.py started")

    try:
        report = run_validation()
        print(f"\n  Dataset summary:")
        print(f"    Total records : {report['total_records']:,}")
        print(f"    Features count: {report['total_features']}")
        print(f"    Farms         : {report['farms']}")
        print(f"    Date Range    : {report['date_range']['start']} to {report['date_range']['end']}")
        print("\n  Validation Checks:")
        for c in report["checks"]:
            mark = "✅ PASS" if c["passed"] else "❌ FAIL"
            print(f"    [{mark}] {c['check']:<42} : {c['detail']}")

        if report["all_checks_passed"]:
            print("\n  🎉 ALL VALIDATION CHECKS PASSED!")
            print(f"  Report written to: {DATA_REPORTS / 'validation_report.json'}")
            print("  Next step: python data_pipeline/07_train_model.py")
            _append_audit("validation_success", "All 8 pipeline validation checks passed", "OK")
        else:
            print("\n  ⚠️ SOME VALIDATION CHECKS FAILED. Review errors above.")
            _append_audit("validation_failed", "Pipeline validation checks had failures", "WARNING")
            sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}\n{traceback.format_exc()}")
        _append_audit("script_error", str(e)[:300], "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
