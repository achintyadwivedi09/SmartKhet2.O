import { useState, useEffect } from 'react';
import { useApi } from './useApi';
import { getFogNodes } from '../services/api';
import { wsManager } from '../services/websocket';
import type { FogNode, WSMessage } from '../types';

export function useFogNodes() {
  const { data, loading, error, refetch } = useApi<FogNode[]>(
    () => getFogNodes(),
    [],
    { pollMs: 10000 }
  );
  const [nodes, setNodes] = useState<FogNode[]>([]);

  useEffect(() => {
    if (data) setNodes(data);
  }, [data]);

  useEffect(() => {
    wsManager.connect();
    const handler = (msg: WSMessage) => {
      if (msg.type === 'fog_status_update') {
        const updated = msg.payload as FogNode;
        setNodes(prev =>
          prev.map(n => n.node_id === updated.node_id ? { ...n, ...updated } : n)
        );
      }
    };
    wsManager.subscribe(handler);
    return () => wsManager.unsubscribe(handler);
  }, []);

  return { nodes, loading, error, refetch };
}

export default useFogNodes;
