/**
 * RetailVision AI - PHASE 6 Chart Components
 * Reusable charts using Recharts
 */

'use client';

import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { Card, CardHeader, CardTitle } from './Dashboard';

export interface ChartDataPoint {
  name?: string;
  time?: string;
  timestamp?: string;
  value?: number;
  customers?: number;
  interactions?: number;
  dwellTime?: number;
  zone?: string;
  [key: string]: any;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
const DARK_COLORS = ['#60a5fa', '#34d399', '#fbbf24', '#f87171', '#a78bfa'];

/**
 * Line Chart Component - Trends
 */
export interface LineChartProps {
  data: ChartDataPoint[];
  title?: string;
  lines?: Array<{ key: string; name: string; color?: string }>;
  height?: number;
  loading?: boolean;
}

export const TrendLineChart: React.FC<LineChartProps> = ({
  data,
  title,
  lines = [{ key: 'value', name: 'Value', color: '#3b82f6' }],
  height = 300,
  loading,
}) => {
  if (loading) {
    return (
      <Card>
        {title && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
        )}
        <div
          className="animate-pulse rounded bg-slate-200 dark:bg-slate-700"
          style={{ height: `${height}px` }}
        />
      </Card>
    );
  }

  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <div className="w-full">
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              dark="#475569"
            />
            <XAxis
              dataKey={lines[0]?.key === 'time' ? 'time' : 'timestamp'}
              stroke="#64748b"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            {lines.map((line, index) => (
              <Line
                key={line.key}
                type="monotone"
                dataKey={line.key}
                stroke={line.color || COLORS[index % COLORS.length]}
                name={line.name}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

/**
 * Area Chart Component - Filled trends
 */
export interface AreaChartProps {
  data: ChartDataPoint[];
  title?: string;
  dataKey: string;
  dataName?: string;
  color?: string;
  height?: number;
  loading?: boolean;
}

export const TrendAreaChart: React.FC<AreaChartProps> = ({
  data,
  title,
  dataKey,
  dataName,
  color = '#3b82f6',
  height = 300,
  loading,
}) => {
  if (loading) {
    return (
      <Card>
        {title && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
        )}
        <div
          className="animate-pulse rounded bg-slate-200 dark:bg-slate-700"
          style={{ height: `${height}px` }}
        />
      </Card>
    );
  }

  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <div className="w-full">
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.8} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              dark="#475569"
            />
            <XAxis
              dataKey="timestamp"
              stroke="#64748b"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              fillOpacity={1}
              fill="url(#colorValue)"
              name={dataName || dataKey}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

/**
 * Bar Chart Component
 */
export interface BarChartProps {
  data: ChartDataPoint[];
  title?: string;
  bars?: Array<{ key: string; name: string; color?: string }>;
  height?: number;
  loading?: boolean;
}

export const BarChartComponent: React.FC<BarChartProps> = ({
  data,
  title,
  bars = [{ key: 'value', name: 'Value', color: '#3b82f6' }],
  height = 300,
  loading,
}) => {
  if (loading) {
    return (
      <Card>
        {title && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
        )}
        <div
          className="animate-pulse rounded bg-slate-200 dark:bg-slate-700"
          style={{ height: `${height}px` }}
        />
      </Card>
    );
  }

  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <div className="w-full">
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              dark="#475569"
            />
            <XAxis
              dataKey="name"
              stroke="#64748b"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            {bars.map((bar, index) => (
              <Bar
                key={bar.key}
                dataKey={bar.key}
                fill={bar.color || COLORS[index % COLORS.length]}
                name={bar.name}
                radius={[8, 8, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

/**
 * Pie Chart Component
 */
export interface PieChartProps {
  data: Array<{ name: string; value: number }>;
  title?: string;
  height?: number;
  loading?: boolean;
}

export const PieChartComponent: React.FC<PieChartProps> = ({
  data,
  title,
  height = 300,
  loading,
}) => {
  if (loading) {
    return (
      <Card>
        {title && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
        )}
        <div
          className="animate-pulse rounded bg-slate-200 dark:bg-slate-700"
          style={{ height: `${height}px` }}
        />
      </Card>
    );
  }

  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <div className="w-full">
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) =>
                `${name} ${(percent * 100).toFixed(0)}%`
              }
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

/**
 * Heatmap-like Bar Chart for Zone Analytics
 */
export interface ZoneHeatmapProps {
  data: Array<{
    zone: string;
    value: number;
    intensity: 'high' | 'medium' | 'low';
  }>;
  title?: string;
  height?: number;
  loading?: boolean;
}

export const ZoneHeatmap: React.FC<ZoneHeatmapProps> = ({
  data,
  title,
  height = 300,
  loading,
}) => {
  if (loading) {
    return (
      <Card>
        {title && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
        )}
        <div
          className="animate-pulse rounded bg-slate-200 dark:bg-slate-700"
          style={{ height: `${height}px` }}
        />
      </Card>
    );
  }

  const getIntensityColor = (intensity: 'high' | 'medium' | 'low') => {
    const colors = {
      high: '#ef4444',
      medium: '#f59e0b',
      low: '#3b82f6',
    };
    return colors[intensity];
  };

  const chartData = data.map((item) => ({
    ...item,
    fill: getIntensityColor(item.intensity),
  }));

  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <div className="w-full">
        <ResponsiveContainer width="100%" height={height}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ left: 100 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              dark="#475569"
            />
            <XAxis type="number" stroke="#64748b" style={{ fontSize: '12px' }} />
            <YAxis
              dataKey="zone"
              type="category"
              stroke="#64748b"
              style={{ fontSize: '12px' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Bar dataKey="value" radius={[0, 8, 8, 0]}>
              {chartData.map((item, index) => (
                <Cell key={`cell-${index}`} fill={item.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

/**
 * Multi-Metric Area Chart
 */
export interface MultiMetricChartProps {
  data: ChartDataPoint[];
  title?: string;
  metrics?: Array<{ key: string; name: string; color?: string }>;
  height?: number;
  loading?: boolean;
}

export const MultiMetricChart: React.FC<MultiMetricChartProps> = ({
  data,
  title,
  metrics = [
    { key: 'customers', name: 'Customers', color: '#3b82f6' },
    { key: 'interactions', name: 'Interactions', color: '#10b981' },
  ],
  height = 350,
  loading,
}) => {
  if (loading) {
    return (
      <Card>
        {title && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
        )}
        <div
          className="animate-pulse rounded bg-slate-200 dark:bg-slate-700"
          style={{ height: `${height}px` }}
        />
      </Card>
    );
  }

  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <div className="w-full">
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data}>
            <defs>
              {metrics.map((metric, index) => (
                <linearGradient
                  key={metric.key}
                  id={`gradient-${metric.key}`}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="5%"
                    stopColor={metric.color || COLORS[index % COLORS.length]}
                    stopOpacity={0.8}
                  />
                  <stop
                    offset="95%"
                    stopColor={metric.color || COLORS[index % COLORS.length]}
                    stopOpacity={0}
                  />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              dark="#475569"
            />
            <XAxis
              dataKey="timestamp"
              stroke="#64748b"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            {metrics.map((metric, index) => (
              <Area
                key={metric.key}
                type="monotone"
                dataKey={metric.key}
                stroke={metric.color || COLORS[index % COLORS.length]}
                fill={`url(#gradient-${metric.key})`}
                name={metric.name}
                stackId="1"
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

/**
 * Radar Chart for Customer Segments
 */
export interface RadarChartProps {
  data: ChartDataPoint[];
  title?: string;
  height?: number;
  loading?: boolean;
}

export const RadarChartComponent: React.FC<RadarChartProps> = ({
  data,
  title,
  height = 300,
  loading,
}) => {
  if (loading) {
    return (
      <Card>
        {title && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
        )}
        <div
          className="animate-pulse rounded bg-slate-200 dark:bg-slate-700"
          style={{ height: `${height}px` }}
        />
      </Card>
    );
  }

  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <div className="w-full">
        <ResponsiveContainer width="100%" height={height}>
          <RadarChart data={data}>
            <PolarGrid stroke="#475569" />
            <PolarAngleAxis dataKey="name" stroke="#64748b" />
            <PolarRadiusAxis stroke="#64748b" />
            <Radar
              name="Value"
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.6}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
