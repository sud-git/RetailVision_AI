/**
 * RetailVision AI - PHASE 6 Custom Hooks
 * React hooks for WebSocket, API, and state management
 */

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { WebSocketEvent } from '@/types';
import { getWebSocketClient } from '@/lib/websocket';
import { getAPIClient } from '@/lib/api';

/**
 * Hook for WebSocket connection and event handling
 */
export function useWebSocket(channels: string[] = []) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const wsRef = useRef(getWebSocketClient());

  useEffect(() => {
    const ws = wsRef.current;

    // Status handler
    const handleStatus = (status: string) => {
      setConnected(status === 'connected');
      setError(status === 'error' ? 'WebSocket connection error' : null);
    };

    // Event handler
    const handleEvent = (event: WebSocketEvent) => {
      setEvents((prev) => {
        // Keep last 100 events
        const updated = [event, ...prev].slice(0, 100);
        return updated;
      });
    };

    ws.onStatusChange(handleStatus);
    ws.onEvent(handleEvent);

    // Subscribe to channels
    channels.forEach((channel) => {
      ws.subscribe(channel);
    });

    // Connect if not already connected
    if (!ws.isConnected()) {
      ws.connect().catch((err) => {
        console.error('WebSocket connection failed:', err);
        setError('Failed to connect to WebSocket');
      });
    }

    return () => {
      // Unsubscribe on unmount
      channels.forEach((channel) => {
        ws.unsubscribe(channel);
      });
    };
  }, [channels]);

  const subscribe = useCallback((channel: string) => {
    wsRef.current.subscribe(channel);
  }, []);

  const unsubscribe = useCallback((channel: string) => {
    wsRef.current.unsubscribe(channel);
  }, []);

  const send = useCallback((message: any) => {
    wsRef.current.send(message);
  }, []);

  return {
    connected,
    connecting: !connected && !error,
    error,
    events,
    subscribe,
    unsubscribe,
    send,
  };
}

/**
 * Hook for API queries with React Query
 */
export function useAnalyticsOverview() {
  return useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: async () => {
      const client = getAPIClient();
      const response = await client.getAnalyticsOverview();
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // 60 seconds
  });
}

export function useRecentEvents(limit: number = 50) {
  return useQuery({
    queryKey: ['events', 'recent', limit],
    queryFn: async () => {
      const client = getAPIClient();
      const response = await client.getRecentEvents(0, limit);
      return response.data;
    },
    staleTime: 10000,
    refetchInterval: 15000,
  });
}

export function useAlerts(limit: number = 50) {
  return useQuery({
    queryKey: ['alerts', limit],
    queryFn: async () => {
      const client = getAPIClient();
      const response = await client.getAlerts(0, limit);
      return response.data;
    },
    staleTime: 10000,
    refetchInterval: 20000,
  });
}

export function useCriticalAlerts() {
  return useQuery({
    queryKey: ['alerts', 'critical'],
    queryFn: async () => {
      const client = getAPIClient();
      const response = await client.getCriticalAlerts(0, 50);
      return response.data;
    },
    staleTime: 5000,
    refetchInterval: 10000,
  });
}

