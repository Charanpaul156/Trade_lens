import React, { useState } from 'react';
import { useHealthCheck } from '../hooks/useHealthCheck';
import { StatusBadge } from '../components/StatusBadge';
import { ResearchAnalyzerView } from '../components/ResearchAnalyzerView';
import { getApiBaseUrl } from '../services/api';
import {
  Compass,
  Server,
  RefreshCw,
  Terminal,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle,
  Sparkles,
  Cpu,
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const { status, data, error, latencyMs, lastChecked, refetch } = useHealthCheck(8000);
  const apiBaseUrl = getApiBaseUrl();
  const [activeTab, setActiveTab] = useState<'research' | 'health'>('research');

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col selection:bg-indigo-500/20 selection:text-indigo-300">
      {/* Ambient background glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[750px] h-[380px] bg-indigo-600/10 blur-[140px] rounded-full" />
        <div className="absolute top-1/3 -left-40 w-[450px] h-[450px] bg-cyan-600/10 blur-[150px] rounded-full" />
        <div className="absolute bottom-10 right-0 w-[500px] h-[350px] bg-purple-600/10 blur-[160px] rounded-full" />
      </div>

      {/* Navigation Header */}
      <header className="relative z-10 border-b border-slate-800/80 bg-[#070b14]/80 backdrop-blur-xl sticky top-0">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 p-[1px] shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-[#0b1120] rounded-[11px] flex items-center justify-center">
                <Compass className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                TradeLens <span className="text-indigo-400">AI</span>
              </span>
            </div>
            <span className="hidden sm:inline-flex items-center gap-1 ml-2 px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles className="w-2.5 h-2.5 text-indigo-400" />
              <span>Step 2: Gemini AI Research</span>
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Nav Tabs */}
            <div className="flex items-center p-1 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
              <button
                type="button"
                onClick={() => setActiveTab('research')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                  activeTab === 'research'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Research Studio</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('health')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                  activeTab === 'health'
                    ? 'bg-slate-800 text-slate-100 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>Backend Health</span>
              </button>
            </div>

            <StatusBadge status={status} latencyMs={latencyMs} />
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 max-w-6xl mx-auto px-6 py-10 w-full flex flex-col">
        {/* Hero Section */}
        <div className="text-center max-w-2xl mx-auto mb-10 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs text-slate-300 backdrop-blur-sm">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Structured Extraction &bull; Provenance Tracking &bull; Zero Hallucinations</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Turn Trading Hypotheses into{' '}
            <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
              Rigorous Experiments
            </span>
          </h1>

          <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto leading-relaxed">
            Translate informal trading questions into structured parameters. Identify subjective
            triggers, surface missing exit conditions, and enforce quantitative backtest readiness.
          </p>
        </div>

        {/* Dynamic Tab Content */}
        {activeTab === 'research' ? (
          <ResearchAnalyzerView />
        ) : (
          <div className="w-full max-w-3xl mx-auto space-y-6 animate-fadeIn">
            {/* Backend Connection & Health Status Card */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl p-6 shadow-2xl space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                    <Server className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-white">FastAPI Connection Status</h2>
                    <p className="text-xs text-slate-400">Live communication &amp; latency probe</p>
                  </div>
                </div>

                <button
                  onClick={() => refetch()}
                  disabled={status === 'checking'}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 active:bg-slate-800 border border-slate-700 transition disabled:opacity-50"
                  title="Ping backend now"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${status === 'checking' ? 'animate-spin' : ''}`} />
                  <span>Ping Now</span>
                </button>
              </div>

              {/* Connection Metadata Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-500 block mb-1">State</span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        status === 'connected'
                          ? 'bg-emerald-400'
                          : status === 'checking'
                          ? 'bg-amber-400 animate-pulse'
                          : 'bg-rose-400'
                      }`}
                    />
                    <span className="font-semibold capitalize text-slate-200">{status}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-500 block mb-1">API Base URL</span>
                  <span className="font-mono text-slate-300 truncate block" title={apiBaseUrl}>
                    {apiBaseUrl}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-500 block mb-1">Endpoints</span>
                  <span className="font-mono text-indigo-400 block truncate">
                    /api/health &amp; /api/research/analyze
                  </span>
                </div>
              </div>

              {/* Response Payload Inspector */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1.5 font-medium">
                    <Terminal className="w-3.5 h-3.5 text-slate-500" />
                    Response Payload
                  </span>
                  {lastChecked && (
                    <span className="text-[11px] text-slate-500">
                      Last checked: {lastChecked.toLocaleTimeString()}
                    </span>
                  )}
                </div>

                <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950/90 font-mono text-xs p-4 text-slate-300">
                  {status === 'connected' && data && (
                    <pre className="text-emerald-400 whitespace-pre-wrap">
                      {JSON.stringify(data, null, 2)}
                    </pre>
                  )}

                  {status === 'checking' && (
                    <div className="text-amber-400/80 py-2 flex items-center gap-2">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Querying backend health endpoint...</span>
                    </div>
                  )}

                  {(status === 'disconnected' || status === 'error') && (
                    <div className="text-rose-400 py-2 space-y-1">
                      <p className="font-semibold">Connection Failed</p>
                      <p className="text-[11px] text-rose-300/80">{error}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Incremental Workflow Readiness Preview */}
        <div className="mt-14 max-w-4xl mx-auto w-full">
          <div className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-3 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5" />
            <span>Architecture Roadmap &bull; System Lifecycle</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/30 text-slate-400">
              <div className="font-semibold text-slate-300 mb-1 flex items-center justify-between">
                <span>1. Foundation</span>
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <p className="text-[11px] text-slate-500">FastAPI + React/TS/Tailwind decoupled architecture</p>
            </div>

            <div className="p-3.5 rounded-xl border border-indigo-500/30 bg-indigo-500/5 text-slate-300">
              <div className="font-semibold text-indigo-300 mb-1 flex items-center justify-between">
                <span>2. Gemini Research Engine</span>
                <CheckCircle className="w-3.5 h-3.5 text-indigo-400" />
              </div>
              <p className="text-[11px] text-slate-400">
                LLM structured parameter extraction &amp; provenance audit
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-dashed border-slate-800 bg-slate-950/20 text-slate-500">
              <div className="font-semibold text-slate-400 mb-1 flex items-center justify-between">
                <span>3. Quant Backtester</span>
                <ArrowRight className="w-3 h-3 text-slate-600" />
              </div>
              <p className="text-[11px] text-slate-600">Historical dataset execution &amp; alpha verification</p>
            </div>
          </div>
        </div>
      </main>

      {/* Minimal Footer */}
      <footer className="relative z-10 border-t border-slate-800/60 py-6 text-center text-xs text-slate-600">
        <p>TradeLens AI &bull; AI Quantitative Trading Research Assistant &bull; Step 2 Complete</p>
      </footer>
    </div>
  );
};
