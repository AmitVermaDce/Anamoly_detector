# Anomaly Detection Application

A production-grade full-stack application for detecting anomalies in Snowflake data using multiple algorithms, with an interactive React dashboard.

## Architecture

```
anomaly-detection-app/
├── backend/          FastAPI + Snowflake + scikit-learn + Azure Key Vault
│   ├── app/
│   │   ├── core/     Config, logging, exceptions
│   │   ├── db/       Snowflake client, SQL query loader, Azure CredentialManager
│   │   ├── models/   Pydantic schemas + detector implementations
│   │   ├── services/ Data service + anomaly detection orchestration
│   │   ├── api/v1/   API routes (health, anomaly detection)
│   │   ├── sql/      All queries in a single .sql file
│   │   └── config/   Azure + Snowflake config (config.yaml)
│   └── tests/        Pytest suite
├── frontend/         React 18 + Vite + TypeScript + TailwindCSS
│   ├── src/
│   │   ├── components/  UI, layout, charts
│   │   ├── pages/       Dashboard, AnomalyDetails
│   │   ├── services/    Class-based API client
│   │   ├── store/       Zustand state management
│   │   └── hooks/       React Query + custom hooks
│   └── Dockerfile
├── docker-compose.yml
├── start.sh            One-command launcher
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Snowflake account
- Docker & Docker Compose (optional)

## Quick Start (Single Command)

```bash
./start.sh
```

This builds the frontend, installs backend dependencies, and starts the unified server on `http://localhost:8000`.

### What `./start.sh` Does
1. Validates Python 3.11+ and Node.js 20+
2. Creates `backend/.env` from `.env.example` if missing
3. Installs frontend dependencies (`npm install`)
4. Builds the React app into `frontend/dist/`
5. Creates Python virtual environment (`.venv`) if missing
6. Installs backend dependencies (`pip install -e ".[dev]"`)
7. Starts **one** uvicorn server on port `8000`

### After It Runs

| URL | What |
|-----|------|
| `http://localhost:8000/` | **Dashboard** (React SPA) |
| `http://localhost:8000/docs` | Swagger API docs |
| `http://localhost:8000/api/v1` | API base path |

## Azure Key Vault Integration

The app supports fetching Snowflake credentials from Azure Key Vault using Managed Identity.

### Config File

Edit `backend/app/config/config.yaml`:

```yaml
key_vault:
  name: your-keyvault-name
  managed_identity_client_id: your-managed-identity-client-id

snowflake:
  database: YOUR_DATABASE
  warehouse: YOUR_WAREHOUSE
  schema: YOUR_SCHEMA
  role: YOUR_ROLE
  user_domain: optum.com
```

### Secret Names Expected in Key Vault

- `snowflake-secret-user`
- `snowflake-private-key`
- `snowflake-key-passphrase`
- `snowflake-secret-account`
- `snowflake-secret-role`

### Fallback

If Key Vault is unreachable, the app automatically falls back to `.env` / environment variables.

## Docker

```bash
docker-compose up --build
```

Open `http://localhost:8000/`.

## Dev Mode (Separate Servers)

```bash
# Terminal 1 — Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev   # runs on :5173, proxies /api to :8000
```

## Anomaly Detection Algorithms

1. **Isolation Forest** — Tree-based unsupervised detection
2. **Z-Score** — Statistical thresholding for normal distributions
3. **DBSCAN** — Density-based clustering for arbitrary distributions

## Key Design Decisions

- **Class-based Python** — Every module uses OOP with dependency injection
- **Strategy Pattern** — Detectors inherit from `BaseDetector`; algorithms are swappable via API
- **Single SQL File** — All queries live in `backend/app/sql/queries.sql` with named tags
- **React Query + Zustand** — Server state vs. client state cleanly separated
- **Tailwind + CSS Variables** — Dark/light mode via CSS custom properties
