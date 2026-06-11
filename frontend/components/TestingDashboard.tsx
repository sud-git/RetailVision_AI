import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import {
  Alert,
  AlertDescription,
} from '@/components/ui/alert';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Activity,
  Eye,
  Users,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader,
  RefreshCw,
  Camera,
  TrendingUp,
  Clock,
  Zap,
} from 'lucide-react';

interface ServiceStatus {
  name: string;
  healthy: boolean;
  status_code: number;
  response_time_ms: number;
  message: string;
}

interface SystemStatus {
  timestamp: string;
  uptime_seconds: number;
  overall_healthy: boolean;
  database: ServiceStatus;
  redis: ServiceStatus;
  backend_api: ServiceStatus;
  frontend?: ServiceStatus;
}

interface DetectedObject {
  id: string;
  class: string;
  confidence: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface SystemEvent {
  id: string;
  type: string;
  timestamp: string;
  data: Record<string, any>;
}

/**
 * Testing Dashboard Component
 * 
 * Comprehensive testing interface for localhost demo and validation.
 * Shows system health, video streaming, object detection, and events.
 */
export default function TestingDashboard() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Simulated data for demo
  const [detectedObjects] = useState<DetectedObject[]>([
    { id: '1', class: 'person', confidence: 0.95, x: 100, y: 50, width: 80, height: 150 },
    { id: '2', class: 'person', confidence: 0.87, x: 300, y: 80, width: 75, height: 140 },
    { id: '3', class: 'backpack', confidence: 0.78, x: 50, y: 200, width: 60, height: 80 },
  ]);

  const [recentEvents] = useState<SystemEvent[]>([
    { id: '1', type: 'detection', timestamp: new Date().toISOString(), data: { class: 'person', confidence: 0.95 } },
    { id: '2', type: 'tracking', timestamp: new Date(Date.now() - 5000).toISOString(), data: { track_id: '101', class: 'person' } },
    { id: '3', type: 'event', timestamp: new Date(Date.now() - 10000).toISOString(), data: { event_type: 'loitering', zone: '1' } },
  ]);

