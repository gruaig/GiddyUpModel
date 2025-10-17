"""
Scoring & Publishing Pipeline

Loads ability-only model → scores today's races → joins T-60 market snapshot →
computes edge & EV → filters by thresholds → publishes signals to DB
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import mlflow
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from giddyup.data.feature_lists import ABILITY_FEATURES
from giddyup.publish.signals import publish as publish_signals
from giddyup.price.value import fair_odds, ev_win, kelly_fraction

load_dotenv()

# ===== Configuration =====
PG_DSN = os.getenv("PG_DSN")
engine = create_engine(PG_DSN, pool_pre_ping=True)

# Thresholds (can be env vars later)
EDGE_MIN = float(os.getenv("EDGE_MIN", "0.03"))  # 3pp minimum edge
ODDS_MIN = float(os.getenv("ODDS_MIN", "2.0"))   # Avoid heavy favorites
EV_MIN = float(os.getenv("EV_MIN", "0.02"))      # 2% minimum EV after commission
COMMISSION = float(os.getenv("COMMISSION", "0.02"))  # 2% exchange fee
KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", "0.25"))  # Quarter Kelly
MAX_STAKE = float(os.getenv("MAX_STAKE", "0.5"))  # Max 0.5 units per bet


def get_today_features(date_str: str) -> pl.DataFrame:
    """
    Get ability features for all horses racing on target date.
    
    CRITICAL: Uses ONLY ability features (no market data).
    
    Args:
        date_str: Target date (YYYY-MM-DD)
        
    Returns:
        DataFrame with race_id, horse_id, and all ABILITY_FEATURES
    """
    print(f"\n📊 Fetching ability features for {date_str}...")
    
    # Import here to avoid circular dependency
    from giddyup.data.build import build_training_data
    
    # Build features for target date
    # This will compute GPR and all other ability features
    df = build_training_data(
        date_from=date_str,
        date_to=date_str,
        output_path=None  # Don't save to disk
    )
    
    # Filter to only today's races
    df = df.filter(pl.col("race_date") == pl.lit(date_str).str.strptime(pl.Date, "%Y-%m-%d"))
    
    # Select relevant columns
    cols = ["race_id", "horse_id", "horse_name", "off_time"] + ABILITY_FEATURES
    df = df.select([c for c in cols if c in df.columns])
    
    print(f"   ✅ Loaded {len(df)} horses across {df['race_id'].n_unique()} races")
    
    return df


def get_market_snapshot_T_minus(date_str: str, minutes_before: int = 60) -> pl.DataFrame:
    """
    Get market snapshot T-60 (or specified minutes before off).
    
    Args:
        date_str: Target date
        minutes_before: Minutes before off time to snapshot (default 60)
        
    Returns:
        DataFrame with race_id, horse_id, decimal_odds, source, snapshot_ts
    """
    print(f"\n💰 Fetching T-{minutes_before} market snapshot for {date_str}...")
    
    # Query to get best price at T-60
    # Note: Adjust table/column names based on your actual schema
    sql = f"""
    WITH target_races AS (
        SELECT 
            race_id,
            off_time,
            off_time - INTERVAL '{minutes_before} minutes' AS target_time
        FROM racing.races
        WHERE DATE(off_time AT TIME ZONE 'UTC') = DATE '{date_str}'
    ),
    snapshots AS (
        SELECT 
            r.race_id,
            r.horse_id,
            r.decimal_odds,
            r.source,
            r.snapped_at,
            ABS(EXTRACT(EPOCH FROM (r.snapped_at - tr.target_time))) AS time_diff_sec
        FROM market.price_snapshots r
        JOIN target_races tr USING (race_id)
        WHERE r.snapped_at BETWEEN tr.target_time - INTERVAL '15 minutes' 
                                AND tr.target_time + INTERVAL '15 minutes'
    ),
    best_snapshot AS (
        SELECT 
            race_id,
            horse_id,
            decimal_odds,
            source,
            snapped_at,
            ROW_NUMBER() OVER (PARTITION BY race_id, horse_id ORDER BY time_diff_sec) AS rn
        FROM snapshots
    )
    SELECT 
        race_id,
        horse_id,
        decimal_odds,
        source,
        snapped_at AS snapshot_ts
    FROM best_snapshot
    WHERE rn = 1
    AND decimal_odds >= 1.01
    ORDER BY race_id, decimal_odds;
    """
    
    with engine.begin() as cx:
        df = pl.read_database(sql, connection=cx.connection)
    
    if len(df) == 0:
        print(f"   ⚠️  No market data found for {date_str}")
        print(f"   Check that:")
        print(f"      1. Races exist for this date")
        print(f"      2. Price snapshots have been collected")
        print(f"      3. Table names match: market.price_snapshots")
    else:
        print(f"   ✅ Loaded prices for {df['horse_id'].n_unique()} horses")
    
    return df


def compute_vig_free_probabilities(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert market odds to vig-free probabilities per race.
    
    Removes bookmaker overround to get true market implied probabilities.
    
    Args:
        df: DataFrame with race_id, decimal_odds
        
    Returns:
        DataFrame with added columns: q_market, overround, q_vigfree
    """
    print(f"\n🧮 Computing vig-free market probabilities...")
    
    # Market implied probability
    df = df.with_columns([
        (1.0 / pl.col("decimal_odds")).alias("q_market")
    ])
    
    # Calculate overround per race
    overround = df.group_by("race_id").agg([
        pl.col("q_market").sum().alias("overround")
    ])
    
    df = df.join(overround, on="race_id")
    
    # Vig-free probability (normalize to sum to 1.0)
    df = df.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
    ])
    
    # Sanity check overround
    overround_stats = df.select("overround").unique()
    mean_overround = overround_stats["overround"].mean()
    
    print(f"   Average overround: {mean_overround:.3f} ({(mean_overround-1)*100:.1f}% margin)")
    
    if mean_overround < 1.0 or mean_overround > 1.40:
        print(f"   ⚠️  WARNING: Unusual overround detected!")
        print(f"   Expected: 1.00-1.40, Got: {mean_overround:.3f}")
    else:
        print(f"   ✅ Overround is in expected range")
    
    return df


