"""
SmartKhet 2.0 — Phase 1 & 2: Report Generation
==============================================
Script 08 — Comprehensive HTML & JSON Report Generator

Run from backend/ directory:
    python data_pipeline/08_generate_reports.py

Generates:
  1. data/reports/data_quality_report.html
  2. data/reports/model_evaluation_report.html
  3. data/reports/pipeline_summary.json
"""

import os
import sys
import json
import base64
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).resolve().parent
BACKEND_DIR  = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_METADATA  = PROJECT_ROOT / "data" / "metadata"
DATA_MODELS    = PROJECT_ROOT / "data" / "models"
DATA_REPORTS   = PROJECT_ROOT / "data" / "reports"
PLOTS_DIR      = DATA_REPORTS / "plots"
DOCS_DIR       = PROJECT_ROOT / "docs"
AUDIT_LOG      = DOCS_DIR / "SMARTKHET_PROJECT_AUDIT_LOG.csv"

DATA_REPORTS.mkdir(parents=True, exist_ok=True)


def _ts() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _b64_image(image_path: Path) -> str:
    if not image_path.exists():
        return ""
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def generate_pipeline_summary():
    reg_path  = DATA_METADATA / "dataset_registry.json"
    val_path  = DATA_REPORTS / "validation_report.json"
    meta_path = DATA_MODELS / "model_metadata.json"

    datasets = []
    if reg_path.exists():
        with open(reg_path, "r", encoding="utf-8") as f:
            datasets = json.load(f).get("datasets", [])

    validation = {}
    if val_path.exists():
        with open(val_path, "r", encoding="utf-8") as f:
            validation = json.load(f)

    model_meta = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            model_meta = json.load(f)

    summary = {
        "project": "SmartKhet 2.0",
        "generated_at": _ts(),
        "total_datasets_registered": len(datasets),
        "validation_status": "PASSED" if validation.get("all_checks_passed") else "PENDING_OR_FAILED",
        "total_processed_records": validation.get("total_records", 0),
        "model_deployed": model_meta.get("model_name", "None"),
        "model_version": model_meta.get("model_version", "None"),
        "test_r2": model_meta.get("metrics", {}).get("random_forest", {}).get("r2", 0.0),
        "test_rmse": model_meta.get("metrics", {}).get("random_forest", {}).get("rmse", 0.0),
        "farms_configured": ["TN001 (Thanjavur)", "TN002 (Coimbatore)", "TN003 (Madurai)"]
    }

    out_file = DATA_REPORTS / "pipeline_summary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary, datasets, validation, model_meta


def generate_html_reports(summary, datasets, validation, model_meta):
    # 1. Data Quality HTML Report
    dq_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SmartKhet 2.0 — Data Quality & Integrity Report</title>