  // Fetch system status
  const fetchSystemStatus = useCallback(async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${apiUrl}/api/v1/health`);
      if (!response.ok) throw new Error('Failed to fetch status');
      
      const data = await response.json();
      setSystemStatus(data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Status fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    fetchSystemStatus();
    
    if (autoRefresh) {
      const interval = setInterval(fetchSystemStatus, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fetchSystemStatus]);

  const getStatusIcon = (healthy: boolean) => {
    return healthy ? (
      <CheckCircle className="w-5 h-5 text-green-500" />
    ) : (
      <XCircle className="w-5 h-5 text-red-500" />
    );
  };

  const getStatusColor = (healthy: boolean) => {
    return healthy ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Testing Dashboard</h1>
              <p className="text-gray-600 mt-1">Localhost Demo & System Status</p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => fetchSystemStatus()}
                disabled={loading}
                className="p-2 hover:bg-gray-200 rounded-lg disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-600">Auto-refresh</span>
              </label>
            </div>
          </div>
          {lastUpdate && (
            <p className="text-xs text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <AlertDescription className="text-red-700">
              Error: {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-4 gap-2 mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="services">Services</TabsTrigger>
            <TabsTrigger value="demo">Demo Stream</TabsTrigger>
            <TabsTrigger value="events">Events</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* System Health */}
            {systemStatus && (
              <>
                <Card className={`border-2 ${systemStatus.overall_healthy ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {systemStatus.overall_healthy ? (
                        <CheckCircle className="w-6 h-6 text-green-600" />
                      ) : (
                        <AlertCircle className="w-6 h-6 text-red-600" />
                      )}
                      System Status
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                      <div>
                        <p className="text-sm text-gray-600">Status</p>
                        <p className="text-2xl font-bold">
                          {systemStatus.overall_healthy ? 'Healthy' : 'Degraded'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Uptime</p>
                        <p className="text-2xl font-bold">
                          {(systemStatus.uptime_seconds / 60).toFixed(1)}m
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Services</p>
                        <p className="text-2xl font-bold">
                          {Object.values(systemStatus.services).filter(s => s.healthy).length}/{Object.keys(systemStatus.services).length}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Response Time</p>
                        <p className="text-2xl font-bold">
                          {(systemStatus.backend_api.response_time_ms).toFixed(1)}ms
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Status Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Database */}
                  <Card className={`border ${getStatusColor(systemStatus.database.healthy)}`}>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">Database</p>
                          <p className="text-lg font-semibold">{systemStatus.database.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {systemStatus.database.response_time_ms.toFixed(2)}ms
                          </p>
                        </div>
                        {getStatusIcon(systemStatus.database.healthy)}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Redis */}
                  <Card className={`border ${getStatusColor(systemStatus.redis.healthy)}`}>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">Redis Cache</p>
                          <p className="text-lg font-semibold">{systemStatus.redis.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {systemStatus.redis.response_time_ms.toFixed(2)}ms
                          </p>
                        </div>
                        {getStatusIcon(systemStatus.redis.healthy)}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Backend API */}
                  <Card className={`border ${getStatusColor(systemStatus.backend_api.healthy)}`}>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">Backend API</p>
                          <p className="text-lg font-semibold">{systemStatus.backend_api.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {systemStatus.backend_api.response_time_ms.toFixed(2)}ms
                          </p>
                        </div>
                        {getStatusIcon(systemStatus.backend_api.healthy)}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            )}
          </TabsContent>

          {/* Services Tab */}
          <TabsContent value="services" className="space-y-4">
            {systemStatus && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(systemStatus.services).map(([name, service]: [string, any]) => (
                    <Card key={name} className="border">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base flex items-center justify-between">
                          <span className="capitalize">{name.replace('_', ' ')}</span>
                          {getStatusIcon(service.healthy)}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Status:</span>
                          <span className="font-semibold">{service.healthy ? 'Healthy' : 'Unhealthy'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Response Time:</span>
                          <span className="font-semibold">{service.response_time_ms.toFixed(2)}ms</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Status Code:</span>
                          <span className="font-semibold">{service.status_code}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Message:</span>
                          <span className="font-semibold text-right">{service.message}</span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </>
            )}
          </TabsContent>

          {/* Demo Stream Tab */}
          <TabsContent value="demo" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Camera className="w-5 h-5" />
                  Video Stream Demo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Video Placeholder */}
                  <div className="bg-gray-900 rounded-lg aspect-video flex items-center justify-center">
                    <div className="text-center">
                      <Eye className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                      <p className="text-gray-400">Video Stream Placeholder</p>
                      <p className="text-sm text-gray-500 mt-1">
                        Connect to CCTV source or upload MP4
                      </p>
                    </div>
                  </div>

                  {/* Stream Controls */}
                  <div className="grid grid-cols-2 gap-4">
                    <button className="bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
                      Start Stream
                    </button>
                    <button className="bg-red-600 text-white py-2 rounded-lg hover:bg-red-700">
                      Stop Stream
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detected Objects */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Detected Objects ({detectedObjects.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {detectedObjects.map((obj) => (
                    <div key={obj.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-semibold capitalize">{obj.class} #{obj.id}</p>
                        <p className="text-sm text-gray-600">Tracking ID: {obj.id}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">{(obj.confidence * 100).toFixed(1)}%</p>
                        <p className="text-xs text-gray-500">Confidence</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Events Tab */}
          <TabsContent value="events" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Recent Events ({recentEvents.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentEvents.map((event) => (
                    <div key={event.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <div className="mt-1">
                        <Zap className="w-4 h-4 text-yellow-600" />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold capitalize">{event.type}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {JSON.stringify(event.data).substring(0, 100)}...
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Quick Links */}
        <Card className="mt-8 bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-base">Quick Links & Commands</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-semibold mb-2">📍 Service URLs</p>
                <ul className="space-y-1 text-gray-700">
                  <li>Backend: http://localhost:8000</li>
                  <li>Frontend: http://localhost:3000</li>
                  <li>API Docs: http://localhost:8000/docs</li>
                  <li>Health: http://localhost:8000/api/v1/health</li>
                </ul>
              </div>
              <div>
                <p className="font-semibold mb-2">⚙️ Test Commands</p>
                <ul className="space-y-1 text-gray-700">
                  <li>curl http://localhost:8000/health</li>
                  <li>curl http://localhost:8000/api/v1/diagnostics</li>
                  <li>curl http://localhost:8000/ping</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
