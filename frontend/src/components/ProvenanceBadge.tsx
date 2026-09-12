import React from 'react';
import { ParameterSource } from '../types/research';
import { ShieldCheck, Sparkles, AlertCircle, HelpCircle } from 'lucide-react';

interface ProvenanceBadgeProps {
  source: ParameterSource;
  confidence?: number;
  requiresConfirmation?: boolean;
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({
  source,
  confidence,
  requiresConfirmation,
}) => {
  const getBadgeConfig = () => {
    switch (source) {
      case 'USER_EXPLICIT':
        return {
          label: 'User Explicit',
          icon: ShieldCheck,
          bg: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
        };
      case 'AI_INFERRED':
        return {
          label: 'AI Inferred',
          icon: Sparkles,
          bg: 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400',
        };
      case 'SYSTEM_DEFAULT':
        return {
          label: 'System Default',
          icon: HelpCircle,
          bg: 'bg-slate-500/10 border-slate-500/20 text-slate-400',
        };
      case 'MISSING':
      default:
        return {
          label: 'Missing',
          icon: AlertCircle,
          bg: 'bg-rose-500/10 border-rose-500/20 text-rose-400',
        };
    }
  };

  const config = getBadgeConfig();
  const Icon = config.icon;

  return (
    <div className="inline-flex items-center gap-1.5 flex-wrap">
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium border ${config.bg}`}
      >
        <Icon className="w-3 h-3" />
        <span>{config.label}</span>
        {confidence !== undefined && source !== 'MISSING' && (
          <span className="opacity-75 text-[10px]">({Math.round(confidence * 100)}%)</span>
        )}
      </span>

      {requiresConfirmation && source !== 'MISSING' && (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-medium bg-amber-500/10 border border-amber-500/20 text-amber-400">
          <span>Requires Confirmation</span>
        </span>
      )}
    </div>
  );
};
