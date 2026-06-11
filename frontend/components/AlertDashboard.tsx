/**
 * Phase 8: Alert Dashboard Component
 * Real-time alert feed with filtering and management
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';
import { AlertCircle, CheckCircle, X, Filter, RefreshCw } from 'lucide-react';

interface Alert {
  id: string;
  alert_type: 'INFO' | 'WARNING' | 'HIGH' | 'CRITICAL';
  title: string;
  description: string;
  priority: number;
  risk_score: number;
  confidence: number;
  customer_id?: string;
  zone_id?: number;
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

interface AlertStats {
  total_alerts: number;
  critical_alerts: number;
  high_alerts: number;
  warning_alerts: number;
  info_alerts: number;
  acknowledged_count: number;
  resolved_count: number;
}

const AlertDashboard: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'ACTIVE' | 'CRITICAL' | 'HIGH'>('ACTIVE');
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch alerts
  const fetchAlerts = useCallback(async () => {
    try {
      const url = filter === 'ALL' 
        ? '/api/v1/alerts'
        : `/api/v1/alerts/${filter.toLowerCase()}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success && data.data.alerts) {
        setAlerts(data.data.alerts);
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  // Fetch statistics
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/statistics/alerts');
      const data = await response.json();
      
      if (data.success && data.data) {
        setStats(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  // Initial load and setup refresh interval
  useEffect(() => {
    fetchAlerts();
    fetchStats();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchAlerts();
        fetchStats();
      }, 5000); // Refresh every 5 seconds

      return () => clearInterval(interval);
    }
  }, [filter, autoRefresh, fetchAlerts, fetchStats]);

  // Acknowledge alert
  const handleAcknowledge = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          acknowledged_by: 'user',
          action_taken: 'Acknowledged',
        }),
      });

      if (response.ok) {
        setAlerts(alerts.map(a => 
          a.id === alertId 
            ? { ...a, status: 'acknowledged' as const }
            : a
        ));
        fetchStats();
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  // Resolve alert
  const handleResolve = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        setAlerts(alerts.filter(a => a.id !== alertId));
        fetchStats();
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const getAlertColor = (type: string): string => {
    switch (type) {
      case 'CRITICAL':
        return 'bg-red-50 border-red-200';
      case 'HIGH':
        return 'bg-orange-50 border-orange-200';
      case 'WARNING':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const getAlertIcon = (type: string): React.ReactNode => {
    const iconClass = {
      'CRITICAL': 'text-red-600',
      'HIGH': 'text-orange-600',
      'WARNING': 'text-yellow-600',
      'INFO': 'text-blue-600',
    }[type] || 'text-gray-600';

    return <AlertCircle className={`w-5 h-5 ${iconClass}`} />;
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'ALL') return true;
    if (filter === 'ACTIVE') return alert.status === 'active';
    if (filter === 'CRITICAL') return alert.alert_type === 'CRITICAL';
    if (filter === 'HIGH') return alert.alert_type === 'HIGH';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alert Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time alert monitoring and management</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => {
              fetchAlerts();
              fetchStats();
            }}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          <label className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm font-medium">Auto-refresh</span>
          </label>
        </div>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-gray-600 text-sm">Total Alerts</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{stats.total_alerts}</div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg border border-red-200">
            <div className="text-red-600 text-sm font-medium">Critical</div>
            <div className="text-2xl font-bold text-red-600 mt-1">{stats.critical_alerts}</div>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
            <div className="text-orange-600 text-sm font-medium">High</div>
            <div className="text-2xl font-bold text-orange-600 mt-1">{stats.high_alerts}</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
            <div className="text-yellow-600 text-sm font-medium">Warning</div>
            <div className="text-2xl font-bold text-yellow-600 mt-1">{stats.warning_alerts}</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <div className="text-green-600 text-sm font-medium">Resolved</div>
            <div className="text-2xl font-bold text-green-600 mt-1">{stats.resolved_count}</div>
          </div>
        </div>
      )}

      {/* Filter Buttons */}
      <div className="flex gap-2 border-b">
        {(['ALL', 'ACTIVE', 'CRITICAL', 'HIGH'] as const).map(filterType => (
          <button
            key={filterType}
            onClick={() => setFilter(filterType)}
            className={`px-4 py-2 font-medium transition ${
              filter === filterType
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {filterType}
          </button>
        ))}
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-8 text-gray-600">Loading alerts...</div>
        ) : filteredAlerts.length === 0 ? (
          <div className="text-center py-8 text-gray-600">No alerts found</div>
        ) : (
          filteredAlerts.map(alert => (
            <div
              key={alert.id}
              className={`border rounded-lg p-4 ${getAlertColor(alert.alert_type)} transition`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  {getAlertIcon(alert.alert_type)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                      <span className={`text-xs font-bold px-2 py-1 rounded ${
                        alert.alert_type === 'CRITICAL' ? 'bg-red-200 text-red-800' :
                        alert.alert_type === 'HIGH' ? 'bg-orange-200 text-orange-800' :
                        alert.alert_type === 'WARNING' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-blue-200 text-blue-800'
                      }`}>
                        {alert.alert_type}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        alert.status === 'resolved' ? 'bg-green-200 text-green-800' :
                        alert.status === 'acknowledged' ? 'bg-blue-200 text-blue-800' :
                        'bg-gray-200 text-gray-800'
                      }`}>
                        {alert.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mt-1">{alert.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                      {alert.customer_id && <span>Customer: {alert.customer_id}</span>}
                      {alert.zone_id && <span>Zone: {alert.zone_id}</span>}
                      <span>Risk: {(alert.risk_score * 100).toFixed(0)}%</span>
                      <span>Priority: {alert.priority}</span>
                      <span>{format(new Date(alert.created_at), 'MMM d, HH:mm:ss')}</span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 ml-4">
                  {alert.status === 'active' && (
                    <>
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm transition"
                      >
                        Acknowledge
                      </button>
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm transition"
                      >
                        Resolve
                      </button>
                    </>
                  )}
                  {alert.status === 'acknowledged' && (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm transition"
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </div>

              {/* Risk Score Visualization */}
              <div className="mt-3 bg-white bg-opacity-50 rounded p-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium">Risk Score:</span>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        alert.risk_score > 0.7 ? 'bg-red-500' :
                        alert.risk_score > 0.4 ? 'bg-orange-500' :
                        'bg-yellow-500'
                      }`}
                      style={{ width: `${alert.risk_score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">{(alert.risk_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AlertDashboard;
