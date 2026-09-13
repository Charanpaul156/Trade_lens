# TradeLens AI

> **Quantitative Trading Research Assistant: From Informal Ideas to Structured Experiments**

TradeLens AI is a research prototype that transforms natural-language trading questions into structured, mathematically bounded quantitative research experiments. It guides researchers through a formal six-stage lifecycle: **ASK → ANALYZE → CLARIFY → DEFINE → TEST → LEARN**.

> [!IMPORTANT]
> **Research Prototype Disclaimer**: TradeLens AI is an academic and research prototype designed for strategy formulation and methodology testing. It is **not** a production trading system, does **not** connect to live brokerages, does **not** execute real capital trades, and does **not** provide investment or financial advice.

---

## 1. The Research Lifecycle

TradeLens AI enforces a structured, step-by-step quantitative research pipeline to eliminate ambiguous assumptions and prevent methodological errors:

```
┌─────────┐      ┌───────────┐      ┌───────────┐      ┌──────────┐      ┌──────────┐      ┌───────────┐
│   ASK   ├─────►│  ANALYZE  ├─────►│  CLARIFY  ├─────►│  DEFINE  ├─────►│   TEST   ├─────►│   LEARN   │
└─────────┘      └───────────┘      └───────────┘      └──────────┘      └──────────┘      └───────────┘
Natural-          AI/Mock            User Confirms       Locked Spec       Deterministic     Empirical
Language          Parameter          Unresolved          & Provenance      Simulation        Synthesis &
Hypothesis        Extraction         Ambiguities         Safety Gate       (No Lookahead)    Evidence Tier
```

1. **ASK**:
   The researcher submits an informal trading research question in natural language (e.g., *"Does buying NIFTY when daily RSI drops below 30 yield positive 5-day returns?"*).
2. **ANALYZE**:
   The system parses the question into a structured `ResearchExperiment` schema, extracting market context, signal conditions, position exit rules, and backtest bounds. It identifies missing or ambiguous parameters. Works with both offline deterministic mock analysis and Google Gemini models.
3. **CLARIFY**:
   The user explicitly confirms default parameters or supplies missing parameters through an interactive clarification interface. Parameters are never silently guessed or assumed.
4. **DEFINE**:
   A backend safety gate validates that all execution-critical parameters have explicit provenance (`USER_EXPLICIT` or confirmed `AI_INFERRED`) and zero unresolved items, locking the experiment into a canonical `DefinedExperimentSpec` execution contract.
5. **TEST**:
   The locked specification is executed by a deterministic backtest simulation engine using synthetic reference data. Enforces strict zero look-ahead bias ($t$ close signal $\to t+1$ open fill), conservative same-bar collision handling, and explicit friction modeling.
6. **LEARN**:
   A deterministic, rule-based synthesis engine evaluates simulation output without an LLM, generating structured performance observations, friction drag audits, risk assessments, methodological limitations, and prioritized research questions, categorized into mutually exclusive evidence tiers.

---

## 2. System Architecture

TradeLens AI follows a decoupled client-server architecture with strict schema boundaries:

```
┌────────────────────────────────────────────────────────┐
│                   Frontend (Client)                    │
│      React 19 + TypeScript + Vite + Tailwind CSS       │
│                  Port: 5173 (Default)                  │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / REST (JSON)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Backend (Server)                     │
│              FastAPI + Pydantic + Uvicorn              │
│                  Port: 8000 (Default)                  │
├────────────────────────────────────────────────────────┤
│ Research Services:                                     │
│  • research_analyzer.py   (Extraction & Parsing)       │
│  • experiment_validator.py (Schema & Consistency Rules)│
│  • experiment_clarifier.py (Interactive Clarifications)│
│  • backtest_engine.py      (Deterministic Simulation)  │
│  • research_learner.py     (Deterministic Synthesis)   │
└────────────────────────────────────────────────────────┘
```

