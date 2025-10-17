# Instructions — Python‑First Modeling Pipeline for HorseRacingDatabase

_Last updated: 2025‑10‑16 (Europe/Madrid)_

These instructions show you how to stand up a **modern, Python‑first** modeling stack that
trains, validates, calibrates, **scores** races on a schedule, and **publishes** signals
to Postgres for the Go API/UI to read. Everything modeling‑related is in **Python**; the API
remains **read‑only**.

---

## 1) Prerequisites

- **Python** 3.10+ (3.11/3.12 recommended).
- **PostgreSQL** 13+ reachable from your modeling box.
- (Optional) **Redis** for API caching.
- (Optional) **S3/MinIO** bucket for model/artifact storage.
- Shell with `curl`/`bash` and OpenSSL.

> Timezone: we’ll schedule jobs in **Europe/Madrid**.

---

## 2) Create the repo & environment (with `uv`)

We’ll use **uv** (a fast Python package & project manager) to create a reproducible environment.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

mkdir -p hrd-modeling && cd hrd-modeling
uv init --package hrdml

uv add \
  polars pyarrow duckdb \
  lightgbm xgboost scikit-learn \
  mlflow \
  prefect \
  sqlalchemy psycopg[binary] \
  pydantic \
  hydra-core \
  great-expectations evidently \
  python-dotenv \
  pandas

uv add -D ruff mypy black
```

Project layout:

```
hrd-modeling/
  pyproject.toml
  .venv/
  .env
  hrdml/
    data/
    features/
    models/
    price/
    publish/
    registry/
    flows/
    __init__.py
  tests/
```

`.env` example (do **not** commit to git):

```dotenv
PG_DSN=postgresql+psycopg://user:pass@host:5432/yourdb
MLFLOW_TRACKING_URI=http://mlflow.yourdomain:5000
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=miniosecret
TZ=Europe/Madrid
```

---

## 3) Prepare the database schema

Run these SQL migrations (e.g., via psql or your migrations tool):

```sql
CREATE SCHEMA IF NOT EXISTS modeling;

