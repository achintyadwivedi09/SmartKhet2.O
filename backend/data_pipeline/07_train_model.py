"""
SmartKhet 2.0 — Phase 2: ML Model Training & Evaluation
=======================================================
Script 07 — Model Training (Random Forest, XGBoost, Baseline)

Run from backend/ directory:
    python data_pipeline/07_train_model.py

Objective:
  Predict next-day soil moisture (soil_moisture_next_day) using:
  - Current & lagged soil moisture (soil_moisture, lag1, lag2, ma3, ma7)
  - Rainfall variables (rainfall_lag1, cum3, cum7)
  - Weather variables (temperature, relative_humidity)
  - Temporal variables (month, day_of_year, season)

Splitting Strategy:
  Strict chronological split (70% train, 15% validation, 15% test)
  Ensures no temporal leakage. Preprocessing fits only on training split.

Deliverables:
  - data/models/rf_model.joblib
  - data/models/xgb_model.joblib (if xgboost installed)
  - data/models/scaler.joblib
  - data/models/model_metadata.json
  - data/models/feature_importance.json
  - Plots in data/reports/plots/
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
DATA_MODELS     = PROJECT_ROOT / "data" / "models"
DATA_REPORTS    = PROJECT_ROOT / "data" / "reports"
PLOTS_DIR       = DATA_REPORTS / "plots"
AUDIT_LOG       = PROJECT_ROOT / "docs" / "SMARTKHET_PROJECT_AUDIT_LOG.csv"

DATA_MODELS.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

try:
    import numpy as np
    import pandas as pd
    import joblib
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, median_absolute_error
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"[ERROR] Required ML packages missing: {e}")
    sys.exit(1)

# Check XGBoost
HAS_XGBOOST = False
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    pass


def _ts() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _append_audit(action: str, detail: str, status: str = "INFO"):
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        header_needed = not AUDIT_LOG.exists()
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            if header_needed:
                f.write("timestamp,script,action,detail,status\n")
            f.write(f'{_ts()},07_train_model,"{action}","{detail}",{status}\n')
    except Exception:
        pass


def compute_metrics(y_true, y_pred):
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    medae = float(median_absolute_error(y_true, y_pred))
    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "median_ae": round(medae, 4),
        "sample_size": int(len(y_true))
    }


def train_and_evaluate():
    csv_path = DATA_PROCESSED / "ml_ready_dataset.csv"
    meta_path = DATA_METADATA / "feature_list.json"

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}. Run pipeline scripts 01 through 05 first.")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    feature_cols = meta["features"]
    target_col   = meta["target"]

    print(f"  Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])

    # Ensure chronological sort
    df = df.sort_values(by=["date", "farm_id"]).reset_index(drop=True)
    n = len(df)
    print(f"  Total records: {n:,}")

    # Chronological Split: 70% Train, 15% Val, 15% Test
    train_idx = int(0.70 * n)
    val_idx   = int(0.85 * n)

    df_train = df.iloc[:train_idx].copy()
    df_val   = df.iloc[train_idx:val_idx].copy()
    df_test  = df.iloc[val_idx:].copy()

    print(f"  Chronological splits:")
    print(f"    Train      : {len(df_train):,} ({df_train['date'].min().date()} to {df_train['date'].max().date()})")
    print(f"    Validation : {len(df_val):,} ({df_val['date'].min().date()} to {df_val['date'].max().date()})")
    print(f"    Test       : {len(df_test):,} ({df_test['date'].min().date()} to {df_test['date'].max().date()})")

    X_train = df_train[feature_cols].values
    y_train = df_train[target_col].values

    X_val   = df_val[feature_cols].values
    y_val   = df_val[target_col].values

    X_test  = df_test[feature_cols].values
    y_test  = df_test[target_col].values

    # Preprocessing: StandardScaler fitted ON TRAIN ONLY
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled   = scaler.transform(X_val)
    X_test_scaled  = scaler.transform(X_test)

    joblib.dump(scaler, DATA_MODELS / "scaler.joblib")

    # 1. Baseline Model: Persistence (Next day = Today's moisture)
    # Today's moisture index in features
    sm_idx = feature_cols.index("soil_moisture_lag1") if "soil_moisture_lag1" in feature_cols else feature_cols.index("soil_moisture")
    y_pred_baseline = X_test[:, sm_idx]
    baseline_metrics = compute_metrics(y_test, y_pred_baseline)
    print(f"\n  Baseline (Persistence) Test Metrics: {baseline_metrics}")

    # 2. Model A: Random Forest Regressor
    print("\n  Training Model A: RandomForestRegressor...")
    rf_params = {
        "n_estimators": 200,
        "max_depth": 14,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "random_state": 42,
        "n_jobs": -1
    }
    rf = RandomForestRegressor(**rf_params)
    rf.fit(X_train, y_train)  # Trees can train directly on unscaled features

    y_val_rf  = rf.predict(X_val)
    y_test_rf = rf.predict(X_test)

    rf_val_metrics  = compute_metrics(y_val, y_val_rf)
    rf_test_metrics = compute_metrics(y_test, y_test_rf)
    print(f"  Random Forest Validation Metrics: {rf_val_metrics}")
    print(f"  Random Forest Test Metrics      : {rf_test_metrics}")

    joblib.dump(rf, DATA_MODELS / "rf_model.joblib")

    # Feature Importance for Random Forest
    rf_importances = dict(zip(feature_cols, [round(float(v), 4) for v in rf.feature_importances_]))
    sorted_importances = dict(sorted(rf_importances.items(), key=lambda item: item[1], reverse=True))

    with open(DATA_MODELS / "feature_importance.json", "w", encoding="utf-8") as f:
        json.dump(sorted_importances, f, indent=2)

    # 3. Model B: XGBoost Regressor
    xgb_test_metrics = None
    xgb_params = {}
    if HAS_XGBOOST:
        print("\n  Training Model B: XGBRegressor...")
        xgb_params = {
            "n_estimators": 250,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "random_state": 42
        }
        xgb_model = xgb.XGBRegressor(**xgb_params)
        xgb_model.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)], verbose=False)

        y_test_xgb = xgb_model.predict(X_test_scaled)
        xgb_test_metrics = compute_metrics(y_test, y_test_xgb)
        print(f"  XGBoost Test Metrics            : {xgb_test_metrics}")
        joblib.dump(xgb_model, DATA_MODELS / "xgb_model.joblib")

    # 4. Generate Visualizations (Actual vs Predicted & Feature Importance)
    print("\n  Generating model evaluation charts...")
    # Plot 1: Actual vs Predicted (Test Set)
    plt.figure(figsize=(8, 6), dpi=150)
    plt.scatter(y_test, y_test_rf, alpha=0.35, color="#2D6A4F", edgecolors="none", s=25, label="RF Predictions")
    min_val = min(y_test.min(), y_test_rf.min())
    max_val = max(y_test.max(), y_test_rf.max())
    plt.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=1.5, label="Perfect 1:1 Fit")
    plt.xlabel("Actual Next-Day Soil Moisture (m³/m³)")
    plt.ylabel("Predicted Soil Moisture (m³/m³)")
    plt.title(f"Random Forest: Actual vs. Predicted Soil Moisture\nTest R² = {rf_test_metrics['r2']:.3f} | RMSE = {rf_test_metrics['rmse']:.4f}")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plot1_path = PLOTS_DIR / "actual_vs_predicted.png"
    plt.savefig(plot1_path)
    plt.close()

    # Plot 2: Feature Importance Bar Chart
    plt.figure(figsize=(9, 6), dpi=150)
    feat_names = list(sorted_importances.keys())[:10]
    feat_vals  = [sorted_importances[k] for k in feat_names]
    plt.barh(feat_names[::-1], feat_vals[::-1], color="#52B788")
    plt.xlabel("MDI Feature Importance")
    plt.title("Top 10 Feature Importances (Random Forest Regressor)")
    plt.grid(axis="x", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plot2_path = PLOTS_DIR / "feature_importance.png"
    plt.savefig(plot2_path)
    plt.close()

    # Plot 3: Residual Distribution
    residuals = y_test - y_test_rf
    plt.figure(figsize=(8, 5), dpi=150)
    plt.hist(residuals, bins=40, color="#2D6A4F", alpha=0.8, edgecolor="white")
    plt.axvline(0, color="red", linestyle="--", linewidth=1.5)
    plt.xlabel("Residual Error (Actual - Predicted)")
    plt.ylabel("Frequency")
    plt.title(f"Prediction Residual Distribution (Mean: {np.mean(residuals):.4f}, Std: {np.std(residuals):.4f})")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plot3_path = PLOTS_DIR / "residual_distribution.png"
    plt.savefig(plot3_path)
    plt.close()

    # 5. Metadata Save
    meta_info = {
        "model_name": "Random Forest Regressor (Soil Moisture)",
        "model_version": "2.0.0",
        "training_timestamp": _ts(),
        "dataset_version": "ml_ready_v2.0",
        "target_variable": target_col,
        "features": feature_cols,
        "split_ratio": {"train": 0.70, "val": 0.15, "test": 0.15},
        "sample_counts": {
            "train": len(df_train),
            "val": len(df_val),
            "test": len(df_test),
            "total": n
        },
        "hyperparameters": rf_params,
        "metrics": {
            "baseline": baseline_metrics,
            "random_forest": rf_test_metrics,
            "xgboost": xgb_test_metrics if HAS_XGBOOST else None
        },
        "artifacts": {
            "rf_model": "data/models/rf_model.joblib",
            "scaler": "data/models/scaler.joblib",
            "feature_importance": "data/models/feature_importance.json",
            "plot_actual_vs_predicted": "data/reports/plots/actual_vs_predicted.png",
            "plot_feature_importance": "data/reports/plots/feature_importance.png",
            "plot_residuals": "data/reports/plots/residual_distribution.png"
        }
    }

    with open(DATA_MODELS / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, indent=2)

    _append_audit(
        "model_trained",
        f"RF trained on {len(df_train):,} samples. Test R2={rf_test_metrics['r2']}, RMSE={rf_test_metrics['rmse']}",
        "OK"
    )

    return meta_info


def main():
    print("\n" + "█" * 70)
    print("  SmartKhet 2.0 — 07_train_model.py")
    print("  Phase 2: Machine Learning Model Training & Evaluation")
    print("█" * 70)
    print(f"  Timestamp : {_ts()}")

    _append_audit("script_started", "07_train_model.py started")

    try:
        meta = train_and_evaluate()
        print("\n  🎯 Model Training Completed Successfully!")
        print("  Comparison Summary (Test Set):")
        print("  " + "-" * 55)
        print(f"  {'Model':<18} | {'MAE':<7} | {'RMSE':<7} | {'R²':<7} | {'MedAE':<7}")
        print("  " + "-" * 55)
        b = meta["metrics"]["baseline"]
        rf = meta["metrics"]["random_forest"]
        print(f"  {'Baseline':<18} | {b['mae']:<7.4f} | {b['rmse']:<7.4f} | {b['r2']:<7.4f} | {b['median_ae']:<7.4f}")
        print(f"  {'Random Forest':<18} | {rf['mae']:<7.4f} | {rf['rmse']:<7.4f} | {rf['r2']:<7.4f} | {rf['median_ae']:<7.4f}")
        if meta["metrics"]["xgboost"]:
            xg = meta["metrics"]["xgboost"]
            print(f"  {'XGBoost':<18} | {xg['mae']:<7.4f} | {xg['rmse']:<7.4f} | {xg['r2']:<7.4f} | {xg['median_ae']:<7.4f}")
        print("  " + "-" * 55)
        print(f"\n  Artifacts saved to: {DATA_MODELS}")
        print(f"  Evaluation plots saved to: {PLOTS_DIR}")

    except Exception as e:
        print(f"\n[ERROR] Model training failed: {e}\n{traceback.format_exc()}")
        _append_audit("script_error", str(e)[:300], "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