The FastAPI backend owns all validation logic, provenance safety gates, deterministic synthetic data generation, trade simulation, and learning synthesis. The React frontend provides the reactive interactive user interface for each phase.

---

## 3. Project Structure

```
Trade Lens/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── health.py             # Health check endpoint (/api/health)
│   │   │   │   └── research.py           # Research lifecycle endpoints (/api/research/*)
│   │   │   └── router.py                 # Central API route registration
│   │   ├── core/
│   │   │   └── config.py                 # Pydantic Settings & environment loader
│   │   ├── models/                       # Domain models
│   │   ├── schemas/
│   │   │   ├── health.py                 # Health check response schemas
│   │   │   └── research.py               # Experiment, Spec, Backtest & Learn schemas
│   │   ├── services/
│   │   │   ├── backtest_engine.py        # Deterministic simulation & order execution engine
│   │   │   ├── experiment_clarifier.py   # Parameter clarification handler
│   │   │   ├── experiment_validator.py   # Formal validation & consistency rules
│   │   │   ├── research_analyzer.py      # Abstract analyzer, Mock & Gemini implementations
│   │   │   └── research_learner.py       # Rule-based research interpretation engine
│   │   └── main.py                       # ASGI app initialization & CORS middleware
│   ├── tests/
│   │   ├── test_backtest_engine.py       # Simulation, timing & collision tests (14 tests)
│   │   ├── test_defined_experiment.py    # DEFINE safety gate tests (12 tests)
│   │   ├── test_experiment_clarifier.py  # Clarification loop tests (9 tests)
│   │   ├── test_gemini_analyzer.py       # Gemini API integration tests (4 tests)
│   │   ├── test_research_analyzer.py     # Base analyzer & health tests (6 tests)
│   │   └── test_research_learner.py      # LEARN synthesis & evidence level tests (12 tests)
│   ├── .env.example                      # Backend environment template
│   ├── requirements.txt                  # Python dependencies
│   └── README.md                         # Backend service guide
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BacktestResultView.tsx    # Phase 4 TEST: Equity curve, metrics & ledger
│   │   │   ├── DefinedExperimentView.tsx # Phase 3 DEFINE: Locked spec & provenance audit
│   │   │   ├── LearnReportView.tsx       # Phase 5 LEARN: Evidence tier & synthesis report
│   │   │   ├── MissingInfoCard.tsx       # Phase 2 CLARIFY: Parameter input card
│   │   │   ├── ProvenanceBadge.tsx       # Parameter source & confidence badge
│   │   │   ├── ResearchAnalyzerView.tsx  # Phase 1 ASK & ANALYZE: Research question input
│   │   │   └── StatusBadge.tsx           # Health check indicator
│   │   ├── hooks/                        # Custom React hooks (useHealthCheck)
│   │   ├── pages/
│   │   │   └── HomePage.tsx              # Main dashboard view
│   │   ├── services/
│   │   │   └── api.ts                    # Typed API client for all research endpoints
│   │   ├── types/
│   │   │   ├── health.ts                 # Health types
│   │   │   └── research.ts               # Complete research lifecycle TypeScript types
│   │   ├── App.tsx                       # Root UI container
│   │   └── main.tsx                      # Vite React entrypoint
│   ├── .env.example                      # Frontend environment template
│   ├── package.json                      # Node dependencies & build scripts
│   └── README.md                         # Frontend client guide
├── docs/
│   └── architecture.md                   # Detailed technical design document
└── README.md                             # Authoritative project README
```

---

## 4. Setup & Installation

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.12 / 3.14)
- **Node.js**: 18+ (tested on Node.js 22 / 24 LTS)
- **npm** or preferred package manager

---

### Backend Setup

The backend virtual environment is located at `backend/.venv/`:

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

---

### Frontend Setup

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

---

## 5. Configuration & Analyzer Modes

