type MessageHandler = (data: any) => void;

class WebSocketManager {
  private ws: WebSocket | null = null;
  private listeners = new Map<string, Set<MessageHandler>>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private token: string | null = null;

  connect(token: string) {
    this.token = token;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.ws = new WebSocket(`${protocol}//${host}/ws?token=${token}`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'subscribe' || message.type === 'unsubscribe') return;
        const listeners = this.listeners.get(message.job_id);
        if (listeners) {
          listeners.forEach(cb => cb(message));
        }
      } catch { /* ignore parse errors */ }
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts && this.token) {
        const delay = 1000 * Math.pow(2, this.reconnectAttempts);
        setTimeout(() => {
          this.reconnectAttempts++;
          if (this.token) this.connect(this.token);
        }, delay);
      }
    };
  }

  disconnect() {
    this.token = null;
    this.ws?.close();
    this.ws = null;
  }

  subscribe(jobId: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'subscribe', job_id: jobId }));
    }
  }

  unsubscribe(jobId: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'unsubscribe', job_id: jobId }));
    }
  }

  addListener(jobId: string, callback: MessageHandler) {
    if (!this.listeners.has(jobId)) {
      this.listeners.set(jobId, new Set());
    }
    this.listeners.get(jobId)!.add(callback);
  }

  removeListener(jobId: string, callback: MessageHandler) {
    this.listeners.get(jobId)?.delete(callback);
  }

  get connected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsManager = new WebSocketManager();
