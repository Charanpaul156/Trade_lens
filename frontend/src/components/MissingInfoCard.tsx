import React from 'react';
import { MissingInfoItem, MissingSeverity } from '../types/research';
import { AlertTriangle, AlertCircle, Info, HelpCircle } from 'lucide-react';

interface MissingInfoCardProps {
  item: MissingInfoItem;
  onApplyDefault?: (field: string, value: string) => void;
}

export const MissingInfoCard: React.FC<MissingInfoCardProps> = ({ item, onApplyDefault }) => {
  const getSeverityBadge = (severity: MissingSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return {
          icon: AlertCircle,
          label: 'Critical Requirement',
          containerBg: 'border-rose-900/50 bg-rose-950/20 text-rose-300',
          badgeBg: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
        };
      case 'WARNING':
        return {
          icon: AlertTriangle,
          label: 'Warning',
          containerBg: 'border-amber-900/40 bg-amber-950/20 text-amber-300',
          badgeBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        };
      case 'INFO':
      default:
        return {
          icon: Info,
          label: 'Clarification',
          containerBg: 'border-sky-900/40 bg-sky-950/20 text-sky-300',
          badgeBg: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
        };
    }
  };

  const style = getSeverityBadge(item.severity);
  const Icon = style.icon;

  return (
    <div className={`p-4 rounded-xl border ${style.containerBg} space-y-2.5 transition-all`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 shrink-0" />
          <span className="font-semibold text-xs capitalize text-white tracking-wide">
            {item.field.replace('_', ' ')}
          </span>
        </div>
        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border ${style.badgeBg}`}>
          {style.label}
        </span>
      </div>

      <p className="text-xs text-slate-300 leading-relaxed">{item.description}</p>

      <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 space-y-2">
        <div className="flex items-start gap-2">
          <HelpCircle className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
          <p className="text-[11px] font-medium text-slate-200">{item.clarification_prompt}</p>
        </div>

        {item.suggested_defaults && item.suggested_defaults.length > 0 && (
          <div className="pt-1.5 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">
              Suggested Defaults:
            </span>
            {item.suggested_defaults.map((suggestion, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onApplyDefault?.(item.field, suggestion)}
                className="px-2 py-0.5 rounded-md text-[11px] bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition active:scale-95"
                title={`Select: ${suggestion}`}
              >
                + {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
