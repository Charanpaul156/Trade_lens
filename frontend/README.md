# TradeLens AI - Frontend Application

React 19 + TypeScript single-page application built on Vite and styled with Tailwind CSS.

## Directory Structure

```
frontend/
├── src/
│   ├── components/           # UI components (e.g. StatusBadge)
│   ├── pages/                # Views and screens (e.g. HomePage)
│   ├── services/             # API clients and HTTP communication
│   ├── types/                # TypeScript interfaces (HealthResponse, etc.)
│   ├── hooks/                # React custom hooks (useHealthCheck, etc.)
│   ├── lib/                  # Shared utilities (clsx/tailwind-merge)
│   ├── App.tsx               # Root component
│   ├── main.tsx              # DOM mounting
│   └── index.css             # Tailwind base styles
├── package.json              # Project dependencies
├── vite.config.ts            # Vite bundler config
├── tailwind.config.js        # Tailwind CSS config
├── tsconfig.json             # TypeScript compiler config
├── .env.example              # Frontend environment variables template
└── README.md
```

## Setup & Running

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   ```

   Verify `VITE_API_BASE_URL` points to your backend instance (default `http://localhost:8000`).

3. Start development server:
   ```bash
   npm run dev
   ```

4. Build for production:
   ```bash
   npm run build
   ```
