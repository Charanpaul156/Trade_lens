import React, { useState } from 'react';
import { DefinedExperimentSpec } from '../types/research';
import { ProvenanceBadge } from './ProvenanceBadge';
import {
  CheckCircle,
  Copy,
  Check,
  ArrowLeft,
  Play,
  Lock,
  ShieldCheck,
  Layers,
  TrendingUp,
  Clock,
  Calendar,
  Code2,
  FileCheck2,
} from 'lucide-react';

interface DefinedExperimentViewProps {
  spec: DefinedExperimentSpec;
  latencyMs?: number | null;
  onBackToEdit: () => void;
}

export const DefinedExperimentView: React.FC<DefinedExperimentViewProps> = ({
  spec,
  latencyMs,
  onBackToEdit,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [showJson, setShowJson] = useState<boolean>(false);

  const handleCopyJson = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(spec, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner / Breadcrumb & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl border border-emerald-500/40 bg-gradient-to-r from-emerald-950/30 via-slate-900/60 to-slate-900/40 backdrop-blur-xl shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Phase 3 &bull; DEFINE
              </span>
              {latencyMs && (
                <span className="text-[11px] text-slate-500">
                  Validated in {latencyMs}ms
                </span>
              )}
            </div>
            <h3 className="text-base font-bold text-white mt-1">
              Defined Quantitative Experiment Specification
            </h3>
            <p className="text-xs text-slate-400">
              Execution contract locked &bull; All parameters validated with zero unconfirmed assumptions
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={onBackToEdit}
            className="px-3.5 py-2 rounded-xl text-xs font-medium text-slate-300 hover:text-white border border-slate-700 bg-slate-800/80 hover:bg-slate-700/80 transition flex items-center gap-1.5 active:scale-95"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Edit / Re-clarify</span>
          </button>

          <button
            type="button"
            onClick={() => setShowJson(!showJson)}
            className="px-3.5 py-2 rounded-xl text-xs font-medium text-indigo-300 hover:text-indigo-200 border border-indigo-500/40 bg-indigo-950/30 hover:bg-indigo-900/40 transition flex items-center gap-1.5 active:scale-95"
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>{showJson ? 'View Visual Spec' : 'Inspect JSON'}</span>
          </button>
        </div>
      </div>

      {/* Hypothesis Formulation Box */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-xl space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Formal Research Hypothesis
            </h4>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>VERIFIED &amp; LOCKED</span>
          </span>
        </div>
        <p className="text-xs text-slate-400 font-mono">
          <strong className="text-slate-300">Prompt:</strong> &ldquo;{spec.research_question}&rdquo;
        </p>
        {spec.hypothesis && (
          <blockquote className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-200 italic leading-relaxed">
            &ldquo;{spec.hypothesis}&rdquo;
          </blockquote>
        )}
      </div>

      {/* JSON Inspection View or Visual Contract Grid */}
      {showJson ? (
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950/80 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Machine-Readable Execution Contract (JSON)
              </h4>
            </div>
            <button
              type="button"
              onClick={handleCopyJson}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 transition flex items-center gap-1.5 shadow-sm active:scale-95"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-300" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy JSON Contract</span>
                </>
              )}
            </button>
          </div>
          <pre className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-[11px] font-mono text-emerald-300/90 overflow-x-auto max-h-96 leading-relaxed">
            {JSON.stringify(spec, null, 2)}
          </pre>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Card 1: Market Context */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-xl space-y-3.5">
            <div className="flex items-center gap-2 pb-2.5 border-b border-slate-800/80">
              <Layers className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                1. Market Context &amp; Aggregation
              </h4>
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/50 border border-slate-850">
                <span className="text-slate-400 font-medium">Target Instrument</span>
                <span className="font-mono font-bold text-white">{spec.market_context.instrument}</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/50 border border-slate-850">
                <span className="text-slate-400 font-medium">Bar Aggregation</span>
                <span className="font-mono font-bold text-indigo-300">{spec.market_context.timeframe}</span>
              </div>
            </div>
          </div>

          {/* Card 2: Signal & Regimes */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-xl space-y-3.5">
            <div className="flex items-center gap-2 pb-2.5 border-b border-slate-800/80">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                2. Signal Logic &amp; Market Filters
              </h4>
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-850 space-y-1">
                <span className="text-slate-400 font-medium block">Entry Trigger Rule</span>
                <p className="font-mono text-emerald-300 font-medium">{spec.signal_rules.entry_condition}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-850 space-y-1">
                <span className="text-slate-400 font-medium block">Regime &amp; Volatility Filters</span>
                {spec.signal_rules.filters && spec.signal_rules.filters.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 pt-0.5">
                    {spec.signal_rules.filters.map((f, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px] font-mono">
                        {f}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-slate-500 italic text-[11px]">None (Unfiltered execution)</span>
                )}
              </div>
            </div>
          </div>

          {/* Card 3: Position & Risk */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-xl space-y-3.5">
            <div className="flex items-center gap-2 pb-2.5 border-b border-slate-800/80">
              <Clock className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                3. Trade Management &amp; Invalidation
              </h4>
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-850 space-y-1">
                <span className="text-slate-400 font-medium block">Exit Condition (Target / Stop)</span>
                <p className="font-mono text-amber-300 font-medium">
                  {spec.position_rules.exit_condition || <span className="text-slate-500 italic font-sans">Governed by holding period limit</span>}
                </p>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/50 border border-slate-850">
                <span className="text-slate-400 font-medium">Maximum Holding Duration</span>
                <span className="font-mono font-bold text-amber-300">
                  {spec.position_rules.holding_period || <span className="text-slate-500 italic font-sans font-normal">Condition-based exit</span>}
                </span>
              </div>
            </div>
          </div>

          {/* Card 4: Simulation Boundaries */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-xl space-y-3.5">
            <div className="flex items-center gap-2 pb-2.5 border-b border-slate-800/80">
              <Calendar className="w-4 h-4 text-cyan-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                4. Backtest Boundaries &amp; Cost Friction
              </h4>
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/50 border border-slate-850">
                <span className="text-slate-400 font-medium">Historical Sample Period</span>
                <span className="font-mono font-bold text-cyan-300">{spec.backtest_bounds.test_period}</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/50 border border-slate-850">
                <span className="text-slate-400 font-medium">Friction &amp; Slippage Model</span>
                <span className="font-mono font-bold text-slate-200">{spec.backtest_bounds.cost_assumptions}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Provenance Audit Verification Section */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Safety Gate &amp; Parameter Provenance Audit
            </h4>
          </div>
          <span className="text-[11px] text-emerald-400 font-medium flex items-center gap-1">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>100% Verified Parameters &bull; 0 Unresolved Assumptions</span>
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {spec.provenance_audit.map((record) => (
            <div
              key={record.field}
              className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800 flex flex-col justify-between gap-1.5"
            >
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400">
                {record.field.replace('_', ' ')}
              </span>
              <div className="flex items-center justify-between">
                <ProvenanceBadge source={record.source} confidence={record.confidence} />
                <Check className="w-3 h-3 text-emerald-400" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Bar: Locked Run Backtest Milestone Gate */}
      <div className="p-6 rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900/60 to-purple-950/30 backdrop-blur-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Next Milestone &bull; TEST
            </span>
            <span className="text-xs font-bold text-white">Quantitative Backtesting Engine</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            The experiment definition is formally locked. Simulation against historical market data will be activated in the next milestone.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            disabled
            className="px-5 py-2.5 rounded-xl text-xs font-bold text-slate-400 bg-slate-800/80 border border-slate-700 cursor-not-allowed opacity-70 flex items-center gap-2"
            title="Backtesting simulation engine will be activated in the TEST milestone"
          >
            <Play className="w-4 h-4 text-slate-500" />
            <span>Run Backtest &bull; Coming in TEST milestone</span>
          </button>
        </div>
      </div>
    </div>
  );
};
