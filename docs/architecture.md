# TradeLens AI: Technical Architecture Specification

## 1. System Overview

TradeLens AI is an AI-assisted trading research platform that translates informal natural-language trading hypotheses into structured, clarified, mathematically validated, tested, and synthesized research experiments.

The platform enforces a strict six-stage research lifecycle:
$$\text{ASK} \longrightarrow \text{ANALYZE} \longrightarrow \text{CLARIFY} \longrightarrow \text{DEFINE} \longrightarrow \text{TEST} \longrightarrow \text{LEARN}$$

```
┌────────────────────────────────────────────────────────┐
│                   Frontend (Client)                    │
│      React 19 + TypeScript + Vite + Tailwind CSS       │
│  - ResearchAnalyzerView     - MissingInfoCard          │
│  - ProvenanceBadge          - DefinedExperimentView    │
│  - BacktestResultView       - LearnReportView          │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON (Stateless)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Backend (Server)                     │
│              FastAPI + Pydantic + Uvicorn              │
├────────────────────────────────────────────────────────┤
│ API Layer:                                             │
│  • /api/health                                         │
│  • /api/research/analyze   • /api/research/clarify     │
│  • /api/research/define    • /api/research/test        │
│  • /api/research/learn                                 │
├────────────────────────────────────────────────────────┤
│ Service Layer:                                         │
│  1. research_analyzer.py   (Extraction & Ambiguity)    │
│  2. experiment_clarifier.py (Explicit Parameter Update)│
│  3. experiment_validator.py (Readiness Verification)   │
│  4. backtest_engine.py      (Deterministic Simulation) │
│  5. research_learner.py     (Deterministic Synthesis)  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Principles

1. **Stateless & Decoupled**:
   - The application does not rely on a persistent database, user sessions, or browser cookies.
   - Experiments and specifications flow through typed Pydantic payloads across REST boundaries.

2. **Single Canonical Source of Truth**:
   - `ResearchExperiment` serves as the primary mutable source of truth during formulation.
   - Once validated, it projects into an immutable execution contract: `DefinedExperimentSpec`.

3. **No Hidden Assumptions (Provenance Tracking)**:
   - Every parameter tracks its origin (`USER_EXPLICIT` vs `AI_INFERRED`), confidence score (0.0 to 1.0), and whether it requires explicit confirmation (`requires_confirmation`).
   - The DEFINE safety gate strictly blocks execution if any parameter has unconfirmed inferences.

4. **Zero Look-Ahead Bias & Determinism**:
   - All simulated orders evaluate signals strictly on historical data available up to candle $t$ close.
   - Entry orders execute at candle $t+1$ open.
   - The backtesting and learning engines are completely offline and deterministic: identical experiment specifications produce bit-for-bit identical price series, trades, equity curves, and learning reports.

5. **Separation of LLM and Deterministic Computation**:
   - An LLM (Google Gemini) is utilized **only** in Phase 1 (ANALYZE) for unstructured text extraction.
   - DEFINE, TEST, and LEARN are deterministic and do not rely on LLM-generated decisions.

---

## 3. Backend Service Responsibilities

### 1. `ResearchAnalyzer` (`app/services/research_analyzer.py`)
- Defines the abstract base analyzer contract `BaseResearchAnalyzer`.
- **`DeterministicMockAnalyzer`**: Fast, offline, heuristic-based parameter extractor. Requires zero API keys and zero network connectivity.
- **`GeminiResearchAnalyzer`**: Calls the Google Gemini API (`google-genai` SDK) using structured output schemas (`response_schema=ResearchExperiment`).
- Extracts `instrument`, `timeframe`, `entry_condition`, `exit_condition`, `holding_period`, `test_period`, and `cost_assumptions`.
- Identifies missing or ambiguous parameters and populates `missing_information`.

### 2. `ExperimentClarifier` (`app/services/experiment_clarifier.py`)
- Accepts structured user clarifications (`FieldClarification`) to update missing or ambiguous experiment parameters.
- Updates parameter source to `USER_EXPLICIT`, sets confidence to 1.0, and marks `requires_confirmation = False`.
- Re-runs validation to promote status to `READY` when all mandatory parameters are resolved.

### 3. `ExperimentValidator` (`app/services/experiment_validator.py`)
- Validates completeness and consistency of `ResearchExperiment`.
- Ensures at least one valid position exit rule (`exit_condition` or `holding_period`) is defined.
- Sets status to `NEEDS_CLARIFICATION` if critical fields are absent.

### 4. `BacktestEngine` (`app/services/backtest_engine.py`)
- Enforces internal separation of concerns:
  1. **Data Generation**: Generates synthetic OHLC reference bars using a pseudo-random Linear Congruential Generator (LCG) seeded with the SHA-256 hash of the `DefinedExperimentSpec`.
  2. **Signal Evaluation**: Evaluates indicators and entry conditions strictly at candle $t$ close.
  3. **Order Execution & Position Management**: Executes entries at candle $t+1$ open. Employs conservative same-bar collision handling (assuming `STOP_LOSS` occurs first if both bounds are crossed in a single bar).
  4. **Friction Accounting**: Deducts slippage per side, tracking gross return, net return, and friction drag separately.
  5. **Metrics Calculation**: Computes robust summary statistics without `NaN` or `Infinity`. Sharpe ratio is descriptive only.

### 5. `ResearchLearner` (`app/services/research_learner.py`)
- Evaluates `BacktestResult` deterministically without LLM calls.
- Classifies results into mutually exclusive evidence tiers.
- Formulates scientific research directions (parameter sensitivity, regime filtering, historical tick testing) while strictly avoiding trading advice.

---

## 4. Canonical Specification Flow & DEFINE Safety Gate

```
                  ┌──────────────────────┐
                  │  ResearchExperiment  │  (Mutable, contains provenance & missing info)
                  └──────────┬───────────┘
                             │
                  POST /api/research/define
                             │
            ┌────────────────▼────────────────┐
            │   DEFINE Safety Gate Checks:    │
            │  1. Status == READY?            │
            │  2. len(missing_info) == 0?     │
            │  3. Critical fields non-empty?  │
            │  4. requires_confirmation==False│
            │  5. Exit rule present & confirmed│
            └────────────────┬────────────────┘
                             │ (Pass)
                             ▼
                ┌──────────────────────────┐
                │   DefinedExperimentSpec  │  (Immutable execution contract)
                └──────────────────────────┘
