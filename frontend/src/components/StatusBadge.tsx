import React from 'react';
import { ConnectionStatus } from '../types/health';
import { cn } from '../lib/utils';
import { Activity, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

interface StatusBadgeProps {
  status: ConnectionStatus;
  latencyMs?: number | null;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  latencyMs,
  className,
}) => {
  const configs = {
    connected: {
      bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
      dot: 'bg-emerald-400',
      ping: 'bg-emerald-400',
      label: 'Connected',
      icon: CheckCircle2,
    },
    checking: {
      bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      dot: 'bg-amber-400',
      ping: 'bg-amber-400',
      label: 'Connecting...',
      icon: RefreshCw,
    },
    disconnected: {
      bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      dot: 'bg-rose-400',
      ping: 'bg-rose-400',
      label: 'Disconnected',
      icon: AlertCircle,
    },
    error: {
      bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      dot: 'bg-rose-400',
      ping: 'bg-rose-400',
      label: 'Connection Error',
      icon: AlertCircle,
    },
  };

  const current = configs[status];
  const Icon = current.icon;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full border text-xs font-medium tracking-wide transition-all shadow-sm backdrop-blur-md',
        current.bg,
        className
      )}
    >
      <span className="relative flex h-2 w-2">
        {status === 'connected' && (
          <span
            className={cn(
              'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
              current.ping
            )}
          />
        )}
        <span
          className={cn('relative inline-flex rounded-full h-2 w-2', current.dot)}
        />
      </span>

      <span className="flex items-center gap-1.5">
        <Icon className={cn('w-3.5 h-3.5', status === 'checking' && 'animate-spin')} />
        <span>{current.label}</span>
      </span>

      {status === 'connected' && latencyMs !== null && latencyMs !== undefined && (
        <span className="pl-1.5 border-l border-emerald-500/20 text-[11px] font-mono opacity-80 flex items-center gap-1">
          <Activity className="w-3 h-3 text-emerald-400" />
          {latencyMs}ms
        </span>
      )}
    </div>
  );
};
