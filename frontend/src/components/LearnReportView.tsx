import React from 'react';
import { LearnReport, EvidenceLevel } from '../types/research';
import {
  ArrowLeft,
  AlertTriangle,
  Lightbulb,
  ShieldAlert,
  Activity,
  DollarSign,
  Compass,
  FileCheck2,
} from 'lucide-react';

interface LearnReportViewProps {
  report: LearnReport;
  latencyMs?: number | null;
  onBackToSimulation: () => void;
}

export const LearnReportView: React.FC<LearnReportViewProps> = ({
  report,
  latencyMs,
  onBackToSimulation,
}) => {
  const getEvidenceBadge = (level: EvidenceLevel) => {
    switch (level) {
      case 'SYNTHETIC_CANDIDATE_FOR_REAL_DATA':
        return {
          label: 'Candidate for Real Historical Data',
          badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          desc: 'Positive synthetic expectancy withstands friction. Recommended for validation against real historical feeds.',
        };
      case 'SYNTHETIC_FRICTION_DOMINATED':
        return {
          label: 'Friction-Dominated Return',
          badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          desc: 'Positive gross edge was absorbed by transaction friction. Stress-testing cost models is critical.',
        };
      case 'SYNTHETIC_NEGATIVE_EDGE':
        return {
          label: 'Negative Expectancy',
          badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          desc: 'Simulated strategy produced negative net returns. Alternative entry or regime hypotheses needed.',
        };
      case 'SYNTHETIC_INSUFFICIENT_DATA':
      default:
        return {
          label: 'Insufficient Trade Sample',
          badgeClass: 'bg-slate-700/40 text-slate-300 border-slate-600/40',
          desc: 'Fewer than 3 trades observed. Statistical variance is too high to draw valid conclusions.',
        };
    }
  };

  const badgeInfo = getEvidenceBadge(report.evidence_level);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 1. Mandatory Synthetic Data Disclaimer */}
      <div className="p-4 rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-950/40 via-slate-900/80 to-slate-900/60 backdrop-blur-xl shadow-xl flex items-start gap-3.5">
        <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 shrink-0 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Research Synthesis Disclaimer
            </span>
            {latencyMs && (
              <span className="text-[11px] text-slate-400">
                Synthesized in {latencyMs}ms
              </span>
            )}
          </div>
          <p className="text-xs font-semibold text-amber-200 mt-1">
            {report.disclaimer}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            The interpretations below represent structured research observations on simulated reference bars. They do not constitute financial advice, parameter optimization, or live execution forecasts.
          </p>
        </div>
      </div>

      {/* 2. Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl border border-purple-500/30 bg-gradient-to-r from-purple-950/30 via-slate-900/60 to-indigo-950/30 backdrop-blur-xl shadow-2xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
              Phase 5 &bull; LEARN
            </span>
            <span className="text-xs text-slate-400">
              {report.instrument} &bull; {report.timeframe}
            </span>
          </div>
          <div className="flex items-center gap-3 mt-1.5 flex-wrap">
            <h3 className="text-base font-bold text-white">
              Quantitative Research Interpretation Report
            </h3>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${badgeInfo.badgeClass}`}>
              {badgeInfo.label}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Experiment ID: <span className="font-mono text-slate-300">{report.experiment_id}</span> &bull; {badgeInfo.desc}
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            type="button"
            onClick={onBackToSimulation}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white border border-slate-700 bg-slate-800/80 hover:bg-slate-700/80 transition flex items-center gap-1.5 active:scale-95 shadow-md"
          >
            <ArrowLeft className="w-4 h-4 text-purple-400" />
            <span>Back to Simulation Results</span>
          </button>
        </div>
      </div>

      {/* 3. Executive Summary */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl space-y-2">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
          <FileCheck2 className="w-4 h-4 text-purple-400" />
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Executive Research Summary
          </h4>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed font-normal pt-1">
          {report.summary}
        </p>
      </div>

      {/* 4. Three-Column Observations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Performance Observations */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Performance Findings
              </h4>
            </div>
            <ul className="space-y-2.5 mt-3 text-xs text-slate-300">
              {report.performance_observations.map((obs, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-cyan-400 font-bold mt-0.5">&bull;</span>
                  <span>{obs}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Friction & Cost Analysis */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <DollarSign className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Transaction Cost Drag
              </h4>
            </div>
            <div className="mt-3 text-xs text-slate-300 leading-relaxed">
              <p>{report.friction_observation}</p>
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400">
            Friction models slippage per side subtracted from each round-trip trade.
          </div>
        </div>

        {/* Risk & Drawdowns */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Risk &amp; Drawdowns
              </h4>
            </div>
            <ul className="space-y-2.5 mt-3 text-xs text-slate-300">
              {report.risk_observations.map((risk, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-rose-400 font-bold mt-0.5">&bull;</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* 5. Epistemic Limitations & Boundaries */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Methodological Boundaries &amp; Limitations
          </h4>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-300 pt-1">
          {report.limitations.map((lim, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-start gap-2.5">
              <span className="text-amber-400 font-mono text-[10px] mt-0.5 font-bold">#{idx + 1}</span>
              <p className="text-slate-300 leading-relaxed text-[11px]">{lim}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 6. Concrete Next Research Steps */}
      <div className="p-6 rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/30 via-slate-900/60 to-purple-950/20 backdrop-blur-xl space-y-4 shadow-xl">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-indigo-400" />
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Recommended Next Research Directions
            </h4>
          </div>
          <span className="text-[11px] text-indigo-300 font-medium">
            Scientific Exploration &bull; Not Trading Advice
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {report.next_research_steps.map((step, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-slate-950/60 border border-indigo-950/80 hover:border-indigo-800/60 transition flex items-start gap-3"
            >
              <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 shrink-0 mt-0.5">
                <Lightbulb className="w-3.5 h-3.5" />
              </div>
              <p className="text-xs text-slate-200 leading-relaxed">
                {step}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