```

The DEFINE endpoint enforces that no unconfirmed assumption or unverified AI-inferred default can ever reach the simulation engine.

---

## 5. TEST Simulation Methodology & Constraints

- **Deterministic Reference Data**: Generated from the experiment specification hash. Results are illustrative and explicitly labeled as synthetic reference data.
- **Timing Convention**: Signal on candle $t$ close $\to$ Fill on candle $t+1$ open.
- **Same-Bar Target/Stop Collision**: Conservative stop-first convention.
- **Holding Period Exits**: Positions exit at candle $t+1+H$ open.
- **Descriptive Sharpe**: Descriptive in this prototype; never claimed as proof of statistical significance.

---

## 6. LEARN Evidence Levels & Priority

The LEARN engine evaluates results using strict mutually exclusive deterministic priority:

$$\text{total\_trades} \in \{0, 1, 2\} \implies \mathbf{SYNTHETIC\_INSUFFICIENT\_DATA}$$
$$\text{gross\_return} > 0 \land \text{net\_return} \le 0 \implies \mathbf{SYNTHETIC\_FRICTION\_DOMINATED}$$
$$\text{net\_return} \le 0 \implies \mathbf{SYNTHETIC\_NEGATIVE\_EDGE}$$
$$\text{net\_return} > 0 \implies \mathbf{SYNTHETIC\_CANDIDATE\_FOR\_REAL\_DATA}$$

---

## 7. Research Honesty & Boundaries

1. **Synthetic Data**: Never described as calibrated or proof of live-market performance.
2. **No Trading Advice**: The engine formulates empirical research questions and hypotheses, never execution instructions or position sizing advice.
3. **No Optimization**: The engine does not curve-fit or search parameter space.
4. **Real Data Validation Requirement**: All conclusions explicitly advise testing on actual historical tick/OHLC data before drawing quantitative inferences.
