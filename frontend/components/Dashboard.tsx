/**
 * RetailVision AI - PHASE 6 Dashboard Components
 * Reusable UI components for the dashboard
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';

/**
 * KPI Card Component
 */
export interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  trend?: number;
  trendLabel?: string;
  loading?: boolean;
  error?: string;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  icon,
  trend,
  trendLabel,
  loading,
  error,
  variant = 'default',
}) => {
  const variantClasses = {
    default: 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700',
    primary: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    success: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    warning: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
    danger: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
  };

  return (
    <div
      className={cn(
        'rounded-lg border p-6 transition-all hover:shadow-md',
        variantClasses[variant]
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
            {title}
          </p>

          {loading ? (
            <div className="mt-2 h-8 w-24 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          ) : error ? (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
          ) : (
            <div className="mt-2">
              <p className="text-3xl font-bold text-slate-900 dark:text-white">
                {value}
                {unit && <span className="text-lg text-slate-500">{unit}</span>}
              </p>

              {trend !== undefined && (
                <div className="mt-2 flex items-center gap-1">
                  <span
                    className={cn(
                      'text-sm font-medium',
                      trend >= 0
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    )}
                  >
                    {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
                  </span>
                  {trendLabel && (
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {trendLabel}
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {icon && (
          <div className="ml-4 flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Event Feed Item Component
 */
export interface EventFeedItemProps {
  timestamp: string;
  title: string;
  description: string;
  severity?: 'critical' | 'high' | 'medium' | 'low';
  icon?: React.ReactNode;
  actions?: React.ReactNode;
}

export const EventFeedItem: React.FC<EventFeedItemProps> = ({
  timestamp,
  title,
  description,
  severity = 'medium',
  icon,
  actions,
}) => {
  const severityColors = {
    critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    high: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    medium: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
    low: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  };

  const severityDotColors = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-amber-500',
    low: 'bg-blue-500',
  };

  return (
    <div className="flex gap-4 border-b border-slate-200 p-4 dark:border-slate-700 last:border-0">
      <div className="flex flex-col items-center gap-2">
        <div className={cn('h-3 w-3 rounded-full', severityDotColors[severity])} />
        <div className="w-0.5 flex-1 bg-slate-200 dark:bg-slate-700" />
      </div>

      <div className="flex-1">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="font-medium text-slate-900 dark:text-white">{title}</p>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              {description}
            </p>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">
              {new Date(timestamp).toLocaleTimeString()}
            </p>
          </div>

          {actions && <div className="ml-4">{actions}</div>}
        </div>
      </div>

      {icon && (
        <div className="flex items-center">
          <div className="text-slate-400 dark:text-slate-600">{icon}</div>
        </div>
      )}
    </div>
  );
};

/**
 * Event Feed Container
 */
export interface EventFeedProps {
  items: EventFeedItemProps[];
  loading?: boolean;
  empty?: string;
  maxHeight?: string;
}

export const EventFeed: React.FC<EventFeedProps> = ({
  items,
  loading,
  empty = 'No events',
  maxHeight = 'max-h-96',
}) => {
  return (
    <div
      className={cn(
        'rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900',
        maxHeight,
        'overflow-y-auto'
      )}
    >
      {loading ? (
        <div className="flex items-center justify-center p-8">
          <div className="text-slate-500">Loading...</div>
        </div>
      ) : items.length === 0 ? (
        <div className="flex items-center justify-center p-8">
          <div className="text-slate-500">{empty}</div>
        </div>
      ) : (
        items.map((item, index) => <EventFeedItem key={index} {...item} />)
      )}
    </div>
  );
};

/**
 * Alert Badge Component
 */
export interface AlertBadgeProps {
  severity: 'critical' | 'high' | 'medium' | 'low';
  count: number;
  label?: string;
}

export const AlertBadge: React.FC<AlertBadgeProps> = ({
  severity,
  count,
  label,
}) => {
  const bgColors = {
    critical: 'bg-red-100 dark:bg-red-900/30',
    high: 'bg-orange-100 dark:bg-orange-900/30',
    medium: 'bg-amber-100 dark:bg-amber-900/30',
    low: 'bg-blue-100 dark:bg-blue-900/30',
  };

  const textColors = {
    critical: 'text-red-800 dark:text-red-400',
    high: 'text-orange-800 dark:text-orange-400',
    medium: 'text-amber-800 dark:text-amber-400',
    low: 'text-blue-800 dark:text-blue-400',
  };

  const dotColors = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-amber-500',
    low: 'bg-blue-500',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium',
        bgColors[severity],
        textColors[severity]
      )}
    >
      <span className={cn('h-2 w-2 rounded-full', dotColors[severity])} />
      {count} {label || severity}
    </div>
  );
};

/**
 * Status Indicator Component
 */
export interface StatusIndicatorProps {
  status: 'healthy' | 'warning' | 'error' | 'offline';
  label?: string;
  pulse?: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  pulse = true,
}) => {
  const colors = {
    healthy: 'bg-green-500',
    warning: 'bg-amber-500',
    error: 'bg-red-500',
    offline: 'bg-slate-500',
  };

  const textColors = {
    healthy: 'text-green-700 dark:text-green-400',
    warning: 'text-amber-700 dark:text-amber-400',
    error: 'text-red-700 dark:text-red-400',
    offline: 'text-slate-700 dark:text-slate-400',
  };

  return (
    <div className="flex items-center gap-2">
      <div className="relative inline-block">
        <div className={cn('h-3 w-3 rounded-full', colors[status])} />
        {pulse && (
          <div
            className={cn(
              'absolute inset-0 inline-block h-3 w-3 rounded-full animate-pulse',
              colors[status]
            )}
          />
        )}
      </div>
      {label && (
        <span className={cn('text-sm font-medium capitalize', textColors[status])}>
          {label}
        </span>
      )}
    </div>
  );
};

/**
 * Loading Skeleton Component
 */
export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div
    className={cn(
      'animate-pulse rounded-md bg-slate-200 dark:bg-slate-700',
      className
    )}
  />
);

/**
 * Card Component
 */
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ children, className, ...props }) => (
  <div
    className={cn(
      'rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900',
      className
    )}
    {...props}
  >
    {children}
  </div>
);

/**
 * Card Header
 */
export const CardHeader: React.FC<CardProps> = ({ children, className, ...props }) => (
  <div
    className={cn(
      'mb-4 flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-700',
      className
    )}
    {...props}
  >
    {children}
  </div>
);

/**
 * Card Title
 */
export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => (
  <h3 className={cn('text-lg font-semibold text-slate-900 dark:text-white', className)}>
    {children}
  </h3>
);

/**
 * Button Component
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'default',
  size = 'md',
  loading,
  children,
  disabled,
  className,
  ...props
}) => {
  const variantClasses = {
    default:
      'bg-slate-200 hover:bg-slate-300 text-slate-900 dark:bg-slate-700 dark:hover:bg-slate-600',
    primary:
      'bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-700 dark:hover:bg-blue-600',
    secondary:
      'bg-slate-100 hover:bg-slate-200 text-slate-900 dark:bg-slate-800 dark:hover:bg-slate-700',
    danger: 'bg-red-600 hover:bg-red-700 text-white dark:bg-red-700 dark:hover:bg-red-600',
    ghost: 'hover:bg-slate-100 text-slate-900 dark:hover:bg-slate-800 dark:text-white',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />}
      {children}
    </button>
  );
};

/**
 * Badge Component
 */
export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', className, ...props }) => {
  const variantClasses = {
    default: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200',
    primary: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
    danger: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-sm font-medium',
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
};