def score_and_filter(
    df: pl.DataFrame,
    model_name: str = "hrd_win_prob",
    model_stage: str = "Production"
) -> pl.DataFrame:
    """
    Score horses with ability model, compute edge/EV, filter by thresholds.
    
    Args:
        df: DataFrame with ability features and market data
        model_name: MLflow model name
        model_stage: MLflow stage (Production, Staging, etc.)
        
    Returns:
        DataFrame with scored horses meeting betting criteria
    """
    print(f"\n🎯 Scoring with model: {model_name} ({model_stage})")
    
    # Load model from MLflow
    model_uri = f"models:/{model_name}/{model_stage}"
    print(f"   Loading model from: {model_uri}")
    
    try:
        model = mlflow.pyfunc.load_model(model_uri)
    except Exception as e:
        print(f"   ❌ Failed to load model: {e}")
        print(f"   Make sure model is registered and promoted to {model_stage}")
        return pl.DataFrame()
    
    print(f"   ✅ Model loaded successfully")
    
    # Prepare features
    X = df.select([f for f in ABILITY_FEATURES if f in df.columns])
    
    # Handle missing values
    X = X.with_columns([
        pl.col(col).fill_null(0) for col in X.columns
    ])
    
    # Predict
    print(f"   Predicting on {len(df)} horses...")
    p_model = model.predict(X.to_pandas()).astype(float)
    
    # Add predictions to dataframe
    df = df.with_columns([
        pl.Series(name="p_model", values=p_model)
    ])
    
    # Compute fair odds
    df = df.with_columns([
        (1.0 / pl.col("p_model")).alias("fair_odds_win")
    ])
    
    # Compute edge
    df = df.with_columns([
        (pl.col("p_model") - pl.col("q_vigfree")).alias("edge_prob")
    ])
    
    # Compute EV (after commission)
    def calc_ev(p, odds):
        return ev_win(p, odds, COMMISSION)
    
    df = df.with_columns([
        pl.struct(["p_model", "decimal_odds"]).map_elements(
            lambda x: calc_ev(x["p_model"], x["decimal_odds"]),
            return_dtype=pl.Float64
        ).alias("ev_after_commission")
    ])
    
    # Compute Kelly stake
    def calc_kelly(p, odds):
        k = kelly_fraction(p, odds, COMMISSION)
        return min(KELLY_FRACTION * k, MAX_STAKE)
    
    df = df.with_columns([
        pl.struct(["p_model", "decimal_odds"]).map_elements(
            lambda x: calc_kelly(x["p_model"], x["decimal_odds"]),
            return_dtype=pl.Float64
        ).alias("stake_units")
    ])
    
    # ===== Filter by thresholds =====
    print(f"\n🔍 Applying filters:")
    print(f"   Edge >= {EDGE_MIN:.3f} ({EDGE_MIN*100:.1f}pp)")
    print(f"   Odds >= {ODDS_MIN:.2f}")
    print(f"   EV >= {EV_MIN:.3f} ({EV_MIN*100:.1f}%)")
    
    n_before = len(df)
    
    picks = df.filter(
        (pl.col("edge_prob") >= EDGE_MIN) &
        (pl.col("decimal_odds") >= ODDS_MIN) &
        (pl.col("ev_after_commission") >= EV_MIN) &
        (pl.col("stake_units") > 0.0)
    )
    
    n_after = len(picks)
    print(f"   {n_before} horses → {n_after} bets ({n_after/max(1,n_before)*100:.1f}%)")
    
    return picks


