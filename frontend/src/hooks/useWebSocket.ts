import { useEffect, useRef, useState } from 'react';

interface WebSocketHook {
  lastMessage: string | null;
  readyState: number;
  sendMessage: (message: string) => void;
}

export const useWebSocket = (url: string): WebSocketHook => {
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setReadyState(WebSocket.OPEN);
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setReadyState(WebSocket.CLOSED);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setReadyState(WebSocket.CLOSED);
    };

    ws.current.onmessage = (event) => {
      setLastMessage(event.data);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  const sendMessage = (message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(message);
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  return {
    lastMessage,
    readyState,
    sendMessage
  };
}; 