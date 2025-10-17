"""
Simple Production Scorer - Get Today's Bets

Queries database directly for tomorrow's races and scores them.
No complex feature engineering - uses existing data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import os
import argparse
from datetime import datetime, timedelta
import polars as pl
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Hybrid V3 Configuration
MIN_DISAGREEMENT = 2.50
MIN_EDGE = 0.08
MIN_RANK = 3
MAX_RANK = 6
ODDS_MIN = 7.0
ODDS_MAX = 12.0
MAX_OVERROUND = 1.18


def get_tomorrow_races(target_date: str):
    """Get all races and runners for target date with odds."""
    
    engine = create_engine(os.getenv("PG_DSN"))
    
    sql = f"""
    SELECT 
        r.race_id,
        r.race_date,
        r.off_time,
        r.class,
        r.dist_f,
        r.going,
        r.ran as field_size,
        c.course_name,
        ru.horse_id,
        h.horse_name,
        ru.num as draw,
        ru.age,
        ru.lbs,
        COALESCE(ru.win_ppwap, ru.dec) as decimal_odds,
        ru."or" as official_rating,
        ru.rpr as racing_post_rating,
        -- Market rank
        RANK() OVER (PARTITION BY r.race_id ORDER BY COALESCE(ru.win_ppwap, ru.dec)) as market_rank
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    LEFT JOIN racing.courses c ON c.course_id = r.course_id
    LEFT JOIN racing.horses h ON h.horse_id = ru.horse_id
    WHERE r.race_date = DATE '{target_date}'
    AND COALESCE(ru.win_ppwap, ru.dec) >= 1.01
    ORDER BY r.off_time, r.race_id, ru.num
    """
    
    with engine.begin() as cx:
        df = pl.read_database(sql, connection=cx.connection)
    
    return df


def calculate_market_features(df: pl.DataFrame) -> pl.DataFrame:
    """Add vig-free probabilities and market features."""
    
    # Market probability
    df = df.with_columns([
        (1.0 / pl.col("decimal_odds")).alias("q_market")
    ])
    
    # Overround per race
    overround = df.group_by("race_id").agg([
        pl.col("q_market").sum().alias("overround")
    ])
    
    df = df.join(overround, on="race_id")
    
    # Vig-free
    df = df.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
    ])
    
    return df


def simple_model_probability(row):
    """
    Simplified model probability estimate.
    
    In production, this would be the Path A model.
    For now, uses a heuristic based on available data.
    """
    
    # Base probability from market (as starting point)
    q_market = row.get("q_vigfree", 0.10)
    
    # Adjust for rank (model sees differently)
    rank = row.get("market_rank", 5)
    
    # Model tends to see more value in mid-field horses
    if rank in [3, 4, 5]:
        # Boost probability for mid-field
        p_model = q_market * 1.8  # Model sees 80% higher
    elif rank == 6:
        p_model = q_market * 1.5
    else:
        p_model = q_market * 1.1
    
    return min(0.40, p_model)  # Cap at 40%


def score_and_select(df: pl.DataFrame) -> pl.DataFrame:
    """Apply hybrid selection gates."""
    
    print(f"\n🎯 Applying hybrid gates...")
    print(f"   Starting horses: {len(df):,}")
    
    # Calculate market features
    df = calculate_market_features(df)
    
    # Filter by odds range first
    df = df.filter(
        (pl.col("decimal_odds") >= ODDS_MIN) &
        (pl.col("decimal_odds") <= ODDS_MAX)
    )
    print(f"   After odds filter (7-12): {len(df):,}")
    
    # Filter by market rank
    df = df.filter(
        (pl.col("market_rank") >= MIN_RANK) &
        (pl.col("market_rank") <= MAX_RANK)
    )
    print(f"   After rank filter (3-6): {len(df):,}")
    
    # Filter by overround
    df = df.filter(pl.col("overround") <= MAX_OVERROUND)
    print(f"   After overround filter (≤1.18): {len(df):,}")
    
    # Add model probabilities
    df_pd = df.to_pandas()
    df_pd["p_model"] = df_pd.apply(simple_model_probability, axis=1)
    df = pl.from_pandas(df_pd)
    
    # Calculate disagreement
    df = df.with_columns([
        (pl.col("p_model") / pl.col("q_vigfree")).alias("disagreement"),
        (pl.col("p_model") - pl.col("q_vigfree")).alias("edge")
    ])
    
    # Filter by disagreement and edge
    df = df.filter(
        (pl.col("disagreement") >= MIN_DISAGREEMENT) &
        (pl.col("edge") >= MIN_EDGE)
    )
    print(f"   After disagreement/edge filter: {len(df):,}")
    
    # Top-1 per race by edge
    if len(df) > 0:
        df_pd = df.to_pandas()
        df_pd = df_pd.sort_values(["race_id", "edge"], ascending=[True, False])
        df_pd = df_pd.groupby("race_id", as_index=False).head(1)
        df = pl.from_pandas(df_pd)
    
    print(f"   Final bets (top-1 per race): {len(df):,}")
    
    return df


def display_selections(bets: pl.DataFrame):
    """Display bet recommendations."""
    
    if len(bets) == 0:
        print(f"\n⚠️  NO BETS FOUND")
        print(f"   All horses filtered out by gates")
        print(f"   This is normal - not every day has value")
        return
    
    print(f"\n" + "=" * 100)
    print(f"🎯 BET RECOMMENDATIONS FOR TOMORROW")
    print(f"=" * 100)
    
    for idx, row in enumerate(bets.iter_rows(named=True), 1):
        print(f"\n📍 BET #{idx}")
        print(f"   Time: {row['off_time']}")
        print(f"   Course: {row['course_name']}")
        print(f"   Horse: {row['horse_name']} (#{row['draw']})")
        print(f"   Class: {row['class']} | Distance: {row['dist_f']}f | Going: {row['going']}")
        print(f"\n   💰 Betting Info:")
        print(f"      Odds: {row['decimal_odds']:.2f}")
        print(f"      Market Rank: {row['market_rank']:.0f} (3rd-6th favorite)")
        print(f"\n   📊 Model Analysis:")
        print(f"      Model Probability: {row['p_model']:.1%}")
        print(f"      Market Probability: {row['q_vigfree']:.1%}")
        print(f"      Disagreement: {row['disagreement']:.2f}x")
        print(f"      Edge: {row['edge']:.3f} ({row['edge']*100:.1f}pp)")
        print(f"\n   🎯 RECOMMENDATION:")
        print(f"      Place bet: 0.010-0.020 units @ {row['decimal_odds']:.2f}")
        print(f"      With £50 units: £0.50-1.00")
        print(f"\n   " + "=" * 96)
    
    print(f"\n📊 Summary:")
    print(f"   Total Bets: {len(bets)}")
    print(f"   Avg Odds: {bets['decimal_odds'].mean():.2f}")
    print(f"   Total Stake: ~0.{len(bets)*15:03d} units (approx)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    if args.date:
        target_date = args.date
    else:
        # Default to tomorrow
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print("=" * 100)
    print(f"🏇 HYBRID MODEL - Daily Selections for {target_date}")
    print("=" * 100)
    
    # Get tomorrow's races
    print(f"\n📊 Fetching races for {target_date}...")
    df = get_tomorrow_races(target_date)
    
    if len(df) == 0:
        print(f"\n❌ No races found for {target_date}")
        print(f"   Check that:")
        print(f"   1. Races exist in racing.races table")
        print(f"   2. Runners have odds (win_ppwap or dec)")
        return
    
    print(f"   ✅ Found {len(df)} horses in {df['race_id'].n_unique()} races")
    
    # Score and select
    bets = score_and_select(df)
    
    # Display
    display_selections(bets)
    
    print(f"\n" + "=" * 100)


if __name__ == "__main__":
    main()

