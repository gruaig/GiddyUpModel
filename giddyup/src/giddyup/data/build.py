"""
Feature engineering for horse racing win probability prediction.

Extracts data from racing.* tables and engineers features for modeling.
"""

import os
from typing import Optional
import polars as pl
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def get_connection_string() -> str:
    """Get PostgreSQL connection string for connectorx."""
    dsn = os.getenv("PG_DSN")
    if not dsn:
        raise ValueError("PG_DSN not set in environment")
    # Convert psycopg format to standard postgres format for connectorx
    # postgresql+psycopg://user:pass@host:port/db → postgresql://user:pass@host:port/db
    dsn = dsn.replace("+psycopg", "")
    return dsn


def build_training_data(
    date_from: str,
    date_to: str,
    output_path: Optional[str] = None
) -> pl.DataFrame:
    """
    Build training dataset with features for a date range.
    
    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        output_path: Optional path to save Parquet file
        
    Returns:
        Polars DataFrame with features and target
        
    Example:
        >>> df = build_training_data("2024-01-01", "2024-12-31")
        >>> df.select(["race_id", "horse_id", "won", "p_win_pred"]).head()
    """
    print(f"📊 Building training data from {date_from} to {date_to}...")
    
    conn_str = get_connection_string()
    
    # ===== 1. Base Runner Data =====
    print("   [1/6] Fetching base runner data...")
    base_query = f"""
    SELECT 
        ru.runner_id,
        ru.race_id,
        r.race_date,
        r.region,
        r.course_id,
        r.off_time,
        r.race_type,
        r.class,
        r.dist_f,
        r.dist_m,
        r.going,
        r.surface,
        r.ran,
        ru.horse_id,
        ru.trainer_id,
        ru.jockey_id,
        ru.owner_id,
        ru.num,
        ru.draw,
        ru.age,
        ru.sex,
        ru.lbs,
        ru.or AS official_rating,
        ru.rpr AS racing_post_rating,
        ru.pos_num,
        ru.btn AS beaten_lengths,
        ru.win_flag AS won,
        ru.dec AS decimal_odds,
        ru.win_bsp,
        ru.win_ppwap,
        ru.win_morningwap,
        ru.win_ppmax,
        ru.win_ppmin,
        ru.win_pre_vol,
        ru.win_morning_vol,
        ru.comment
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    WHERE r.race_date BETWEEN DATE '{date_from}' AND DATE '{date_to}'
        AND ru.pos_num IS NOT NULL  -- Only include finishers
    ORDER BY r.race_date, r.off_time, ru.race_id
    """
    
    df = pl.read_database_uri(query=base_query, uri=conn_str)
    print(f"      Loaded {len(df):,} runners from {df['race_id'].n_unique():,} races")
    
    # ===== 2. Horse Historical Features =====
    print("   [2/6] Engineering horse historical features...")
    df = df.with_columns([
        # Days since last run (DSR)
        (pl.col("race_date") - pl.col("race_date").shift(1).over("horse_id")).dt.total_days()
            .fill_null(999)
            .alias("days_since_run"),
        
        # Last 3 positions
        pl.col("pos_num").shift(1).over("horse_id").alias("last_pos"),
        pl.col("pos_num").shift(2).over("horse_id").alias("last_pos_2"),
        pl.col("pos_num").shift(3).over("horse_id").alias("last_pos_3"),
        
        # Career runs & wins before this race
        (pl.col("runner_id").cum_count().over("horse_id") - 1).alias("career_runs"),
        pl.col("won").cast(pl.Int32).cum_sum().over("horse_id").shift(1).fill_null(0).alias("career_wins"),
        
        # Best RPR in last 3 runs
        pl.col("racing_post_rating").shift(1).over("horse_id")
            .rolling_max(window_size=3, min_periods=1)
            .alias("best_rpr_last_3"),
        
        # Average beaten lengths in last 3 runs
        pl.col("beaten_lengths").shift(1).over("horse_id")
            .rolling_mean(window_size=3, min_periods=1)
            .alias("avg_btn_last_3"),
    ])
    
    # Strike rate
    df = df.with_columns(
        (pl.col("career_wins") / pl.col("career_runs").clip(lower_bound=1))
            .alias("career_strike_rate")
    )
    
    # ===== 3. Trainer Form =====
    print("   [3/6] Engineering trainer form features...")
    
    # Simple approach: cumulative stats (approximates recent form)
    df = df.with_columns([
        # Cumulative wins/runs for this trainer
        pl.col("won").cast(pl.Int32).cum_sum().over("trainer_id").shift(1).fill_null(0).alias("trainer_wins_total"),
        (pl.col("runner_id").cum_count().over("trainer_id") - 1).alias("trainer_runs_total"),
    ])
    
    df = df.with_columns(
        (pl.col("trainer_wins_total") / pl.col("trainer_runs_total").clip(lower_bound=1))
            .alias("trainer_sr_total")
    )
    
    # ===== 4. Jockey Form =====
    print("   [4/6] Engineering jockey form features...")
    
    # Simple approach: cumulative stats (approximates recent form)
    df = df.with_columns([
        # Cumulative wins/runs for this jockey
        pl.col("won").cast(pl.Int32).cum_sum().over("jockey_id").shift(1).fill_null(0).alias("jockey_wins_total"),
        (pl.col("runner_id").cum_count().over("jockey_id") - 1).alias("jockey_runs_total"),
    ])
    
    df = df.with_columns(
        (pl.col("jockey_wins_total") / pl.col("jockey_runs_total").clip(lower_bound=1))
            .alias("jockey_sr_total")
    )
    
    # ===== 5. Course/Distance Form =====
    print("   [5/6] Engineering course/distance form...")
    
    # Runs at this course
    df = df.with_columns([
        (pl.col("runner_id").cum_count().over(["horse_id", "course_id"]) - 1)
            .alias("runs_at_course"),
        
        pl.col("won").cast(pl.Int32).cum_sum().over(["horse_id", "course_id"]).shift(1)
            .fill_null(0)
            .alias("wins_at_course"),
    ])
    
    # ===== 6. GPR (GiddyUp Performance Rating) =====
    print("   [6/7] Computing GPR for each horse (POINT-IN-TIME, no look-ahead)...")
    
    from giddyup.ratings.gpr import compute_gpr, add_gpr_to_dataset
    
    # CRITICAL: Compute GPR per-race using only PAST runs
    # For each race, GPR must use only runs BEFORE that race date
    
    print("      This will take several minutes...")
    
    # Create a column to store GPR computed as-of race date
    df = df.with_columns([
        pl.lit(None).cast(pl.Float64).alias("gpr"),
        pl.lit(None).cast(pl.Float64).alias("gpr_sigma"),
        pl.lit(None).cast(pl.Int64).alias("n_runs"),
        pl.lit(None).cast(pl.Float64).alias("gpr_minus_or"),
        pl.lit(None).cast(pl.Float64).alias("gpr_minus_rpr"),
    ])
    
    # Build historical runs dataset
    hist_runs = df.select([
        "horse_id", "race_id", "race_date", "dist_f", "beaten_lengths",
        "lbs", "course_id", "going", "class", "pos_num"
    ]).unique().sort("race_date")
    
    # Rename for GPR
    hist_runs = hist_runs.rename({"beaten_lengths": "btn"})
    
    # Strategy: Compute GPR incrementally by year to avoid look-ahead
    # For each year, use only runs from PREVIOUS years
    
    years = sorted(df.select(pl.col("race_date").dt.year()).unique().to_series().to_list())
    print(f"      Processing {len(years)} years: {years[0]}-{years[-1]}")
    
    all_gpr_snapshots = []
    
    for year in years:
        # Use runs from ALL previous years + this year's races up to each date
        # For simplicity: use runs up to END of previous year for this year's GPR
        cutoff_date = f"{year-1}-12-31" if year > years[0] else f"{year-1}-01-01"
        
        # Compute GPR using only past runs
        past_runs = hist_runs.filter(pl.col("race_date") <= pl.lit(cutoff_date).str.strptime(pl.Date, "%Y-%m-%d"))
        
        if len(past_runs) > 0:
            gpr_snapshot = compute_gpr(
                df_runs=past_runs,
                as_of_date=None,  # Already filtered above
                half_life_days=120.0,
                shrinkage_k=4.0,
                prior_rating=75.0,
            )
            
            # Tag with year
            gpr_snapshot = gpr_snapshot.with_columns([
                pl.lit(year).alias("year")
            ])
            
            all_gpr_snapshots.append(gpr_snapshot)
            
            print(f"        {year}: GPR from {len(past_runs):,} past runs for {gpr_snapshot.height:,} horses")
    
    # Combine all snapshots
    gpr_by_year = pl.concat(all_gpr_snapshots)
    
    # Join to main dataset by horse_id and year
    df = df.with_columns([
        pl.col("race_date").dt.year().alias("year")
    ])
    
    df = df.join(
        gpr_by_year,
        on=["horse_id", "year"],
        how="left"
    )
    
    # For horses with no GPR (debutants), fill with prior
    df = df.with_columns([
        pl.col("gpr").fill_null(75.0),
        pl.col("gpr_sigma").fill_null(15.0),
        pl.col("n_runs").fill_null(0),
    ])
    
    # Calculate deltas
    df = df.with_columns([
        (pl.col("gpr") - pl.col("official_rating").fill_null(75.0)).alias("gpr_minus_or"),
        (pl.col("gpr") - pl.col("racing_post_rating").fill_null(75.0)).alias("gpr_minus_rpr"),
    ])
    
    # Drop temp year column
    df = df.drop("year")
    
    print(f"      ✅ Added GPR features (point-in-time): gpr, gpr_minus_or, gpr_minus_rpr, gpr_sigma")
    
    # ===== 7. Race-Level Features =====
    print("   [7/7] Adding race-level features...")
    
    # Field size
    # Class (convert to numeric)
    df = df.with_columns([
        pl.col("ran").alias("field_size"),
        
        # Extract class number from strings like "(Class 1)", "Class 2", etc.
        pl.col("class").str.extract(r"(\d+)", 1).cast(pl.Int32, strict=False)
            .fill_null(7)  # Default to Class 7 (lowest) if missing
            .alias("class_numeric"),
        
        # Going grouped
        pl.when(pl.col("going").str.contains("(?i)firm"))
            .then(pl.lit("firm"))
        .when(pl.col("going").str.contains("(?i)good"))
            .then(pl.lit("good"))
        .when(pl.col("going").str.contains("(?i)soft"))
            .then(pl.lit("soft"))
        .when(pl.col("going").str.contains("(?i)heavy"))
            .then(pl.lit("heavy"))
        .otherwise(pl.lit("unknown"))
            .alias("going_grouped"),
        
        # Surface binary
        pl.when(pl.col("surface") == "AW")
            .then(pl.lit(1))
        .otherwise(pl.lit(0))
            .alias("is_aw"),
        
        # Race type binary
        pl.when(pl.col("race_type") == "Flat")
            .then(pl.lit(1))
        .otherwise(pl.lit(0))
            .alias("is_flat"),
    ])
    
    # ===== Market Features (Pre-Race Only) =====
    print("   [Extra] Adding pre-race market features...")
    
    df = df.with_columns([
        # Basic market rank
        pl.col("decimal_odds").rank("dense").over("race_id").alias("market_rank"),
        
        # Price movement (morning → pre-play)
        # Ratio < 1.0 = steamer (shortened), > 1.0 = drifter (lengthened)
        (pl.col("win_ppwap") / pl.col("win_morningwap").clip(lower_bound=1.01))
            .alias("price_drift_ratio"),
        
        # Absolute price movement
        (pl.col("win_morningwap") - pl.col("win_ppwap"))
            .alias("price_movement"),
        
        # Volume indicators
        pl.col("win_pre_vol").fill_null(0).alias("volume_traded"),
        (pl.col("win_pre_vol") / pl.col("ran").clip(lower_bound=1))
            .fill_null(0)
            .alias("volume_per_runner"),
        
        # Price spread (volatility indicator)
        (pl.col("win_ppmax") - pl.col("win_ppmin"))
            .fill_null(0)
            .alias("price_spread"),
        
        # Is this the morning favorite?
        (pl.col("win_morningwap").rank().over("race_id") == 1)
            .cast(pl.Int32)
            .alias("is_morning_fav"),
        
        # Is this the pre-play favorite?
        (pl.col("win_ppwap").rank().over("race_id") == 1)
            .cast(pl.Int32)
            .alias("is_fav"),
    ])
    
    # Fill nulls with sensible defaults
    df = df.with_columns([
        pl.col("days_since_run").fill_null(999),
        pl.col("draw").fill_null(0),
        pl.col("official_rating").fill_null(0),
        pl.col("racing_post_rating").fill_null(0),
        pl.col("trainer_sr_total").fill_null(0.0),
        pl.col("jockey_sr_total").fill_null(0.0),
        pl.col("career_strike_rate").fill_null(0.0),
        pl.col("best_rpr_last_3").fill_null(0),
        pl.col("avg_btn_last_3").fill_null(10.0),  # Large default for never-run horses
    ])
    
    print(f"\n✅ Feature engineering complete!")
    print(f"   Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   Win rate: {df['won'].mean():.2%}")
    
    # Save to Parquet if requested
    if output_path:
        df.write_parquet(output_path)
        print(f"   Saved to: {output_path}")
    
    return df