### Recommended First-Run: Offline Mock Mode
By default, TradeLens AI supports a completely offline, zero-cost mock analyzer. It requires **no external API keys** and allows full exploration of the entire research lifecycle.

In `backend/.env`:
```ini
PROJECT_NAME="TradeLens AI"
API_V1_STR="/api"
HOST=0.0.0.0
PORT=8000
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:3000"]

# Recommended for local offline development:
RESEARCH_ANALYZER_PROVIDER=mock
```

### Optional: Google Gemini Mode
To enable live AI parameter extraction via Google's Gemini models:

1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. In `backend/.env`, set:
   ```ini
   RESEARCH_ANALYZER_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
> [!NOTE]
> The Gemini API key is maintained securely on the backend and is **never** transmitted to the frontend.

### Frontend Configuration
In `frontend/.env`:
```ini
VITE_API_BASE_URL=http://localhost:8000
```

---

## 6. Running the Application

### 1. Start the Backend Service
From the `backend/` directory (with `.venv` activated):
```bash
uvicorn app.main:app --reload --port 8000
```
- Backend API root: `http://localhost:8000`
- Interactive OpenAPI Docs (Swagger): `http://localhost:8000/docs`
- Health check verification: `http://localhost:8000/api/health`

### 2. Start the Frontend Client
From the `frontend/` directory:
```bash
npm run dev
```
- Web Application UI: `http://localhost:5173`

---

## 7. API Reference

All research endpoints are completely stateless:

| Method | Endpoint | Description | Input Schema | Output Schema | Key Properties |
|:---|:---|:---|:---|:---|:---|
| `GET` | `/api/health` | System health check | None | `HealthResponse` | Operational verification |
| `POST` | `/api/research/analyze` | Extracts experiment from natural language | `ResearchAnalyzeRequest` | `ResearchAnalyzeResponse` | Supports mock or Gemini; flags missing parameters |
| `POST` | `/api/research/clarify` | Applies explicit user parameter clarifications | `ResearchClarifyRequest` | `ResearchExperiment` | Revalidates completeness; updates provenance |
| `POST` | `/api/research/define` | Locks experiment into defined execution contract | `ResearchDefineRequest` | `DefinedExperimentSpec` | Strict provenance safety gate; zero unconfirmed assumptions |
| `POST` | `/api/research/test` | Runs deterministic backtest simulation | `TestExecutionRequest` | `BacktestResult` | Zero look-ahead bias; conservative collision fills |
| `POST` | `/api/research/learn` | Generates transparent research interpretation | `ResearchLearnRequest` | `LearnReport` | Deterministic rule-based; mutually exclusive evidence tiers |

---

## 8. TEST Simulation Methodology

The TEST engine simulates strategy behavior against deterministic synthetic reference data under strict quantitative constraints:

- **Synthetic Reference Data**: Generates price bars using a pseudo-random Linear Congruential Generator (LCG) seeded deterministically from the SHA-256 hash of the `DefinedExperimentSpec`. Identical specifications produce bit-for-bit identical price series, trades, and metrics.
- **Zero Look-Ahead Bias**: Signal evaluation is isolated strictly to candle $t$ close. Entry orders execute at candle $t+1$ open. Intra-bar data for candle $t+1$ is never visible when deciding whether an entry condition was triggered.
- **Conservative Same-Bar Collision Resolution**: When a candle's High and Low cross both the profit target and the stop-loss price and intra-bar sequence cannot be determined, the engine conservatively presumes `STOP_LOSS` triggered first.
- **Holding Period Exits**: Positions hold for exactly $H$ forward bars, exiting at candle $t+1+H$ open.
- **Single Active Position**: No pyramiding or concurrent entries while a position is active.
- **Friction Accounting**: Slippage and transaction friction are parsed from `cost_assumptions` (e.g., `0.05% slippage per side`), subtracted from gross trade returns, and tracked separately as friction drag.
- **Descriptive Sharpe Ratio**: Annualized Sharpe ratio is computed purely descriptively and is **not** presented as evidence of statistical significance.

