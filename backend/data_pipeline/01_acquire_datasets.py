"""
SmartKhet 2.0 — Phase 1: Data Acquisition
==========================================
Script 01 — Acquire Datasets

Run from backend/ directory:
    python data_pipeline/01_acquire_datasets.py

This script:
  1. Prints manual download instructions for IMD and MOSDAC datasets
  2. Attempts ERA5 download via cdsapi (if configured)
  3. Attempts Kaggle supplementary download (if kaggle CLI configured)
  4. Creates data/metadata/acquisition_log.json
  5. Logs all activity to audit trail
"""

import os
import sys
import json
import subprocess
import datetime
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — resolve project root regardless of CWD
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_RAW        = PROJECT_ROOT / "data" / "raw"
DATA_METADATA   = PROJECT_ROOT / "data" / "metadata"
ACQUISITION_LOG = DATA_METADATA / "acquisition_log.json"
AUDIT_LOG       = PROJECT_ROOT / "docs" / "SMARTKHET_PROJECT_AUDIT_LOG.csv"

# Ensure directories exist
for d in [DATA_RAW, DATA_METADATA]:
    d.mkdir(parents=True, exist_ok=True)


def _ts() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _append_audit(action: str, detail: str, status: str = "INFO"):
    """Append a row to the project-wide audit CSV."""
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        header_needed = not AUDIT_LOG.exists()
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            if header_needed:
                f.write("timestamp,script,action,detail,status\n")
            ts = _ts()
            line = f'{ts},01_acquire_datasets,"{action}","{detail}",{status}\n'
            f.write(line)
    except Exception as e:
        print(f"  [WARN] Could not write audit log: {e}")


def print_imd_instructions():
    """Print manual download instructions for IMD Gridded Rainfall dataset."""
    print("\n" + "=" * 70)
    print("DATASET 1: IMD 0.25° Gridded Daily Rainfall  [IMD_RF_001]")
    print("=" * 70)
    print("""
  SOURCE  : https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html
  FORMAT  : NetCDF (.nc)
  LICENSE : Government of India Open Data License

  MANUAL DOWNLOAD STEPS:
  1. Visit: https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html
  2. Register for a free account if prompted.
  3. Select desired year range (recommend 2019-2023 for this project).
  4. Download annual NetCDF files (e.g. RF25_ind2019_rfp25.nc).
  5. Place ALL downloaded .nc files in:
       {raw}/IMD_rainfall/
  6. Re-run this script after placement for auto-detection.

  NOTE: This dataset requires MANUAL download due to portal authentication.
  The pipeline will work with the demo dataset if IMD files are absent.
""".format(raw=DATA_RAW))
    _append_audit("IMD_instructions_printed", "Manual download instructions displayed for IMD_RF_001")


def print_mosdac_instructions():
    """Print manual download instructions for MOSDAC Soil Moisture."""
    print("\n" + "=" * 70)
    print("DATASET 2: ISRO MOSDAC Soil Moisture  [MOSDAC_SM_001]")
    print("=" * 70)
    print("""
  SOURCE  : https://www.mosdac.gov.in/soil-moisture-0
  FORMAT  : NetCDF / HDF5
  LICENSE : SAC/ISRO data policy

  MANUAL DOWNLOAD STEPS:
  1. Visit: https://www.mosdac.gov.in
  2. Register for free at: https://www.mosdac.gov.in/register
  3. After approval (~1-2 days), log in and navigate to:
       Catalogue → Land → Soil Moisture
  4. Select spatial subset covering Tamil Nadu:
       Lat: 8°N to 13.5°N,  Lon: 76.5°E to 80.5°E
  5. Download daily soil moisture files for 2019-2023.
  6. Place files in:
       {raw}/MOSDAC_soil_moisture/
  7. Re-run this script after placement for auto-detection.

  NOTE: FTP bulk access requires portal approval. Manual download recommended.
  The pipeline will use the demo dataset if MOSDAC files are absent.
""".format(raw=DATA_RAW))
    _append_audit("MOSDAC_instructions_printed", "Manual download instructions displayed for MOSDAC_SM_001")


