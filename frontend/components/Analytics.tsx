/*
 * Advanced Analytics Components for PHASE 7 Dashboard
 * 
 * Components for:
 * - Interactive heatmaps
 * - Journey visualization
 * - Engagement analytics
 * - Business insights display
 */

import React, { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ChartDataPoint } from '@/types';

// ==================== HEATMAP COMPONENT ====================

export interface HeatmapProps {
  gridData: number[][];
  width?: number;
  height?: number;
  cellSize?: number;
  hotspots?: Array<{ x: number; y: number; intensity: number; count: number }>;
  title?: string;
  loading?: boolean;
}

export const InteractiveHeatmap: React.FC<HeatmapProps> = ({
  gridData,
  width = 1920,
  height = 1080,
  cellSize = 40,
  hotspots = [],
  title = "Customer Movement Heatmap",
  loading = false
}) => {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !gridData || loading) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = 'rgba(255, 255, 255, 1)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw heatmap
    const cols = Math.ceil(width / cellSize);
    const rows = Math.ceil(height / cellSize);

    for (let row = 0; row < Math.min(rows, gridData.length); row++) {
      for (let col = 0; col < Math.min(cols, gridData[row].length); col++) {
        const intensity = gridData[row][col];
        
        // Color map: blue (cold) to red (hot)
        const hue = (1 - intensity) * 240; // Blue to Red
        const color = `hsl(${hue}, 100%, ${50 + intensity * 10}%)`;
        
        ctx.fillStyle = color;
        ctx.fillRect(col * cellSize, row * cellSize, cellSize, cellSize);
      }
    }

    // Draw hotspots with circles
    hotspots.forEach(hotspot => {
      ctx.strokeStyle = 'rgba(255, 0, 0, 0.7)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(hotspot.x, hotspot.y, 20 + hotspot.intensity * 30, 0, 2 * Math.PI);
      ctx.stroke();
      
      // Add label
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
      ctx.font = 'bold 12px Arial';
      ctx.fillText(`${hotspot.count}`, hotspot.x - 5, hotspot.y - 5);
    });

  }, [gridData, width, height, cellSize, hotspots, loading]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      setMousePos({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
    }
  };

  return (
    <div className="w-full p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h3>
        {loading && <div className="text-sm text-slate-500">Loading...</div>}
      </div>
      
      <div className="overflow-x-auto">
        <canvas
          ref={canvasRef}
          width={Math.min(width, 800)}
          height={Math.min(height, 600)}
          onMouseMove={handleMouseMove}
          className="border border-slate-300 dark:border-slate-600 cursor-crosshair"
        />
      </div>
      
      {mousePos && (
        <div className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Position: ({Math.round(mousePos.x)}, {Math.round(mousePos.y)})
        </div>
      )}

      <div className="mt-3 text-xs text-slate-500">
        <span className="inline-block mr-4">🔵 Cold (Low Traffic)</span>
        <span className="inline-block">🔴 Hot (High Traffic)</span>
      </div>
    </div>
  );
};

// ==================== JOURNEY VISUALIZATION ====================

export interface JourneyPoint {
  zone: number;
  time: number;
  x: number;
  y: number;
}

export interface JourneyVisualizationProps {
  journeys: Array<{ path: Array<[number, number]>; duration: number }>;
  title?: string;
  height?: number;
}

