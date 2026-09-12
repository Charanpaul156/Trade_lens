# TradeLens AI - Backend Service

FastAPI-powered asynchronous backend service for TradeLens AI.

## Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── health.py       # Health check route (/api/health)
│   │   ├── __init__.py
│   │   └── router.py           # Combined API router
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # App configuration and CORS settings
│   ├── models/                 # Domain & persistence models (for future phases)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── health.py           # Pydantic schemas for health endpoint
│   ├── services/               # Quantitative & AI services (for future phases)
│   └── main.py                 # FastAPI application entrypoint
├── requirements.txt            # Python dependencies
├── .env.example                # Backend environment template
└── README.md
```

## Setup & Running

1. Create and activate a virtual environment:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   ```

4. Run development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Test the Health Endpoint:
   ```bash
   curl http://localhost:8000/api/health
   ```

   Response:
   ```json
   {
     "status": "ok",
     "service": "trade-lens-ai"
   }
   ```
