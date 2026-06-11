/**
 * RetailVision AI - PHASE 6 TypeScript Types
 * Complete type definitions for dashboard, API responses, and events
 */

// ============================================================================
// API Response Types
// ============================================================================

export interface Customer {
  id: string;
  external_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  customer_tier: 'vip' | 'frequent' | 'standard';
  lifetime_visits: number;
  lifetime_purchase_value: number;
  is_active: boolean;
  is_flagged: boolean;
  flag_reason?: string;
  preferences?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TrackingSession {
  id: string;
  customer_id: string;
  entry_time: string;
  exit_time?: string;
  total_duration_seconds: number;
  zones_visited: number;
  total_interactions: number;
  total_dwell_time_seconds: number;
  engagement_level: 'high' | 'medium' | 'low';
  is_completed: boolean;
  session_status: string;
  anomaly_flags?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ShelfInteraction {
  id: string;
  customer_id: string;
  tracking_session_id: string;
  interaction_type: 'entry' | 'exit' | 'engagement' | 'comparing' | 'pickup' | 'putback';
  zone_id: string;
  zone_name: string;
  start_time: string;
  end_time?: string;
  duration_seconds: number;
  engagement_level: 'high' | 'medium' | 'low';
  is_prolonged: boolean;
  items_examined?: number;
  product_ids?: string[];
  product_names?: string[];
  confidence_score: number;
  data_quality: number;
  created_at: string;
  updated_at: string;
}

export interface DwellTimeRecord {
  id: string;
  customer_id: string;
  tracking_session_id: string;
  zone_id: string;
  zone_name: string;
  dwell_time_seconds: number;
  first_visit: string;
  last_visit: string;
  visit_count: number;
  engagement_intensity: 'high' | 'medium' | 'low';
  interaction_count: number;
  revisit_frequency: number;
  avg_interaction_per_visit: number;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  customer_id?: string;
  alert_type: string;
  alert_severity: 'critical' | 'high' | 'medium' | 'low';
  alert_title: string;
  alert_description: string;
  zone_id?: string;
  related_session_id?: string;
  metadata?: Record<string, any>;
  is_active: boolean;
  is_acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved_at?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface SystemEvent {
  id: string;
  event_type: string;
  event_category: string;
  customer_id?: string;
  session_id?: string;
  zone_id?: string;
  event_data?: Record<string, any>;
  event_severity: 'critical' | 'high' | 'medium' | 'low';
  is_processed: boolean;
  processing_status?: string;
  processing_results?: Record<string, any>;
  created_at: string;
  timestamp: string;
}

export interface AnalyticsSnapshot {
  id: string;
  snapshot_period: 'hourly' | 'daily' | 'weekly' | 'monthly';
  period_start: string;
  period_end: string;
  total_customers: number;
  total_interactions: number;
  avg_dwell_time_seconds: number;
  zone_metrics?: Record<string, any>;
  engagement_breakdown?: Record<string, any>;
  customer_segments?: Record<string, any>;
  anomaly_count: number;
  anomaly_types?: string[];
  peak_hour?: string;
  peak_hour_customer_count?: number;
  data_quality_score: number;
  processing_duration_ms: number;
  created_at: string;
}

// ============================================================================
// API Response Wrapper Types
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  data_list?: T[];
  total?: number;
  message?: string;
  timestamp?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  skip: number;
  limit: number;
  timestamp?: string;
}

export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  database: string;
  redis: string;
  phase: string;
  service?: string;
}

export interface SystemMetrics {
  total_customers: number;
  total_sessions: number;
  total_interactions: number;
  avg_dwell_time: number;
  active_sessions: number;
  zone_count: number;
  peak_hour: string;
  system_uptime_seconds: number;
}

export interface AnalyticsOverview {
  total_customers_today: number;
  active_customers: number;
  total_interactions: number;
  avg_dwell_time_seconds: number;
  total_zones: number;
  active_zones: number;
  peak_zone: string;
  customer_tier_breakdown?: Record<string, number>;
  interaction_breakdown?: Record<string, number>;
}

// ============================================================================
// WebSocket Event Types
// ============================================================================

export interface WebSocketEvent<T = any> {
  type: string;
  event_type?: string;
  channel: string;
  data: T;
  timestamp: string;
}

export interface InteractionEvent {
  customer_id: string;
  session_id: string;
  zone_id: string;
  zone_name: string;
  interaction_type: string;
  engagement_level: string;
  duration_seconds: number;
  timestamp: string;
}

export interface DetectionEvent {
  customer_id: string;
  zone_id: string;
  confidence: number;
  tracking_id: number;
  timestamp: string;
}

export interface AnomalyEvent {
  anomaly_type: string;
  severity: string;
  zone_id?: string;
  customer_id?: string;
  description: string;
  timestamp: string;
}

export interface AlertEvent {
  alert_id: string;
  alert_type: string;
  alert_severity: string;
  alert_title: string;
  zone_id?: string;
  timestamp: string;
}

export interface AnalyticsUpdate {
  metric: string;
  value: number;
  zone_id?: string;
  timestamp: string;
}

// ============================================================================
// Dashboard State Types
// ============================================================================

export interface DashboardMetrics {
  activeCustomers: number;
  totalInteractions: number;
  avgDwellTime: number;
  activeAlerts: number;
  systemHealth: 'healthy' | 'warning' | 'error';
  lastUpdated: string;
}

export interface RealtimeStats {
  customersOnline: number;
  eventsPerMinute: number;
  activeZones: number;
  avgInteractionDuration: number;
  systemLoad: number;
}

export interface HeatmapData {
  zone_id: string;
  zone_name: string;
  customer_count: number;
  interaction_count: number;
  avg_dwell_time: number;
  intensity: 'high' | 'medium' | 'low';
  x?: number;
  y?: number;
}

export interface TrendData {
  timestamp: string;
  customers: number;
  interactions: number;
  dwellTime: number;
  alerts: number;
}

export interface ZoneStats {
  zone_id: string;
  zone_name: string;
  visitor_count: number;
  interaction_count: number;
  avg_dwell_time_seconds: number;
  peak_time: string;
  engagement_level: string;
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  trend?: number;
  trendLabel?: string;
  loading?: boolean;
  error?: string;
}

export interface EventFeedItemProps {
  event: SystemEvent | ShelfInteraction | Alert;
  type: 'event' | 'interaction' | 'alert';
  timestamp: string;
  description: string;
  severity?: 'critical' | 'high' | 'medium' | 'low';
}

export interface AlertPanelProps {
  alerts: Alert[];
  onAcknowledge?: (alertId: string) => void;
  onResolve?: (alertId: string) => void;
  maxItems?: number;
}

export interface ChartDataPoint {
  time: string;
  customers?: number;
  interactions?: number;
  dwellTime?: number;
  value?: number;
  zone?: string;
}

// ============================================================================
// Configuration Types
// ============================================================================

export interface DashboardConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
  apiKey: string;
  refreshInterval: number;
  wsReconnectInterval: number;
  maxRetries: number;
}

export interface ThemeConfig {
  mode: 'light' | 'dark';
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
  };
}

// ============================================================================
// Filter & Query Types
// ============================================================================

export interface FilterParams {
  startDate?: string;
  endDate?: string;
  zoneId?: string;
  customerTier?: 'vip' | 'frequent' | 'standard';
  severity?: 'critical' | 'high' | 'medium' | 'low';
  skip?: number;
  limit?: number;
}

export interface QueryOptions {
  enabled?: boolean;
  staleTime?: number;
  cacheTime?: number;
  retry?: number | boolean;
  retryDelay?: number;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseWebSocketReturn {
  connected: boolean;
  connecting: boolean;
  error?: string;
  events: WebSocketEvent[];
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  send: (message: any) => void;
}

export interface UseAPIReturn<T> {
  data?: T;
  loading: boolean;
  error?: string;
  refetch: () => void;
}

export interface UsePaginationReturn {
  page: number;
  limit: number;
  total: number;
  goToPage: (page: number) => void;
  nextPage: () => void;
  prevPage: () => void;
}