def publish_signals(picks: pl.DataFrame, model_id: int = 1) -> int:
    """
    Publish signals to modeling.signals table.
    
    Args:
        picks: DataFrame with betting signals
        model_id: Model ID from modeling.models
        
    Returns:
        Number of rows published
    """
    print(f"\n📤 Publishing {len(picks)} signals to database...")
    
    now = datetime.utcnow()
    rows = []
    
    for r in picks.iter_rows(named=True):
        rows.append({
            "as_of": now,
            "race_id": int(r["race_id"]),
            "horse_id": int(r["horse_id"]),
            "model_id": model_id,
            "p_win": float(r["p_model"]),
            "p_place": None,
            "fair_odds_win": float(r["fair_odds_win"]),
            "fair_odds_place": None,
            "best_odds_win": float(r["decimal_odds"]),
            "best_odds_src": r.get("source", "T-60"),
            "ew_places": None,
            "ew_fraction": None,
            "edge_win": float(r["ev_after_commission"]),
            "edge_ew": None,
            "kelly_fraction": float(r["stake_units"] / max(1e-9, KELLY_FRACTION)),
            "stake_units": float(r["stake_units"]),
            "liquidity_ok": True,
            "reasons": [
                {"feature": "gpr", "value": r.get("gpr")},
                {"feature": "gpr_minus_or", "value": r.get("gpr_minus_or")},
                {"edge_prob": float(r["edge_prob"])},
                {"ev": float(r["ev_after_commission"])},
            ],
        })
    
    if rows:
        from giddyup.publish.signals import publish
        n_published = publish(rows)
        print(f"   ✅ Published {n_published} signals")
        return n_published
    else:
        print(f"   ⚠️  No signals to publish")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Score races and publish signals")
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD), default: tomorrow")
    parser.add_argument("--model-name", type=str, default="hrd_win_prob", help="MLflow model name")
    parser.add_argument("--model-stage", type=str, default="Production", help="MLflow model stage")
    parser.add_argument("--t-minus", type=int, default=60, help="Minutes before off for snapshot")
    
    args = parser.parse_args()
    
    # Default to tomorrow
    if args.date:
        target_date = args.date
    else:
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print("=" * 80)
    print("🏇 GIDDYUP SCORING & PUBLISHING PIPELINE")
    print("=" * 80)
    print(f"\n📅 Target Date: {target_date}")
    print(f"🤖 Model: {args.model_name} ({args.model_stage})")
    print(f"⏰ Price Snapshot: T-{args.t_minus}")
    print(f"\n⚙️  Thresholds:")
    print(f"   Edge: {EDGE_MIN:.3f} ({EDGE_MIN*100:.1f}pp)")
    print(f"   Odds: {ODDS_MIN:.2f}+")
    print(f"   EV: {EV_MIN:.3f} ({EV_MIN*100:.1f}%)")
    print(f"   Commission: {COMMISSION:.3f} ({COMMISSION*100:.1f}%)")
    print(f"   Kelly: {KELLY_FRACTION:.2f} (max stake: {MAX_STAKE:.2f}u)")
    
    # Step 1: Get ability features
    ability_df = get_today_features(target_date)
    
    if len(ability_df) == 0:
        print(f"\n❌ No races found for {target_date}")
        return
    
    # Step 2: Get market snapshot
    market_df = get_market_snapshot_T_minus(target_date, args.t_minus)
    
    if len(market_df) == 0:
        print(f"\n❌ No market data available for {target_date}")
        return
    
    # Step 3: Join ability + market
    df = ability_df.join(market_df, on=["race_id", "horse_id"], how="inner")
    
    print(f"\n🔗 Joined ability + market: {len(df)} horses")
    
    # Step 4: Compute vig-free probabilities
    df = compute_vig_free_probabilities(df)
    
    # Step 5: Score and filter
    picks = score_and_filter(df, args.model_name, args.model_stage)
    
    if len(picks) == 0:
        print(f"\n⚠️  No qualifying bets found for {target_date}")
        print(f"   Try relaxing thresholds or checking model calibration")
        return
    
    # Step 6: Publish
    publish_signals(picks)
    
    # Summary
    print(f"\n" + "=" * 80)
    print(f"✅ SCORING COMPLETE")
    print(f"=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Races: {picks['race_id'].n_unique()}")
    print(f"   Bets: {len(picks)}")
    print(f"   Avg Odds: {picks['decimal_odds'].mean():.2f}")
    print(f"   Avg Edge: {picks['edge_prob'].mean():.3f} ({picks['edge_prob'].mean()*100:.1f}pp)")
    print(f"   Avg Stake: {picks['stake_units'].mean():.3f}u")
    print(f"   Total Stake: {picks['stake_units'].sum():.2f}u")
    
    # Show top 5 bets
    print(f"\n🎯 Top 5 Bets by EV:")
    top5 = picks.sort("ev_after_commission", descending=True).head(5)
    print(top5.select(["horse_name", "decimal_odds", "fair_odds_win", "edge_prob", "stake_units"]))


if __name__ == "__main__":
    main()
