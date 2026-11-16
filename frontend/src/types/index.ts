// ============================================================
// SmartKhet 2.0 — TypeScript Type Definitions
// ============================================================

// ─── Farm & Sensor Data ───────────────────────────────────────
export interface Farm {
  farm_id: string;        // e.g. "TN001"
  name: string;
  location: string;
  crop: string;
  latitude: number;
  longitude: number;
  area_ha: number;
  fog_node_id: string;
  created_at: string;
}

export interface DataRecord {
  id: number;
  farm_id: string;
  date: string;           // ISO date string
  rainfall_mm: number;
  soil_moisture: number;  // 0–1
  temperature_c: number;
  humidity_pct: number;
  source: string;         // "IMD" | "NASA POWER" | "ICAR" | "OpenWeather"
  is_predicted?: boolean;
}

// ─── Big Data / Pipeline ─────────────────────────────────────
export interface Dataset {
  id: string;
  name: string;
  source: string;
  format: string;
  records: number;
  status: 'downloaded' | 'documented' | 'processing' | 'error';
  downloaded_at?: string;
  description: string;
  url?: string;
  features: string[];
}

export interface DatasetRegistry {
  datasets: Dataset[];
  total_records: number;
  pipeline_version: string;
  last_updated: string;
}

export interface PipelineStats {
  total_records: number;
  missing_before: number;
  missing_after: number;
  duplicates_removed: number;
  features_engineered: number;
  stages_complete: number;
  processing_log: string[];
}

// ─── ML Models ───────────────────────────────────────────────
export interface ModelMetrics {
  mae: number;
  rmse: number;
  r2: number;
  median_ae: number;
  train_size: number;
  val_size: number;
  test_size: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ActualVsPredicted {
  actual: number;
  predicted: number;
  date?: string;
}

export interface MLModel {
  model_id: string;
  name: string;
  algorithm: string;      // "RandomForest" | "XGBoost" | "Baseline"
  version: string;
  trained_at: string;
  metrics: ModelMetrics;
  feature_importances: FeatureImportance[];
  is_active: boolean;
  description: string;
}

export interface Prediction {
  id: number;
  farm_id: string;
  model_id: string;
  predicted_date: string;
  predicted_moisture: number;
  recommendation: string;
  confidence: number;
  created_at: string;
  source: 'fog' | 'cloud';
}

// ─── Fog Computing ───────────────────────────────────────────
export interface FogNode {
  node_id: string;
  farm_id: string;
  farm_name: string;
  is_online: boolean;
  model_version: string;
  last_inference_at: string;
  inference_latency_ms: number;
  local_decisions_count: number;
  pending_sync_count: number;
  event_queue_depth: number;
  recent_recommendation: string;
  uptime_pct: number;
  cpu_usage_pct: number;
  memory_usage_pct: number;
}

export interface FogEvent {
  id: number;
  node_id: string;
  farm_id: string;
  event_type: string;
  details: string;
  timestamp: string;
  synced: boolean;
  latency_ms?: number;
}

export interface FogInferenceResult {
  farm_id: string;
  node_id: string;
  predicted_moisture: number;
  recommendation: string;
  confidence: number;
  latency_ms: number;
  timestamp: string;
  source: 'fog_local';
}

// ─── Cloud ───────────────────────────────────────────────────
export interface CloudStatus {
  connected: boolean;
  stored_records: number;
  pending_uploads: number;
  last_sync_at: string | null;
  endpoint_url: string;
}

export interface SyncEvent {
  id: number;
  node_id: string;
  farm_id: string;
  records_synced: number;
  status: 'success' | 'failed' | 'partial';
  timestamp: string;
  bytes_transferred: number;
  latency_ms: number;
}

// ─── Audit ───────────────────────────────────────────────────
export interface AuditLog {
  id: number;
  timestamp: string;
  event_type: string;
  farm_id: string | null;
  dataset_id: string | null;
  model_id: string | null;
  node_id: string | null;
  action: string;
  status: 'success' | 'failure' | 'warning';
  user: string;
  details: string;
  records_affected: number;
  duration_ms: number;
  ip_address: string;
  session_id: string;
  version: string;
  environment: string;
  source: string;
  error_code: string | null;
  checksum: string | null;
  parent_event_id: number | null;
}

export type AuditFilters = {
  start_date?: string;
  end_date?: string;
  event_type?: string;
  farm_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
};

// ─── Experiments ─────────────────────────────────────────────
export interface ExperimentConfig {
  mode: 'fog_first' | 'cloud_only';
  network_delay_ms: number;
  packet_loss_pct: number;
  num_records: number;
}

export interface ExperimentResult {
  experiment_id: string;
  config: ExperimentConfig;
  avg_latency_ms: number;
  median_latency_ms: number;
  p95_latency_ms: number;
  success_rate: number;
  bytes_transmitted: number;
  network_messages: number;
  decisions_during_outage: number;
  fog_latency_ms?: number;
  cloud_latency_ms?: number;
  timestamp: string;
  status: 'running' | 'completed' | 'paused' | 'failed';
  progress_pct?: number;
  latency_series?: Array<{ t: number; latency: number }>;
}

// ─── WebSocket ───────────────────────────────────────────────
export type WSMessageType =
  | 'fog_status_update'
  | 'inference_result'
  | 'cloud_sync'
  | 'experiment_progress'
  | 'alert';

export interface WSMessage {
  type: WSMessageType;
  payload: unknown;
  timestamp: string;
}

// ─── API Response Wrappers ────────────────────────────────────
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ─── Analytics ───────────────────────────────────────────────
export interface AnalyticsOverview {
  farms_count: number;
  active_datasets: number;
  fog_nodes_online: number;
  fog_nodes_total: number;
  active_model: string;
  pending_syncs: number;
  model_metrics: ModelMetrics;
  last_updated: string;
}
