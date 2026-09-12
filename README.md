# TradeLens AI

> **Turn trading ideas into structured research experiments.**

TradeLens AI is an AI-powered Trading Research Assistant designed to help quantitative traders and researchers translate informal trading hypotheses into structured, reproducible experiments and actionable analysis.

---

## Architecture Overview

TradeLens AI uses a decoupled client-server architecture:

```
┌─────────────────────────┐               ┌──────────────────────────┐
│   React + TypeScript    │  REST (JSON)  │      FastAPI Backend     │
│   Tailwind CSS (Vite)   ├──────────────►│   Pydantic + Uvicorn     │
│   Port: 5173            │◄──────────────┤   Port: 8000             │
└─────────────────────────┘               └──────────────────────────┘
```

- **Frontend**: Modular React 19 + TypeScript application bundled with Vite and styled with Tailwind CSS. Includes typed API services, reactive state hooks, and component encapsulation.
- **Backend**: High-performance FastAPI ASGI backend with strict Pydantic schemas, modular routing, and clear separation across `api`, `core`, `models`, `schemas`, and `services`.

For deeper architecture details, see [docs/architecture.md](docs/architecture.md).

---

## Project Structure

```
trade-lens-ai/
├── frontend/             # React + TypeScript + Vite + Tailwind CSS
├── backend/              # Python + FastAPI + Pydantic + Uvicorn
├── docs/                 # Architecture and specifications
├── .gitignore            # Git ignore specification
├── .env.example          # Sample global environment variables
└── README.md             # Project documentation
```

---

## Quickstart & Setup

### Prerequisites

- **Python**: 3.10+ (tested with Python 3.12/3.14)
- **Node.js**: 18+ (tested with Node.js 24 LTS)
- **npm** or package manager of choice

---

### 1. Backend Setup

1. Navigate to the backend directory:
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

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

5. Start the backend development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. Verify the health endpoint:
   - Endpoint: `http://localhost:8000/api/health`
   - Interactive Docs (Swagger UI): `http://localhost:8000/docs`

---

### 2. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```

5. Open your browser at:
   - `http://localhost:5173`

---

## Available Development Commands

| Service | Command | Description |
| :--- | :--- | :--- |
| **Backend** | `uvicorn app.main:app --reload --port 8000` | Start FastAPI server with live reload |
| **Frontend** | `npm run dev` | Start Vite development server |
| **Frontend** | `npm run build` | Compile TypeScript and produce production bundle |
| **Frontend** | `npm run preview` | Preview production build locally |

---

## Health Check API Contract

- **Method**: `GET`
- **Route**: `/api/health`
- **Response**:
  ```json
  {
    "status": "ok",
    "service": "trade-lens-ai"
  }
  ```
