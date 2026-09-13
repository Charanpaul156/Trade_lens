import React, { useState } from 'react';
import { BacktestResult, DefinedExperimentSpec } from '../types/research';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Layers,
  Sparkles,
  DollarSign,
  Percent,
} from 'lucide-react';

interface BacktestResultViewProps {
  result: BacktestResult;
  spec: DefinedExperimentSpec;
  latencyMs?: number | null;
  onBackToDefinition: () => void;
}

export const BacktestResultView: React.FC<BacktestResultViewProps> = ({
  result,
  spec,
  latencyMs,
  onBackToDefinition,
}) => {
  const [selectedTab, setSelectedTab] = useState<'trades' | 'equity' | 'audit'>('trades');
  const [hoveredPoint, setHoveredPoint] = useState<{
    date: string;
    equity: number;
    drawdown_pct: number;
    in_trade: boolean;
  } | null>(null);

  const { metrics } = result;
  const isNetPositive = metrics.net_return_pct >= 0;

  // Calculate SVG dimensions for Equity Curve
  const svgWidth = 800;
  const svgHeight = 260;
  const padding = { top: 20, right: 30, bottom: 40, left: 70 };
  const chartWidth = svgWidth - padding.left - padding.right;
  const chartHeight = svgHeight - padding.top - padding.bottom;

  const equities = result.equity_curve.map((p) => p.equity);
  const minEquity = Math.min(...equities, result.initial_capital * 0.95);
  const maxEquity = Math.max(...equities, result.initial_capital * 1.05);
  const equityRange = maxEquity - minEquity || 1;

  const points = result.equity_curve.map((p, idx) => {
    const x = padding.left + (idx / Math.max(1, result.equity_curve.length - 1)) * chartWidth;
    const y = padding.top + chartHeight - ((p.equity - minEquity) / equityRange) * chartHeight;
    return { x, y, point: p };
  });

  const pathD = points.length > 0
    ? `M ${points[0].x} ${points[0].y} ` + points.slice(1).map((p) => `L ${p.x} ${p.y}`).join(' ')
    : '';

  const areaD = points.length > 0
    ? `${pathD} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`
    : '';

  const baselineY = padding.top + chartHeight - ((result.initial_capital - minEquity) / equityRange) * chartHeight;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 1. Mandatory Synthetic Reference Disclaimer */}
      <div className="p-4 rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-950/40 via-slate-900/80 to-slate-900/60 backdrop-blur-xl shadow-xl flex items-start gap-3.5">
        <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 shrink-0 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Deterministic Simulation
            </span>
            {latencyMs && (
              <span className="text-[11px] text-slate-400">
                Simulated in {latencyMs}ms
              </span>
            )}
            <span className="text-[10px] text-slate-500 font-mono">
              Seed: #{result.reproducible_seed}
            </span>
          </div>
          <p className="text-xs font-semibold text-amber-200 mt-1">
            {result.simulation_disclaimer}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            This backtest was executed against synthetic historical reference bars. No live market feeds, broker connections, or trading capabilities are present.
          </p>
        </div>
      </div>

      {/* 2. Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/30 via-slate-900/60 to-indigo-950/30 backdrop-blur-xl shadow-2xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              Phase 4 &bull; TEST
            </span>
            <span className="text-xs text-slate-400">
              {result.instrument} &bull; {result.timeframe} &bull; {result.test_period}
            </span>
          </div>
          <h3 className="text-base font-bold text-white mt-1">
            Deterministic Backtest Simulation Results
          </h3>
          <p className="text-xs text-slate-400">
            Experiment ID: <span className="font-mono text-slate-300">{result.experiment_id}</span>
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={onBackToDefinition}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white border border-slate-700 bg-slate-800/80 hover:bg-slate-700/80 transition flex items-center gap-1.5 active:scale-95 shadow-md"
          >
            <ArrowLeft className="w-4 h-4 text-cyan-400" />
            <span>Back to Definition</span>
          </button>
        </div>
      </div>

      {/* 3. Performance KPI Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {/* Net Return */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Net Return</span>
            {isNetPositive ? (
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-rose-400" />
            )}
          </div>
          <div className="mt-2">
            <div className={`text-2xl font-bold tracking-tight ${isNetPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isNetPositive ? '+' : ''}{metrics.net_return_pct}%
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              ${result.final_equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        {/* Gross Return & Friction Drag */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Gross Return</span>
            <DollarSign className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2">
            <div className="text-xl font-bold text-slate-200">
              {metrics.gross_return_pct >= 0 ? '+' : ''}{metrics.gross_return_pct}%
            </div>
            <div className="text-[11px] text-amber-400 mt-0.5">
              Friction drag: -{metrics.friction_drag_pct}%
            </div>
          </div>
        </div>

        {/* Win Rate */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Win Rate</span>
            <Percent className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-white">
              {metrics.win_rate_pct}%
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              {metrics.winning_trades}W / {metrics.losing_trades}L ({metrics.total_trades} trades)
            </div>
          </div>
        </div>

        {/* Profit Factor */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Profit Factor</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-white">
              {metrics.profit_factor}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Gross gains / losses
            </div>
          </div>
        </div>

        {/* Max Drawdown */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Max Drawdown</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-rose-400">
              -{metrics.max_drawdown_pct}%
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Peak-to-trough
            </div>
          </div>
        </div>

        {/* Sharpe Ratio */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Sharpe Ratio</span>
            <Sparkles className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-white">
              {metrics.sharpe_ratio !== null && metrics.sharpe_ratio !== undefined ? metrics.sharpe_ratio : 'N/A'}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              {metrics.total_trades < 2 ? 'Requires ≥2 trades' : 'Annualized risk-adj'}
            </div>
          </div>
        </div>

        {/* Avg Trade Return */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Avg Trade Return</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2">
            <div className="text-xl font-bold text-slate-200">
              {metrics.avg_trade_return_pct >= 0 ? '+' : ''}{metrics.avg_trade_return_pct}%
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Per round-trip trade
            </div>
          </div>
        </div>

        {/* Avg Holding Period */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Avg Holding Time</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2">
            <div className="text-xl font-bold text-slate-200">
              {metrics.avg_holding_bars} bars
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Execution to exit
            </div>
          </div>
        </div>
      </div>

      {/* 4. Equity Curve Visualizer */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Simulated Portfolio Equity Curve
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Evolution of starting capital (${result.initial_capital.toLocaleString()}) across {result.equity_curve.length} reference bars
            </p>
          </div>
          {hoveredPoint && (
            <div className="px-3 py-1 rounded-xl bg-slate-800/90 border border-slate-700 text-xs flex items-center gap-3">
              <span className="text-slate-400 font-mono">{hoveredPoint.date}</span>
              <span className="font-bold text-white font-mono">
                ${hoveredPoint.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
              <span className="text-rose-400 text-[11px]">
                DD: -{hoveredPoint.drawdown_pct}%
              </span>
              {hoveredPoint.in_trade && (
                <span className="px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[10px] font-bold">
                  IN TRADE
                </span>
              )}
            </div>
          )}
        </div>

        <div className="w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="w-full h-auto max-h-[300px] select-none"
          >
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const val = minEquity + (1 - ratio) * equityRange;
              const y = padding.top + ratio * chartHeight;
              return (
                <g key={ratio}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={svgWidth - padding.right}
                    y2={y}
                    stroke="#334155"
                    strokeDasharray="4 4"
                    strokeOpacity="0.4"
                  />
                  <text
                    x={padding.left - 8}
                    y={y + 4}
                    textAnchor="end"
                    fill="#64748b"
                    fontSize="10"
                    fontFamily="monospace"
                  >
                    ${Math.round(val).toLocaleString()}
                  </text>
                </g>
              );
            })}

            {/* Initial capital baseline */}
            {baselineY >= padding.top && baselineY <= padding.top + chartHeight && (
              <line
                x1={padding.left}
                y1={baselineY}
                x2={svgWidth - padding.right}
                y2={baselineY}
                stroke="#64748b"
                strokeWidth="1"
                strokeDasharray="2 2"
                strokeOpacity="0.6"
              />
            )}

            {/* Area Fill */}
            {areaD && <path d={areaD} fill="url(#equityGradient)" />}

            {/* Line Path */}
            {pathD && (
              <path
                d={pathD}
                fill="none"
                stroke="#06b6d4"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Interactive hover points / hitboxes */}
            {points.map((p, idx) => (
              <circle
                key={idx}
                cx={p.x}
                cy={p.y}
                r={p.point.in_trade ? 3 : 1.5}
                fill={p.point.in_trade ? '#38bdf8' : '#64748b'}
                className="cursor-pointer transition-all hover:r-5 hover:fill-amber-400"
                onMouseEnter={() => setHoveredPoint(p.point)}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            ))}

            {/* Date labels on X-axis */}
            {points.length > 1 && (
              <>
                <text
                  x={padding.left}
                  y={svgHeight - 15}
                  textAnchor="start"
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {result.equity_curve[0].date}
                </text>
                <text
                  x={svgWidth - padding.right}
                  y={svgHeight - 15}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {result.equity_curve[result.equity_curve.length - 1].date}
                </text>
              </>
            )}
          </svg>
        </div>
      </div>

      {/* 5. Tabs: Simulated Trade Ledger vs Execution Audit */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            type="button"
            onClick={() => setSelectedTab('trades')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
              selectedTab === 'trades'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Simulated Trade Ledger ({result.trades.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setSelectedTab('audit')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
              selectedTab === 'audit'
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Execution Protocol &amp; Audit</span>
          </button>
        </div>

        {/* Tab 1: Trade Ledger */}
        {selectedTab === 'trades' && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl overflow-hidden">
            {result.trades.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                No trades were triggered during the backtest simulation window.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800 font-semibold uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="py-3 px-4">#</th>
                      <th className="py-3 px-4">Entry Date</th>
                      <th className="py-3 px-4">Entry Price</th>
                      <th className="py-3 px-4">Exit Date</th>
                      <th className="py-3 px-4">Exit Price</th>
                      <th className="py-3 px-4">Holding</th>
                      <th className="py-3 px-4">Exit Reason</th>
                      <th className="py-3 px-4 text-right">Gross %</th>
                      <th className="py-3 px-4 text-right">Friction %</th>
                      <th className="py-3 px-4 text-right">Net %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {result.trades.map((trade) => {
                      const netReturnPct = (trade.net_pnl_pct * 100).toFixed(2);
                      const grossReturnPct = (trade.gross_pnl_pct * 100).toFixed(2);
                      const frictionPct = (trade.friction_paid_pct * 100).toFixed(2);
                      const isWin = trade.is_win;

                      let reasonBadgeStyle = 'bg-slate-800 text-slate-300 border-slate-700';
                      if (trade.exit_reason === 'PROFIT_TARGET') {
                        reasonBadgeStyle = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
                      } else if (trade.exit_reason === 'STOP_LOSS') {
                        reasonBadgeStyle = 'bg-rose-500/10 text-rose-300 border-rose-500/30';
                      } else if (trade.exit_reason === 'HOLDING_PERIOD_EXPIRY') {
                        reasonBadgeStyle = 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30';
                      }

                      return (
                        <tr key={trade.trade_id} className="hover:bg-slate-800/40 transition">
                          <td className="py-3 px-4 text-slate-400">#{trade.trade_id}</td>
                          <td className="py-3 px-4 text-white">{trade.entry_date}</td>
                          <td className="py-3 px-4 text-slate-300">${trade.entry_price.toFixed(2)}</td>
                          <td className="py-3 px-4 text-white">{trade.exit_date}</td>
                          <td className="py-3 px-4 text-slate-300">${trade.exit_price.toFixed(2)}</td>
                          <td className="py-3 px-4 text-slate-400">{trade.holding_bars} bars</td>
                          <td className="py-3 px-4 font-sans">
                            <span className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded-md border ${reasonBadgeStyle}`}>
                              {trade.exit_reason}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right text-slate-300">
                            {trade.gross_pnl_pct >= 0 ? '+' : ''}{grossReturnPct}%
                          </td>
                          <td className="py-3 px-4 text-right text-amber-400">
                            -{frictionPct}%
                          </td>
                          <td className={`py-3 px-4 text-right font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {trade.net_pnl_pct >= 0 ? '+' : ''}{netReturnPct}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Execution Protocol & Audit */}
        {selectedTab === 'audit' && (
          <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl space-y-4 text-xs">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-400" />
              Deterministic Execution Protocol Audit
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">
                  Look-Ahead Bias Elimination
                </span>
                <p className="text-slate-300">
                  {result.execution_timing_convention}
                </p>
                <p className="text-slate-400 text-[11px]">
                  Signals are strictly evaluated at candle <span className="font-mono text-cyan-300">t</span> close. Orders execute at candle <span className="font-mono text-cyan-300">t+1</span> open. Candle t+1 high/low/close data is never visible to signal evaluation.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">
                  Same-Bar Collision Resolution
                </span>
                <p className="text-slate-300">
                  Conservative Stop-Loss First Convention
                </p>
                <p className="text-slate-400 text-[11px]">
                  If a single candle's range touches both the profit target and stop loss, the engine conservatively presumes the stop loss was triggered first, preventing overly optimistic fills.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">
                  Cost &amp; Friction Model
                </span>
                <p className="text-slate-300">
                  {spec.backtest_bounds.cost_assumptions}
                </p>
                <p className="text-slate-400 text-[11px]">
                  Slippage and transaction friction are modeled per trade side and subtracted from trade returns. Gross return and net return are computed and audited separately.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">
                  Deterministic Reproducibility
                </span>
                <p className="text-slate-300 font-mono">
                  Seed: #{result.reproducible_seed}
                </p>
                <p className="text-slate-400 text-[11px]">
                  Synthetic market data generation and simulated fills are fully deterministic functions of the experiment specification hash. Re-running the same spec yields identical results.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
