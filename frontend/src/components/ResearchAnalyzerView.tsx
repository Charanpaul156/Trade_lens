import React, { useState } from 'react';
import { analyzeResearchQuestion, clarifyExperiment, ApiError } from '../services/api';
import { ResearchAnalyzeResponse, ExtractedField, FieldClarification } from '../types/research';
import { ProvenanceBadge } from './ProvenanceBadge';
import { MissingInfoCard } from './MissingInfoCard';
import {
  Sparkles,
  ArrowRight,
  Send,
  Loader2,
  FileCheck,
  AlertTriangle,
  HelpCircle,
  Lightbulb,
  Clock,
  TrendingUp,
  Sliders,
  ShieldCheck,
  CheckCircle,
  RotateCcw,
} from 'lucide-react';

const PRESET_IDEAS = [
  {
    title: 'NIFTY Volatility Filter',
    question: 'Does buying NIFTY after a 1% fall work better during high-volatility periods?',
  },
  {
    title: 'Subjective / Ambiguous Entry',
    question: 'Does buying NIFTY after a sharp fall work?',
  },
  {
    title: 'Equity Dip with Missing Exit',
    question: 'Does buying AAPL on 2% dip work?',
  },
  {
    title: 'Fully Specified Experiment',
    question:
      'Does buying SPY after a 1.5% drop, holding for 5 days with target 2% and stop loss 1%, work from 2020 to 2024?',
  },
];

