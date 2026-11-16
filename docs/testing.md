# SmartKhet 2.0: Automated Testing Strategy & Test Plan

## 1. Test Architecture

SmartKhet 2.0 uses `pytest` for automated test execution across 5 dedicated test suites in `tests/`:

- `tests/data/test_data_pipeline.py`: Validates NetCDF parsing, interpolation limits, unit standardization, and feature engineering.
- `tests/ml/test_ml_model.py`: Checks target leakage, chronological train/test separation, prediction ranges, and model serialization.
- `tests/fog/test_fog_nodes.py`: Evaluates edge node autonomy, local ML execution, event buffering during cloud outages, and sync flushing.
- `tests/backend/test_api.py`: Tests FastAPI REST routes, Pydantic schemas, and WebSocket feeds.
- `tests/integration/test_full_pipeline.py`: End-to-end integration from raw records to Fog actuation and audit export.

---

## 2. Test Execution Command

Run all tests from the project root:
```powershell
python -m pytest tests/ -v
```

---

## 3. Quality Assurance Standards

1. **Deterministic Reproducibility:** Fixed random seeds (`seed=42`) for train/test splits.
2. **Zero Mocked Evaluations:** Metric calculations (MAE, RMSE, R²) run against actual holdout test samples.
3. **Fault Injection:** Cloud disconnection tests programmatically sever sockets and verify edge decision continuity.

