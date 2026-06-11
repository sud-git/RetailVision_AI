/**
 * RetailVision AI - PHASE 6 Main Dashboard Page
 * Complete real-time analytics dashboard
 */

'use client';

import React, { useEffect, useState } from 'react';
import {
  KPICard,
  EventFeed,
  Card,
  CardHeader,
  CardTitle,
  AlertBadge,
  StatusIndicator,
  Skeleton,
  Button,
} from '@/components/Dashboard';
import {
  TrendLineChart,
  TrendAreaChart,
  MultiMetricChart,
  ZoneHeatmap,
  PieChartComponent,
} from '@/components/Charts';
import {
  useDashboardData,
  useWebSocket,
  useRealtimeMetrics,
  useEventStream,
  useLocalStorage,
  useDarkMode,
} from '@/hooks';
import { Alert, SystemEvent, ShelfInteraction } from '@/types';
import { initAPIClient, getAPIClient } from '@/lib/api';
import { initWebSocketClient } from '@/lib/websocket';

// Demo icons - replace with actual icon library in production
const Icons = {
  Users: () => <span className="text-xl">👥</span>,
  Zap: () => <span className="text-xl">⚡</span>,
  Clock: () => <span className="text-xl">⏱️</span>,
  AlertTriangle: () => <span className="text-xl">⚠️</span>,
  Activity: () => <span className="text-xl">📊</span>,
  TrendingUp: () => <span className="text-xl">📈</span>,
};