export const ResearchAnalyzerView: React.FC = () => {
  const [question, setQuestion] = useState<string>(
    'Does buying NIFTY after a 1% fall work better during high-volatility periods?'
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isClarifying, setIsClarifying] = useState<boolean>(false);
  const [response, setResponse] = useState<ResearchAnalyzeResponse | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [clarifyError, setClarifyError] = useState<string | null>(null);

  // Staged clarifications: field -> chosen value
  const [stagedClarifications, setStagedClarifications] = useState<Record<string, string>>({});

  const handleAnalyze = async (queryToAnalyze?: string) => {
    const targetQuery = queryToAnalyze ?? question;
    if (!targetQuery.trim() || targetQuery.trim().length < 3) {
      setError('Please enter a research question with at least 3 characters.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setClarifyError(null);
    setStagedClarifications({});

    try {
      const result = await analyzeResearchQuestion(targetQuery.trim());
      setResponse(result.data);
      setLatency(result.latencyMs);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while analyzing the hypothesis.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handlePresetClick = (presetText: string) => {
    setQuestion(presetText);
    handleAnalyze(presetText);
  };

  const handleStageClarification = (field: string, value: string) => {
    setStagedClarifications((prev) => ({
      ...prev,
      [field]: value,
    }));
    setClarifyError(null);
  };

  const handleClearClarification = (field: string) => {
    setStagedClarifications((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const handleConfirmClarifications = async () => {
    if (!response?.experiment) return;

    const stagedKeys = Object.keys(stagedClarifications);
    if (stagedKeys.length === 0) return;

    setIsClarifying(true);
    setClarifyError(null);

    const clarifications: FieldClarification[] = stagedKeys.map((field) => ({
      field,
      value: field === 'filters' ? [stagedClarifications[field]] : stagedClarifications[field],
    }));

    try {
      const result = await clarifyExperiment({
        experiment: response.experiment,
        clarifications,
      });
      setResponse(result.data);
      setLatency(result.latencyMs);
      setStagedClarifications({});
    } catch (err) {
      if (err instanceof ApiError) {
        setClarifyError(err.message);
      } else {
        setClarifyError('Failed to apply clarifications to experiment.');
      }
    } finally {
      setIsClarifying(false);
    }
  };

  const experiment = response?.experiment;
  const stagedCount = Object.keys(stagedClarifications).length;

  const renderParameterRow = (
    label: string,
    field: ExtractedField<any>,
    formatValue?: (val: any) => React.ReactNode
  ) => {
    const isMissing = field.source === 'MISSING' || field.value === null;

    return (
      <tr className="border-b border-slate-800/80 hover:bg-slate-800/20 transition">
        <td className="py-3 px-4 text-xs font-semibold text-slate-300 whitespace-nowrap">
          {label}
        </td>
        <td className="py-3 px-4 text-xs">
          {isMissing ? (
            <span className="text-slate-500 italic">Not specified</span>
          ) : formatValue ? (
            formatValue(field.value)
          ) : (
            <span className="text-slate-100 font-mono">
              {Array.isArray(field.value) ? field.value.join(', ') : String(field.value)}
            </span>
          )}
        </td>
        <td className="py-3 px-4 whitespace-nowrap">
          <ProvenanceBadge
            source={field.source}
            confidence={field.confidence}
            requiresConfirmation={field.requires_confirmation}
          />
        </td>
        <td className="py-3 px-4 text-xs text-slate-400 max-w-xs truncate">
          {field.notes ? (
            <span className="text-amber-300/90" title={field.notes}>
              {field.notes}
            </span>
          ) : field.raw_text ? (
            <span className="font-mono text-[11px] text-slate-500">"{field.raw_text}"</span>
          ) : (
            <span className="text-slate-600">&mdash;</span>
          )}
        </td>
      </tr>
    );
  };

  return (
    <div className="w-full space-y-8">
      {/* Input & Formulator Box */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl p-6 shadow-2xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">AI Research Hypothesis Studio</h2>
              <p className="text-xs text-slate-400">
                ASK &rarr; CLARIFY &rarr; DEFINE quantitative backtest specifications
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
              <span>Zero Silent Assumptions</span>
            </span>
          </div>
        </div>

        {/* Preset Trading Hypotheses */}
        <div className="space-y-2">
          <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            <span>Sample Hypotheses to Test:</span>
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PRESET_IDEAS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handlePresetClick(preset.question)}
                className="text-left p-2.5 rounded-xl border border-slate-800 bg-slate-950/40 hover:bg-slate-800/50 hover:border-slate-700 text-xs transition group"
              >
                <div className="font-semibold text-slate-300 group-hover:text-indigo-300 flex items-center justify-between">
                  <span>{preset.title}</span>
                  <ArrowRight className="w-3 h-3 text-slate-600 group-hover:text-indigo-400 transition transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-[11px] text-slate-500 truncate mt-1">{preset.question}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Query Input Area */}
        <div className="space-y-3">
          <div className="relative">
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Does buying NIFTY after a 1% fall work better during high-volatility periods?"
              className="w-full rounded-xl bg-slate-950/80 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 p-4 text-sm text-slate-200 placeholder-slate-600 transition resize-none outline-none"
            />
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-xs text-slate-500">
              {latency !== null && (
                <span className="inline-flex items-center gap-1 text-slate-400">
                  <Clock className="w-3 h-3 text-slate-500" />
                  Processed in <span className="font-mono text-indigo-400 font-semibold">{latency}ms</span>
                </span>
              )}
            </div>

            <button
              type="button"
              disabled={isLoading || isClarifying}
              onClick={() => handleAnalyze()}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white font-medium text-xs shadow-lg shadow-indigo-500/20 active:scale-95 transition disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing with Gemini...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Structure Experiment</span>
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>

      {/* Structured Experiment Results View */}
      {experiment && (
        <div className="space-y-6 animate-fadeIn">
          {/* READY Banner when fully defined */}
          {experiment.status === 'READY' && (
            <div className="p-4 rounded-2xl border border-emerald-500/30 bg-emerald-950/20 backdrop-blur-xl flex items-center gap-3">
              <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-300">
                  Experiment Specification Finalized &amp; Ready
                </h4>
                <p className="text-xs text-emerald-400/90 mt-0.5">
                  All quantitative parameters, execution triggers, holding periods, and friction assumptions are fully confirmed.
                </p>
              </div>
            </div>
          )}

          {/* Status Header & Hypothesis Formulation */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
              <div className="flex items-center gap-2.5">
                <FileCheck className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Experiment Specification
                </h3>
              </div>

              <div>
                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
                    experiment.status === 'READY'
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                      : experiment.status === 'NEEDS_CLARIFICATION'
                      ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                      : 'bg-slate-500/10 border-slate-500/20 text-slate-400'
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      experiment.status === 'READY'
                        ? 'bg-emerald-400'
                        : experiment.status === 'NEEDS_CLARIFICATION'
                        ? 'bg-amber-400 animate-pulse'
                        : 'bg-slate-400'
                    }`}
                  />
                  <span>Status: {experiment.status.replace('_', ' ')}</span>
                </span>
              </div>
            </div>

            {/* Academic Hypothesis Card */}
            {experiment.hypothesis && (
              <div className="p-4 rounded-xl bg-slate-950/70 border border-indigo-500/20 space-y-1.5">
                <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>Formulated Quantitative Hypothesis</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-serif italic">
                  "{experiment.hypothesis}"
                </p>
              </div>
            )}
          </div>

          {/* Parameter Provenance Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl overflow-hidden shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-400" />
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Extracted Strategy Parameters
                </h4>
              </div>
              <span className="text-[11px] text-slate-500">Full Provenance Audit</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-[11px] uppercase tracking-wider text-slate-500">
                    <th className="py-2.5 px-4">Parameter</th>
                    <th className="py-2.5 px-4">Extracted Value</th>
                    <th className="py-2.5 px-4">Provenance</th>
                    <th className="py-2.5 px-4">Extraction Notes &amp; Raw Anchor</th>
                  </tr>
                </thead>
                <tbody>
                  {renderParameterRow('Instrument', experiment.instrument)}
                  {renderParameterRow('Timeframe', experiment.timeframe)}
                  {renderParameterRow('Entry Condition', experiment.entry_condition)}
                  {renderParameterRow('Exit Condition', experiment.exit_condition)}
                  {renderParameterRow('Holding Period', experiment.holding_period)}
                  {renderParameterRow('Regime / Filters', experiment.filters, (val) =>
                    val && val.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {val.map((f: string, i: number) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-slate-800 text-[11px] text-slate-300"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-500 italic">None</span>
                    )
                  )}
                  {renderParameterRow('Historical Test Period', experiment.test_period)}
                  {renderParameterRow('Cost Assumptions', experiment.cost_assumptions)}
                </tbody>
              </table>
            </div>
          </div>

          {/* Missing Information & Interactive Clarification Section */}
          {experiment.missing_information && experiment.missing_information.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl p-6 shadow-2xl space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-amber-400" />
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Required Clarifications &amp; Parameter Gaps (
                    {experiment.missing_information.length})
                  </h4>
                </div>
                <span className="text-[11px] text-slate-400">
                  Select or enter values below, then click Confirm Clarifications
                </span>
              </div>

              {/* Floating / Sticky Clarification Action Bar when staged */}
              {stagedCount > 0 && (
                <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fadeIn">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="font-semibold text-white">
                      {stagedCount} {stagedCount === 1 ? 'clarification' : 'clarifications'} staged
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      &bull; Ready to merge into experiment specification
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setStagedClarifications({})}
                      disabled={isClarifying}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 border border-slate-700 bg-slate-900 transition flex items-center gap-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Reset</span>
                    </button>

                    <button
                      type="button"
                      disabled={isClarifying}
                      onClick={handleConfirmClarifications}
                      className="px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 shadow-md shadow-emerald-500/20 active:scale-95 transition flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {isClarifying ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Applying...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Confirm Clarifications ({stagedCount})</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {clarifyError && (
                <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{clarifyError}</span>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {experiment.missing_information.map((item, idx) => (
                  <MissingInfoCard
                    key={idx}
                    item={item}
                    stagedValue={stagedClarifications[item.field]}
                    onStageClarification={handleStageClarification}
                    onClearClarification={handleClearClarification}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
