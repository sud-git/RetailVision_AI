"""
Advanced Analytics Hooks for PHASE 7

Custom hooks for:
- Heatmap data fetching and updates
- Journey analytics
- Zone engagement analysis
- Business insights
- Real-time analytics updates
"""

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useEffect } from 'react';
import { getAPIClient } from '@/lib/api';
import { getWebSocketClient } from '@/lib/websocket';

// ==================== HEATMAP HOOKS ====================

export function useHeatmapRealtime() {
  const client = getAPIClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['heatmap', 'latest'],
    queryFn: () => client.request('/analytics/heatmaps/latest'),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000,
  });

  return {
    heatmap: data?.data,
    isLoading,
    error: error?.message,
    refresh: refetch,
  };
}

export function useHeatmapByDate(date: Date) {
  const client = getAPIClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['heatmap', 'daily', date.toISOString().split('T')[0]],
    queryFn: () => 
      client.request(`/analytics/heatmaps/daily?date=${date.toISOString()}`),
    enabled: !!date,
    staleTime: 60000,
  });

  return {
    heatmap: data?.data,
    isLoading,
    error: error?.message,
  };
}

export function useHeatmapByHour(date: Date, hour: number) {
  const client = getAPIClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['heatmap', 'hourly', date.toISOString().split('T')[0], hour],
    queryFn: () =>
      client.request(`/analytics/heatmaps/hourly?date=${date.toISOString()}&hour=${hour}`),
    enabled: !!date && hour >= 0 && hour < 24,
    staleTime: 60000,
  });

  return {
    heatmap: data?.data,
    isLoading,
    error: error?.message,
  };
}

export function useGenerateHeatmap(type: 'real_time' | 'hourly' | 'daily' | 'weekly' = 'real_time') {
  const client = getAPIClient();
  const queryClient = useQueryClient();
  const [isGenerating, setIsGenerating] = useState(false);

  const generate = useCallback(async (date?: Date) => {
    setIsGenerating(true);
    try {
      const result = await client.request('/analytics/heatmaps/generate', {
        method: 'POST',
        body: JSON.stringify({ heatmap_type: type, date: date?.toISOString() }),
      });
      
      queryClient.invalidateQueries({ queryKey: ['heatmap'] });
      return result.data;
    } finally {
      setIsGenerating(false);
    }
  }, [client, queryClient, type]);

  return { generate, isGenerating };
}

// ==================== JOURNEY HOOKS ====================

export function useJourneySummary(customerId: string) {
  const client = getAPIClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['journey', 'summary', customerId],
    queryFn: () =>
      client.request(`/analytics/journeys/summary?customer_id=${customerId}`),
    enabled: !!customerId,
    staleTime: 30000,
  });

  return {
    journey: data?.data,
    isLoading,
    error: error?.message,
  };
}

export function useJourneyAnalytics() {
  const client = getAPIClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['analytics', 'journeys'],
    queryFn: () => client.request('/analytics/journeys/analytics'),
    staleTime: 60000,
  });

  return {
    analytics: data?.data,
    isLoading,
    error: error?.message,
    refresh: refetch,
  };
}

export function useCommonRoutes(limit: number = 5) {
  const client = getAPIClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'routes', limit],
    queryFn: () =>
      client.request(`/analytics/journeys/routes?limit=${limit}`),
    staleTime: 60000,
  });

  return {
    routes: data?.data?.routes || [],
    isLoading,
    error: error?.message,
  };
}

// ==================== ZONE ENGAGEMENT HOOKS ====================

export function useZoneEngagement(date?: Date) {
  const client = getAPIClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'zones', 'engagement', date?.toISOString()],
    queryFn: () => {
      const params = date ? `?date=${date.toISOString()}` : '';
      return client.request(`/analytics/zones/engagement${params}`);
    },
    staleTime: 30000,
  });

  return {
    zones: data?.data?.zones || [],
    isLoading,
    error: error?.message,
  };
}

export function useTopZones(limit: number = 5) {
  const client = getAPIClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'zones', 'top', limit],
    queryFn: () =>
      client.request(`/analytics/zones/top?limit=${limit}`),
    staleTime: 30000,
  });

  return {
    topZones: data?.data?.top_zones || [],
    isLoading,
    error: error?.message,
  };
}

export function useUnderperformingZones(limit: number = 5) {
  const client = getAPIClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'zones', 'underperforming', limit],
    queryFn: () =>
      client.request(`/analytics/zones/underperforming?limit=${limit}`),
    staleTime: 30000,
  });

  return {
    underperformingZones: data?.data?.underperforming_zones || [],
    isLoading,
    error: error?.message,
  };
}

