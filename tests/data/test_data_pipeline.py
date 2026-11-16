"""
SmartKhet 2.0 — Data Pipeline & Preprocessing Tests
"""
import os
import json
import pytest
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_METADATA  = PROJECT_ROOT / "data" / "metadata"


def test_processed_dataset_exists():
    csv_file = DATA_PROCESSED / "ml_ready_dataset.csv"
    assert csv_file.exists(), "Processed ML dataset ml_ready_dataset.csv must exist"
    df = pd.read_csv(csv_file)
    assert len(df) > 5000, f"Expected >5000 rows, got {len(df)}"


def test_feature_list_metadata():
    feat_file = DATA_METADATA / "feature_list.json"
    assert feat_file.exists(), "feature_list.json metadata must exist"
    with open(feat_file, "r") as f:
        meta = json.load(f)
    assert "features" in meta
    assert len(meta["features"]) >= 15, "Expected at least 15 features"
    assert meta["target"] == "soil_moisture_next_day"


def test_zero_target_leakage():
    feat_file = DATA_METADATA / "feature_list.json"
    with open(feat_file, "r") as f:
        meta = json.load(f)
    features = meta["features"]
    target = meta["target"]
    assert target not in features, "Target must not be present in feature list (Leakage Prevention)"


def test_soil_moisture_physical_ranges():
    csv_file = DATA_PROCESSED / "ml_ready_dataset.csv"
    df = pd.read_csv(csv_file)
    assert (df["soil_moisture_lag1"] >= 0.0).all()
    assert (df["soil_moisture_lag1"] <= 1.0).all()
    assert (df["soil_moisture_next_day"] >= 0.0).all()
    assert (df["soil_moisture_next_day"] <= 1.0).all()


def test_no_missing_values_in_ml_dataset():
    csv_file = DATA_PROCESSED / "ml_ready_dataset.csv"
    df = pd.read_csv(csv_file)
    assert df.isna().sum().sum() == 0, "ML dataset must have zero missing/NaN values"

