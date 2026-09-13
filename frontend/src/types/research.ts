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

