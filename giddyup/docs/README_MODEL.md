# GiddyUpModel - Python Modeling Pipeline

**Python-first modeling stack for horse racing predictions**

Built: October 16, 2025

---

## 📋 Overview

GiddyUpModel is a modern MLOps pipeline for training, calibrating, and deploying horse racing win probability models. It sits alongside the existing Go API and publishes predictions to Postgres for consumption by the frontend.

### Architecture

```
Python Modeling                     Go API (Read-Only)
┌─────────────────┐                ┌──────────────────┐
│ Feature Eng     │                │                  │
│ (Polars/DuckDB) │                │  GET /signals/*  │
│       ↓         │                │                  │
│ Model Training  │                │  Reads from:     │
│ (LightGBM/XGB)  │                │  modeling.signals│
│       ↓         │                │  modeling.models │
│ Calibration     │                │  modeling.bets   │
│ (Isotonic)      │                │                  │
│       ↓         │                └──────────────────┘
│ Scoring/Pricing │                         ↑
│       ↓         │                         │
│ Publish Signals │─────────────────────────┘
│ (to Postgres)   │
└─────────────────┘
```

---

## ✅ Task 1 Complete: Bootstrap

### What Was Built

1. **Project Structure** - Python package with `uv`
2. **Database Schema** - `modeling` schema with 3 tables
3. **Signal Publisher** - Upsert logic for predictions
4. **Migration System** - SQL migrations with runner
5. **Smoke Test** - End-to-end verification

### Files Created

```
GiddyUpModel/giddyup/
├── pyproject.toml              # Project dependencies
├── .env                        # Database credentials
├── migrations/
│   └── 001_modeling_schema.sql # Schema DDL
├── src/giddyup/
│   ├── __init__.py
│   └── publish/
│       ├── __init__.py
│       └── signals.py          # Signal upsert logic
└── tools/
    ├── migrate.py              # Migration runner
    ├── seed_model.py           # Seed demo model
    └── smoke_signal.py         # Smoke test
```

---

## 🗄️ Database Schema

### modeling.models
Model registry - tracks trained models

| Column | Type | Description |
|--------|------|-------------|
| model_id | BIGSERIAL | Primary key |
| name | TEXT | Model name (e.g., `hrd_win_prob`) |
| version | TEXT | Version (e.g., `0.0.1`) |
| stage | TEXT | `production`, `staging`, `development` |
| artifact_uri | TEXT | MLflow artifact location |
| metrics_json | JSONB | Training metrics |
| created_at | TIMESTAMPTZ | Creation timestamp |

**Unique**: `(name, version)`

### modeling.signals
Predictions for upcoming races

| Column | Type | Description |
|--------|------|-------------|
| signal_id | BIGSERIAL | Primary key |
| as_of | TIMESTAMPTZ | When prediction was made |
| race_id | BIGINT | Race identifier (from racing.races) |
| horse_id | BIGINT | Horse identifier (from racing.horses) |
| model_id | BIGINT | Model that generated this signal |
| p_win | DOUBLE | Win probability |
| fair_odds_win | DOUBLE | Implied fair odds |
| best_odds_win | DOUBLE | Best available market odds |
| edge_win | DOUBLE | Expected value |
| kelly_fraction | DOUBLE | Kelly criterion stake |
| stake_units | DOUBLE | Recommended stake (units) |
| reasons_json | JSONB | Feature impacts/explanations |

**Unique**: `(as_of, race_id, horse_id, model_id)`

### modeling.bets
Actual bets placed for performance tracking

| Column | Type | Description |
|--------|------|-------------|
| bet_id | BIGSERIAL | Primary key |
| ts | TIMESTAMPTZ | Bet timestamp |
| race_id | BIGINT | Race identifier |
| horse_id | BIGINT | Horse identifier |
| side | TEXT | `win`, `ew`, `place` |
| odds | DOUBLE | Odds taken |
| stake | DOUBLE | Stake amount |
| clv_close_odds | DOUBLE | Closing Line Value |
| pnl | DOUBLE | Profit/Loss after settlement |

---

## 🚀 Quick Start

