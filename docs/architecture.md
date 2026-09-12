# TradeLens AI Architecture Overview

TradeLens AI is designed to turn qualitative trading ideas into structured, verifiable quantitative research experiments.

## Architectural Principles

1. **Separation of Concerns**:
   - **Frontend**: Dedicated React single-page application focusing on interactive research workflows, hypothesis definition, parameter tuning, and research report visualization.
   - **Backend**: Clean FastAPI service providing modular REST endpoints, schema validation, and decoupled service orchestration.

2. **Decoupled API Contract**:
   - The frontend communicates with the backend via explicit typed schema contracts.
   - Base URLs and environment specific settings are injected via environment variables (`VITE_API_BASE_URL`).

3. **Incremental Extensibility**:
   - The system is engineered to cleanly host future capabilities without architectural refactoring:
     - LLM Prompting & Reasoning pipelines (Service Layer)
     - Market Data Ingestion & Providers (Data Layer / Services)
     - Hypothesis Formulation & Experiment Runs (Models / Schemas)
     - Backtesting Engine execution (Services / Tasks)

---

## Directory Structure

```
trade-lens-ai/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # API Route Handlers & Central Router
│   │   │   └── routes/       # Endpoint definitions (health, etc.)
│   │   ├── core/             # App configuration, settings, security
│   │   ├── models/           # Domain entities and ORM/database schemas
│   │   ├── schemas/          # Pydantic request/response validation
│   │   ├── services/         # Business logic and external service integrations
│   │   └── main.py           # FastAPI ASGI entrypoint & middleware
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Backend environment variables
│   └── README.md
├── frontend/                 # React + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # High-level views and screen layouts
│   │   ├── services/         # API clients and HTTP abstractions
│   │   ├── types/            # TypeScript interfaces and types
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Shared utilities and helpers
│   │   ├── App.tsx           # Main application component
│   │   └── main.tsx          # React DOM mounting
│   ├── package.json          # Node dependencies and scripts
│   ├── .env.example          # Frontend environment variables
│   └── README.md
├── docs/                     # Project documentation
│   └── architecture.md       # Architecture specifications
├── .gitignore                # Root git ignore rules
├── .env.example              # Root environment template
└── README.md                 # Primary project guide
```
