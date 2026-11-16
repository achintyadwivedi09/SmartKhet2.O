import type { ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  icon: ReactNode;
  label?: string;
  title?: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'flat';
  trendValue?: string;
  subtitle?: string;
  subtext?: string;
  color?: 'green' | 'blue' | 'orange' | 'purple' | 'red';
}

const colorMap = {
  green:  { bg: 'bg-green-50',  icon: 'text-green-600',  badge: 'bg-green-100 text-green-700' },
  blue:   { bg: 'bg-blue-50',   icon: 'text-blue-600',   badge: 'bg-blue-100 text-blue-700' },
  orange: { bg: 'bg-orange-50', icon: 'text-orange-600', badge: 'bg-orange-100 text-orange-700' },
  purple: { bg: 'bg-purple-50', icon: 'text-purple-600', badge: 'bg-purple-100 text-purple-700' },
  red:    { bg: 'bg-red-50',    icon: 'text-red-600',    badge: 'bg-red-100 text-red-700' },
};

export default function MetricCard({
  icon, label, title, value, unit, trend, trendValue, subtitle, subtext, color = 'green',
}: MetricCardProps) {
  const displayLabel = label || title || '';
  const displaySub = subtitle || subtext || '';
  const c = colorMap[color];
  return (
    <div className="bg-white rounded-xl shadow-card p-5 hover:shadow-card-hover transition-shadow border border-sk-border">
      <div className="flex items-start justify-between">
        <div className={`w-10 h-10 ${c.bg} rounded-lg flex items-center justify-center ${c.icon}`}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${c.badge}`}>
            {trend === 'up' && <TrendingUp className="w-3 h-3" />}
            {trend === 'down' && <TrendingDown className="w-3 h-3" />}
            {trend === 'flat' && <Minus className="w-3 h-3" />}
            {trendValue}
          </div>
        )}
      </div>
      <div className="mt-3">
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-sk-text">{value}</span>
          {unit && <span className="text-sm text-sk-text-secondary">{unit}</span>}
        </div>
        <div className="text-sm font-medium text-sk-text-secondary mt-0.5">{displayLabel}</div>
        {displaySub && <div className="text-xs text-gray-400 mt-0.5">{displaySub}</div>}
      </div>
    </div>
  );
}
