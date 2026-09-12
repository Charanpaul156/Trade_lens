import React, { useState, useEffect } from 'react';
import { MissingInfoItem, MissingSeverity } from '../types/research';
import { AlertTriangle, AlertCircle, Info, HelpCircle, Check, X, Edit3 } from 'lucide-react';

interface MissingInfoCardProps {
  item: MissingInfoItem;
  stagedValue?: string;
  onStageClarification: (field: string, value: string) => void;
  onClearClarification: (field: string) => void;
}

export const MissingInfoCard: React.FC<MissingInfoCardProps> = ({
  item,
  stagedValue,
  onStageClarification,
  onClearClarification,
}) => {
  const [customInput, setCustomInput] = useState<string>('');
  const [isCustomMode, setIsCustomMode] = useState<boolean>(false);

  useEffect(() => {
    if (stagedValue && !item.suggested_defaults?.includes(stagedValue)) {
      setCustomInput(stagedValue);
      setIsCustomMode(true);
    }
  }, [stagedValue, item.suggested_defaults]);

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

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customInput.trim()) {
      onStageClarification(item.field, customInput.trim());
    }
  };

  return (
    <div className={`p-4 rounded-xl border ${style.containerBg} space-y-3 transition-all`}>
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

      <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 space-y-2.5">
        <div className="flex items-start gap-2">
          <HelpCircle className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
          <p className="text-[11px] font-medium text-slate-200">{item.clarification_prompt}</p>
        </div>

        {/* Suggested Defaults Pills */}
        {item.suggested_defaults && item.suggested_defaults.length > 0 && (
          <div className="pt-1.5 border-t border-slate-800/80 space-y-1.5">
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold block">
              Suggested Options:
            </span>
            <div className="flex flex-wrap items-center gap-1.5">
              {item.suggested_defaults.map((suggestion, idx) => {
                const isSelected = stagedValue === suggestion;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setIsCustomMode(false);
                      onStageClarification(item.field, suggestion);
                    }}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition flex items-center gap-1 ${
                      isSelected
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm'
                        : 'bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 active:scale-95'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3 text-emerald-400" />}
                    <span>{suggestion}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Custom Input Toggle / Form */}
        <div className="pt-2 border-t border-slate-800/80">
          {!isCustomMode ? (
            <button
              type="button"
              onClick={() => setIsCustomMode(true)}
              className="text-[11px] text-slate-400 hover:text-indigo-300 flex items-center gap-1 transition"
            >
              <Edit3 className="w-3 h-3" />
              <span>Or specify custom {item.field.replace('_', ' ')}...</span>
            </button>
          ) : (
            <form onSubmit={handleCustomSubmit} className="flex items-center gap-2">
              <input
                type="text"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder={`Enter custom ${item.field.replace('_', ' ')}`}
                className="flex-1 px-2.5 py-1 rounded-md bg-slate-950 border border-slate-700 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={!customInput.trim()}
                className="px-2.5 py-1 rounded-md bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium transition"
              >
                Set
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsCustomMode(false);
                  setCustomInput('');
                }}
                className="p-1 text-slate-400 hover:text-slate-200"
                title="Cancel custom input"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </form>
          )}
        </div>

        {/* Currently Staged Value Status */}
        {stagedValue && (
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
            <span className="text-emerald-400 flex items-center gap-1">
              <Check className="w-3 h-3" />
              <span>Staged: <strong className="font-mono text-white">{stagedValue}</strong></span>
            </span>
            <button
              type="button"
              onClick={() => {
                onClearClarification(item.field);
                setCustomInput('');
                setIsCustomMode(false);
              }}
              className="text-[10px] text-rose-400 hover:text-rose-300 transition"
            >
              Clear
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
