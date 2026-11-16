# SmartKhet 2.0: Permanent Audit & Traceability System

## 1. Audit Principles

SmartKhet 2.0 implements an immutable, append-only audit trail recording every significant lifecycle event.

The primary audit log is stored in SQLite table `audit_logs` and exported chronologically to:
`docs/SMARTKHET_PROJECT_AUDIT_LOG.csv`

---

## 2. The 20 Mandatory Audit Schema Columns

1. `Audit_ID`: Unique integer identifier.
2. `UTC_Timestamp`: ISO 8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SS.fffZ`).
3. `Event_Type`: High-level operational category (`SYSTEM_STARTUP`, `FEATURE_ENGINEERING`, `MODEL_TRAINING`, `EDGE_INFERENCE`, `SYNC_EVENT`, `OUTAGE_DETECTED`).
4. `Event_Category`: Component group (`DATA`, `ML`, `FOG`, `CLOUD`, `SECURITY`).
5. `Actor`: Initiating process or user (`pipeline_worker`, `fog_runtime`, `coordinator`).
6. `Farm_ID`: Associated farm code (`TN001`, `TN002`, `TN003`, or `ALL`).
7. `Fog_Node_ID`: Associated edge node (`FOG-TN001` or `N/A`).
8. `Dataset_ID`: Associated dataset identifier (`IMD_RF_001`, `ml_ready_v2`).
9. `Source_Record_ID`: Primary key or reference in underlying table.
10. `Model_Version`: Model artifact version in memory (`rf-v2.0`).
11. `Previous_State`: State before operation (`UNINITIALIZED`, `CONNECTED`, `TRAINING`).
12. `New_State`: State after operation (`ACTIVE`, `DISCONNECTED`, `COMPLETED`).
13. `Operation_Details`: Human-readable summary of executed logic.
14. `Input_Summary`: Brief summary of input parameters or feature vector.
15. `Output_Summary`: Summary of output prediction or decision.
16. `Processing_Duration_MS`: Actual software execution time in milliseconds.
17. `Cloud_Status`: State of central cloud link at time of event (`CONNECTED` or `OFFLINE`).
18. `Synchronization_Status`: State of event sync (`SYNCED`, `BUFFERED_EDGE`, `N/A`).
19. `Success_Failure`: Binary outcome status (`SUCCESS`, `WARNING`, `FAILURE`).
20. `Error_Details`: Stack trace or exception description if applicable.

---

## 3. CSV Export Procedure

The audit ledger can be exported on-demand via:
- **CLI / Python:** `python -c "from services.audit_service import audit_service; audit_service.export_csv()"`
- **HTTP API:** `GET /audit/export`
- **Dashboard UI:** Click "Export Audit Log (CSV)" on the Data Audit page.

