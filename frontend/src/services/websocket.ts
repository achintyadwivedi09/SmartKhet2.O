import { useEffect, useRef, useCallback } from 'react';
import type { WSMessage } from '../types';

type MessageHandler = (msg: WSMessage) => void;

const WS_URL = 'ws://localhost:8000/ws';
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT = 10;

class WebSocketManager {
  private ws: WebSocket | null = null;
  private handlers = new Set<MessageHandler>();
  private reconnectCount = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;
    try {
      this.ws = new WebSocket(WS_URL);
      this.ws.onopen = () => {
        console.log('[WS] Connected');
        this.reconnectCount = 0;
      };
      this.ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data) as WSMessage;
          this.handlers.forEach(h => h(msg));
        } catch {
          // ignore malformed messages
        }
      };
      this.ws.onclose = () => {
        console.log('[WS] Disconnected');
        if (this.shouldReconnect && this.reconnectCount < MAX_RECONNECT) {
          this.reconnectCount++;
          this.reconnectTimer = setTimeout(() => this.connect(), RECONNECT_DELAY_MS);
        }
      };
      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      // ignore connection errors — backend may not be running
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  subscribe(handler: MessageHandler) {
    this.handlers.add(handler);
  }

  unsubscribe(handler: MessageHandler) {
    this.handlers.delete(handler);
  }

  get readyState() {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

// Singleton shared across the app
export const wsManager = new WebSocketManager();

export default wsManager;
