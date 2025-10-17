"""
Signal publisher - upserts predictions to modeling.signals table.

This module handles writing model predictions to the database with
automatic conflict resolution (ON CONFLICT DO UPDATE).
"""

from typing import Iterable
from sqlalchemy import text, create_engine
from dotenv import load_dotenv
import os
import json
import datetime as dt


# Load environment and create engine
load_dotenv()
_engine = create_engine(os.getenv("PG_DSN"), pool_pre_ping=True)


# Upsert SQL statement
_UPSERT_SQL = text("""
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
    """
    Publish signals to the modeling.signals table.
    
    Args:
        rows: Iterable of signal dictionaries. Each dict should contain:
            - race_id (int): Race identifier
            - horse_id (int): Horse identifier
            - model_id (int): Model identifier
            - p_win (float): Win probability
            - fair_odds_win (float): Fair odds for win
            - edge_win (float, optional): Expected value
            - kelly_fraction (float, optional): Kelly stake fraction
            - stake_units (float, optional): Recommended stake
            - ... other optional fields
            
    Returns:
        int: Number of rows upserted
        
    Example:
        >>> signals = [
        ...     {
        ...         "race_id": 123456,
        ...         "horse_id": 42,
        ...         "model_id": 1,
        ...         "p_win": 0.15,
        ...         "fair_odds_win": 6.67,
        ...         "edge_win": 0.05,
        ...         "kelly_fraction": 0.02,
        ...         "stake_units": 0.1,
        ...     }
        ... ]
        >>> publish(signals)
        1
    """
    now = dt.datetime.utcnow()
    
    with _engine.begin() as connection:
        count = 0
        for row in rows:
            # Prepare row with defaults
            prepared_row = {
                **row,
                "as_of": row.get("as_of", now),
                "reasons_json": json.dumps(row.get("reasons", [])),
            }
            
            # Execute upsert
            connection.execute(_UPSERT_SQL, prepared_row)
            count += 1
    
    return count