### 1. Run Migration

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/migrate.py
```

### 2. Seed Demo Model

```bash
uv run python tools/seed_model.py
```

### 3. Run Smoke Test

```bash
uv run python tools/smoke_signal.py
```

### 4. Verify in Database

```sql
-- Check models
SELECT * FROM modeling.models;

-- Check signals
SELECT race_id, horse_id, p_win, best_odds_win, edge_win
FROM modeling.signals
ORDER BY signal_id DESC
LIMIT 5;
```

---

## 📦 Dependencies

**Production:**
- `polars` - Fast dataframe operations
- `pyarrow` - Arrow format for Polars
- `duckdb` - SQL analytics on dataframes
- `lightgbm` - Gradient boosting (primary)
- `xgboost` - Gradient boosting (alternative)
- `scikit-learn` - ML utilities, calibration
- `mlflow` - Experiment tracking & model registry
- `sqlalchemy` - Database ORM
- `psycopg[binary]` - PostgreSQL driver
- `prefect` - Workflow orchestration
- `hydra-core` - Configuration management
- `pydantic` - Data validation
- `python-dotenv` - Environment variables

**Development:**
- `ruff` - Fast linter
- `mypy` - Type checking
- `black` - Code formatter

---

## 🔐 Environment Variables

Create `.env` in the project root:

```bash
# Database Connection
PG_DSN=postgresql+psycopg://postgres:password@localhost:5432/horse_db

# Timezone (for scheduling)
TZ=Europe/Madrid

# MLflow (optional - add later)
# MLFLOW_TRACKING_URI=http://localhost:5000
# MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
# AWS_ACCESS_KEY_ID=minio
# AWS_SECRET_ACCESS_KEY=miniosecret
```

---

## 📊 Verification

### Current Status

✅ **Database Schema**: Created  
✅ **Tables**: 3 tables (models, signals, bets)  
✅ **Indexes**: 4 indexes created  
✅ **Demo Model**: Seeded (model_id=1)  
✅ **Demo Signal**: Published (signal_id=2)  

### Database Query Results

```sql
-- modeling.models
 model_id |     name     | version |    stage    
----------+--------------+---------+-------------
        1 | hrd_win_prob | 0.0.1   | development

-- modeling.signals
 signal_id | race_id | horse_id | p_win | fair_odds_win | edge_win 
-----------+---------+----------+-------+---------------+----------
         2 |  123456 |       42 |  0.12 |          8.33 |     0.20
```

---

## 📝 Next Steps

### Task 2: Feature Engineering Pipeline
- Create `giddyup/data/build.py`
- Pull data from `racing.*` tables
- Engineer features (speed figs, trainer form, draw bias, etc.)
- Export to Parquet for training

### Task 3: Model Training
- Create `giddyup/models/lightgbm_trainer.py`
- GroupKFold cross-validation (by race_id)
- Isotonic calibration for probabilities
- Log to MLflow with metrics

### Task 4: Scoring Pipeline
- Create `giddyup/flows/score_today.py`
- Load production model from MLflow
- Score upcoming races
- Calculate pricing/value (Kelly, EV)
- Publish to `modeling.signals`

### Task 5: Orchestration
- Create Prefect deployment
- Schedule: 08:00 Europe/Madrid daily
- Refresh cadence: 10min → 1min near race time

### Task 6: Monitoring
- Great Expectations checkpoints
- Evidently drift reports
- CLV tracking vs closing prices

---

## 🏗️ Design Principles

1. **Python for Modeling** - All ML code in Python, never Go
2. **Read-Only API** - Go API only reads `modeling.*` tables
3. **Idempotent Upserts** - Safe to re-run scoring jobs
4. **Explicit Schema** - `modeling` separate from `racing`
5. **MLflow Registry** - Single source of truth for models
6. **Timezone-Aware** - All schedules in `Europe/Madrid`

---

## 📚 References

- **Task Spec**: `/home/smonaghan/GiddyUpModel/Instructions.md`
- **Database**: Reads from `racing.*` schema (read-only)
- **API**: Go API at `http://localhost:8000`

---

**Status**: ✅ Task 1 Complete (Bootstrap)  
**Next**: Task 2 (Feature Engineering Pipeline)  
**Date**: October 16, 2025

