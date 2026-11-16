"""
SmartKhet 2.0 — Experiments API Routes
Track and compare ML experiment runs.
"""
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.db_models import ExperimentRun
from models.schemas import ExperimentRunCreate, ExperimentRunResponse
import os
from app.config import PROJECT_ROOT, FEATURE_LIST_PATH
from services.audit_service import audit_service
from services.ml_service import ml_service, FEATURE_COLS
import pandas as pd

import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

router = APIRouter()


@router.get("/", response_model=List[ExperimentRunResponse])
def list_experiments(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return (
        db.query(ExperimentRun)
        .order_by(ExperimentRun.started_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{experiment_id}", response_model=ExperimentRunResponse)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.query(ExperimentRun).filter(ExperimentRun.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.post("/", response_model=ExperimentRunResponse, status_code=201)
def create_experiment(payload: ExperimentRunCreate, db: Session = Depends(get_db)):
    """Register a new experiment run record (without running training)."""
    exp = ExperimentRun(**payload.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.post("/run-quick")
def run_quick_experiment(
    model_type: str = "RandomForest",
    n_estimators: int = 50,
    max_depth: int = 8,
    dataset_size: int = 1000,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Run a quick ML experiment with the specified model type and hyperparameters.
    Uses synthetic demo data only.
    Supported model_type: RandomForest, GradientBoosting
    """
    allowed_types = {"RandomForest", "GradientBoosting"}
    if model_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"model_type must be one of {allowed_types}",
        )

    exp = ExperimentRun(
        experiment_name=f"{model_type} quick-run n={n_estimators} depth={max_depth}",
        description="Quick experiment using synthetic demo data.",
        model_type=model_type,
        hyperparameters={"n_estimators": n_estimators, "max_depth": max_depth},
        dataset_size=dataset_size,
        features_used=FEATURE_COLS,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    try:
        csv_file = os.path.join(PROJECT_ROOT, "data", "processed", "ml_ready_dataset.csv")
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            cols = [c for c in FEATURE_COLS if c in df.columns]
            sample_df = df.sample(n=min(len(df), dataset_size), random_state=42)
            X = sample_df[cols].values
            y = sample_df["soil_moisture_next_day"].values
        else:
            rng = np.random.default_rng(42)
            X = rng.uniform(0.1, 0.4, (dataset_size, len(FEATURE_COLS)))
            y = X[:, 0] * 0.95 + rng.normal(0, 0.01, dataset_size)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        t0 = time.time()
        if model_type == "RandomForest":
            model = RandomForestRegressor(
                n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1
            )
        else:
            model = GradientBoostingRegressor(
                n_estimators=n_estimators, max_depth=max_depth, random_state=42
            )
        model.fit(X_train, y_train)
        training_time = time.time() - t0

        y_pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2 = float(r2_score(y_test, y_pred))
        mae = float(mean_absolute_error(y_test, y_pred))

        exp.accuracy = round(r2, 4)
        exp.rmse = round(rmse, 4)
        exp.r2_score = round(r2, 4)
        exp.mae = round(mae, 4)
        exp.training_time_seconds = round(training_time, 2)
        exp.status = "completed"
        exp.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(exp)

        audit_service.log_event(
            db,
            action="experiment.run",
            resource_type="ExperimentRun",
            resource_id=str(exp.id),
            details={"model_type": model_type, "r2": r2},
        )

    except Exception as e:
        exp.status = "failed"
        exp.notes = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Experiment failed: {e}")

    return ExperimentRunResponse.model_validate(exp)


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.query(ExperimentRun).filter(ExperimentRun.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.delete(exp)
    db.commit()
    return {"status": "deleted", "experiment_id": experiment_id}
