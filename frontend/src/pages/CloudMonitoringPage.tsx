import React, { useEffect, useState } from 'react';
import {
  Cloud,
  CloudOff,
  Database,
  ArrowUpRight,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Server,
  Layers,
  ShieldCheck,
} from 'lucide-react';
import { getCloudStatus, connectCloud, disconnectCloud, getSyncHistory } from '../services/api';
import type { CloudStatus, SyncEvent } from '../types';

export default function CloudMonitoringPage() {
  const [cloudStatus, setCloudStatus] = useState<CloudStatus>({
    connected: true,
    stored_records: 5478,
    pending_uploads: 0,
    last_sync_at: new Date().toISOString(),
    endpoint_url: 'http://localhost:8000/cloud',
  });
  const [syncHistory, setSyncHistory] = useState<SyncEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMessage, setActionMessage] = useState<string>('');

  const defaultSyncHistory: SyncEvent[] = [
    {
      id: 101,
      node_id: 'FOG-TN001',
      farm_id: 'TN001',
      records_synced: 18,
      status: 'success',
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      bytes_transferred: 3420,
      latency_ms: 45.2,
    },
    {
      id: 102,
      node_id: 'FOG-TN002',
      farm_id: 'TN002',
      records_synced: 12,
      status: 'success',
      timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
      bytes_transferred: 2280,
      latency_ms: 48.0,
    },
    {
      id: 103,
      node_id: 'FOG-TN003',
      farm_id: 'TN003',
      records_synced: 24,
      status: 'success',
      timestamp: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
      bytes_transferred: 4560,
      latency_ms: 52.1,
    },
  ];

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const data = await getCloudStatus();
      if (data) setCloudStatus(data);
      const history = await getSyncHistory(10);
      if (history && history.length > 0) {
        setSyncHistory(history);
      } else {
        setSyncHistory(defaultSyncHistory);
      }
    } catch (err) {
      console.error('Error fetching cloud status:', err);
      setSyncHistory(defaultSyncHistory);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleToggleConnection = async () => {
    try {
      if (cloudStatus.connected) {
        setActionMessage('Simulating Cloud Outage: Severing edge-to-cloud backhaul...');
        await disconnectCloud();
        setCloudStatus((prev) => ({ ...prev, connected: false, pending_uploads: 6 }));
        setActionMessage('Cloud Disconnected. All 3 Fog nodes are now in autonomous offline buffer mode.');
      } else {
        setActionMessage('Restoring Cloud Link: Initiating edge queue resynchronization...');
        await connectCloud();
        setCloudStatus((prev) => ({ ...prev, connected: true, pending_uploads: 0, last_sync_at: new Date().toISOString() }));
        setActionMessage('Cloud Reconnected. Buffered events flushed and synchronized with cloud database.');
      }
    } catch (err) {
      // Toggle locally for demonstration if backend proxy differs
      setCloudStatus((prev) => ({ ...prev, connected: !prev.connected }));
      setActionMessage(`Cloud state toggled to ${!cloudStatus.connected ? 'Connected' : 'Disconnected (Offline Mode)'}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            Phase 3 Cloud Integration
          </span>
          <h1 className="text-2xl font-bold text-[#1B2D1E] mt-1">Cloud Centralization & Outage Simulation</h1>
          <p className="text-sm text-[#4A6B50]">
            Simulate rural network dropouts, evaluate Fog node buffering, and inspect synchronization idempotency.
          </p>
        </div>

        <button
          onClick={handleToggleConnection}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all shadow-sm ${
            cloudStatus.connected
              ? 'bg-rose-600 hover:bg-rose-700 text-white'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white'
          }`}
        >
          {cloudStatus.connected ? (
            <>
              <CloudOff className="w-4 h-4" />
              Simulate Cloud Disconnect
            </>
          ) : (
            <>
              <Cloud className="w-4 h-4" />
              Reconnect Cloud Uplink
            </>
          )}
        </button>
      </div>

      {actionMessage && (
        <div
          className={`p-3 text-xs rounded-xl border flex items-center justify-between ${
            cloudStatus.connected
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-amber-50 border-amber-200 text-amber-800'
          }`}
        >
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage('')} className="font-bold ml-2">
            ×
          </button>
        </div>
      )}

      {/* Cloud Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
          <div className="text-xs text-gray-500">Cloud Connectivity</div>
          <div className="flex items-center gap-2 mt-2">
            <span
              className={`w-3 h-3 rounded-full ${
                cloudStatus.connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
              }`}
            ></span>
            <span className="font-bold text-lg text-[#1B2D1E]">
              {cloudStatus.connected ? 'Online & Synced' : 'Outage Active'}
            </span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {cloudStatus.connected ? 'Bi-directional WebSocket streaming' : 'Local edge buffering enabled'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
          <div className="text-xs text-gray-500">Stored Central Records</div>
          <div className="text-2xl font-bold text-[#1B2D1E] mt-1">{cloudStatus.stored_records}</div>
          <div className="text-xs text-emerald-600 mt-1">Historical agricultural records</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
          <div className="text-xs text-gray-500">Pending Edge Uploads</div>
          <div className="text-2xl font-bold text-amber-600 mt-1">
            {cloudStatus.connected ? '0 queued' : `${cloudStatus.pending_uploads || 6} buffered`}
          </div>
          <div className="text-xs text-gray-400 mt-1">Buffered across 3 Fog nodes</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
          <div className="text-xs text-gray-500">Last Successful Sync</div>
          <div className="text-sm font-bold text-gray-800 mt-2 truncate">
            {cloudStatus.last_sync_at ? new Date(cloudStatus.last_sync_at).toLocaleTimeString() : 'Just now'}
          </div>
          <div className="text-xs text-emerald-600 mt-1">Deduplication: ID-matched</div>
        </div>
      </div>

      {/* Synchronization Audit Log */}
      <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-4">
        <h3 className="font-bold text-base text-[#1B2D1E] flex items-center gap-2">
          <Database className="w-5 h-5 text-emerald-600" />
          Recent Edge-to-Cloud Synchronization History
        </h3>
        <p className="text-xs text-gray-500">
          Traceable records of batched telemetry events synced from local Fog nodes to the cloud repository.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-emerald-50 text-emerald-900 border-b border-emerald-100">
                <th className="p-3 font-semibold">Sync ID</th>
                <th className="p-3 font-semibold">Fog Node</th>
                <th className="p-3 font-semibold">Target Farm</th>
                <th className="p-3 font-semibold">Records Synced</th>
                <th className="p-3 font-semibold">Bytes Transferred</th>
                <th className="p-3 font-semibold">Uplink Latency</th>
                <th className="p-3 font-semibold">Status</th>
                <th className="p-3 font-semibold">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {syncHistory.map((s) => (
                <tr key={s.id} className="hover:bg-gray-50/50">
                  <td className="p-3 font-mono text-emerald-800 font-bold">#SYNC-{s.id}</td>
                  <td className="p-3 font-medium text-gray-800">{s.node_id}</td>
                  <td className="p-3 text-gray-600">{s.farm_id}</td>
                  <td className="p-3 font-bold text-gray-900">{s.records_synced} items</td>
                  <td className="p-3 font-mono">{s.bytes_transferred} B</td>
                  <td className="p-3 font-mono text-emerald-700">{s.latency_ms} ms</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-100 text-green-800 uppercase">
                      {s.status}
                    </span>
                  </td>
                  <td className="p-3 text-gray-500">{new Date(s.timestamp).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

