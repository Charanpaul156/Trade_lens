# TradeLens AI - Frontend Client

Single-page quantitative research interface built with React 19, TypeScript, Tailwind CSS, and Vite.

---

## Directory Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── BacktestResultView.tsx    # Phase 4 TEST: Interactive equity curve, KPI grid, and trade ledger
│   │   ├── DefinedExperimentView.tsx # Phase 3 DEFINE: Locked spec inspection & parameter provenance audit
│   │   ├── LearnReportView.tsx       # Phase 5 LEARN: Evidence tier badge, research findings & next steps
│   │   ├── MissingInfoCard.tsx       # Phase 2 CLARIFY: Interactive parameter resolution card
│   │   ├── ProvenanceBadge.tsx       # Parameter origin (USER_EXPLICIT / AI_INFERRED) & confidence badge
│   │   ├── ResearchAnalyzerView.tsx  # Phase 1 ASK & ANALYZE: Research question input and extraction display
│   │   └── StatusBadge.tsx           # Backend connectivity & health status indicator
│   ├── hooks/
│   │   └── useHealthCheck.ts         # Hook polling backend health and measuring latency
│   ├── lib/
│   │   └── utils.ts                  # Styling utilities (clsx & tailwind-merge)
│   ├── pages/
│   │   └── HomePage.tsx              # Main dashboard view hosting the research workflow
│   ├── services/
│   │   └── api.ts                    # Typed HTTP client for all research endpoints
│   ├── types/
│   │   ├── health.ts                 # Health check types
│   │   └── research.ts               # Complete TypeScript types for all 6 research lifecycle phases
│   ├── App.tsx                       # Root layout and theme container
│   ├── index.css                     # Tailwind CSS imports and theme utilities
│   └── main.tsx                      # React DOM mounting
├── package.json                      # Dependencies and build scripts
├── vite.config.ts                    # Vite bundler configuration
├── tailwind.config.js                # Tailwind theme extensions
├── tsconfig.json                     # TypeScript compiler configuration
├── .env.example                      # Frontend environment template
└── README.md                         # Frontend client documentation
```

---

## The Frontend Research Workflow

Frontend workflow supporting the research lifecycle from ANALYZE through LEARN, with the user's ASK serving as the initial input. The overall research lifecycle remains:

$$\text{ASK} \longrightarrow \text{ANALYZE} \longrightarrow \text{CLARIFY} \longrightarrow \text{DEFINE} \longrightarrow \text{TEST} \longrightarrow \text{LEARN}$$

The frontend interface supports each stage:

1. **ASK & ANALYZE (`ResearchAnalyzerView`)**:
   - User inputs a trading research query.
   - Triggers `analyzeResearchQuestion` against `/api/research/analyze`.
   - Renders extracted parameters along with confidence scores and provenance badges.

2. **CLARIFY (`MissingInfoCard` & `ProvenanceBadge`)**:
   - If any parameters are missing or require confirmation, the user is presented with interactive options to clarify or accept suggested defaults.
   - Calls `clarifyExperiment` against `/api/research/clarify`.

3. **DEFINE (`DefinedExperimentView`)**:
   - Once all parameters are resolved, user clicks **Lock & Define Experiment**.
   - Calls `defineExperiment` against `/api/research/define`.
   - Displays the formal hypothesis, complete parameter specifications, and a provenance audit checklist.

4. **TEST (`BacktestResultView`)**:
   - User clicks **Run Backtest Simulation**.
   - Calls `runBacktestSimulation` against `/api/research/test`.
   - Renders the synthetic simulation disclaimer, performance KPI metrics (Net Return, Gross Return, Friction Drag, Win Rate, Profit Factor, Max Drawdown, Sharpe), responsive SVG equity curve, and the complete trade ledger table.

5. **LEARN (`LearnReportView`)**:
   - User clicks **Generate Research Synthesis & Learnings**.
   - Calls `generateLearnReport` against `/api/research/learn`.
   - Displays the mutually exclusive evidence level badge (`SYNTHETIC_CANDIDATE_FOR_REAL_DATA`, `SYNTHETIC_FRICTION_DOMINATED`, etc.), executive summary, 3-column observations grid (Performance, Cost Drag, Risk), methodological boundaries, and recommended next research directions.

---

## Setup & Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Verify `VITE_API_BASE_URL` matches your backend address (default: `http://localhost:8000`).

3. **Start local development server**:
   ```bash
   npm run dev
   ```
   Access the web app at `http://localhost:5173`.

4. **Production Build & Verification**:
   ```bash
   npm run build
   ```
   Runs TypeScript type checking (`tsc -b`) and bundles production assets into `dist/`.
