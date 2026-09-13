# TradeLens AI - Backend Service

FastAPI-powered asynchronous backend service managing quantitative experiment extraction, formal validation, deterministic backtest simulation, and research learning synthesis.

---

## Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py             # Health check endpoint (/api/health)
│   │   │   └── research.py           # Research lifecycle endpoints (/api/research/*)
│   │   ├── __init__.py
│   │   └── router.py                 # Combined API router
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                 # Settings (Pydantic BaseSettings) & environment loader
│   ├── models/                       # Domain models
│   ├── schemas/
│   │   ├── __init__.py               # Central schema exports
│   │   ├── health.py                 # Health check Pydantic schemas
│   │   └── research.py               # Experiment, Spec, Backtest, and Learn schemas
│   ├── services/
│   │   ├── __init__.py               # Central service exports
│   │   ├── backtest_engine.py        # Deterministic simulation, zero-lookahead order execution
│   │   ├── experiment_clarifier.py   # User clarification handler
│   │   ├── experiment_validator.py   # Research experiment validation & readiness rules
│   │   ├── research_analyzer.py      # Abstract analyzer, Mock & Gemini implementations
│   │   └── research_learner.py       # Rule-based research interpretation & evidence synthesizer
│   └── main.py                       # FastAPI application entrypoint & CORS middleware
├── tests/
│   ├── __init__.py
│   ├── test_backtest_engine.py       # Backtest execution & timing tests (14 tests)
│   ├── test_defined_experiment.py    # DEFINE stage provenance gate tests (12 tests)
│   ├── test_experiment_clarifier.py  # Clarification loop tests (9 tests)
│   ├── test_gemini_analyzer.py       # Gemini API integration tests (4 tests)
│   ├── test_research_analyzer.py     # Base analyzer & health tests (6 tests)
│   └── test_research_learner.py      # LEARN synthesis & evidence level tests (12 tests)
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
└── README.md                         # Backend service guide
```

---

## Environment Configuration

Configuration is loaded using Pydantic Settings in `app/core/config.py`:

| Variable | Type | Default | Description |
|:---|:---|:---|:---|
| `PROJECT_NAME` | `str` | `"TradeLens AI"` | Application display name |
| `API_V1_STR` | `str` | `"/api"` | API prefix |
| `HOST` | `str` | `"0.0.0.0"` | Bind host |
| `PORT` | `int` | `8000` | Bind port |
| `BACKEND_CORS_ORIGINS` | `list` | `["http://localhost:5173", ...]` | Allowed CORS origins for frontend |
| `RESEARCH_ANALYZER_PROVIDER` | `str` | `"mock"` (or `"gemini"`) | Analysis backend provider |
| `GEMINI_API_KEY` | `str` | `None` | Google GenAI API key (required if provider is `gemini`) |
| `GEMINI_MODEL` | `str` | `"gemini-2.5-flash"` | Gemini model selection |

### Analyzer Modes

1. **Mock Mode (`RESEARCH_ANALYZER_PROVIDER=mock`) [Recommended for development]**:
   - Operates completely offline without external network calls.
   - Deterministically extracts structured experiment parameters based on heuristic patterns.
   - Requires zero API keys.

2. **Gemini Mode (`RESEARCH_ANALYZER_PROVIDER=gemini`)**:
   - Uses the official `google-genai` SDK to call Google Gemini models.
   - Leverages structured JSON output (`response_schema=ResearchExperiment`) for extraction.
   - Requires setting `GEMINI_API_KEY`.

---

## Setup & Running

1. **Create and activate a virtual environment**:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

4. **Run development server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Verify server**:
   - Health endpoint: `http://localhost:8000/api/health`
   - OpenAPI Docs: `http://localhost:8000/docs`

---

## API Routes & Endpoints

All endpoints are registered under `/api`:

### 1. Health Check
- `GET /api/health` — Verifies service status and returns `{"status": "ok", "service": "trade-lens-ai"}`.

### 2. Research Lifecycle
- `POST /api/research/analyze` — Parses natural-language question into `ResearchExperiment`.
- `POST /api/research/clarify` — Applies user field clarifications to an experiment.
- `POST /api/research/define` — Strict safety gate projecting a READY experiment into `DefinedExperimentSpec`.
- `POST /api/research/test` — Simulates strategy execution with zero look-ahead bias and conservative fills.
- `POST /api/research/learn` — Synthesizes deterministic research observations and evidence level.

---

## Running Automated Tests

Run the full pytest suite from the repository root:
```powershell
.\backend\.venv\Scripts\pytest backend/tests -v
```
Or from the `backend/` directory:
```bash
pytest tests -v
```

The test suite contains 57 automated tests covering:
- Mock and Gemini analyzer parsing
- Validation error handling and completeness rules
- Clarification loop parameter injection
- DEFINE provenance confirmation gate
- Zero look-ahead bias and conservative same-bar collision resolution
- Exact holding periods and friction deductions
- Deterministic reproducibility
- Mutually exclusive evidence levels and research honesty constraints
- Verification that TEST and LEARN make zero external network or LLM calls
