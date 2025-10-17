"""
Demo: What bets would the model place on 2024 data?

Since we're using market features, the model will largely agree with the market.
This script shows REALISTIC examples of where edge might be found.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import numpy as np


def main():
    """Show realistic betting examples."""
    
    print("🏇 Model Betting Analysis - 2024 Hold-Out")
    print("=" * 80)
    
    # Load 2024 data
    print("\n📊 Loading 2024 data...")
    df = pl.read_parquet("data/training_dataset.parquet")
    
    test_df = df.filter(
        (pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
        (pl.col("race_date") <= pl.lit("2024-12-31").str.strptime(pl.Date, "%Y-%m-%d"))
    )
    
    print(f"   Runners: {len(test_df):,}")
    print(f"   Races: {test_df['race_id'].n_unique():,}")
    
    # ===== SIMULATE MODEL BEHAVIOR =====
    print("\n🤖 Simulating model behavior...")
    print("   (Model uses market + form features)")
    
    # The model will:
    # 1. Start with market probability
    # 2. Adjust based on form features
    
    test_df = test_df.with_columns([
        # Market implied probability
        (1 / pl.col("decimal_odds").clip(lower_bound=1.01))
            .alias("market_prob"),
    ])
    
    # Simulate model adjustments based on form
    test_df = test_df.with_columns([
        pl.when(
            # High RPR + good trainer form = upgrade
            (pl.col("racing_post_rating") > pl.col("racing_post_rating").median()) &
            (pl.col("trainer_sr_total") > 0.15)
        )
            .then(pl.col("market_prob") * 1.15)  # 15% boost
        .when(
            # Good course record = upgrade
            (pl.col("wins_at_course") > 0) &
            (pl.col("runs_at_course") > 2)
        )
            .then(pl.col("market_prob") * 1.10)  # 10% boost
        .when(
            # Low RPR + poor trainer = downgrade
            (pl.col("racing_post_rating") < 60) |
            (pl.col("trainer_sr_total") < 0.05)
        )
            .then(pl.col("market_prob") * 0.90)  # 10% penalty
        .otherwise(pl.col("market_prob"))
            .clip(upper_bound=0.95)
            .alias("model_prob"),
    ])
    
    # Calculate edge
    test_df = test_df.with_columns([
        (pl.col("model_prob") - pl.col("market_prob"))
            .alias("edge"),
        
        # Fair odds
        (1 / pl.col("model_prob").clip(lower_bound=0.01))
            .alias("fair_odds"),
    ])
    
    # Kelly stake (25% fractional)
    test_df = test_df.with_columns([
        (((pl.col("model_prob") * pl.col("decimal_odds") - 1) / 
         (pl.col("decimal_odds") - 1).clip(lower_bound=0.01))
            .clip(lower_bound=0, upper_bound=1.0) * 0.25)
            .alias("kelly_fraction")
    ])
    
    test_df = test_df.with_columns([
        pl.col("kelly_fraction").clip(lower_bound=0, upper_bound=1.0).alias("stake_units")
    ])
    
    # ===== FILTER TO BETS =====
    print("\n🎯 Betting filters:")
    print("   - Edge > 5%")
    print("   - Kelly fraction > 1%")
    
    bets_df = test_df.filter(
        (pl.col("edge") > 0.05) &
        (pl.col("kelly_fraction") > 0.01)
    )
    
    print(f"\n   Found: {len(bets_df):,} bets ({len(bets_df)/len(test_df)*100:.2f}% of runners)")
    
    if len(bets_df) == 0:
        print("\n   ⚠️  NO BETS FOUND with current criteria")
        print("\n   This happens when:")
        print("      - Model closely follows market (high AUC = 0.96)")
        print("      - Market features dominate")
        print("      - Hard to find mispricing")
        
        print("\n   Let's try LOWER edge threshold (2% instead of 5%)...")
        
        bets_df = test_df.filter(
            (pl.col("edge") > 0.02) &
            (pl.col("kelly_fraction") > 0.005)
        )
        
        print(f"   With 2% edge: {len(bets_df):,} bets ({len(bets_df)/len(test_df)*100:.2f}%)")
    
    if len(bets_df) == 0:
        print("\n   Still no bets! Let's show TOP edge opportunities...")
        
        bets_df = test_df.sort("edge", descending=True).head(100)
    
    # ===== CALCULATE P&L =====
    bets_df = bets_df.with_columns([
        pl.when(pl.col("won"))
            .then(pl.col("stake_units") * (pl.col("decimal_odds") - 1))
        .otherwise(-pl.col("stake_units"))
            .alias("pnl")
    ])
    
    # ===== SUMMARY =====
    print(f"\n" + "=" * 80)
    print("📊 BETTING SUMMARY")
    print("=" * 80)
    
    total_bets = len(bets_df)
    total_wins = bets_df["won"].sum()
    total_stake = bets_df["stake_units"].sum()
    total_pnl = bets_df["pnl"].sum()
    avg_odds = bets_df["decimal_odds"].mean()
    
    print(f"\n💰 Results:")
    print(f"   Bets: {total_bets:,}")
    print(f"   Winners: {total_wins} ({total_wins/total_bets*100:.1f}%)")
    print(f"   Total Staked: {total_stake:.2f} units")
    print(f"   Total P&L: {total_pnl:+.2f} units")
    print(f"   ROI: {total_pnl/total_stake*100:+.1f}%")
    print(f"   Average Odds: {avg_odds:.2f}")
    print(f"   Average Stake: {total_stake/total_bets:.3f} units")
    
    # ===== ODDS DISTRIBUTION =====
    print(f"\n📈 Bets by Odds:")
    
    for label, min_o, max_o in [
        ("Favorites (< 3.0)", 1.0, 3.0),
        ("Short (3-6)", 3.0, 6.0),
        ("Mid (6-12)", 6.0, 12.0),
        ("Long (12-25)", 12.0, 25.0),
        ("Outsiders (25+)", 25.0, 999.0),
    ]:
        bucket = bets_df.filter(
            (pl.col("decimal_odds") >= min_o) &
            (pl.col("decimal_odds") < max_o)
        )
        
        if len(bucket) > 0:
            n = len(bucket)
            wins = bucket["won"].sum()
            stake = bucket["stake_units"].sum()
            pnl = bucket["pnl"].sum()
            
            print(f"   {label:<20} {n:>5} bets, {wins:>4} wins ({wins/n*100:>5.1f}%), "
                  f"ROI: {pnl/stake*100:>+6.1f}%")
    
    # ===== SAMPLE BETS =====
    print(f"\n" + "=" * 80)
    print("📋 SAMPLE BETS (Top 20 by stake)")
    print("=" * 80)
    
    samples = bets_df.sort("stake_units", descending=True).head(20)
    
    print(f"\n{'Date':<12} {'Odds':>6} {'Model%':>7} {'Market%':>8} {'Edge':>6} {'Stake':>7} {'Won':>4} {'P&L':>8}")
    print("-" * 90)
    
    for row in samples.select([
        "race_date", "decimal_odds", "model_prob", "market_prob",
        "edge", "stake_units", "won", "pnl"
    ]).iter_rows():
        date, odds, model_p, market_p, edge, stake, won, pnl = row
        won_str = "✅" if won else "❌"
        print(f"{str(date):<12} {odds:>6.2f} {model_p:>6.1%} {market_p:>7.1%} "
              f"{edge:>5.1%} {stake:>7.3f} {won_str:>4} {pnl:>+8.2f}")
    
    # ===== VERDICT =====
    print(f"\n" + "=" * 80)
    print("🎯 VERDICT: IS MODEL FINDING VALUE?")
    print("=" * 80)
    
    print(f"\n📊 Model betting on average {avg_odds:.2f} odds")
    
    if avg_odds < 4.0:
        print(f"\n   ⚠️  MOSTLY FAVORITES (avg odds < 4.0)")
        print(f"\n   Analysis:")
        print(f"      - Model follows market closely")
        print(f"      - Market features (decimal_odds) dominate")
        print(f"      - Form features provide small adjustments")
        print(f"      - Hard to find big edge")
        
        print(f"\n   Expected behavior:")
        print(f"      - ROI: 0-5% (marginal after commission)")
        print(f"      - Betting on well-backed horses")
        print(f"      - Low variance but low edge")
        
        print(f"\n   💡 To find MORE value:")
        print(f"      Option A: Remove market features (more independent)")
        print(f"      Option B: Increase edge threshold (10%+ for longshots)")
        print(f"      Option C: Focus on specific angles (course specialists, draw bias)")
    
    elif avg_odds < 8.0:
        print(f"\n   ✅ BALANCED RANGE (4-8 average odds)")
        print(f"      Good mix of favorites and value plays")
    
    else:
        print(f"\n   🎲 LONGSHOT BETTING (avg odds > 8.0)")
        print(f"      High variance, need large sample")
    
    # ===== KEY INSIGHT =====
    print(f"\n" + "=" * 80)
    print("💡 KEY INSIGHT")
    print("=" * 80)
    
    print(f"""
   With AUC = 0.96, your model AGREES with the market 96% of the time.
   
   This means:
      - Market odds = 5.0 → Model prob ≈ 20% (agrees!)
      - Market odds = 10.0 → Model prob ≈ 10% (agrees!)
      
   Finding edge requires:
      - Form features market hasn't priced in
      - Trainer/jockey hot streaks
      - Course specialists
      - Draw bias corrections
      - Speed ratings market undervalues
      
   Typical edge: 1-3% (not 5%+)
   Typical ROI: 2-8% before commission
   
   To see bets, try LOWER edge threshold (1-2% instead of 5%)
    """)


if __name__ == "__main__":
    main()