// ==================== ENGAGEMENT METRICS HOOKS ====================

export function useOverallEngagement(date?: Date) {
  const client = getAPIClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['analytics', 'engagement', 'overall', date?.toISOString()],
    queryFn: () => {
      const params = date ? `?date=${date.toISOString()}` : '';
      return client.request(`/analytics/engagement/overall${params}`);
    },
    staleTime: 30000,
  });

  return {
    metrics: data?.data,
    isLoading,
    error: error?.message,
    refresh: refetch,
  };
}

// ==================== INSIGHTS HOOKS ====================

export function useBusinessInsights(limit: number = 5) {
  const client = getAPIClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['analytics', 'insights', limit],
    queryFn: () =>
      client.request(`/analytics/insights?limit=${limit}`),
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000,
  });

  return {
    insights: data?.data?.insights || [],
    isLoading,
    error: error?.message,
    refresh: refetch,
  };
}

export function useGenerateInsights(date?: Date) {
  const client = getAPIClient();
  const queryClient = useQueryClient();
  const [isGenerating, setIsGenerating] = useState(false);

  const generate = useCallback(async () => {
    setIsGenerating(true);
    try {
      const result = await client.request('/analytics/insights/generate', {
        method: 'POST',
        body: JSON.stringify({ date: date?.toISOString() }),
      });
      
      queryClient.invalidateQueries({ queryKey: ['analytics', 'insights'] });
      return result.data;
    } finally {
      setIsGenerating(false);
    }
  }, [client, queryClient, date]);

  return { generate, isGenerating };
}

// ==================== REPORTS HOOK ====================

export function useGenerateReport(
  startDate: Date,
  endDate: Date,
  reportType: 'comprehensive' | 'daily' | 'weekly' = 'comprehensive'
) {
  const client = getAPIClient();
  const [isGenerating, setIsGenerating] = useState(false);
  const [report, setReport] = useState(null);

  const generate = useCallback(async () => {
    setIsGenerating(true);
    try {
      const result = await client.request('/analytics/reports/generate', {
        method: 'POST',
        body: JSON.stringify({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          report_type: reportType,
        }),
      });
      
      setReport(result.data);
      return result.data;
    } finally {
      setIsGenerating(false);
    }
  }, [client, startDate, endDate, reportType]);

  return { generate, isGenerating, report };
}

// ==================== REAL-TIME ANALYTICS HOOK ====================

export function useRealtimeAnalytics() {
  const [metrics, setMetrics] = useState({
    heatmapUpdates: 0,
    journeyUpdates: 0,
    engagementUpdates: 0,
    lastUpdate: new Date(),
  });

  const ws = getWebSocketClient();

  useEffect(() => {
    const handleEvent = (event: any) => {
      if (event.type === 'heatmap_update') {
        setMetrics(m => ({ ...m, heatmapUpdates: m.heatmapUpdates + 1, lastUpdate: new Date() }));
      } else if (event.type === 'journey_update') {
        setMetrics(m => ({ ...m, journeyUpdates: m.journeyUpdates + 1, lastUpdate: new Date() }));
      } else if (event.type === 'engagement_update') {
        setMetrics(m => ({ ...m, engagementUpdates: m.engagementUpdates + 1, lastUpdate: new Date() }));
      }
    };

    ws.onEvent(handleEvent);

    return () => {
      // Cleanup
    };
  }, [ws]);

  return metrics;
}

// ==================== ANALYTICS COMPOSITE HOOK ====================

export function useAdvancedAnalytics(date?: Date) {
  const heatmap = useHeatmapRealtime();
  const journeys = useJourneyAnalytics();
  const zones = useZoneEngagement(date);
  const engagement = useOverallEngagement(date);
  const insights = useBusinessInsights(10);
  const routes = useCommonRoutes(5);

  const isLoading = heatmap.isLoading || journeys.isLoading || zones.isLoading;
  const error = heatmap.error || journeys.error || zones.error;

  return {
    heatmap: heatmap.heatmap,
    journeys: journeys.analytics,
    zones,
    engagement: engagement.metrics,
    insights: insights.insights,
    routes,
    isLoading,
    error,
    refresh: () => {
      heatmap.refresh();
      journeys.refresh();
      engagement.refresh();
      insights.refresh();
    }
  };
}