export interface DashboardPageProps {
  apiBaseUrl?: string;
  wsBaseUrl?: string;
  apiKey?: string;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  apiBaseUrl = 'http://localhost:8000',
  wsBaseUrl = 'ws://localhost:8000/ws',
  apiKey = 'demo-key-12345',
}) => {
  const [initialized, setInitialized] = useState(false);
  const [timeRange, setTimeRange] = useLocalStorage('dashboardTimeRange', 24);
  const { isDarkMode, toggle: toggleDarkMode } = useDarkMode();

  // Initialize API and WebSocket clients
  useEffect(() => {
    if (!initialized) {
      initAPIClient({
        apiBaseUrl,
        wsBaseUrl,
        apiKey,
        refreshInterval: 30000,
        wsReconnectInterval: 3000,
        maxRetries: 5,
      });

      initWebSocketClient({
        url: wsBaseUrl,
        maxRetries: 5,
        retryInterval: 3000,
        heartbeatInterval: 30000,
      });

      setInitialized(true);
    }
  }, [initialized, apiBaseUrl, wsBaseUrl, apiKey]);

  // Fetch data
  const { overview, recentEvents, alerts, metrics, health, realtimeMetrics, isLoading } =
    useDashboardData();

  const { events: eventStream } = useEventStream(['events', 'interactions', 'alerts'], 20);

  // Generate mock trend data for demo
  const generateTrendData = () => {
    const now = new Date();
    return Array.from({ length: 24 }).map((_, i) => {
      const date = new Date(now.getTime() - (24 - i) * 3600000);
      return {
        timestamp: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        customers: Math.floor(Math.random() * 50) + 20,
        interactions: Math.floor(Math.random() * 150) + 50,
        dwellTime: Math.floor(Math.random() * 300) + 100,
      };
    });
  };

  const trendData = generateTrendData();

  // Zone data for heatmap
  const zoneData = [
    { zone: 'Shelf A1', value: 45, intensity: 'high' as const },
    { zone: 'Shelf A2', value: 32, intensity: 'medium' as const },
    { zone: 'Shelf B1', value: 28, intensity: 'medium' as const },
    { zone: 'Shelf B2', value: 18, intensity: 'low' as const },
    { zone: 'Entrance', value: 52, intensity: 'high' as const },
  ];

  // Customer tier distribution
  const tierData = [
    { name: 'VIP', value: overview?.customer_tier_breakdown?.vip || 15 },
    { name: 'Frequent', value: overview?.customer_tier_breakdown?.frequent || 45 },
    { name: 'Standard', value: overview?.customer_tier_breakdown?.standard || 40 },
  ];

  // Interaction breakdown
  const interactionData = [
    { name: 'Entry', value: overview?.interaction_breakdown?.entry || 25 },
    { name: 'Engagement', value: overview?.interaction_breakdown?.engagement || 40 },
    { name: 'Comparison', value: overview?.interaction_breakdown?.comparing || 20 },
    { name: 'Pickup', value: overview?.interaction_breakdown?.pickup || 15 },
  ];

  // Convert events to feed items
  const eventFeedItems = eventStream.slice(0, 15).map((event) => {
    const timestamp = event.timestamp || new Date().toISOString();
    const data = event.data || {};

    return {
      timestamp,
      title: event.event_type || 'Event',
      description: `${data.zone_id || 'Zone'}: ${data.interaction_type || data.event_type || 'Activity'}`,
      severity: (
        {
          'critical': 'critical',
          'high': 'high',
          'medium': 'medium',
          'low': 'low',
        } as const
      )[event.type] || 'medium',
    };
  });

  // Critical alerts
  const criticalAlerts = alerts?.filter(
    (a) => a.alert_severity === 'critical'
  ) || [];
  const highAlerts = alerts?.filter((a) => a.alert_severity === 'high') || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-950/80">
        <div className="flex items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              RetailVision AI
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Real-Time Store Intelligence Dashboard - PHASE 6
            </p>
          </div>

          <div className="flex items-center gap-4">
            <StatusIndicator
              status={health?.database === 'connected' ? 'healthy' : 'error'}
              label={`Database`}
              pulse={true}
            />
            <StatusIndicator
              status={health?.redis === 'connected' ? 'healthy' : 'error'}
              label={`Redis`}
              pulse={true}
            />
            <StatusIndicator
              status={realtimeMetrics.connected ? 'healthy' : 'offline'}
              label={`WebSocket`}
              pulse={true}
            />

            <div className="h-6 w-px bg-slate-200 dark:bg-slate-700" />

            <select
              value={timeRange}
              onChange={(e) => setTimeRange(parseInt(e.target.value))}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
            >
              <option value={1}>Last 1 Hour</option>
              <option value={6}>Last 6 Hours</option>
              <option value={24}>Last 24 Hours</option>
              <option value={7}>Last 7 Days</option>
            </select>

            <Button
              variant="ghost"
              size="sm"
              onClick={toggleDarkMode}
              title="Toggle dark mode"
            >
              {isDarkMode ? '☀️' : '🌙'}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {/* KPI Cards Row 1 */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <KPICard
            title="Active Customers"
            value={realtimeMetrics.activeCustomers || 0}
            unit="online"
            icon={<Icons.Users />}
            trend={12}
            trendLabel="vs last hour"
            loading={isLoading}
            variant="primary"
          />
          <KPICard
            title="Total Interactions"
            value={overview?.total_interactions || 0}
            unit="today"
            icon={<Icons.Activity />}
            trend={8}
            trendLabel="vs yesterday"
            loading={isLoading}
            variant="success"
          />
          <KPICard
            title="Avg Dwell Time"
            value={Math.round(overview?.avg_dwell_time_seconds || 0)}
            unit="seconds"
            icon={<Icons.Clock />}
            trend={-3}
            trendLabel="vs average"
            loading={isLoading}
            variant="warning"
          />
          <KPICard
            title="Critical Alerts"
            value={criticalAlerts.length}
            unit="active"
            icon={<Icons.AlertTriangle />}
            trend={criticalAlerts.length > 0 ? 100 : 0}
            loading={isLoading}
            variant={criticalAlerts.length > 0 ? 'danger' : 'default'}
          />
        </div>

        {/* Real-Time Metrics */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  Events/Minute
                </span>
                <span className="rounded-full bg-blue-100 px-3 py-1 text-sm font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                  {realtimeMetrics.eventsPerMinute}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div
                  className="h-full bg-blue-500 transition-all duration-500"
                  style={{ width: `${Math.min(realtimeMetrics.eventsPerMinute * 2, 100)}%` }}
                />
              </div>
            </div>
          </Card>

          <Card>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  Active Zones
                </span>
                <span className="rounded-full bg-green-100 px-3 py-1 text-sm font-bold text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  {realtimeMetrics.activeZones}/{overview?.total_zones || 0}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div
                  className="h-full bg-green-500 transition-all duration-500"
                  style={{
                    width: `${(realtimeMetrics.activeZones / (overview?.total_zones || 1)) * 100}%`,
                  }}
                />
              </div>
            </div>
          </Card>

          <Card>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  System Health
                </span>
                <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-bold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                  {health?.status || 'Unknown'}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div
                  className="h-full bg-amber-500 transition-all duration-500"
                  style={{ width: '85%' }}
                />
              </div>
            </div>
          </Card>
        </div>

        {/* Charts Grid */}
        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <TrendLineChart
            data={trendData}
            title="Customer Activity Trend"
            lines={[
              { key: 'customers', name: 'Customers', color: '#3b82f6' },
              { key: 'interactions', name: 'Interactions', color: '#10b981' },
            ]}
            height={300}
            loading={isLoading}
          />

          <TrendAreaChart
            data={trendData}
            title="Average Dwell Time Trend"
            dataKey="dwellTime"
            dataName="Dwell Time (seconds)"
            color="#8b5cf6"
            height={300}
            loading={isLoading}
          />
        </div>

        {/* Zone Heatmap and Customer Distribution */}
        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ZoneHeatmap
            data={zoneData}
            title="Zone Heat Map - Engagement Intensity"
            height={350}
            loading={isLoading}
          />

          <div className="space-y-6">
            <PieChartComponent
              data={tierData}
              title="Customer Tier Distribution"
              height={300}
              loading={isLoading}
            />
          </div>
        </div>

        {/* Interaction Breakdown and Alerts */}
        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <PieChartComponent
              data={interactionData}
              title="Interaction Types"
              height={300}
              loading={isLoading}
            />
          </div>

          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Active Alerts</CardTitle>
                <div className="flex gap-2">
                  {criticalAlerts.length > 0 && (
                    <AlertBadge severity="critical" count={criticalAlerts.length} />
                  )}
                  {highAlerts.length > 0 && (
                    <AlertBadge severity="high" count={highAlerts.length} />
                  )}
                </div>
              </CardHeader>

              <div className="space-y-3">
                {alerts && alerts.length > 0 ? (
                  alerts.slice(0, 5).map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-center justify-between rounded-lg border border-slate-200 p-3 dark:border-slate-700"
                    >
                      <div className="flex-1">
                        <p className="font-medium text-slate-900 dark:text-white">
                          {alert.alert_title}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {new Date(alert.created_at).toLocaleString()}
                        </p>
                      </div>
                      <AlertBadge severity={alert.alert_severity} count={1} />
                    </div>
                  ))
                ) : (
                  <p className="text-center text-slate-500 dark:text-slate-400">
                    No active alerts
                  </p>
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* Event Feed */}
        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Real-Time Event Stream</CardTitle>
              </CardHeader>
              <EventFeed
                items={eventFeedItems}
                loading={isLoading}
                empty="Waiting for events..."
                maxHeight="max-h-96"
              />
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Event Statistics</CardTitle>
            </CardHeader>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Total Events
                  </span>
                  <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {eventStream.length}
                  </span>
                </div>
              </div>
              <div className="h-px bg-slate-200 dark:bg-slate-700" />
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Interactions
                  </span>
                  <span className="text-lg font-semibold text-green-600 dark:text-green-400">
                    {eventStream.filter((e) => e.event_type === 'interaction').length}
                  </span>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Alerts
                  </span>
                  <span className="text-lg font-semibold text-red-600 dark:text-red-400">
                    {eventStream.filter((e) => e.event_type === 'alert').length}
                  </span>
                </div>
              </div>
              <div className="h-px bg-slate-200 dark:bg-slate-700" />
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>Last updated</span>
                <span>{new Date().toLocaleTimeString()}</span>
              </div>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