def print_era5_instructions():
    """Print ERA5 CDS API instructions and attempt download if configured."""
    print("\n" + "=" * 70)
    print("DATASET 3: ERA5-Land Hourly Temperature  [ERA5_TH_001]")
    print("=" * 70)
    print("""
  SOURCE  : https://cds.climate.copernicus.eu/
  FORMAT  : NetCDF / GRIB
  LICENSE : Copernicus License v1.2
  DOI     : 10.24381/cds.e2161bac

  API SETUP (one-time):
  1. Register at: https://cds.climate.copernicus.eu/user/register
  2. After login, copy your UID and API key from:
       https://cds.climate.copernicus.eu/user/<UID>
  3. Create file ~/.cdsapirc with contents:
       url: https://cds.climate.copernicus.eu/api/v2
       key: <UID>:<API_KEY>
  4. Install client:  pip install cdsapi

  ERA5 DOWNLOAD SCRIPT (save as era5_download.py and run separately):
  ----------------------------------------------------------------
  import cdsapi
  c = cdsapi.Client()
  c.retrieve(
      'reanalysis-era5-land',
      {
          'variable': ['2m_temperature', '2m_dewpoint_temperature'],
          'year': [str(y) for y in range(2019, 2024)],
          'month': [f'{m:02d}' for m in range(1, 13)],
          'day':   [f'{d:02d}' for d in range(1, 32)],
          'time':  ['06:00', '12:00', '18:00'],
          'area':  [13.5, 76.5, 8.0, 80.5],   # Tamil Nadu bounding box
          'format': 'netcdf',
      },
      'era5_tamilnadu_2019_2023.nc'
  )
  ----------------------------------------------------------------
  Place output in: {raw}/ERA5/
""".format(raw=DATA_RAW))

    # Attempt cdsapi import — just check availability
    try:
        import cdsapi  # noqa: F401
        print("  [OK] cdsapi is installed. Configure ~/.cdsapirc to enable auto-download.")
        _append_audit("ERA5_cdsapi_found", "cdsapi library is installed; API key configuration required")
    except ImportError:
        print("  [INFO] cdsapi not installed. Run: pip install cdsapi")
        _append_audit("ERA5_cdsapi_missing", "cdsapi library not found; pip install cdsapi to enable")


def attempt_kaggle_download() -> dict:
    """Attempt to download Kaggle supplementary weather dataset."""
    print("\n" + "=" * 70)
    print("DATASET 4: India Weather Data — Kaggle  [KAGGLE_IWD_001]")
    print("=" * 70)

    result = {
        "dataset_id": "KAGGLE_IWD_001",
        "status": "not_attempted",
        "timestamp": _ts(),
        "file_path": None,
        "error": None
    }

    kaggle_dest = DATA_RAW / "kaggle_india_weather"
    kaggle_dest.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    existing = list(kaggle_dest.glob("*.csv"))
    if existing:
        print(f"  [OK] Kaggle data already present: {[f.name for f in existing]}")
        result["status"] = "already_present"
        result["file_path"] = str(existing[0])
        _append_audit("KAGGLE_already_present", str(existing[0]), "OK")
        return result

    # Check kaggle CLI
    try:
        proc = subprocess.run(
            ["kaggle", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode != 0:
            raise RuntimeError("kaggle CLI returned non-zero")
        print(f"  [OK] Kaggle CLI found: {proc.stdout.strip()}")
    except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired) as e:
        print("  [SKIP] Kaggle CLI not found or not configured.")
        print("  To enable, run:  pip install kaggle")
        print("  Then place your API token at: ~/.kaggle/kaggle.json")
        result["status"] = "skipped_no_cli"
        result["error"] = str(e)
        _append_audit("KAGGLE_cli_missing", "kaggle CLI not found; supplementary dataset skipped", "WARN")
        return result

    # Attempt download
    try:
        print("  [INFO] Attempting Kaggle download (may take a moment)…")
        proc = subprocess.run(
            [
                "kaggle", "datasets", "download",
                "-d", "redwankarimsony/weather-data-desc",
                "-p", str(kaggle_dest),
                "--unzip"
            ],
            capture_output=True, text=True, timeout=120
        )
        if proc.returncode == 0:
            csvs = list(kaggle_dest.glob("*.csv"))
            if csvs:
                result["status"] = "downloaded"
                result["file_path"] = str(csvs[0])
                print(f"  [OK] Downloaded: {[f.name for f in csvs]}")
                _append_audit("KAGGLE_downloaded", str(csvs[0]), "OK")
            else:
                result["status"] = "downloaded_no_csv"
                result["error"] = "Download succeeded but no CSV found"
                print("  [WARN] Download succeeded but no CSV found in output.")
                _append_audit("KAGGLE_no_csv", "No CSV found after download", "WARN")
        else:
            result["status"] = "download_failed"
            result["error"] = proc.stderr.strip()
            print(f"  [WARN] Kaggle download failed: {proc.stderr.strip()}")
            _append_audit("KAGGLE_download_failed", proc.stderr.strip()[:200], "WARN")
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Download timed out after 120s"
        print("  [WARN] Kaggle download timed out.")
        _append_audit("KAGGLE_timeout", "Download timed out after 120s", "WARN")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"  [ERROR] Unexpected error: {e}")
        _append_audit("KAGGLE_error", str(e)[:200], "ERROR")

    return result


