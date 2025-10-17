"""
Market features for hybrid model scoring.

CRITICAL: These are NEVER used in training, ONLY at prediction/scoring time.
"""

import os
import polars as pl
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def add_market_features_from_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add market-derived features from existing decimal_odds column.
    
    Use this when market snapshot isn't available but decimal_odds is in the dataframe.
    
    Args:
        df: DataFrame with decimal_odds column
        
    Returns:
        DataFrame with market features added
    """
    
    if "decimal_odds" not in df.columns:
        raise ValueError("decimal_odds column required")
    
    # Filter to valid odds
    df = df.filter(
        pl.col("decimal_odds").is_not_null() &
        (pl.col("decimal_odds") >= 1.01)
    )
    
    # Market rank (1 = favorite)
    df = df.with_columns([
        pl.col("decimal_odds").rank(method="min").over("race_id").alias("market_rank")
    ])
    
    # Market probability
    df = df.with_columns([
        (1.0 / pl.col("decimal_odds")).alias("q_market")
    ])
    
    # Overround per race
    overround = df.group_by("race_id").agg([
        pl.col("q_market").sum().alias("overround")
    ])
    
    df = df.join(overround, on="race_id", how="left")
    
    # Vig-free probability
    df = df.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
    ])
    
    # Is favorite
    df = df.with_columns([
        (pl.col("market_rank") == 1).alias("is_favorite"),
        (pl.col("market_rank") == 2).alias("is_second_fav"),
    ])
    
    # Odds percentile in field
    df = df.with_columns([
        (pl.col("market_rank") / pl.col("market_rank").max().over("race_id") * 100)
            .alias("odds_percentile")
    ])
    
    return df


def get_market_snapshot_t60(
    race_ids: list,
    conn_str: str = None,
    minutes_before: int = 60
) -> pl.DataFrame:
    """
    Get market snapshot T-60 (or specified minutes before off).
    
    Args:
        race_ids: List of race IDs to fetch
        conn_str: Database connection string
        minutes_before: Minutes before off time
        
    Returns:
        DataFrame with race_id, horse_id, decimal_odds, snapshot_ts
    """
    
    if not race_ids:
        return pl.DataFrame()
    
    engine = create_engine(conn_str or os.getenv("PG_DSN"), pool_pre_ping=True)
    
    # Convert list to PostgreSQL array format
    race_ids_str = "{" + ",".join(map(str, race_ids)) + "}"
    
    sql = text("""
    WITH target_times AS (
        SELECT 
            race_id,
            off_time,
            off_time - INTERVAL ':minutes minutes' AS target_time
        FROM racing.races
        WHERE race_id = ANY(:race_ids::bigint[])
    ),
    snapshots AS (
        SELECT 
            s.race_id,
            s.horse_id,
            s.decimal_odds,
            s.source,
            s.snapped_at,
            ABS(EXTRACT(EPOCH FROM (s.snapped_at - t.target_time))) AS time_diff_sec
        FROM market.price_snapshots s
        JOIN target_times t USING (race_id)
        WHERE s.snapped_at BETWEEN t.target_time - INTERVAL '15 minutes'
                                AND t.target_time + INTERVAL '15 minutes'
        AND s.decimal_odds >= 1.01
    ),
    best_snapshot AS (
        SELECT 
            race_id,
            horse_id,
            decimal_odds,
            snapped_at,
            ROW_NUMBER() OVER (PARTITION BY race_id, horse_id ORDER BY time_diff_sec) AS rn
        FROM snapshots
    )
    SELECT 
        race_id,
        horse_id,
        decimal_odds,
        snapped_at AS snapshot_ts
    FROM best_snapshot
    WHERE rn = 1
    ORDER BY race_id, decimal_odds
    """)
    
    try:
        with engine.begin() as cx:
            df = pl.read_database(
                sql, 
                connection=cx.connection,
                params={"race_ids": race_ids_str, "minutes": minutes_before}
            )
        
        # Add market features
        df = add_market_features_from_data(df)
        
        return df
        
    except Exception as e:
        print(f"⚠️  Market snapshot query failed: {e}")
        print(f"   Falling back to decimal_odds from racing.runners")
        return pl.DataFrame()


def fallback_to_runner_odds(race_ids: list, conn_str: str = None) -> pl.DataFrame:
    """
    Fallback: Use decimal_odds from racing.runners when snapshots unavailable.
    
    Args:
        race_ids: List of race IDs
        conn_str: Database connection string
        
    Returns:
        DataFrame with race_id, horse_id, decimal_odds
    """
    
    engine = create_engine(conn_str or os.getenv("PG_DSN"), pool_pre_ping=True)
    
    race_ids_str = "{" + ",".join(map(str, race_ids)) + "}"
    
    sql = text("""
    SELECT 
        race_id,
        horse_id,
        COALESCE(win_ppwap, dec) as decimal_odds
    FROM racing.runners
    WHERE race_id = ANY(:race_ids::bigint[])
    AND COALESCE(win_ppwap, dec) >= 1.01
    ORDER BY race_id, COALESCE(win_ppwap, dec)
    """)
    
    with engine.begin() as cx:
        df = pl.read_database(
            sql,
            connection=cx.connection,
            params={"race_ids": race_ids_str}
        )
    
    # Add market features
    df = add_market_features_from_data(df)
    
    return df

