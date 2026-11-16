"""
SmartKhet 2.0 — Machine Learning Model & Evaluation Tests
"""
import os
import json
import joblib
import pytest
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_MODELS = PROJECT_ROOT / "data" / "models"


def test_model_artifacts_exist():
    rf_file = DATA_MODELS / "rf_model.joblib"
    meta_file = DATA_MODELS / "model_metadata.json"
    assert rf_file.exists(), "rf_model.joblib must exist"
    assert meta_file.exists(), "model_metadata.json must exist"


def test_model_evaluation_metrics():
    meta_file = DATA_MODELS / "model_metadata.json"
    with open(meta_file, "r") as f:
        meta = json.load(f)
    
    rf_metrics = meta["metrics"]["random_forest"]
    assert rf_metrics["r2"] > 0.80, f"Expected R² > 0.80, got {rf_metrics['r2']}"
    assert rf_metrics["rmse"] < 0.02, f"Expected RMSE < 0.02, got {rf_metrics['rmse']}"
    assert rf_metrics["mae"] < 0.01, f"Expected MAE < 0.01, got {rf_metrics['mae']}"


def test_random_forest_inference():
    rf_file = DATA_MODELS / "rf_model.joblib"
    model = joblib.load(rf_file)
    dummy_x = np.zeros((1, model.n_features_in_))
    pred = model.predict(dummy_x)[0]
    assert isinstance(pred, float) or isinstance(pred, np.floating)
    assert 0.0 <= pred <= 1.0, f"Predicted soil moisture {pred} out of range [0, 1]"

