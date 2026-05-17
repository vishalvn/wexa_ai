/**
 * Custom React hook for WebSocket connection.
 * Handles connection, reconnection, and message routing.
 */
'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from './store';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout>();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const connect = useCallback(() => {
    if (!user?.organization?.id) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const token = localStorage.getItem('access_token');
    const ws = new WebSocket(`${WS_URL}/${user.organization.id}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WS] Connected');
      // Start heartbeat ping every 30s
      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping');
      }, 30000);
      (ws as any)._pingInterval = ping;
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleMessage(message);
      } catch {
        // pong response — ignore
      }
    };

    ws.onclose = () => {
      console.log('[WS] Disconnected, reconnecting in 3s...');
      clearInterval((ws as any)._pingInterval);
      reconnectTimerRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = (error) => {
      console.error('[WS] Error:', error);
      ws.close();
    };
  }, [user?.organization?.id]);

  const handleMessage = useCallback((message: { type: string; data: any }) => {
    switch (message.type) {
      case 'new_event':
        // Invalidate event queries so charts auto-refresh
        queryClient.invalidateQueries({ queryKey: ['events'] });
        break;

      case 'alert_triggered':
        // Invalidate alert queries to show new notification
        queryClient.invalidateQueries({ queryKey: ['alerts'] });
        // TODO: show toast notification
        break;

      case 'dashboard_refresh':
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        break;
    }
  }, [queryClient]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { isConnected: wsRef.current?.readyState === WebSocket.OPEN };
}