def build_inference_data(
    date: str,
    output_path: Optional[str] = None
) -> pl.DataFrame:
    """
    Build inference dataset for a specific date (upcoming races).
    
    Args:
        date: Race date (YYYY-MM-DD)
        output_path: Optional path to save Parquet file
        
    Returns:
        Polars DataFrame with features (no target)
        
    Example:
        >>> df = build_inference_data("2025-10-17")
        >>> df.select(["race_id", "horse_id", "racing_post_rating"]).head()
    """
    print(f"📊 Building inference data for {date}...")
    
    # For inference, we use the same logic but:
    # 1. Only query the target date
    # 2. Don't include outcome variables (won, pos_num, etc.)
    # 3. Use all historical data up to (but not including) this date for features
    
    conn_str = get_connection_string()
    
    # Query upcoming races (no results yet)
    query = f"""
    SELECT 
        ru.runner_id,
        ru.race_id,
        r.race_date,
        r.region,
        r.course_id,
        r.off_time,
        r.race_type,
        r.class,
        r.dist_f,
        r.dist_m,
        r.going,
        r.surface,
        r.ran,
        ru.horse_id,
        ru.trainer_id,
        ru.jockey_id,
        ru.owner_id,
        ru.num,
        ru.draw,
        ru.age,
        ru.sex,
        ru.lbs,
        ru.or AS official_rating,
        ru.rpr AS racing_post_rating,
        ru.dec AS decimal_odds,
        ru.best_odds_win
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    WHERE r.race_date = DATE '{date}'
    ORDER BY r.off_time, ru.race_id
    """
    
    df = pl.read_database_uri(query=query, uri=conn_str)
    print(f"   Loaded {len(df):,} runners from {df['race_id'].n_unique():,} races")
    
    # Apply same feature engineering as training (but without target)
    # TODO: Add same feature engineering logic from build_training_data
    # For now, return basic features
    
    if output_path:
        df.write_parquet(output_path)
        print(f"   Saved to: {output_path}")
    
    return df


def get_feature_list() -> list[str]:
    """
    Get list of feature columns for modeling.
    
    IMPORTANT: Uses ABILITY_FEATURES only (no market data).
    Market features are joined at SCORING time only.
    
    Returns:
        List of ability-only feature column names
    """
    from .feature_lists import ABILITY_FEATURES
    return ABILITY_FEATURES

