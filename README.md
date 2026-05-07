# Anomaly Detection API

A production-grade Python API for detecting anomalies in Snowflake data using multiple algorithms, with a self-contained HTML dashboard served directly from FastAPI.

## Architecture

```
anomaly-detection-app/
├── src/
│   └── anomaly_detection/
│       ├── app.py              FastAPI application + lifespan
│       ├── state.py            Module-level singletons (config, snowflake_client)
│       ├── config.py           Pydantic Settings (env) + YAML Config
│       ├── exceptions.py       Custom exception hierarchy
│       ├── logger.py             One-time loguru configuration
│       ├── api/
│       │   ├── router.py         API v1 router aggregation
│       │   ├── schemas.py        Pydantic request/response models
│       │   └── endpoints/
│       │       ├── health.py
│       │       └── anomaly.py
│       ├── database/
│       │   ├── snowflake.py      Snowflake connection manager
│       │   ├── queries.py        Named SQL query loader
│       │   └── credentials.py    Azure Key Vault integration
│       ├── detection/
│       │   ├── base.py           Abstract BaseDetector
│       │   ├── factory.py        Registry + create_detector()
│       │   ├── isolation_forest.py
│       │   ├── zscore.py
│       │   └── dbscan.py
│       ├── services/
│       │   ├── detection.py      Orchestration service
│       │   └── data.py           Query + fetch service
│       ├── templates/
│       │   └── index.html        Vanilla JS dashboard
│       └── config/
│           └── config.yaml       Detection levels + paths
├── queries/
│   └── query.sql            Named SQL queries (-- @query markers)
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── start.sh                    One-command launcher
└── .env.example
```

## Prerequisites

- Python 3.9+
- Snowflake account (for data source)
- Azure Key Vault (optional — falls back to .env)

## Quick Start

```bash
./start.sh
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | Dashboard |
| `http://localhost:8000/docs` | Swagger API docs |
| `http://localhost:8000/api/v1/health` | Health check |

## Configuration

### Environment Variables (`.env`)

```bash
# Required for Snowflake
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=your-schema
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_ROLE=your-role

# Optional: key-pair auth
SNOWFLAKE_AUTHENTICATOR=keypair
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/key.pem
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your-passphrase
```

### `config.yaml`

```yaml
key_vault:
  name: "your-keyvault-name"
  managed_identity_client_id: "your-managed-identity-client-id"

snowflake:
  database: "database-name"
  warehouse: "your-warehouse"
  schema: "schema-name"

paths:
  queries_dir: "queries"

query_file: "query.sql"

detection_levels:
  by_client:
    group_cols: ["CLIENT_NAME"]
  by_category:
    group_cols: ["ISSUE_CATEGORY"]

# Override defaults
detection_params:
  zscore_threshold: 3.0
  rolling_window: 30
```

## SQL Query Format

Queries are parsed from a single `.sql` file using named markers:

```sql
-- @query by_client
SELECT ISSUE_RECEIVED AS DT, CLIENT_NAME, COUNT(DISTINCT NUMBER) AS ISSUE_VOLUME
FROM CDW_PRD_CALL_DB.CDW_COVE_RPT_SC.ISSUE_BASE_DETAIL_FACT_TABLE
WHERE source_system = 'OptumRxServiceNow'
GROUP BY ALL;

-- @query by_category
SELECT ...
```

## Detection Algorithms

| Algorithm | Description |
|-----------|-------------|
| **Isolation Forest** | Tree-based isolation of anomalies |
| **Z-Score** | Statistical thresholding for normal distributions |
| **DBSCAN** | Density-based clustering for arbitrary distributions |

## Docker

```bash
docker-compose up --build
```

## Key Design Decisions

- **No Node.js / npm** — Dashboard is vanilla HTML/JS served by Jinja2Templates
- **src layout** — All code lives under `src/anomaly_detection/`
- **Loguru once** — `configure_logging()` called once in lifespan, modules import `logger` directly
- **State singletons** — Config, credential manager, and Snowflake client created once in lifespan
- **Detection factory** — Algorithms register themselves in `detection/factory.py`, no manual wiring
- **Connection reuse** — Snowflake connections are kept alive via `client_session_keep_alive` and reused across requests

## License

MIT