<style>
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #F8FAF5; color: #1B2D1E; margin: 0; padding: 24px; }}
  .container {{ max-width: 1000px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
  h1 {{ color: #2D6A4F; margin-top: 0; }}
  h2 {{ color: #40916C; border-bottom: 2px solid #D8F3DC; padding-bottom: 8px; }}
  .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }}
  .badge-pass {{ background: #D8F3DC; color: #2D6A4F; }}
  .badge-fail {{ background: #FFE5D9; color: #D90429; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; margin-bottom: 24px; }}
  th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #E5E7EB; }}
  th {{ background: #F0FDF4; color: #2D6A4F; font-weight: 600; }}
  .meta-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }}
  .card {{ background: #F9FAFB; padding: 16px; border-radius: 8px; border: 1px solid #E5E7EB; }}
  .card-label {{ font-size: 12px; color: #6B7280; text-transform: uppercase; }}
  .card-value {{ font-size: 20px; font-weight: bold; color: #2D6A4F; margin-top: 4px; }}
</style>
</head>
<body>
<div class="container">
  <h1>🌱 SmartKhet 2.0 — Big Data Quality & Pipeline Audit</h1>
  <p>Automated verification report for agricultural datasets, preprocessing pipeline, and validation checks.</p>
  
  <div class="meta-grid">
    <div class="card">
      <div class="card-label">Overall Status</div>
      <div class="card-value"><span class="badge badge-pass">{summary['validation_status']}</span></div>
    </div>
    <div class="card">
      <div class="card-label">Total Cleaned Records</div>
      <div class="card-value">{summary['total_processed_records']:,}</div>
    </div>
    <div class="card">
      <div class="card-label">Active Datasets</div>
      <div class="card-value">{summary['total_datasets_registered']} Sources</div>
    </div>
  </div>

  <h2>1. Dataset Provenance Registry</h2>
  <table>
    <thead>
      <tr>
        <th>Dataset ID</th>
        <th>Source Name</th>
        <th>Publisher</th>
        <th>Format & Coverage</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
"""
    for ds in datasets:
        dq_html += f"""
      <tr>
        <td><strong>{ds.get('dataset_id')}</strong></td>
        <td>{ds.get('name')}</td>
        <td>{ds.get('publisher')}</td>
        <td>{ds.get('file_format')} ({ds.get('temporal_coverage')})</td>
        <td><span class="badge badge-pass">{ds.get('validation_status')}</span></td>
      </tr>
"""
    dq_html += """
    </tbody>
  </table>

  <h2>2. Automated Pipeline Validation Checks</h2>
  <table>
    <thead>
      <tr>
        <th>Check Description</th>
        <th>Status</th>
        <th>Execution Details</th>
      </tr>
    </thead>
    <tbody>
"""
    for c in validation.get("checks", []):
        badge_cls = "badge-pass" if c["passed"] else "badge-fail"
        mark = "PASS" if c["passed"] else "FAIL"
        dq_html += f"""
      <tr>
        <td>{c['check']}</td>
        <td><span class="badge {badge_cls}">{mark}</span></td>
        <td>{c['detail']}</td>
      </tr>
"""
    dq_html += """
    </tbody>
  </table>

  <p style="margin-top: 32px; font-size: 12px; color: #6B7280; text-align: center;">
    Report automatically compiled by SmartKhet 2.0 Data Quality Engine.
  </p>
</div>
</body>
</html>
"""

    with open(DATA_REPORTS / "data_quality_report.html", "w", encoding="utf-8") as f:
        f.write(dq_html)

    # 2. Model Evaluation HTML Report
    p1_b64 = _b64_image(PLOTS_DIR / "actual_vs_predicted.png")
    p2_b64 = _b64_image(PLOTS_DIR / "feature_importance.png")
    p3_b64 = _b64_image(PLOTS_DIR / "residual_distribution.png")

    rf_m = model_meta.get("metrics", {}).get("random_forest", {})
    bl_m = model_meta.get("metrics", {}).get("baseline", {})
    xg_m = model_meta.get("metrics", {}).get("xgboost")

    eval_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SmartKhet 2.0 — Machine Learning Evaluation Report</title>
<style>
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #F8FAF5; color: #1B2D1E; margin: 0; padding: 24px; }}
  .container {{ max-width: 1050px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
  h1 {{ color: #2D6A4F; margin-top: 0; }}
  h2 {{ color: #40916C; border-bottom: 2px solid #D8F3DC; padding-bottom: 8px; margin-top: 32px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; margin-bottom: 24px; }}
  th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #E5E7EB; }}
  th {{ background: #F0FDF4; color: #2D6A4F; font-weight: 600; }}
  .chart-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px; }}
  .chart-card {{ background: #FAFAFA; border: 1px solid #E5E7EB; border-radius: 8px; padding: 12px; text-align: center; }}
  .chart-card img {{ max-width: 100%; height: auto; border-radius: 6px; }}
  .meta-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
  .card {{ background: #F9FAFB; padding: 16px; border-radius: 8px; border: 1px solid #E5E7EB; }}
  .card-label {{ font-size: 12px; color: #6B7280; text-transform: uppercase; }}
  .card-value {{ font-size: 22px; font-weight: bold; color: #2D6A4F; margin-top: 4px; }}
</style>
</head>
<body>
<div class="container">
  <h1>🌾 SmartKhet 2.0 — ML Soil Moisture Model Evaluation</h1>
  <p>Performance benchmark for next-day volumetric soil moisture prediction (m³/m³) using strict chronological evaluation.</p>

  <div class="meta-grid">
    <div class="card">
      <div class="card-label">Model Architecture</div>
      <div class="card-value">Random Forest</div>
    </div>
    <div class="card">
      <div class="card-label">Test Set R²</div>
      <div class="card-value">{rf_m.get('r2', 'N/A')}</div>
    </div>
    <div class="card">
      <div class="card-label">Test Set RMSE</div>
      <div class="card-value">{rf_m.get('rmse', 'N/A')} m³/m³</div>
    </div>
    <div class="card">
      <div class="card-label">Test Samples</div>
      <div class="card-value">{rf_m.get('sample_size', 'N/A'):,}</div>
    </div>
  </div>

  <h2>1. Model Comparison on Unseen Chronological Test Set</h2>
  <table>
    <thead>
      <tr>
        <th>Model</th>
        <th>MAE (m³/m³)</th>
        <th>RMSE (m³/m³)</th>
        <th>R² Score</th>
        <th>Median AE (m³/m³)</th>
        <th>Sample Size</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Baseline (Persistence)</strong></td>
        <td>{bl_m.get('mae', 'N/A')}</td>
        <td>{bl_m.get('rmse', 'N/A')}</td>
        <td>{bl_m.get('r2', 'N/A')}</td>
        <td>{bl_m.get('median_ae', 'N/A')}</td>
        <td>{bl_m.get('sample_size', 'N/A')}</td>
      </tr>
      <tr style="background: #F0FDF4;">
        <td><strong>Random Forest Regressor (Primary)</strong></td>
        <td><strong>{rf_m.get('mae', 'N/A')}</strong></td>
        <td><strong>{rf_m.get('rmse', 'N/A')}</strong></td>
        <td><strong>{rf_m.get('r2', 'N/A')}</strong></td>
        <td><strong>{rf_m.get('median_ae', 'N/A')}</strong></td>
        <td>{rf_m.get('sample_size', 'N/A')}</td>
      </tr>
"""
    if xg_m:
        eval_html += f"""
      <tr>
        <td><strong>XGBoost Regressor</strong></td>
        <td>{xg_m.get('mae', 'N/A')}</td>
        <td>{xg_m.get('rmse', 'N/A')}</td>
        <td>{xg_m.get('r2', 'N/A')}</td>
        <td>{xg_m.get('median_ae', 'N/A')}</td>
        <td>{xg_m.get('sample_size', 'N/A')}</td>
      </tr>
"""
    eval_html += f"""
    </tbody>
  </table>

  <h2>2. Diagnostic Plots & Explainability</h2>
  <div class="chart-grid">
    <div class="chart-card">
      <h3>Actual vs. Predicted Soil Moisture</h3>
      {f'<img src="{p1_b64}" alt="Actual vs Predicted"/>' if p1_b64 else '<p>Plot not found</p>'}
    </div>
    <div class="chart-card">
      <h3>Top Feature Importances (MDI)</h3>
      {f'<img src="{p2_b64}" alt="Feature Importance"/>' if p2_b64 else '<p>Plot not found</p>'}
    </div>
  </div>

  <div style="margin-top: 24px;" class="chart-card">
    <h3>Residual Distribution</h3>
    {f'<img style="max-width: 600px;" src="{p3_b64}" alt="Residuals"/>' if p3_b64 else '<p>Plot not found</p>'}
  </div>

  <p style="margin-top: 32px; font-size: 12px; color: #6B7280; text-align: center;">
    SmartKhet 2.0 Machine Learning Evaluation Engine • Never presents predictions as ground truth observations.
  </p>
</div>
</body>
</html>
"""

    with open(DATA_REPORTS / "model_evaluation_report.html", "w", encoding="utf-8") as f:
        f.write(eval_html)


def main():
    print("\n" + "█" * 70)
    print("  SmartKhet 2.0 — 08_generate_reports.py")
    print("  Report Compilation")
    print("█" * 70)

    try:
        summary, datasets, validation, model_meta = generate_pipeline_summary()
        generate_html_reports(summary, datasets, validation, model_meta)
        print("  ✅ Successfully generated:")
        print(f"    - {DATA_REPORTS / 'pipeline_summary.json'}")
        print(f"    - {DATA_REPORTS / 'data_quality_report.html'}")
        print(f"    - {DATA_REPORTS / 'model_evaluation_report.html'}")
    except Exception as e:
        print(f"  [ERROR] Report generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

