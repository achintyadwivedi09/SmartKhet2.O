"""
SmartKhet 2.0 — ML API Routes
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.db_models import MLModel, Prediction
from models.schemas import MLModelResponse, PredictionRequest, PredictionResponse
from services.ml_service import ml_service
from services.audit_service import audit_service

router = APIRouter()


@router.get("/model", response_model=Optional[Dict[str, Any]])
def get_model_info(db: Session = Depends(get_db)):
    """Return metadata for the currently active ML model."""
    info = ml_service.get_model_info(db)
    if not info:
        return {"status": "no model trained yet"}
    return info


@router.get("/models", response_model=List[MLModelResponse])
def list_models(db: Session = Depends(get_db)):
    """Return all ML model records (active and historical)."""
    return db.query(MLModel).order_by(MLModel.trained_at.desc()).all()


@router.post("/train")
def train_model(db: Session = Depends(get_db)):
    """
    Train the RandomForest demo model on synthetic data.
    Returns training metrics. Safe to call multiple times.
    """
    result = ml_service.train_demo_model(db)
    audit_service.log_event(
        db,
        action="ml.train",
        resource_type="MLModel",
        resource_id=str(result.get("db_model_id")),
        details={
            "r2_score": result.get("r2_score"),
            "rmse": result.get("rmse"),
            "training_samples": result.get("training_samples"),
        },
    )
    return result


@router.post("/predict", response_model=Dict[str, Any])
def predict(payload: PredictionRequest, db: Session = Depends(get_db)):
    """
    Run ML inference on the provided feature set.
    Returns yield index prediction, label, confidence, and recommendation.
    """
    features = payload.model_dump(exclude={"farm_id"})
    try:
        result = ml_service.predict(features, payload.farm_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Persist prediction
    ml_info = ml_service.get_model_info(db)
    pred = Prediction(
        farm_id=payload.farm_id,
        model_id=ml_info["id"] if ml_info else None,
        input_features=features,
        prediction_value=result["prediction_value"],
        prediction_label=result["prediction_label"],
        confidence=result["confidence"],
        recommendation=result["recommendation"],
        source="api",
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)

    audit_service.log_event(
        db,
        action="ml.predict",
        resource_type="Prediction",
        resource_id=str(pred.id),
        details={"farm_id": payload.farm_id, "label": result["prediction_label"]},
    )

    return {**result, "prediction_id": pred.id, "farm_id": payload.farm_id}


@router.get("/predictions", response_model=List[Dict[str, Any]])
def list_predictions(
    farm_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return recent ML predictions."""
    query = db.query(Prediction)
    if farm_id:
        query = query.filter(Prediction.farm_id == farm_id)
    rows = query.order_by(Prediction.predicted_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "farm_id": r.farm_id,
            "predicted_at": r.predicted_at.isoformat(),
            "prediction_value": r.prediction_value,
            "prediction_label": r.prediction_label,
            "confidence": r.confidence,
            "recommendation": r.recommendation,
            "source": r.source,
        }
        for r in rows
    ]