export const JourneyVisualization: React.FC<JourneyVisualizationProps> = ({
  journeys,
  title = "Customer Journey Paths",
  height = 400
}) => {
  // Prepare data for scatter plot
  const data = journeys.flatMap(journey =>
    journey.path.map((point, idx) => ({
      x: point[0],
      y: point[1],
      journey: journeys.indexOf(journey),
      step: idx
    }))
  );

  return (
    <div className="w-full p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" type="number" label={{ value: 'X Position', position: 'insideBottomRight', offset: -5 }} />
          <YAxis dataKey="y" type="number" label={{ value: 'Y Position', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #ccc' }}
          />
          <Scatter
            name="Journey Points"
            data={data}
            fill="#8b5cf6"
            shape="circle"
          />
        </ScatterChart>
      </ResponsiveContainer>

      <div className="mt-3 text-sm text-slate-600 dark:text-slate-400">
        <p>Total journeys: {journeys.length}</p>
        <p>Total points: {data.length}</p>
      </div>
    </div>
  );
};

// ==================== ZONE ENGAGEMENT CARD ====================

export interface ZoneEngagementData {
  zoneId: number;
  engagementScore: number;
  visitorCount: number;
  conversionRate: number;
  avgDwellTime: number;
  performanceRating: 'excellent' | 'good' | 'average' | 'poor';
}

export interface ZoneEngagementCardProps {
  zone: ZoneEngagementData;
  onClick?: () => void;
}

export const ZoneEngagementCard: React.FC<ZoneEngagementCardProps> = ({
  zone,
  onClick
}) => {
  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'excellent':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'good':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'average':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'poor':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div
      onClick={onClick}
      className="p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 cursor-pointer hover:shadow-lg transition-shadow"
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-white">Zone {zone.zoneId}</h4>
          <span className={`text-xs font-semibold px-2 py-1 rounded ${getRatingColor(zone.performanceRating)}`}>
            {zone.performanceRating.toUpperCase()}
          </span>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-slate-900 dark:text-white">
            {(zone.engagementScore * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-slate-500">Engagement</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p className="text-slate-600 dark:text-slate-400">Visitors</p>
          <p className="font-semibold text-slate-900 dark:text-white">{zone.visitorCount}</p>
        </div>
        <div>
          <p className="text-slate-600 dark:text-slate-400">Conversion</p>
          <p className="font-semibold text-slate-900 dark:text-white">{(zone.conversionRate * 100).toFixed(1)}%</p>
        </div>
        <div className="col-span-2">
          <p className="text-slate-600 dark:text-slate-400">Avg Dwell Time</p>
          <p className="font-semibold text-slate-900 dark:text-white">{zone.avgDwellTime.toFixed(0)}s</p>
        </div>
      </div>

      <div className="mt-3 w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all"
          style={{ width: `${zone.engagementScore * 100}%` }}
        />
      </div>
    </div>
  );
};

// ==================== ZONE ENGAGEMENT GRID ====================

export interface ZoneEngagementGridProps {
  zones: ZoneEngagementData[];
  title?: string;
}

export const ZoneEngagementGrid: React.FC<ZoneEngagementGridProps> = ({
  zones,
  title = "Zone Engagement Analysis"
}) => {
  const [selectedZone, setSelectedZone] = useState<ZoneEngagementData | null>(null);

  return (
    <div className="w-full">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">{title}</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {zones.map(zone => (
          <ZoneEngagementCard
            key={zone.zoneId}
            zone={zone}
            onClick={() => setSelectedZone(zone)}
          />
        ))}
      </div>

      {selectedZone && (
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-700">
          <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
            Zone {selectedZone.zoneId} Details
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm text-blue-800 dark:text-blue-200">
            <div>
              <p className="font-semibold">Engagement Score</p>
              <p className="text-lg">{(selectedZone.engagementScore * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="font-semibold">Total Visitors</p>
              <p className="text-lg">{selectedZone.visitorCount}</p>
            </div>
            <div>
              <p className="font-semibold">Conversion Rate</p>
              <p className="text-lg">{(selectedZone.conversionRate * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="font-semibold">Avg Dwell Time</p>
              <p className="text-lg">{selectedZone.avgDwellTime.toFixed(0)}s</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== BUSINESS INSIGHTS PANEL ====================

export interface Insight {
  id: string;
  type: 'performance' | 'trend' | 'anomaly' | 'recommendation';
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  createdAt: string;
}

export interface InsightsPanelProps {
  insights: Insight[];
  title?: string;
  limit?: number;
}

export const InsightsPanel: React.FC<InsightsPanelProps> = ({
  insights,
  title = "Business Insights",
  limit = 5
}) => {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return '🔴';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟢';
      default:
        return '⚪';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'border-l-red-500';
      case 'medium':
        return 'border-l-yellow-500';
      case 'low':
        return 'border-l-green-500';
      default:
        return 'border-l-gray-500';
    }
  };

  return (
    <div className="w-full">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">{title}</h3>
      
      <div className="space-y-3">
        {insights.slice(0, limit).map(insight => (
          <div
            key={insight.id}
            className={`p-4 bg-white dark:bg-slate-900 rounded-lg border-l-4 ${getSeverityColor(insight.severity)} border border-slate-200 dark:border-slate-700`}
          >
            <div className="flex items-start gap-3">
              <span className="text-xl">{getSeverityIcon(insight.severity)}</span>
              
              <div className="flex-1">
                <h4 className="font-semibold text-slate-900 dark:text-white">
                  {insight.title}
                </h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {insight.description}
                </p>
                <p className="text-xs text-slate-500 mt-2">
                  {new Date(insight.createdAt).toLocaleDateString()}
                </p>
              </div>

              <span className="text-xs font-semibold px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded">
                {insight.type}
              </span>
            </div>
          </div>
        ))}
      </div>

      {insights.length === 0 && (
        <div className="p-4 text-center text-slate-500 dark:text-slate-400">
          No insights available
        </div>
      )}
    </div>
  );
};

// ==================== ROUTE FREQUENCY CHART ====================

export interface Route {
  sequence: string;
  frequency: number;
  avgDuration: number;
  conversionRate: number;
}

export interface RouteChartProps {
  routes: Route[];
  title?: string;
}

export const RouteFrequencyChart: React.FC<RouteChartProps> = ({
  routes,
  title = "Most Common Customer Routes"
}) => {
  const data = routes.map(route => ({
    name: `Route ${routes.indexOf(route) + 1}`,
    frequency: route.frequency,
    sequence: route.sequence
  }));

  return (
    <div className="w-full p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
            content={({ active, payload }) => {
              if (active && payload?.[0]) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white dark:bg-slate-800 p-2 rounded border border-slate-200 dark:border-slate-600">
                    <p className="text-sm font-semibold">{data.name}</p>
                    <p className="text-sm">Frequency: {data.frequency}</p>
                    <p className="text-xs text-slate-500">{data.sequence}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="frequency" fill="#3b82f6" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