def scan_raw_directory() -> dict:
    """Scan data/raw for already-present files and return inventory."""
    inventory = {}
    for category_dir in DATA_RAW.iterdir():
        if category_dir.is_dir():
            files = [f.name for f in category_dir.rglob("*") if f.is_file()]
            inventory[category_dir.name] = files
    return inventory


def save_acquisition_log(kaggle_result: dict):
    """Save acquisition log JSON."""
    inventory = scan_raw_directory()
    log = {
        "generated_at": _ts(),
        "script": "01_acquire_datasets.py",
        "project": "SmartKhet 2.0",
        "note": (
            "IMD and MOSDAC datasets require manual download from their respective portals. "
            "ERA5 requires cdsapi configuration. "
            "The demo dataset (script 03) provides a complete training set for the ML pipeline."
        ),
        "datasets": {
            "IMD_RF_001": {
                "status": "manual_download_required",
                "instructions_displayed": True,
                "portal": "https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html"
            },
            "MOSDAC_SM_001": {
                "status": "manual_download_required",
                "instructions_displayed": True,
                "portal": "https://www.mosdac.gov.in/soil-moisture-0"
            },
            "ERA5_TH_001": {
                "status": "api_key_required",
                "instructions_displayed": True,
                "portal": "https://cds.climate.copernicus.eu/"
            },
            "KAGGLE_IWD_001": kaggle_result
        },
        "raw_directory_inventory": inventory,
        "next_step": "Run 02_inspect_datasets.py to inspect any available files, or 03_generate_demo_dataset.py to create the ML training dataset."
    }
    with open(ACQUISITION_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    print(f"\n  [OK] Acquisition log saved → {ACQUISITION_LOG.relative_to(PROJECT_ROOT)}")
    _append_audit("acquisition_log_saved", str(ACQUISITION_LOG))


def main():
    print("\n" + "█" * 70)
    print("  SmartKhet 2.0 — 01_acquire_datasets.py")
    print("  Phase 1: Data Acquisition")
    print("█" * 70)
    print(f"  Timestamp : {_ts()}")
    print(f"  Project   : {PROJECT_ROOT}")
    print(f"  Output    : {DATA_RAW}")

    _append_audit("script_started", "01_acquire_datasets.py started")

    try:
        print_imd_instructions()
        print_mosdac_instructions()
        print_era5_instructions()
        kaggle_result = attempt_kaggle_download()
        save_acquisition_log(kaggle_result)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error in acquisition script:\n{traceback.format_exc()}")
        _append_audit("script_error", str(e)[:300], "ERROR")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("  ACQUISITION COMPLETE")
    print("  Next step: python data_pipeline/03_generate_demo_dataset.py")
    print("=" * 70 + "\n")
    _append_audit("script_completed", "01_acquire_datasets.py finished successfully", "OK")


if __name__ == "__main__":
    main()
