"""
SmartKhet 2.0 — Phase 1: Data Inspection
=========================================
Script 02 — Inspect Datasets

Run from backend/ directory:
    python data_pipeline/02_inspect_datasets.py

This script:
  1. Scans data/raw/ for any available files (CSV, NetCDF, HDF5, etc.)
  2. For each file: rows, columns, dtypes, date range, missing%, duplicates,
     min/max/mean/std
  3. Generates data/reports/inspection_report.json
  4. Generates data/reports/inspection_report.html (charts embedded as base64)
  5. Saves individual distribution plots to data/reports/plots/
"""

import os
import sys
import json
import base64
import datetime
import traceback
from pathlib import Path
from io import BytesIO

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).resolve().parent
BACKEND_DIR  = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_RAW        = PROJECT_ROOT / "data" / "raw"
DATA_METADATA   = PROJECT_ROOT / "data" / "metadata"
REPORTS_DIR     = PROJECT_ROOT / "data" / "reports"
PLOTS_DIR       = REPORTS_DIR / "plots"
AUDIT_LOG       = PROJECT_ROOT / "docs" / "SMARTKHET_PROJECT_AUDIT_LOG.csv"

for d in [DATA_RAW, DATA_METADATA, REPORTS_DIR, PLOTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _ts() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _append_audit(action: str, detail: str, status: str = "INFO"):
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        header_needed = not AUDIT_LOG.exists()
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            if header_needed:
                f.write("timestamp,script,action,detail,status\n")
            f.write(f'{_ts()},02_inspect_datasets,"{action}","{detail}",{status}\n')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Matplotlib setup (non-interactive backend)
# ---------------------------------------------------------------------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("[WARN] matplotlib not installed — plots will be skipped.")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("[ERROR] pandas is required. Run: pip install pandas")
    sys.exit(1)


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def load_netcdf(path: Path) -> pd.DataFrame:
    """Load a NetCDF file and return a flattened DataFrame (best-effort)."""
    try:
        import xarray as xr
        ds = xr.open_dataset(path)
        df = ds.to_dataframe().reset_index()
        ds.close()
        return df
    except ImportError:
        print(f"    [WARN] xarray not installed; cannot read NetCDF {path.name}. pip install xarray")
        return pd.DataFrame()
    except Exception as e:
        print(f"    [WARN] Could not read NetCDF {path.name}: {e}")
        return pd.DataFrame()


def load_hdf5(path: Path) -> pd.DataFrame:
    """Load HDF5 — try pandas HDFStore first, then h5py flattening."""
    try:
        store = pd.HDFStore(str(path), mode="r")
        keys = store.keys()
        if keys:
            df = store[keys[0]]
        else:
            df = pd.DataFrame()
        store.close()
        return df
    except Exception:
        pass
    try:
        import h5py
        with h5py.File(path, "r") as f:
            datasets = {}

            def visitor(name, obj):
                if isinstance(obj, h5py.Dataset):
                    try:
                        datasets[name] = obj[()]
                    except Exception:
                        pass
            f.visititems(visitor)
        return pd.DataFrame({k: v.flatten()[:1000] for k, v in datasets.items()})
    except ImportError:
        print(f"    [WARN] h5py not installed; cannot read HDF5 {path.name}")
        return pd.DataFrame()
    except Exception as e:
        print(f"    [WARN] Could not read HDF5 {path.name}: {e}")
        return pd.DataFrame()


LOADERS = {
    ".csv": load_csv,
    ".nc": load_netcdf,
    ".nc4": load_netcdf,
    ".h5": load_hdf5,
    ".hdf5": load_hdf5,
    ".xlsx": lambda p: pd.read_excel(p),
    ".xls": lambda p: pd.read_excel(p),
}


def find_files() -> list:
    """Recursively find all data files under data/raw/."""
    files = []
    for path in DATA_RAW.rglob("*"):
        if path.is_file() and path.suffix.lower() in LOADERS:
            files.append(path)
    return files


# ---------------------------------------------------------------------------
# Inspection logic
# ---------------------------------------------------------------------------

def inspect_dataframe(df: pd.DataFrame, file_path: Path) -> dict:
    """Compute profile statistics for a DataFrame."""
    info = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "missing_count": {c: int(df[c].isna().sum()) for c in df.columns},
        "missing_pct": {c: round(float(df[c].isna().mean() * 100), 2) for c in df.columns},
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_stats": {},
        "date_range": None,
    }

    # Numeric stats
    num_cols = df.select_dtypes(include="number").columns.tolist()
    for col in num_cols:
        s = df[col].dropna()
        if len(s) > 0:
            info["numeric_stats"][col] = {
                "min":  round(float(s.min()), 4),
                "max":  round(float(s.max()), 4),
                "mean": round(float(s.mean()), 4),
                "std":  round(float(s.std()), 4),
                "p25":  round(float(s.quantile(0.25)), 4),
                "p50":  round(float(s.quantile(0.50)), 4),
                "p75":  round(float(s.quantile(0.75)), 4),
            }

    # Try to find date column and compute date range
    for col in df.columns:
        if any(kw in col.lower() for kw in ["date", "time", "day", "timestamp"]):
            try:
                dates = pd.to_datetime(df[col], errors="coerce").dropna()
                if len(dates) > 0:
                    info["date_range"] = {
                        "column": col,
                        "start": str(dates.min().date()),
                        "end":   str(dates.max().date()),
                        "count": int(len(dates)),
                    }
                    break
            except Exception:
                pass

    return info


