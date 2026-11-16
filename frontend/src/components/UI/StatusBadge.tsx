type Status = 'online' | 'offline' | 'warning' | 'syncing' | 'success' | 'failure' | 'processing' | 'downloaded' | 'documented';

const map: Record<Status, string> = {
  online:      'bg-green-100 text-green-700 border-green-200',
  offline:     'bg-red-100 text-red-700 border-red-200',
  warning:     'bg-yellow-100 text-yellow-700 border-yellow-200',
  syncing:     'bg-blue-100 text-blue-700 border-blue-200',
  success:     'bg-green-100 text-green-700 border-green-200',
  failure:     'bg-red-100 text-red-700 border-red-200',
  processing:  'bg-orange-100 text-orange-700 border-orange-200',
  downloaded:  'bg-sky-100 text-sky-700 border-sky-200',
  documented:  'bg-purple-100 text-purple-700 border-purple-200',
};

const dots: Record<Status, string> = {
  online:     'bg-green-500',
  offline:    'bg-red-500',
  warning:    'bg-yellow-500',
  syncing:    'bg-blue-500 animate-pulse',
  success:    'bg-green-500',
  failure:    'bg-red-500',
  processing: 'bg-orange-500 animate-pulse',
  downloaded: 'bg-sky-500',
  documented: 'bg-purple-500',
};

interface StatusBadgeProps {
  status: Status;
  label?: string;
  showDot?: boolean;
}

export default function StatusBadge({ status, label, showDot = true }: StatusBadgeProps) {
  const displayLabel = label ?? status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${map[status]}`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${dots[status]}`} />}
      {displayLabel}
    </span>
  );
}
