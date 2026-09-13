export type ExperimentStatus = 'DRAFT' | 'NEEDS_CLARIFICATION' | 'READY';

export type ParameterSource = 'USER_EXPLICIT' | 'AI_INFERRED' | 'SYSTEM_DEFAULT' | 'MISSING';

export type MissingSeverity = 'CRITICAL' | 'WARNING' | 'INFO';

export interface ExtractedField<T = string> {
  value: T | null;
  source: ParameterSource;
  confidence: number;
  requires_confirmation: boolean;
  raw_text?: string | null;
  notes?: string | null;
}

export interface MissingInfoItem {
  field: string;
  description: string;
  severity: MissingSeverity;
  clarification_prompt: string;
  suggested_defaults?: string[] | null;
}

export interface ResearchExperiment {
  research_question: string;
  hypothesis?: string | null;
  status: ExperimentStatus;
  instrument: ExtractedField<string>;
  timeframe: ExtractedField<string>;
  entry_condition: ExtractedField<string>;
  exit_condition: ExtractedField<string>;
  holding_period: ExtractedField<string>;
  filters: ExtractedField<string[]>;
  test_period: ExtractedField<string>;
  cost_assumptions: ExtractedField<string>;
  missing_information: MissingInfoItem[];
}

export interface ResearchAnalyzeRequest {
  question: string;
}

export interface ResearchAnalyzeResponse {
  status: ExperimentStatus;
  experiment: ResearchExperiment;
  missing_information: MissingInfoItem[];
}

export interface FieldClarification {
  field: string;
  value: string | string[];
}

export interface ResearchClarifyRequest {
  experiment: ResearchExperiment;
  clarifications: FieldClarification[];
}

export interface ParameterProvenanceRecord {
  field: string;
  source: ParameterSource;
  confidence: number;
  requires_confirmation: boolean;
}

export interface DefinedMarketContext {
  instrument: string;
  timeframe: string;
}

export interface DefinedSignalRules {
  entry_condition: string;
  filters: string[];
}

export interface DefinedPositionRules {
  exit_condition?: string | null;
  holding_period?: string | null;
}

export interface DefinedBacktestBounds {
  test_period: string;
  cost_assumptions: string;
}

export interface DefinedExperimentSpec {
  research_question: string;
  hypothesis?: string | null;
  market_context: DefinedMarketContext;
  signal_rules: DefinedSignalRules;
  position_rules: DefinedPositionRules;
  backtest_bounds: DefinedBacktestBounds;
  provenance_audit: ParameterProvenanceRecord[];
}

export interface ResearchDefineRequest {
  experiment: ResearchExperiment;
}

export interface SimulatedTrade {
  trade_id: number;
  entry_bar_index: number;
  entry_date: string;
  entry_price: number;
  exit_bar_index: number;
  exit_date: string;
  exit_price: number;
  exit_reason: 'HOLDING_PERIOD_EXPIRY' | 'PROFIT_TARGET' | 'STOP_LOSS' | string;
  gross_pnl_pct: number;
  net_pnl_pct: number;
  friction_paid_pct: number;
  holding_bars: number;
  is_win: boolean;
}

export interface EquityPoint {
  date: string;
  equity: number;
  drawdown_pct: number;
  in_trade: boolean;
}

export interface BacktestMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  net_return_pct: number;
  gross_return_pct: number;
  friction_drag_pct: number;
  profit_factor: number;
  max_drawdown_pct: number;
  avg_trade_return_pct: number;
  avg_holding_bars: number;
  sharpe_ratio?: number | null;
}

export interface BacktestResult {
  experiment_id: string;
  instrument: string;
  timeframe: string;
  test_period: string;
  initial_capital: number;
  final_equity: number;
  metrics: BacktestMetrics;
  equity_curve: EquityPoint[];
  trades: SimulatedTrade[];
  execution_timing_convention: string;
  simulation_disclaimer: string;
  reproducible_seed: number;
}

export interface TestExecutionRequest {
  spec: DefinedExperimentSpec;
  initial_capital?: number;
}