def make_distribution_plots(df: pd.DataFrame, file_stem: str) -> dict:
    """Create distribution histograms for numeric columns; return {col: base64_png}."""
    if not HAS_MPL:
        return {}

    b64_plots = {}
    num_cols = df.select_dtypes(include="number").columns.tolist()

    for col in num_cols[:12]:  # limit to 12 columns
        try:
            fig, ax = plt.subplots(figsize=(5, 3))
            data = df[col].dropna()
            ax.hist(data, bins=40, color="#2E86AB", edgecolor="white", alpha=0.85)
            ax.set_title(f"{col} distribution", fontsize=10)
            ax.set_xlabel(col)
            ax.set_ylabel("Count")
            plt.tight_layout()

            # Save to file
            plot_path = PLOTS_DIR / f"{file_stem}_{col}.png"
            fig.savefig(plot_path, dpi=90)

            # Encode to base64
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=90)
            buf.seek(0)
            b64_plots[col] = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
        except Exception as e:
            print(f"    [WARN] Plot failed for column {col}: {e}")

    return b64_plots


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def build_html_report(all_results: list) -> str:
    """Generate an HTML report with embedded charts."""
    rows_html = ""
    charts_html = ""

    for res in all_results:
        name = res["file_name"]
        info = res.get("profile", {})
        rows_html += f"""
        <tr>
          <td><b>{name}</b></td>
          <td>{info.get('rows', 'N/A')}</td>
          <td>{info.get('columns', 'N/A')}</td>
          <td>{info.get('duplicate_rows', 'N/A')}</td>
          <td>{info.get('date_range', {}).get('start', '—') if info.get('date_range') else '—'}</td>
          <td>{info.get('date_range', {}).get('end', '—') if info.get('date_range') else '—'}</td>
        </tr>"""

        b64_plots = res.get("distribution_plots", {})
        if b64_plots:
            charts_html += f"<h3>📊 {name}</h3><div class='charts'>"
            for col, b64 in b64_plots.items():
                charts_html += (
                    f'<div class="chart-box">'
                    f'<img src="data:image/png;base64,{b64}" alt="{col} distribution"/>'
                    f'<p>{col}</p></div>'
                )
            charts_html += "</div>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>SmartKhet 2.0 — Dataset Inspection Report</title>
