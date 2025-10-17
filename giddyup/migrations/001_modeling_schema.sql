-- Migration 001: Create modeling schema and tables
-- Purpose: Set up ML model registry, signals, and bet tracking
-- Date: 2025-10-16

-- Create the modeling schema (separate from racing schema)
CREATE SCHEMA IF NOT EXISTS modeling;

-- Table: modeling.models
-- Purpose: Model registry - tracks trained models, versions, and metadata
CREATE TABLE IF NOT EXISTS modeling.models (
  model_id       BIGSERIAL PRIMARY KEY,
  name           TEXT NOT NULL,
  version        TEXT NOT NULL,
  stage          TEXT,                    -- e.g., 'production', 'staging', 'archived'
  artifact_uri   TEXT NOT NULL,           -- MLflow artifact location (S3/local path)
  metrics_json   JSONB,                   -- Training metrics (accuracy, log loss, etc.)
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (name, version)
);

-- Table: modeling.signals
-- Purpose: Predictions/signals for each horse in upcoming races
CREATE TABLE IF NOT EXISTS modeling.signals (
  signal_id       BIGSERIAL PRIMARY KEY,
  as_of           TIMESTAMPTZ NOT NULL,  -- When this prediction was generated
  race_id         BIGINT NOT NULL,       -- FK to racing.races (read-only reference)
  horse_id        BIGINT NOT NULL,       -- FK to racing.horses (read-only reference)
  model_id        BIGINT NOT NULL REFERENCES modeling.models(model_id),
  
  -- Win probabilities
  p_win           DOUBLE PRECISION NOT NULL,
  p_place         DOUBLE PRECISION,
  
  -- Fair odds (implied by model probabilities)
  fair_odds_win   DOUBLE PRECISION NOT NULL,
  fair_odds_place DOUBLE PRECISION,
  
  -- Market odds (from exchanges/bookmakers)
  best_odds_win   DOUBLE PRECISION,
  best_odds_src   TEXT,                  -- e.g., 'betfair', 'bet365'
  
  -- Each-way terms
  ew_places       INT,                   -- Number of places paid
  ew_fraction     TEXT,                  -- e.g., '1/5', '1/4'
  
  -- Value metrics
  edge_win        DOUBLE PRECISION,      -- Expected value on win bet
  edge_ew         DOUBLE PRECISION,      -- Expected value on each-way bet
  kelly_fraction  DOUBLE PRECISION,      -- Kelly criterion stake fraction
  stake_units     DOUBLE PRECISION,      -- Recommended stake in units
  
  -- Risk controls
  liquidity_ok    BOOLEAN DEFAULT true,  -- Whether market has sufficient liquidity
  reasons_json    JSONB,                 -- Explanation (feature impacts, etc.)
  
  -- Unique constraint: one signal per timestamp per race/horse/model
  UNIQUE (as_of, race_id, horse_id, model_id)
);

-- Table: modeling.bets
-- Purpose: Track actual bets placed for performance monitoring
CREATE TABLE IF NOT EXISTS modeling.bets (
  bet_id         BIGSERIAL PRIMARY KEY,
  ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
  race_id        BIGINT NOT NULL,       -- FK to racing.races (read-only reference)
  horse_id       BIGINT NOT NULL,       -- FK to racing.horses (read-only reference)
  
  -- Bet details
  side           TEXT NOT NULL CHECK (side IN ('win','ew','place')),
  odds           DOUBLE PRECISION NOT NULL,
  stake          DOUBLE PRECISION NOT NULL,
  expected_ev    DOUBLE PRECISION,      -- Expected value at time of bet
  source         TEXT,                   -- 'betfair', 'smarkets', etc.
  
  -- Post-race analysis
  clv_close_odds DOUBLE PRECISION,      -- Closing Line Value (CLV) tracking
  pnl            DOUBLE PRECISION        -- Profit/loss after settlement
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_signals_race_as_of 
  ON modeling.signals(race_id, as_of DESC);

CREATE INDEX IF NOT EXISTS idx_signals_model_as_of 
  ON modeling.signals(model_id, as_of DESC);

CREATE INDEX IF NOT EXISTS idx_bets_ts 
  ON modeling.bets(ts DESC);

CREATE INDEX IF NOT EXISTS idx_bets_race 
  ON modeling.bets(race_id);

-- Comments for documentation
COMMENT ON SCHEMA modeling IS 'ML modeling schema - predictions, model registry, bet tracking';
COMMENT ON TABLE modeling.models IS 'Model registry - tracks trained models and versions';
COMMENT ON TABLE modeling.signals IS 'Generated predictions/signals for upcoming races';
COMMENT ON TABLE modeling.bets IS 'Actual bets placed for performance tracking and CLV analysis';

