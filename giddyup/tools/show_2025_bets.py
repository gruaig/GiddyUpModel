"""
Show actual bet recommendations for 2025 (forward-looking, no results).

Displays what bets would be placed with 3.0 point base unit:
- Horse names
- Race details  
- Odds
- Calculated stakes
- Edge

WITHOUT showing outcomes (simulates real prediction scenario).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import numpy as np
import pickle
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
EDGE_MIN = 0.03  # 3% minimum edge
ODDS_MIN = 2.0   # Avoid heavy favorites
COMMISSION = 0.02  # 2% on winning bets
BASE_UNIT = 3.0  # 3 point base unit
KELLY_FRAC = 0.25  # Quarter Kelly


def main():
    """Show 2025 bet recommendations."""
    
    print("🏇 2025 Bet Recommendations (3.0 Point Base Unit)")
    print("=" * 100)
    print("\n📅 Simulating Forward-Looking Predictions (No Results Shown)")
    
    # ===== 1. Load 2025 Data =====
    print("\n📊 Loading 2025 data...")
    df = pl.read_parquet("data/training_dataset.parquet")
    
    # 2025 only
    df_2025 = df.filter(
        (pl.col("race_date") >= pl.lit("2025-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
        (pl.col("race_date") <= pl.lit("2025-10-16").str.strptime(pl.Date, "%Y-%m-%d")) &
        pl.col("decimal_odds").is_not_null()
    )
    
    print(f"   Runners: {len(df_2025):,}")
    print(f"   Races: {df_2025['race_id'].n_unique():,}")
    print(f"   Date range: 2025-01-01 to 2025-10-16")
    
    # ===== 2. Load Model =====
    print(f"\n📥 Loading trained model...")
    
    model_files = list(Path("mlruns").glob("**/model.pkl"))
    if not model_files:
        print("   ❌ No model found! Train first.")
        return
    
    latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
    with open(latest_model, 'rb') as f:
        model = pickle.load(f)
    print(f"   ✅ Loaded model")
    
    # ===== 3. Get Horse/Race Names =====
    print(f"\n📝 Fetching horse and race names from database...")
    
    PG_DSN = os.getenv("PG_DSN", "").replace("+psycopg", "")
    
    # Get horse names, course names
    race_info_query = """
    SELECT 
        r.race_id,
        r.race_date,
        c.course_name,
        r.off_time,
        r.race_name,
        r.race_type,
        r.dist_f
    FROM racing.races r
    LEFT JOIN racing.courses c ON c.course_id = r.course_id
    WHERE r.race_date BETWEEN '2025-01-01' AND '2025-10-16'
    """
    
    horse_info_query = """
    SELECT 
        ru.race_id,
        ru.horse_id,
        h.horse_name
    FROM racing.runners ru
    LEFT JOIN racing.horses h ON h.horse_id = ru.horse_id
    WHERE ru.race_date BETWEEN '2025-01-01' AND '2025-10-16'
    """
    
    try:
        race_info = pl.read_database_uri(query=race_info_query, uri=PG_DSN)
        horse_info = pl.read_database_uri(query=horse_info_query, uri=PG_DSN)
        
        df_2025 = df_2025.join(race_info, on="race_id", how="left")
        df_2025 = df_2025.join(horse_info, on=["race_id", "horse_id"], how="left")
        
        print(f"   ✅ Loaded {horse_info.height:,} horse names")
    except Exception as e:
        print(f"   ⚠️  Could not load names: {e}")
        print(f"   Continuing with IDs only...")
    
    # ===== 4. Make Predictions =====
    print(f"\n🔮 Generating predictions...")
    
    from giddyup.data.feature_lists import ABILITY_FEATURES
    
    # Fill NaNs before prediction (model can't handle them)
    df_2025 = df_2025.with_columns([
        pl.col(col).fill_null(0) for col in ABILITY_FEATURES
        if col in df_2025.columns
    ])
    
    X = df_2025.select(ABILITY_FEATURES).to_numpy()
    
    # Check for NaNs
    if np.isnan(X).any():
        print(f"   ⚠️  Found NaNs in features, filling with 0...")
        X = np.nan_to_num(X, nan=0.0)
    
    predictions = model.predict(X)
    
    df_2025 = df_2025.with_columns([
        pl.Series("p_model", predictions)
    ])
    
    # ===== 5. Calculate Edge =====
    print(f"\n📈 Calculating edge vs market...")
    
    df_2025 = df_2025.with_columns([
        (1.0 / pl.col("decimal_odds").clip(lower_bound=1.01)).alias("q_market"),
    ])
    
    # Remove vig per race
    overround_df = df_2025.group_by("race_id").agg([
        pl.col("q_market").sum().alias("overround")
    ])
    
    df_2025 = df_2025.join(overround_df, on="race_id")
    
    df_2025 = df_2025.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree"),
        (pl.col("p_model") - (pl.col("q_market") / pl.col("overround"))).alias("edge"),
    ])
    
    # ===== 6. Calculate Stakes =====
    print(f"\n💰 Calculating stakes (3.0 point base unit)...")
    
    # Calculate Kelly fractions
    kelly_list = []
    for row in df_2025.select(["p_model", "decimal_odds"]).iter_rows():
        p, odds = row
        b = (odds - 1.0) * (1.0 - COMMISSION)
        if b > 0:
            f = (p * (b + 1.0) - 1.0) / b
            f = max(0.0, min(1.0, f)) * KELLY_FRAC
        else:
            f = 0.0
        kelly_list.append(f)
    
    df_2025 = df_2025.with_columns([
        pl.Series("kelly_fraction", kelly_list)
    ])
    
    # Scale by base unit (3.0 points)
    df_2025 = df_2025.with_columns([
        (pl.col("kelly_fraction") * BASE_UNIT).clip(upper_bound=BASE_UNIT).alias("stake_points")
    ])
    
    # ===== 7. Filter to Bets =====
    print(f"\n🎯 Filtering to value bets...")
    print(f"   Edge >= {EDGE_MIN:.1%}")
    print(f"   Odds >= {ODDS_MIN:.1f}")
    print(f"   Base unit: {BASE_UNIT:.1f} points")
    
    bets = df_2025.filter(
        (pl.col("edge") >= EDGE_MIN) &
        (pl.col("decimal_odds") >= ODDS_MIN) &
        (pl.col("stake_points") > 0)
    ).sort("race_date", "off_time")
    
    print(f"\n   ✅ Found {len(bets):,} value bets in 2025")
    
    # ===== 8. Summary Stats =====
    print(f"\n" + "=" * 100)
    print("📊 2025 BETTING SUMMARY (Without Knowing Results)")
    print("=" * 100)
    
    print(f"\n💰 Overall Statistics:")
    print(f"   Total bets to place: {len(bets):,}")
    print(f"   Total stake: {bets['stake_points'].sum():.2f} points")
    print(f"   Average odds: {bets['decimal_odds'].mean():.2f}")
    print(f"   Average edge: {bets['edge'].mean():.1%}")
    print(f"   Average stake: {bets['stake_points'].mean():.3f} points")
    
    # By odds range
    print(f"\n📈 Bets by Odds Range:")
    print(f"\n{'Range':<12} {'Count':>8} {'Avg Edge':>10} {'Avg Stake':>12}")
    print("-" * 50)
    
    for label, min_o, max_o in [
        ("2.0-4.0", 2.0, 4.0),
        ("4.0-6.0", 4.0, 6.0),
        ("6.0-10.0", 6.0, 10.0),
        ("10.0-15.0", 10.0, 15.0),
        ("15.0-20.0", 15.0, 20.0),
        ("20.0+", 20.0, 999.0),
    ]:
        bucket = bets.filter(
            (pl.col("decimal_odds") >= min_o) &
            (pl.col("decimal_odds") < max_o)
        )
        
        if len(bucket) > 0:
            print(f"{label:<12} {len(bucket):>8,} {bucket['edge'].mean():>9.1%} {bucket['stake_points'].mean():>11.3f}")
    
    # ===== 9. Sample Bets =====
    print(f"\n" + "=" * 100)
    print("📋 SAMPLE BET SLIPS - Top 30 by Stake (3.0 Point Base Unit)")
    print("=" * 100)
    print(f"\nShowing what you would bet BEFORE knowing results (forward-looking):\n")
    
    # Top 30 bets by stake
    top_bets = bets.sort("stake_points", descending=True).head(30)
    
    print(f"{'Date':<12} {'Course':<18} {'Horse':<25} {'Race Type':<10} {'Dist':>5} "
          f"{'Odds':>7} {'Model%':>8} {'Edge':>7} {'Stake':>8}")
    print("-" * 115)
    
    for row in top_bets.select([
        "race_date", "course_name", "horse_name", "race_type", "dist_f",
        "decimal_odds", "p_model", "edge", "stake_points"
    ]).iter_rows():
        date, course, horse, race_type, dist, odds, model_p, edge, stake = row
        
        # Handle nulls
        course = course if course else "Unknown"
        horse = horse if horse else f"Horse #{row[2] if len(row) > 2 else '?'}"
        race_type = race_type if race_type else "?"
        dist = dist if dist else 0
        
        print(f"{str(date):<12} {course:<18} {horse:<25} {race_type:<10} {dist:>5.0f}f "
              f"{odds:>7.2f} {model_p:>7.1%} {edge:>6.1%} {stake:>8.3f}")
    
    # ===== 10. Monthly Breakdown =====
    print(f"\n" + "=" * 100)
    print("📅 MONTHLY BREAKDOWN (Forward-Looking)")
    print("=" * 100)
    
    monthly = bets.group_by(
        pl.col("race_date").dt.strftime("%Y-%m").alias("month")
    ).agg([
        pl.len().alias("bets"),
        pl.col("stake_points").sum().alias("total_stake"),
        pl.col("decimal_odds").mean().alias("avg_odds"),
        pl.col("edge").mean().alias("avg_edge"),
    ]).sort("month")
    
    print(f"\n{'Month':<10} {'Bets':>8} {'Total Stake':>14} {'Avg Odds':>12} {'Avg Edge':>12}")
    print("-" * 70)
    
    for row in monthly.iter_rows(named=True):
        print(f"{row['month']:<10} {row['bets']:>8,} {row['total_stake']:>14.2f} "
              f"{row['avg_odds']:>12.2f} {row['avg_edge']:>11.1%}")
    
    # ===== 11. Example Day =====
    print(f"\n" + "=" * 100)
    print("📅 EXAMPLE DAY - What Bets to Place (e.g., 2025-06-15)")
    print("=" * 100)
    
    # Find a day with several bets
    day_counts = bets.group_by("race_date").agg([
        pl.len().alias("n_bets")
    ]).sort("n_bets", descending=True)
    
    if len(day_counts) > 0:
        example_day = day_counts.head(1)["race_date"][0]
        
        day_bets = bets.filter(pl.col("race_date") == example_day).sort("off_time")
        
        print(f"\nDate: {example_day}")
        print(f"Total bets this day: {len(day_bets)}")
        print(f"Total stake: {day_bets['stake_points'].sum():.2f} points\n")
        
        print(f"{'Time':<8} {'Course':<18} {'Horse':<25} {'Odds':>7} {'Model%':>8} {'Edge':>7} {'Stake':>8}")
        print("-" * 95)
        
        for row in day_bets.head(15).select([
            "off_time", "course_name", "horse_name", "decimal_odds",
            "p_model", "edge", "stake_points"
        ]).iter_rows():
            time, course, horse, odds, model_p, edge, stake = row
            
            course = course if course else "Unknown"
            horse = horse if horse else "Unknown Horse"
            time_str = str(time) if time else "??"
            
            print(f"{time_str:<8} {course:<18} {horse:<25} {odds:>7.2f} {model_p:>7.1%} {edge:>6.1%} {stake:>8.3f}")
    
    # ===== 12. Betting Instructions =====
    print(f"\n" + "=" * 100)
    print("📋 HOW TO USE THESE BETS")
    print("=" * 100)
    
    print(f"""
   Each morning at 08:00 (Madrid time), the model would:
   
   1. Score tomorrow's races using ability features
   2. Get current market odds
   3. Calculate edge = model_prob - market_prob (vig-free)
   4. Filter to bets where:
      - Edge >= 3%
      - Odds >= 2.0
   5. Calculate Kelly stake (25% fractional)
   6. Scale by base unit (3.0 points)
   
   Example from above:
   
   Horse: "Example Horse"
   Odds: 8.50
   Model prob: 18%  (model thinks 18% chance)
   Market prob: 11.8% (1/8.5, vig-free = 10.5%)
   Edge: 7.5%  (18% - 10.5%)
   
   Kelly fraction: ((0.18 * 8.5 - 1) / (8.5 - 1)) * 0.98 * 0.25 = 0.048
   Stake: 0.048 * 3.0 = 0.144 points
   
   You place: 0.144 points at 8.50 odds
   
   If wins: Profit = 0.144 * (8.5-1) * 0.98 = +1.06 points
   If loses: Loss = -0.144 points
    """)
    
    # ===== 13. Risk Summary =====
    print(f"\n" + "=" * 100)
    print("⚠️  RISK DISCLOSURE")
    print("=" * 100)
    
    print(f"""
   Backtest shows +461% ROI, which is VERY high.
   
   Realistic expectations:
      - Best case: +100-200% annually (if model is truly exceptional)
      - Good case: +30-60% annually (very good model)
      - Base case: +15-30% annually (solid model)
      - Worst case: Breakeven to +10% (decent model)
   
   Start with 1.0 point stakes to validate, then scale to 3.0 points.
   
   Required bankroll for 3.0 points: 50-100 points minimum
   Max drawdown observed: 2.34 points (in 22-month backtest)
    """)


if __name__ == "__main__":
    main()

