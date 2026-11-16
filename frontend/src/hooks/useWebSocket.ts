import { useEffect, useState, useCallback } from 'react';
import { wsManager } from '../services/websocket';
import type { WSMessage, WSMessageType } from '../types';

interface UseWebSocketOptions {
  onMessage?: (msg: WSMessage) => void;
  filter?: WSMessageType | WSMessageType[];
}

export function useWebSocket(options?: UseWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const handleMessage = useCallback((msg: WSMessage) => {
    const { filter, onMessage } = options ?? {};
    if (filter) {
      const types = Array.isArray(filter) ? filter : [filter];
      if (!types.includes(msg.type)) return;
    }
    setLastMessage(msg);
    onMessage?.(msg);
  }, [options]);

  useEffect(() => {
    wsManager.connect();
    wsManager.subscribe(handleMessage);

    // Poll connection state
    const interval = setInterval(() => {
      setConnected(wsManager.readyState === WebSocket.OPEN);
    }, 1000);

    return () => {
      wsManager.unsubscribe(handleMessage);
      clearInterval(interval);
    };
  }, [handleMessage]);

  return { connected, lastMessage };
}

export default useWebSocket;
