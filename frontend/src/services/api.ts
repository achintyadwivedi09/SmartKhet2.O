import axios from 'axios';
import type {
  Farm, DataRecord, Dataset, DatasetRegistry, PipelineStats,
  MLModel, ModelMetrics, Prediction, ActualVsPredicted,
  FogNode, FogEvent, FogInferenceResult,
  CloudStatus, SyncEvent,
  AuditLog, AuditFilters,
  ExperimentConfig, ExperimentResult,
  AnalyticsOverview,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Error handling ───────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('[API Error]', err.response?.data ?? err.message);
    return Promise.reject(err);
  }
);

// ─── Farms ───────────────────────────────────────────────────
export const getFarms = () => api.get<Farm[]>('/farms').then(r => r.data);
export const getFarm = (id: string) => api.get<Farm>(`/farms/${id}`).then(r => r.data);
export const getFarmData = (id: string, start?: string, end?: string) =>
  api.get<DataRecord[]>(`/farms/${id}/data`, { params: { start, end } }).then(r => r.data);
export const getFarmPredictions = (id: string) =>
  api.get<Prediction[]>(`/farms/${id}/predictions`).then(r => r.data);

// ─── Datasets / Big Data ─────────────────────────────────────
export const getDatasets = () => api.get<Dataset[]>('/datasets').then(r => r.data);
export const getDatasetRegistry = () => api.get<DatasetRegistry>('/datasets/registry').then(r => r.data);
export const getPipelineStats = () => api.get<PipelineStats>('/datasets/pipeline-stats').then(r => r.data);

// ─── ML Models ───────────────────────────────────────────────
export const getMLModels = () => api.get<MLModel[]>('/ml/models').then(r => r.data);
export const getModelMetrics = (id: string) => api.get<ModelMetrics>(`/ml/models/${id}/metrics`).then(r => r.data);
export const getActualVsPredicted = (id: string) =>
  api.get<ActualVsPredicted[]>(`/ml/models/${id}/actual-vs-predicted`).then(r => r.data);
export const predictForFarm = (farmId: string) =>
  api.post<Prediction>(`/ml/predict/farm/${farmId}`).then(r => r.data);
export const runPrediction = (features: Record<string, number>) =>
  api.post<Prediction>('/ml/predict', { features }).then(r => r.data);

// ─── Fog Nodes ────────────────────────────────────────────────
export const getFogNodes = () => api.get<FogNode[]>('/fog/nodes').then(r => r.data);
export const getFogNode = (id: string) => api.get<FogNode>(`/fog/nodes/${id}`).then(r => r.data);
export const runFogInference = (farmId: string, features?: Record<string, number>) =>
  api.post<FogInferenceResult>(`/fog/infer/${farmId}`, { features }).then(r => r.data);
export const getFogEvents = (params?: { limit?: number; node_id?: string }) =>
  api.get<FogEvent[]>('/fog/events', { params }).then(r => r.data);
export const syncFog = () => api.post('/fog/sync').then(r => r.data);

// ─── Cloud ───────────────────────────────────────────────────
export const getCloudStatus = () => api.get<CloudStatus>('/cloud/status').then(r => r.data);
export const connectCloud = () => api.post('/cloud/connect').then(r => r.data);
export const disconnectCloud = () => api.post('/cloud/disconnect').then(r => r.data);
export const getCloudRecords = () => api.get('/cloud/records').then(r => r.data);
export const getSyncHistory = (limit = 20) =>
  api.get<SyncEvent[]>('/cloud/sync-history', { params: { limit } }).then(r => r.data);

// ─── Audit ────────────────────────────────────────────────────
export const getAuditLogs = (filters?: AuditFilters) =>
  api.get<AuditLog[]>('/audit/logs', { params: filters }).then(r => r.data);
export const exportAuditCSV = async () => {
  const res = await api.get('/audit/export', { responseType: 'blob' });
  const url = URL.createObjectURL(res.data);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'smartkhet_audit_log.csv';
  a.click();
  URL.revokeObjectURL(url);
};
export const getAuditStats = () => api.get('/audit/stats').then(r => r.data);

// ─── Analytics ───────────────────────────────────────────────
export const getAnalyticsOverview = () =>
  api.get<AnalyticsOverview>('/analytics/overview').then(r => r.data);
export const getRainfallData = (days = 30) =>
  api.get<DataRecord[]>('/analytics/rainfall', { params: { days } }).then(r => r.data);
export const getSoilMoistureData = (days = 30) =>
  api.get<DataRecord[]>('/analytics/soil-moisture', { params: { days } }).then(r => r.data);
export const getTemperatureData = (days = 30) =>
  api.get<DataRecord[]>('/analytics/temperature', { params: { days } }).then(r => r.data);

// ─── Experiments ─────────────────────────────────────────────
export const runExperiment = (config: ExperimentConfig) =>
  api.post<ExperimentResult>('/experiments/run', config).then(r => r.data);
export const getExperiment = (id: string) =>
  api.get<ExperimentResult>(`/experiments/${id}`).then(r => r.data);
export const pauseExperiment = (id: string) =>
  api.post(`/experiments/${id}/pause`).then(r => r.data);
export const resetExperiment = (id: string) =>
  api.post(`/experiments/${id}/reset`).then(r => r.data);
export const compareExperiments = () =>
  api.get<ExperimentResult[]>('/experiments/compare').then(r => r.data);

export default api;