---

## 9. LEARN Evidence Levels

The LEARN synthesis engine classifies simulation results into four mutually exclusive evidence tiers using strict deterministic priority:

```python
if total_trades == 0:
    return "SYNTHETIC_INSUFFICIENT_DATA"
elif total_trades < 3:
    return "SYNTHETIC_INSUFFICIENT_DATA"
elif gross_return_pct > 0 and net_return_pct <= 0:
    return "SYNTHETIC_FRICTION_DOMINATED"
elif net_return_pct <= 0:
    return "SYNTHETIC_NEGATIVE_EDGE"
else:
    return "SYNTHETIC_CANDIDATE_FOR_REAL_DATA"
```

1. **`SYNTHETIC_INSUFFICIENT_DATA`**: Zero trades or sample size $< 3$. High statistical variance prevents reliable observations.
2. **`SYNTHETIC_FRICTION_DOMINATED`**: Gross return is positive, but transaction costs and slippage turn net return negative.
3. **`SYNTHETIC_NEGATIVE_EDGE`**: Net return is negative, indicating an unfavorable simulated strategy expectancy.
4. **`SYNTHETIC_CANDIDATE_FOR_REAL_DATA`**: Net return remains positive after friction with adequate trade count. Warranted for validation against historical tick/OHLC data.

> [!CAUTION]
> Evidence levels apply strictly to synthetic reference simulations. They are **not** guarantees of live trading edge or future profitability.

---

## 10. Research Honesty & Limitations

- **Synthetic Reference Only**: Results are illustrative demonstrations of rules and timing, not real market historical returns.
- **Single Deterministic Path**: Does not evaluate multi-path stochastic variation across thousands of Monte Carlo simulations.
- **Stationary Distribution**: Synthetic reference bars do not model liquidity crises, gap openings, or structural regime changes.
- **No Optimization / Advice**: The engine formulates empirical research questions (parameter sensitivity, regime stress-testing, historical validation) and strictly refrains from giving parameter optimization or trade execution advice.

---

## 11. Testing & Verification

The repository contains automated unit and integration tests covering the full research lifecycle:

### Running Backend Pytest Suite (57 Tests)
From the repository root:
```powershell
# Windows PowerShell
.\backend\.venv\Scripts\pytest backend/tests -v
```
Or from within `backend/`:
```bash
pytest tests -v
```

### Running Frontend Production Build
From the `frontend/` directory:
```bash
npm run build
```
Compiles all TypeScript components (`tsc -b`) and bundles production assets with Vite (`vite build`).

---

## 12. Interactive Demo Flow

Follow this walkthrough to experience the entire lifecycle:

1. **ASK**: In the dashboard, enter a research query:
   > *"Does buying NIFTY after a 2% single-day drop yield positive returns over a 5-day holding period?"*
2. **ANALYZE**: Click **Analyze Research Question**. The system extracts:
   - Instrument: `NIFTY`
   - Timeframe: `1D`
   - Entry Condition: `Close drops >= 2.0% in one day`
   - Holding Period: `5 trading days maximum`
   - Backtest Bounds: `2020-01-01 to 2024-01-01`
3. **CLARIFY**: The system flags that `exit_condition` requires confirmation. Confirm the suggested take-profit/stop-loss or supply custom values.
4. **DEFINE**: Click **Lock & Define Experiment**. The backend validates provenance, checks critical fields, and generates the `DefinedExperimentSpec` audit card.
5. **TEST**: Click **Run Backtest Simulation**. The deterministic engine executes a zero-lookahead backtest, rendering the performance KPI grid, SVG equity curve, and trade ledger.
6. **LEARN**: Click **Generate Research Synthesis & Learnings**. The system synthesizes the `LearnReport`, classifies the evidence level, and displays concrete next research steps.
