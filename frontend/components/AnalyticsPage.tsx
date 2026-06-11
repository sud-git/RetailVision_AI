/*
 * Phase 7 Advanced Analytics Page Component
 * 
 * Main analytics dashboard featuring:
 * - Interactive heatmaps
 * - Journey visualization
 * - Zone engagement analysis
 * - Business insights
 * - Custom reports
 */

'use client';

import React, { useState } from 'react';
import { Calendar, Download, RefreshCw, TrendingUp, AlertCircle } from 'lucide-react';

import {
  InteractiveHeatmap,
  JourneyVisualization,
  ZoneEngagementGrid,
  InsightsPanel,
  RouteFrequencyChart,
  ZoneEngagementData,
  Insight,
  Route
} from '@/components/Analytics';

import {
  useHeatmapRealtime,
  useJourneyAnalytics,
  useZoneEngagement,
  useBusinessInsights,
  useCommonRoutes,
  useOverallEngagement,
  useGenerateReport,
  useAdvancedAnalytics
} from '@/hooks/analytics';

import { Card, CardHeader, CardTitle, Button, Badge, Skeleton } from '@/components/Dashboard';

interface AnalyticsPageProps {
  apiBaseUrl?: string;
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({
  apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}) => {
  // State
  const [dateRange, setDateRange] = useState<{ start: Date; end: Date }>({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
    end: new Date()
  });
  const [selectedTab, setSelectedTab] = useState<'heatmap' | 'journeys' | 'zones' | 'insights' | 'reports'>('heatmap');
  const [reportType, setReportType] = useState<'comprehensive' | 'daily' | 'weekly'>('comprehensive');

  // Hooks
  const analytics = useAdvancedAnalytics(dateRange.end);
  const { generate: generateReport, isGenerating: isGeneratingReport, report } = useGenerateReport(
    dateRange.start,
    dateRange.end,
    reportType
  );

  // Mock data for demo
  const mockZones: ZoneEngagementData[] = [
    {
      zoneId: 1,
      engagementScore: 0.92,
      visitorCount: 342,
      conversionRate: 0.68,
      avgDwellTime: 287,
      performanceRating: 'excellent'
    },
    {
      zoneId: 2,
      engagementScore: 0.78,
      visitorCount: 256,
      conversionRate: 0.52,
      avgDwellTime: 156,
      performanceRating: 'good'
    },
    {
      zoneId: 3,
      engagementScore: 0.45,
      visitorCount: 189,
      conversionRate: 0.28,
      avgDwellTime: 98,
      performanceRating: 'average'
    },
    {
      zoneId: 4,
      engagementScore: 0.92,
      visitorCount: 398,
      conversionRate: 0.71,
      avgDwellTime: 312,
      performanceRating: 'excellent'
    },
    {
      zoneId: 5,
      engagementScore: 0.32,
      visitorCount: 78,
      conversionRate: 0.15,
      avgDwellTime: 45,
      performanceRating: 'poor'
    },
  ];

  const mockRoutes: Route[] = [
    { sequence: 'z1->z2->z4', frequency: 145, avgDuration: 287, conversionRate: 0.68 },
    { sequence: 'z2->z4->z1', frequency: 98, avgDuration: 234, conversionRate: 0.55 },
    { sequence: 'z4->z2->z1->z5', frequency: 67, avgDuration: 456, conversionRate: 0.42 },
    { sequence: 'z1->z4->z2', frequency: 52, avgDuration: 198, conversionRate: 0.62 },
    { sequence: 'z2->z1->z4->z5', frequency: 38, avgDuration: 378, conversionRate: 0.50 },
  ];

  const mockInsights: Insight[] = [
    {
      id: '1',
      type: 'performance',
      title: 'Zone 4 Shows Exceptional Performance',
      description: 'Zone 4 has achieved the highest engagement score (92%) with 398 visitors today.',
      severity: 'low',
      createdAt: new Date().toISOString()
    },
    {
      id: '2',
      type: 'recommendation',
      title: 'Optimize Zone 5 Product Placement',
      description: 'Zone 5 has low engagement. Consider repositioning products or adding signage.',
      severity: 'high',
      createdAt: new Date().toISOString()
    },
    {
      id: '3',
      type: 'trend',
      title: 'Peak Traffic at 2 PM',
      description: 'Customer traffic peaks between 1-3 PM. Plan staffing accordingly.',
      severity: 'medium',
      createdAt: new Date().toISOString()
    },
    {
      id: '4',
      type: 'anomaly',
      title: 'Unusual Route Pattern',
      description: 'New route pattern detected: z4->z2->z1->z5. This route shows 42% conversion.',
      severity: 'low',
      createdAt: new Date().toISOString()
    },
    {
      id: '5',
      type: 'recommendation',
      title: 'Increase Inventory in Zone 1 & 4',
      description: 'High-performing zones are approaching stock limits. Restock recommended.',
      severity: 'medium',
      createdAt: new Date().toISOString()
    },
  ];

  // Mock heatmap grid
  const mockHeatmapGrid = Array(27).fill(null).map(() =>
    Array(48).fill(null).map(() => Math.random() * 0.8)
  );

  const mockHotspots = [
    { x: 400, y: 300, intensity: 0.9, count: 342 },
    { x: 900, y: 600, intensity: 0.85, count: 398 },
    { x: 200, y: 150, intensity: 0.65, count: 256 },
  ];

  // Mock journeys
  const mockJourneys = [
    {
      path: [[100, 100], [200, 150], [400, 300], [600, 200]],
      duration: 287
    },
    {
      path: [[150, 200], [300, 250], [500, 400], [700, 300]],
      duration: 234
    },
    {
      path: [[50, 300], [250, 350], [450, 400], [650, 500], [750, 400]],
      duration: 456
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
          Advanced Analytics & Heatmap Intelligence
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          PHASE 7: Comprehensive store intelligence analysis
        </p>
      </div>

      {/* Date Range Selector */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          <input
            type="date"
            value={dateRange.start.toISOString().split('T')[0]}
            onChange={(e) => setDateRange({ ...dateRange, start: new Date(e.target.value) })}
            className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
          />
          <span className="text-slate-600 dark:text-slate-400">to</span>
          <input
            type="date"
            value={dateRange.end.toISOString().split('T')[0]}
            onChange={(e) => setDateRange({ ...dateRange, end: new Date(e.target.value) })}
            className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
          />
        </div>

        <Button variant="secondary" size="sm" onClick={() => analytics.refresh}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>

        <Button variant="secondary" size="sm">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-slate-200 dark:border-slate-700">
        {(['heatmap', 'journeys', 'zones', 'insights', 'reports'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              selectedTab === tab
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="space-y-6">
        {/* HEATMAP TAB */}
        {selectedTab === 'heatmap' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Real-Time Customer Movement Heatmap</CardTitle>
              </CardHeader>
              <div className="p-6">
                <InteractiveHeatmap
                  gridData={mockHeatmapGrid}
                  width={1920}
                  height={1080}
                  hotspots={mockHotspots}
                  loading={analytics.isLoading}
                />
              </div>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Heatmap Statistics</CardTitle>
                </CardHeader>
                <div className="p-6 space-y-4">
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Total Samples</p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white">12,847</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Peak Intensity</p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white">0.92</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Active Hotspots</p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white">8</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Coverage</p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white">73%</p>
                  </div>
                </div>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Hotspot Analysis</CardTitle>
                </CardHeader>
                <div className="p-6 space-y-3">
                  {mockHotspots.map((hotspot, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-800 rounded">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold text-slate-900 dark:text-white">Hotspot {idx + 1}</p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">({hotspot.x}, {hotspot.y})</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-slate-900 dark:text-white">{hotspot.count}</p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">customers</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* JOURNEYS TAB */}
        {selectedTab === 'journeys' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Customer Journey Paths</CardTitle>
              </CardHeader>
              <div className="p-6">
                <JourneyVisualization
                  journeys={mockJourneys}
                  height={400}
                />
              </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Journey Analytics</CardTitle>
                </CardHeader>
                <div className="p-6 space-y-4">
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Total Journeys</p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white">1,342</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Unique Routes</p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white">47</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Avg Journey Length</p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white">4.2</p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">zones visited</p>
                  </div>
                </div>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Journey Segments</CardTitle>
                </CardHeader>
                <div className="p-6 space-y-3">
                  <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded">
                    <div className="flex justify-between items-center">
                      <p className="font-semibold text-slate-900 dark:text-white">Browsing</p>
                      <Badge>68%</Badge>
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded">
                    <div className="flex justify-between items-center">
                      <p className="font-semibold text-slate-900 dark:text-white">Seeking</p>
                      <Badge>24%</Badge>
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded">
                    <div className="flex justify-between items-center">
                      <p className="font-semibold text-slate-900 dark:text-white">Purchasing</p>
                      <Badge>8%</Badge>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Most Common Routes</CardTitle>
              </CardHeader>
              <div className="p-6">
                <RouteFrequencyChart routes={mockRoutes} />
              </div>
            </Card>
          </div>
        )}

        {/* ZONES TAB */}
        {selectedTab === 'zones' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Zone Engagement Analysis</CardTitle>
              </CardHeader>
              <div className="p-6">
                <ZoneEngagementGrid zones={mockZones} />
              </div>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Top Performing Zones</CardTitle>
                </CardHeader>
                <div className="p-6 space-y-3">
                  {mockZones.filter(z => z.performanceRating === 'excellent').map(zone => (
                    <div key={zone.zoneId} className="p-3 bg-green-50 dark:bg-green-900 rounded border border-green-200 dark:border-green-700">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold text-slate-900 dark:text-white">Zone {zone.zoneId}</p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">{zone.visitorCount} visitors</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-green-600 dark:text-green-400">{(zone.engagementScore * 100).toFixed(0)}%</p>
                          <p className="text-xs text-slate-600 dark:text-slate-400">engagement</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Zones Needing Attention</CardTitle>
                </CardHeader>
                <div className="p-6 space-y-3">
                  {mockZones.filter(z => z.performanceRating === 'poor' || z.performanceRating === 'average').map(zone => (
                    <div key={zone.zoneId} className="p-3 bg-orange-50 dark:bg-orange-900 rounded border border-orange-200 dark:border-orange-700">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold text-slate-900 dark:text-white">Zone {zone.zoneId}</p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">{zone.visitorCount} visitors</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-orange-600 dark:text-orange-400">{(zone.engagementScore * 100).toFixed(0)}%</p>
                          <p className="text-xs text-slate-600 dark:text-slate-400">engagement</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* INSIGHTS TAB */}
        {selectedTab === 'insights' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Business Intelligence Insights</CardTitle>
              </CardHeader>
              <div className="p-6">
                <InsightsPanel insights={mockInsights} limit={10} />
              </div>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Performance
                  </CardTitle>
                </CardHeader>
                <div className="p-6">
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400">+12%</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">vs. previous week</p>
                </div>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    Anomalies
                  </CardTitle>
                </CardHeader>
                <div className="p-6">
                  <p className="text-3xl font-bold text-amber-600 dark:text-amber-400">3</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">detected today</p>
                </div>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recommendations</CardTitle>
                </CardHeader>
                <div className="p-6">
                  <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">5</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">actionable items</p>
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* REPORTS TAB */}
        {selectedTab === 'reports' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Generate Analytics Report</CardTitle>
              </CardHeader>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
                    Report Type
                  </label>
                  <select
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value as any)}
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="comprehensive">Comprehensive Report</option>
                    <option value="daily">Daily Report</option>
                    <option value="weekly">Weekly Report</option>
                  </select>
                </div>

                <Button
                  onClick={() => generateReport()}
                  disabled={isGeneratingReport}
                  className="w-full"
                >
                  {isGeneratingReport ? 'Generating...' : 'Generate Report'}
                </Button>

                {report && (
                  <div className="mt-4 p-4 bg-green-50 dark:bg-green-900 rounded border border-green-200 dark:border-green-700">
                    <p className="font-semibold text-green-900 dark:text-green-100 mb-2">Report Generated!</p>
                    <p className="text-sm text-green-800 dark:text-green-200">
                      Your {reportType} report is ready for download.
                    </p>
                  </div>
                )}
              </div>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Previous Reports</CardTitle>
              </CardHeader>
              <div className="p-6 space-y-2">
                <div className="p-3 flex justify-between items-center bg-slate-50 dark:bg-slate-800 rounded">
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-white">Weekly Report - May 24-30</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Generated 2 days ago</p>
                  </div>
                  <Button variant="secondary" size="sm">Download</Button>
                </div>
                <div className="p-3 flex justify-between items-center bg-slate-50 dark:bg-slate-800 rounded">
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-white">Daily Report - May 29</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Generated yesterday</p>
                  </div>
                  <Button variant="secondary" size="sm">Download</Button>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-700">
        <p className="text-sm text-blue-900 dark:text-blue-100">
          <strong>PHASE 7 Status:</strong> Advanced Analytics Engine is operational. Last update: {new Date().toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

export default AnalyticsPage;