CREATE TABLE IF NOT EXISTS modeling.models (
  model_id       BIGSERIAL PRIMARY KEY,
  name           TEXT NOT NULL,
  version        TEXT NOT NULL,
  stage          TEXT,
  artifact_uri   TEXT NOT NULL,
  metrics_json   JSONB,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS modeling.signals (
  signal_id       BIGSERIAL PRIMARY KEY,
  as_of           TIMESTAMPTZ NOT NULL,
  race_id         BIGINT NOT NULL,
  horse_id        BIGINT NOT NULL,
  model_id        BIGINT NOT NULL REFERENCES modeling.models(model_id),
  p_win           DOUBLE PRECISION NOT NULL,
  p_place         DOUBLE PRECISION,
  fair_odds_win   DOUBLE PRECISION NOT NULL,
  fair_odds_place DOUBLE PRECISION,
  best_odds_win   DOUBLE PRECISION,
  best_odds_src   TEXT,
  ew_places       INT,
  ew_fraction     TEXT,
  edge_win        DOUBLE PRECISION,
  edge_ew         DOUBLE PRECISION,
  kelly_fraction  DOUBLE PRECISION,
  stake_units     DOUBLE PRECISION,
  liquidity_ok    BOOLEAN DEFAULT true,
  reasons_json    JSONB,
  UNIQUE (as_of, race_id, horse_id, model_id)
);

CREATE TABLE IF NOT EXISTS modeling.bets (
  bet_id         BIGSERIAL PRIMARY KEY,
  ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
  race_id        BIGINT NOT NULL,
  horse_id       BIGINT NOT NULL,
  side           TEXT NOT NULL CHECK (side IN ('win','ew','place')),
  odds           DOUBLE PRECISION NOT NULL,
  stake          DOUBLE PRECISION NOT NULL,
  expected_ev    DOUBLE PRECISION,
  source         TEXT,
  clv_close_odds DOUBLE PRECISION,
  pnl            DOUBLE PRECISION
);
```

---

## 4) Stand up MLflow (tracking + registry)

**Option A: quick local**

```bash
mlflow server \
  --host 0.0.0.0 --port 5000 \
  --backend-store-uri postgresql+psycopg://mlflow:pass@db:5432/mlflow \
  --default-artifact-root s3://mlflow-artifacts/
```

**Option B: container**

Use the official MLflow image and mount a volume for artifacts, or point to S3/MinIO.
Create the registered model `hrd_win_prob` in the UI, and use aliases like `production` / `staging`.

---

## 5) Build datasets with Polars

`hrdml/data/build.py`
```python
import polars as pl
import os

def today_features(conn_str: str, date_str: str) -> pl.LazyFrame:
    races = pl.read_database(
        query=f"""
            SELECT race_id, off_time, course, going, runners
            FROM racing.races
            WHERE race_date = DATE '{date_str}'
        """,
        connection=conn_str,
    )
    runners = pl.read_database(
        query=f"""
            SELECT race_id, horse_id, draw, age, days_since_run, speed_fig, trainer14
            FROM racing.runners
            WHERE race_date = DATE '{date_str}'
        """,
        connection=conn_str,
    )
    lf = (runners.lazy()
          .join(races.lazy(), on="race_id", how="inner")
          .with_columns([
              (pl.col("draw")).alias("draw"),
              (pl.col("speed_fig")).alias("speed_fig"),
              (pl.col("days_since_run")).alias("days_since_run"),
              (pl.col("trainer14")).alias("trainer14"),
          ]))
    return lf
```

Notes:
- Prefer **LazyFrame** pipelines and **Parquet** for speed and reproducibility.
- For heavy joins, consider **DuckDB** as an intermediate SQL step.

---

## 6) Train a model (LightGBM/XGBoost) + calibrate

`hrdml/models/lightgbm.py`
```python
from dataclasses import dataclass
import polars as pl
import numpy as np
import lightgbm as lgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import GroupKFold
import mlflow

@dataclass
class TrainConfig:
    features: list[str]
    target: str = "won"
    groups: str = "race_id"
    params: dict = None
    num_boost_round: int = 2000
    early_stopping_rounds: int = 100

def to_numpy(df: pl.DataFrame, cols: list[str]):
    X = np.column_stack([df[c].to_numpy() for c in cols])
    return X

def train_lgbm(lf: pl.LazyFrame, cfg: TrainConfig):
    with mlflow.start_run() as run:
        df = lf.collect()
        X = to_numpy(df, cfg.features)
        y = df[cfg.target].to_numpy()
        groups = df[cfg.groups].to_numpy()

        gkf = GroupKFold(n_splits=5)
        oof = np.zeros(len(y))
        models = []
        for fold, (tr, va) in enumerate(gkf.split(X, y, groups)):
            dtrain = lgb.Dataset(X[tr], label=y[tr])
            dvalid = lgb.Dataset(X[va], label=y[va])
            params = {"objective": "binary", "metric": "binary_logloss",
                      "learning_rate": 0.05, "num_leaves": 63,
                      "feature_fraction": 0.9} | (cfg.params or {})
            booster = lgb.train(params, dtrain,
                                num_boost_round=cfg.num_boost_round,
                                valid_sets=[dvalid],
                                callbacks=[lgb.early_stopping(cfg.early_stopping_rounds)])
            models.append(booster)
            oof[va] = booster.predict(X[va])

        calibrator = CalibratedClassifierCV(cv="prefit", method="isotonic")
        calibrator.fit(oof.reshape(-1,1), y)

        mlflow.log_params(params)
        mlflow.log_metric("oof_logloss", float(__import__("sklearn.metrics").metrics.log_loss(y, oof)))
        return {"run_id": run.info.run_id}
```

---

## 7) Price, value, and staking utilities

`hrdml/price/value.py`
```python
from typing import NamedTuple

class EWTerms(NamedTuple):
    places: int
    fraction: float

def fair_odds(p: float) -> float:
    return 1.0 / max(1e-9, p)

def ev_win(p: float, O: float) -> float:
    return p * (O - 1.0) - (1.0 - p)

def kelly_fraction(p: float, O: float) -> float:
    k = (p*O - 1.0) / max(1e-9, (O - 1.0))
    return max(0.0, min(1.0, k))
```

---

## 8) Publisher: upsert signals into Postgres

`hrdml/publish/signals.py`
```python
from typing import Iterable
from sqlalchemy import text, create_engine
import json, os, datetime as dt

PG_DSN = os.getenv("PG_DSN")
engine = create_engine(PG_DSN, pool_pre_ping=True)

UPSERT_SQL = text("""
INSERT INTO modeling.signals (
  as_of, race_id, horse_id, model_id,
  p_win, p_place, fair_odds_win, fair_odds_place,
  best_odds_win, best_odds_src,
  ew_places, ew_fraction,
  edge_win, edge_ew, kelly_fraction, stake_units,
  liquidity_ok, reasons_json
) VALUES (
  :as_of, :race_id, :horse_id, :model_id,
  :p_win, :p_place, :fair_odds_win, :fair_odds_place,
  :best_odds_win, :best_odds_src,
  :ew_places, :ew_fraction,
  :edge_win, :edge_ew, :kelly_fraction, :stake_units,
  :liquidity_ok, :reasons_json
)
ON CONFLICT (as_of, race_id, horse_id, model_id)
DO UPDATE SET
  p_win = EXCLUDED.p_win,
  p_place = EXCLUDED.p_place,
  fair_odds_win = EXCLUDED.fair_odds_win,
  fair_odds_place = EXCLUDED.fair_odds_place,
  best_odds_win = EXCLUDED.best_odds_win,
  best_odds_src = EXCLUDED.best_odds_src,
  ew_places = EXCLUDED.ew_places,
  ew_fraction = EXCLUDED.ew_fraction,
  edge_win = EXCLUDED.edge_win,
  edge_ew = EXCLUDED.edge_ew,
  kelly_fraction = EXCLUDED.kelly_fraction,
  stake_units = EXCLUDED.stake_units,
  liquidity_ok = EXCLUDED.liquidity_ok,
  reasons_json = EXCLUDED.reasons_json;
""")

def publish(rows: Iterable[dict]) -> int:
    now = dt.datetime.utcnow()
    with engine.begin() as cx:
        count = 0
        for r in rows:
            r = r | {"as_of": r.get("as_of", now), "reasons_json": json.dumps(r.get("reasons", []))}
            cx.execute(UPSERT_SQL, r)
            count += 1
    return count
```

---

## 9) Scoring job (load model, score, price, publish)

`hrdml/flows/precompute.py`
```python
import os
import polars as pl
import mlflow
from hrdml.data.build import today_features
from hrdml.price.value import fair_odds, ev_win, kelly_fraction
from hrdml.publish.signals import publish

def load_production_model(name: str):
    model_uri = f"models:/{name}/production"
    model = mlflow.pyfunc.load_model(model_uri)
    return model

def run(date_str: str, model_name: str = "hrd_win_prob"):
    lf = today_features(os.getenv("PG_DSN"), date_str)
    df = lf.collect()
    model = load_production_model(model_name)
    p = model.predict(df.select(pl.col("*")).to_pandas())
    BEST_O = 8.0

    rows = []
    for i, row in enumerate(df.iter_rows(named=True)):
        p_win = float(p[i])
        fo = fair_odds(p_win)
        edge = ev_win(p_win, BEST_O)
        k = kelly_fraction(p_win, BEST_O)
        rows.append({
            "race_id": row["race_id"],
            "horse_id": row["horse_id"],
            "model_id": 1,
            "p_win": p_win,
            "p_place": None,
            "fair_odds_win": fo,
            "fair_odds_place": None,
            "best_odds_win": BEST_O,
            "best_odds_src": "exchange",
            "edge_win": edge,
            "kelly_fraction": k * 0.25,
            "stake_units": min(0.5, max(0.0, k * 0.25)),
            "liquidity_ok": True,
            "reasons": [{"feature":"speed_fig","impact":0.7}],
        })
    wrote = publish(rows)
    return wrote
```

---

## 10) Orchestrate with Prefect

```bash
uv run prefect version
uv run prefect server start
uv run prefect agent start -q default
```

Create deployment at **08:00 Europe/Madrid** using `CronSchedule`. Add a second deployment for the **refresh** cadence (10m, then 1m near off).

---

## 11) Validation & Drift

- **Great Expectations** Checkpoints run pre‑publish to block bad data.
- **Evidently** reports run weekly/monthly to detect **data/prediction drift** and alert on thresholds.

---

## 12) Acceptance checks

- By **08:05 CET/CEST**, `modeling.signals` has entries for ≥80% of today’s races.
- `/signals/*` P95 ≤150ms from API cache; responses include `as_of` & `staleness_ms`.
- Positive **CLV** vs. close over the recent OOT window.

---

## 13) References

- Polars: https://docs.pola.rs/
- LightGBM: https://lightgbm.readthedocs.io/ , PDF: https://media.readthedocs.org/pdf/lightgbm/latest/lightgbm.pdf
- XGBoost: https://xgboost.readthedocs.io/ , PDF: https://buildmedia.readthedocs.org/media/pdf/xgboost/latest/xgboost.pdf
- MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
- Prefect quickstart & install: https://docs.prefect.io/v3/get-started/quickstart , https://docs.prefect.io/v3/get-started/install
- Airflow scheduler/DAGs: https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html , https://airflow.apache-airflow/stable/core-concepts/dags.html
- Great Expectations: https://docs.greatexpectations.io/docs/0.18/reference/learn/terms/checkpoint/ , https://docs.greatexpectations.io/docs/0.18/oss/guides/validation/checkpoints/how_to_create_a_new_checkpoint/
- Evidently drift: https://docs.evidentlyai.com/metrics/preset_data_drift , https://docs.evidentlyai.com/metrics/explainer_drift
- SQLAlchemy & Postgres upsert: https://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#insert-on-conflict-upsert , https://www.postgresql.org/docs/current/sql-insert.html
- Hydra: https://hydra.cc/docs/intro/
- uv: https://docs.astral.sh/uv/