export function useSystemMetrics() {
  return useQuery({
    queryKey: ['system', 'metrics'],
    queryFn: async () => {
      const client = getAPIClient();
      const response = await client.getMetrics();
      return response.data;
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: ['system', 'health'],
    queryFn: async () => {
      const client = getAPIClient();
      const response = await client.getHealth();
      return response.data;
    },
    staleTime: 30000,
    refetchInterval: 30000,
  });
}

export function useCustomers(limit: number = 50) {
  return useQuery({
    queryKey: ['customers', limit],
    queryFn: async () => {
      const client = getAPIClient();
      const response = await client.getCustomers(0, limit);
      return response.data;
    },
    staleTime: 60000,
    refetchInterval: 120000,
  });
}

/**
 * Hook for real-time metrics from WebSocket
 */
export function useRealtimeMetrics() {
  const { events, connected } = useWebSocket(['events', 'analytics']);
  const [metrics, setMetrics] = useState({
    activeCustomers: 0,
    eventsPerMinute: 0,
    activeZones: 0,
    lastUpdated: new Date().toISOString(),
  });

  useEffect(() => {
    if (events.length === 0) return;

    // Calculate metrics from recent events
    const now = Date.now();
    const oneMinuteAgo = now - 60000;

    const recentEvents = events.filter((e) => {
      const eventTime = new Date(e.timestamp).getTime();
      return eventTime > oneMinuteAgo;
    });

    const zoneIds = new Set<string>();
    const customerIds = new Set<string>();

    recentEvents.forEach((event) => {
      if (event.data?.zone_id) {
        zoneIds.add(event.data.zone_id);
      }
      if (event.data?.customer_id) {
        customerIds.add(event.data.customer_id);
      }
    });

    setMetrics({
      activeCustomers: customerIds.size,
      eventsPerMinute: recentEvents.length,
      activeZones: zoneIds.size,
      lastUpdated: new Date().toISOString(),
    });
  }, [events]);

  return {
    ...metrics,
    connected,
  };
}

/**
 * Hook for event stream
 */
export function useEventStream(
  channels: string[] = ['events'],
  maxEvents: number = 100
) {
  const { events } = useWebSocket(channels);

  return {
    events: events.slice(0, maxEvents),
    count: events.length,
  };
}

/**
 * Hook for dashboard data with automatic refresh
 */
export function useDashboardData() {
  const overview = useAnalyticsOverview();
  const recentEvents = useRecentEvents(20);
  const alerts = useAlerts(20);
  const metrics = useSystemMetrics();
  const health = useSystemHealth();
  const realtimeMetrics = useRealtimeMetrics();

  const isLoading =
    overview.isLoading ||
    recentEvents.isLoading ||
    alerts.isLoading ||
    metrics.isLoading ||
    health.isLoading;

  const isError =
    overview.isError ||
    recentEvents.isError ||
    alerts.isError ||
    metrics.isError ||
    health.isError;

  return {
    overview: overview.data,
    recentEvents: recentEvents.data,
    alerts: alerts.data,
    metrics: metrics.data,
    health: health.data,
    realtimeMetrics,
    isLoading,
    isError,
    refetch: () => {
      overview.refetch();
      recentEvents.refetch();
      alerts.refetch();
      metrics.refetch();
      health.refetch();
    },
  };
}

/**
 * Hook for pagination
 */
export function usePagination(totalItems: number, pageSize: number = 10) {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(totalItems / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const nextPage = () => {
    goToPage(currentPage + 1);
  };

  const prevPage = () => {
    goToPage(currentPage - 1);
  };

  return {
    currentPage,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    nextPage,
    prevPage,
    canNextPage: currentPage < totalPages,
    canPrevPage: currentPage > 1,
  };
}

/**
 * Hook for timer (countdown)
 */
export function useTimer(initialSeconds: number = 0) {
  const [seconds, setSeconds] = useState(initialSeconds);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isActive && seconds > 0) {
      interval = setInterval(() => {
        setSeconds((s) => s - 1);
      }, 1000);
    } else if (seconds === 0 && isActive) {
      setIsActive(false);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isActive, seconds]);

  const start = () => setIsActive(true);
  const stop = () => setIsActive(false);
  const reset = (initial: number = initialSeconds) => {
    setSeconds(initial);
    setIsActive(false);
  };

  return {
    seconds,
    isActive,
    start,
    stop,
    reset,
  };
}

/**
 * Hook for local storage
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);

      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue] as const;
}

/**
 * Hook for dark mode toggle
 */
export function useDarkMode() {
  const [isDarkMode, setIsDarkMode] = useLocalStorage('darkMode', false);

  useEffect(() => {
    const html = document.documentElement;
    if (isDarkMode) {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggle = () => setIsDarkMode(!isDarkMode);

  return { isDarkMode, toggle };
}
