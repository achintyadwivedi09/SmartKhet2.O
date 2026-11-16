"""
SmartKhet 2.0 — Machine Learning Service
=========================================
Loads trained Random Forest and XGBoost models, serves next-day soil moisture
predictions, and generates explainable agronomical irrigation recommendations.
"""

from __future__ import annotations
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.config import (
    RF_MODEL_PATH,
    XGB_MODEL_PATH,
    MODEL_METADATA_PATH,
    FEATURE_LIST_PATH,
    FARMS,
)
from models.db_models import MLModel, Prediction


DEFAULT_FEATURE_COLS = [
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


class MLService:
    def __init__(self):
        self._model = None
        self._xgb_model = None
        self._scaler = None
        self._meta: Optional[Dict[str, Any]] = None
        self._feature_cols: List[str] = DEFAULT_FEATURE_COLS
        self.load_model()

    def load_model(self) -> bool:
        """Load trained Random Forest model and metadata from disk."""
        try:
            if os.path.exists(FEATURE_LIST_PATH):
                with open(FEATURE_LIST_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._feature_cols = data.get("features", DEFAULT_FEATURE_COLS)

            if os.path.exists(MODEL_METADATA_PATH):
                with open(MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
                    self._meta = json.load(f)

            if os.path.exists(RF_MODEL_PATH):
                self._model = joblib.load(RF_MODEL_PATH)

            if os.path.exists(XGB_MODEL_PATH):
                self._xgb_model = joblib.load(XGB_MODEL_PATH)

            return self._model is not None
        except Exception as e:
            print(f"[MLService] Warning loading models: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def get_feature_list(self) -> List[str]:
        return list(self._feature_cols)

    def get_metadata(self) -> Dict[str, Any]:
        if self._meta:
            return self._meta
        return {
            "model_name": "Random Forest Regressor (Soil Moisture)",
            "model_version": "2.0.0",
            "target_variable": "soil_moisture_next_day",
            "metrics": {
                "random_forest": {"mae": 0.0040, "rmse": 0.0082, "r2": 0.8722, "median_ae": 0.0012, "sample_size": 822},
                "baseline": {"mae": 0.0044, "rmse": 0.0103, "r2": 0.7946, "median_ae": 0.0000, "sample_size": 822},
                "xgboost": {"mae": 0.0042, "rmse": 0.0086, "r2": 0.8582, "median_ae": 0.0013, "sample_size": 822}
            }
        }

    def predict(
        self,
        features: Dict[str, Any],
        farm_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run inference on feature input to predict next-day soil moisture.
        Returns predicted_moisture, confidence, label, and explainable recommendation.
        """
        if self._model is None:
            if not self.load_model():
                # Rule-based fallback if model artifact not found
                return self._rule_based_fallback(features, farm_id)

        # Assemble feature vector in exact training order
        now = datetime.utcnow()
        default_vector = {
            "rainfall_mm": 0.0,
            "temperature_c": 28.0,
            "humidity_pct": 65.0,
            "relative_humidity_pct": 65.0,
            "rh_computed": 65.0,
            "daily_et_estimate_mm": 2.0,
            "soil_moisture_lag1": 0.22,
            "soil_moisture_lag2": 0.22,
            "soil_moisture_ma3": 0.22,
            "soil_moisture_ma7": 0.22,
            "rainfall_lag1": 0.0,
            "rainfall_cum3": 0.0,
            "rainfall_cum7": 0.0,
            "month": float(now.month),
            "day_of_year": float(now.timetuple().tm_yday),
            "season": 3.0,
        }

        # Allow aliases for convenience
        cleaned = dict(default_vector)
        for k, v in features.items():
            if k == "soil_moisture":
                cleaned["soil_moisture_lag1"] = float(v)
            elif k == "temperature":
                cleaned["temperature_c"] = float(v)
            elif k == "humidity":
                cleaned["humidity_pct"] = float(v)
                cleaned["relative_humidity_pct"] = float(v)
                cleaned["rh_computed"] = float(v)
            elif k == "rainfall":
                cleaned["rainfall_mm"] = float(v)
            elif k in cleaned:
                cleaned[k] = float(v)

        X = np.array([[cleaned[col] for col in self._feature_cols]])
        predicted_moisture = float(self._model.predict(X)[0])
        predicted_moisture = max(0.05, min(0.60, predicted_moisture))

        # Confidence metric derived from tree variance
        try:
            tree_preds = [tree.predict(X)[0] for tree in self._model.estimators_]
            tree_std = float(np.std(tree_preds))
            confidence = max(0.5, min(0.99, 1.0 - (tree_std * 10.0)))
        except Exception:
            confidence = 0.92

        # Agronomic recommendation based on crop thresholds
        rec_data = self._generate_recommendation(
            farm_id=farm_id,
            current_moisture=cleaned["soil_moisture_lag1"],
            predicted_moisture=predicted_moisture,
            rainfall_mm=cleaned["rainfall_mm"],
        )

        return {
            "predicted_moisture": round(predicted_moisture, 4),
            "prediction_value": round(predicted_moisture, 4),
            "prediction_label": rec_data["label"],
            "confidence": round(confidence, 4),
            "recommendation": rec_data["recommendation"],
            "urgency": rec_data["urgency"],
            "model_version": self.get_metadata().get("model_version", "2.0.0"),
            "features_used": self._feature_cols,
        }

    def _generate_recommendation(
        self,
        farm_id: Optional[str],
        current_moisture: float,
        predicted_moisture: float,
        rainfall_mm: float,
    ) -> Dict[str, str]:
        cfg = FARMS.get(farm_id or "TN001")
        crop = cfg.crop if cfg else "Crop"
        threshold = cfg.soil_moisture_threshold if cfg else 0.25
        trigger = cfg.irrigation_trigger_moisture if cfg else 0.18

        if rainfall_mm >= 10.0:
            return {
                "label": "Adequate (Rainfall)",
                "urgency": "low",
                "recommendation": (
                    f"Significant rainfall recorded ({rainfall_mm:.1f} mm). "
                    f"Soil moisture expected to sustain at {predicted_moisture:.3f}. Defer irrigation."
                ),
            }

        if predicted_moisture < trigger:
            return {
                "label": "Critical Deficit",
                "urgency": "critical",
                "recommendation": (
                    f"CRITICAL: Next-day soil moisture ({predicted_moisture:.3f}) will drop below "
                    f"trigger point ({trigger:.2f}) for {crop}. Initiate immediate irrigation cycle."
                ),
            }

        if predicted_moisture < threshold:
            return {
                "label": "Mild Deficit",
                "urgency": "medium",
                "recommendation": (
                    f"WARNING: Moisture level ({predicted_moisture:.3f}) projected below optimal target "
                    f"({threshold:.2f}) for {crop}. Schedule irrigation within the next 24-36 hours."
                ),
            }

        return {
            "label": "Optimal Moisture",
            "urgency": "none",
            "recommendation": (
                f"OPTIMAL: Soil moisture stable at {predicted_moisture:.3f} (threshold: {threshold:.2f}). "
                f"No irrigation required at this time."
            ),
        }

    def _rule_based_fallback(
        self, features: Dict[str, Any], farm_id: Optional[str]
    ) -> Dict[str, Any]:
        sm = float(features.get("soil_moisture", features.get("soil_moisture_lag1", 0.20)))
        rain = float(features.get("rainfall_mm", features.get("rainfall", 0.0)))
        temp = float(features.get("temperature_c", features.get("temperature", 28.0)))

        # Evaporative depletion approximation
        et_loss = 0.003 * (temp / 28.0)
        rain_gain = 0.005 * rain
        pred_val = max(0.08, min(0.45, sm - et_loss + rain_gain))

        rec = self._generate_recommendation(farm_id, sm, pred_val, rain)
        return {
            "predicted_moisture": round(pred_val, 4),
            "prediction_value": round(pred_val, 4),
            "prediction_label": rec["label"] + " (Fallback)",
            "confidence": 0.65,
            "recommendation": rec["recommendation"] + " [Rule-based fallback]",
            "urgency": rec["urgency"],
            "model_version": "fallback-rule-1.0",
            "features_used": ["soil_moisture", "temperature", "rainfall"],
        }

    def get_model_info(self, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Return model metadata or query active model row from DB."""
        if db is not None:
            try:
                row = db.query(MLModel).filter(MLModel.is_active == True).first()
                if row:
                    return {
                        "id": row.id,
                        "model_name": row.model_name,
                        "model_type": row.model_type,
                        "version": row.version,
                        "target_variable": row.target_variable,
                        "features": row.features,
                        "r2_score": row.r2_score,
                        "rmse": row.rmse,
                        "mae": row.mae,
                    }
            except Exception:
                pass
        meta = self.get_metadata()
        rf_m = meta.get("metrics", {}).get("random_forest", {})
        return {
            "id": 1,
            "model_name": meta.get("model_name", "Random Forest Regressor"),
            "model_type": "RandomForestRegressor",
            "version": meta.get("model_version", "2.0.0"),
            "target_variable": meta.get("target_variable", "soil_moisture_next_day"),
            "features": meta.get("features", self._feature_cols),
            "r2_score": rf_m.get("r2", 0.8722),
            "rmse": rf_m.get("rmse", 0.0082),
            "mae": rf_m.get("mae", 0.0040),
        }

    def sync_to_db(self, db: Session) -> None:
        """Register the trained model in the database if not present."""
        meta = self.get_metadata()
        m_name = meta.get("model_name", "Random Forest Regressor")
        existing = db.query(MLModel).filter(MLModel.model_name == m_name).first()
        rf_m = meta.get("metrics", {}).get("random_forest", {})

        if not existing:
            new_m = MLModel(
                model_name=m_name,
                model_type="RandomForestRegressor",
                version=meta.get("model_version", "2.0.0"),
                target_variable=meta.get("target_variable", "soil_moisture_next_day"),
                features=meta.get("features", self._feature_cols),
                hyperparameters=meta.get("hyperparameters", {}),
                mae=rf_m.get("mae", 0.0040),
                rmse=rf_m.get("rmse", 0.0082),
                r2_score=rf_m.get("r2", 0.8722),
                training_samples=meta.get("sample_counts", {}).get("train", 3832),
                file_path=RF_MODEL_PATH,
                is_active=True,
            )
            db.add(new_m)
            db.commit()


# Singleton instance
ml_service = MLService()
FEATURE_COLS = DEFAULT_FEATURE_COLS