<style>
  body {{font-family: Arial, sans-serif; margin: 30px; background: #f5f7fa;}}
  h1 {{color: #2E86AB;}} h2 {{color: #333;}} h3 {{color: #555; margin-top: 30px;}}
  table {{border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden;}}
  th {{background: #2E86AB; color: white; padding: 10px;}}
  td {{border: 1px solid #ddd; padding: 8px; text-align: center;}}
  tr:nth-child(even) {{background: #f9f9f9;}}
  .charts {{display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;}}
  .chart-box {{background: white; border-radius: 8px; padding: 10px; text-align: center;
               box-shadow: 0 1px 4px rgba(0,0,0,.1);}}
  .chart-box img {{max-width: 320px;}}
  .meta {{color: #888; font-size: 0.85em;}}
  .note {{background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; border-radius: 4px; margin: 16px 0;}}
</style>
</head>
<body>
<h1>🌾 SmartKhet 2.0 — Dataset Inspection Report</h1>
<p class="meta">Generated: {_ts()} | Script: 02_inspect_datasets.py</p>
<div class="note">
  <b>Note:</b> This report reflects files found in <code>data/raw/</code>.
  If no real datasets are present, run <code>03_generate_demo_dataset.py</code>
  to create the demonstration training dataset.
</div>

<h2>File Summary</h2>
<table>
  <thead><tr>
    <th>File</th><th>Rows</th><th>Columns</th>
    <th>Duplicates</th><th>Date Start</th><th>Date End</th>
  </tr></thead>
  <tbody>{rows_html if rows_html else '<tr><td colspan="6">No data files found in data/raw/</td></tr>'}</tbody>
</table>

<h2>Distribution Charts</h2>
{charts_html if charts_html else '<p>No charts generated (no numeric data found or matplotlib not installed).</p>'}

<hr/>
<p class="meta">SmartKhet 2.0 — Agricultural IoT Big Data Platform | Tamil Nadu</p>
</body>
</html>"""
    return html


def main():
    print("\n" + "█" * 70)
    print("  SmartKhet 2.0 — 02_inspect_datasets.py")
    print("  Phase 1: Dataset Inspection")
    print("█" * 70)
    print(f"  Timestamp : {_ts()}")
    print(f"  Scanning  : {DATA_RAW}\n")

    _append_audit("script_started", "02_inspect_datasets.py started")

    files = find_files()
    if not files:
        print("[INFO] No data files found in data/raw/.")
        print("       Run 01_acquire_datasets.py for download instructions,")
        print("       or run 03_generate_demo_dataset.py to create the demo dataset.")
        _append_audit("no_files_found", "data/raw/ is empty", "WARN")

    all_results = []

    for fpath in files:
        print(f"  Inspecting: {fpath.relative_to(PROJECT_ROOT)}")
        result = {
            "file_name": fpath.name,
            "file_path": str(fpath.relative_to(PROJECT_ROOT)),
            "file_size_kb": round(fpath.stat().st_size / 1024, 2),
            "extension": fpath.suffix.lower(),
            "inspected_at": _ts(),
            "profile": {},
            "distribution_plots": {},
            "error": None,
        }

        try:
            loader = LOADERS.get(fpath.suffix.lower())
            df = loader(fpath)

            if df is None or df.empty:
                result["error"] = "DataFrame is empty after loading"
                print(f"    [WARN] DataFrame is empty.")
            else:
                print(f"    Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
                profile = inspect_dataframe(df, fpath)
                result["profile"] = profile

                if HAS_MPL:
                    b64_plots = make_distribution_plots(df, fpath.stem)
                    result["distribution_plots"] = {
                        col: f"[base64 length {len(v)}]" for col, v in b64_plots.items()
                    }
                    # Keep actual b64 for HTML only
                    result["_b64_plots_for_html"] = b64_plots

                _append_audit(
                    "file_inspected",
                    f"{fpath.name}: {df.shape[0]} rows, {df.shape[1]} cols",
                    "OK"
                )
        except Exception as e:
            result["error"] = str(e)
            print(f"    [ERROR] {e}")
            _append_audit("file_inspection_error", f"{fpath.name}: {str(e)[:100]}", "ERROR")

        all_results.append(result)

    # Prepare JSON report (strip heavy b64)
    json_results = []
    for r in all_results:
        rj = {k: v for k, v in r.items() if k != "_b64_plots_for_html"}
        json_results.append(rj)

    report_json = {
        "generated_at": _ts(),
        "script": "02_inspect_datasets.py",
        "files_scanned": len(files),
        "results": json_results,
    }
    json_path = REPORTS_DIR / "inspection_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)
    print(f"\n  [OK] JSON report → {json_path.relative_to(PROJECT_ROOT)}")

    # Prepare HTML report (inject real b64)
    for r in all_results:
        if "_b64_plots_for_html" in r:
            r["distribution_plots"] = r.pop("_b64_plots_for_html")
        else:
            r.pop("_b64_plots_for_html", None)

    html_content = build_html_report(all_results)
    html_path = REPORTS_DIR / "inspection_report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"  [OK] HTML report → {html_path.relative_to(PROJECT_ROOT)}")

    print(f"\n  Files inspected : {len(files)}")
    print(f"  Plots directory : {PLOTS_DIR.relative_to(PROJECT_ROOT)}")
    print("  Next step: python data_pipeline/03_generate_demo_dataset.py")
    print("=" * 70 + "\n")

    _append_audit("script_completed", f"Inspected {len(files)} files", "OK")


if __name__ == "__main__":
    main()
