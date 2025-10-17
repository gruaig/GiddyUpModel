"""
Backtest with value-based betting strategy.

Tests ability-only model on 2024-2025 hold-out with:
- Edge filter (>= 3%)
- Odds filter (>= 2.0)  
- 2% commission
- Fractional Kelly (25%)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import numpy as np
import pickle
from pathlib import Path

# Configuration
EDGE_MIN = 0.03  # 3% minimum edge
ODDS_MIN = 2.0   # Avoid heavy favorites
COMMISSION = 0.02  # 2% on winning bets
KELLY_FRAC = 0.25  # Quarter Kelly


def calculate_pnl(stake: float, odds: float, won: bool, commission: float = 0.02) -> float:
    """Calculate P&L with commission on winning bets."""
    if won:
        gross_profit = stake * (odds - 1)
        net_profit = gross_profit * (1 - commission)
        return net_profit
    else:
        return -stake


def main():
    """Run value-based backtest."""
    
    print("🏇 Value-Based Backtest - 2024-2025 Hold-Out")
    print("=" * 80)
    print(f"\n🎯 Strategy:")
    print(f"   - Ability-only model (NO market features in training)")
    print(f"   - Edge >= {EDGE_MIN:.1%}")
    print(f"   - Odds >= {ODDS_MIN:.1f}")
    print(f"   - Commission: {COMMISSION:.1%}")
    print(f"   - Fractional Kelly: {KELLY_FRAC:.0%}")
    
    # ===== 1. Load Data =====
    print(f"\n📊 Loading 2024-2025 data...")
    df = pl.read_parquet("data/training_dataset.parquet")
    
    test_df = df.filter(
        (pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
        (pl.col("race_date") <= pl.lit("2025-10-16").str.strptime(pl.Date, "%Y-%m-%d"))
    )
    
    print(f"   Runners: {len(test_df):,}")
    print(f"   Races: {test_df['race_id'].n_unique():,}")
    print(f"   Actual winners: {test_df['won'].sum():,} ({test_df['won'].mean():.1%})")
    
    # ===== 2. Load Model =====
    print(f"\n📥 Loading trained model...")
    
    mlruns_path = Path("mlruns/0")
    model_loaded = False
    
    if mlruns_path.exists():
        run_dirs = [d for d in mlruns_path.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if run_dirs:
            latest_run = max(run_dirs, key=lambda p: p.stat().st_mtime)
            model_path = latest_run / "artifacts" / "calibrated_model" / "model.pkl"
            
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                print(f"   ✅ Loaded model from {latest_run.name}")
                model_loaded = True
    
    if not model_loaded:
        print(f"   ❌ Model not found! Train first with:")
        print(f"      uv run python tools/train_model.py")
        return
    
    # ===== 3. Make Predictions =====
    print(f"\n🔮 Generating predictions...")
    
    from giddyup.data.feature_lists import ABILITY_FEATURES
    
    X = test_df.select(ABILITY_FEATURES).to_numpy()
    predictions = model.predict(X)
    
    test_df = test_df.with_columns([
        pl.Series("p_model", predictions)
    ])
    
    print(f"   Model probabilities: {predictions.min():.1%} to {predictions.max():.1%}")
    print(f"   Average: {predictions.mean():.1%}")
    
    # ===== 4. Calculate Edge =====
    print(f"\n📈 Calculating edge...")
    
    test_df = test_df.with_columns([
        # Market implied probability
        (1.0 / pl.col("decimal_odds").clip(lower_bound=1.01)).alias("q_market"),
    ])
    
    # Remove vig per race
    overround_df = test_df.group_by("race_id").agg([
        pl.col("q_market").sum().alias("overround")
    ])
    
    test_df = test_df.join(overround_df, on="race_id")
    
    test_df = test_df.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree"),
        (pl.col("p_model") - (pl.col("q_market") / pl.col("overround"))).alias("edge"),
    ])
    
    # ===== 5. Calculate Stakes =====
    print(f"\n💰 Calculating stakes...")
    
    # Kelly fraction with commission
    stakes = []
    for row in test_df.select(["p_model", "decimal_odds"]).iter_rows():
        p, odds = row
        b = (odds - 1.0) * (1.0 - COMMISSION)
        if b > 0:
            f = (p * (b + 1.0) - 1.0) / b
            f = max(0.0, min(1.0, f)) * KELLY_FRAC
        else:
            f = 0.0
        stakes.append(f)
    
    test_df = test_df.with_columns([
        pl.Series("kelly_fraction", stakes).clip(upper_bound=1.0).alias("stake_units")
    ])
    
    # ===== 6. Filter to Bets =====
    print(f"\n🎯 Filtering to value bets...")
    print(f"   Edge >= {EDGE_MIN:.1%}")
    print(f"   Odds >= {ODDS_MIN:.2f}")
    
    bets_df = test_df.filter(
        (pl.col("edge") >= EDGE_MIN) &
        (pl.col("decimal_odds") >= ODDS_MIN) &
        (pl.col("stake_units") > 0)
    )
    
    print(f"\n   Bets found: {len(bets_df):,} ({len(bets_df)/len(test_df)*100:.2f}% of runners)")
    
    if len(bets_df) == 0:
        print(f"\n   ⚠️  NO BETS with current criteria")
        print(f"   This means model agrees with market (good calibration!)")
        print(f"   Try lower edge threshold or check model independence")
        return
    
    # ===== 7. Calculate P&L =====
    print(f"\n💵 Calculating P&L with {COMMISSION:.0%} commission...")
    
    pnl_list = []
    for row in bets_df.select(["stake_units", "decimal_odds", "won"]).iter_rows():
        stake, odds, won = row
        pnl = calculate_pnl(stake, odds, won, COMMISSION)
        pnl_list.append(pnl)
    
    bets_df = bets_df.with_columns([
        pl.Series("pnl", pnl_list)
    ])
    
    # ===== 8. Results =====
    print(f"\n" + "=" * 80)
    print("📊 BACKTEST RESULTS (2024-2025)")
    print("=" * 80)
    
    total_bets = len(bets_df)
    total_wins = bets_df["won"].sum()
    total_stake = bets_df["stake_units"].sum()
    total_pnl = bets_df["pnl"].sum()
    avg_odds = bets_df["decimal_odds"].mean()
    avg_edge = bets_df["edge"].mean()
    
    roi = (total_pnl / total_stake * 100) if total_stake > 0 else 0
    
    print(f"\n💰 Financial:")
    print(f"   Bets: {total_bets:,}")
    print(f"   Winners: {total_wins} ({total_wins/total_bets*100:.1f}%)")
    print(f"   Staked: {total_stake:.2f} units")
    print(f"   P&L: {total_pnl:+.2f} units")
    print(f"   ROI: {roi:+.1f}%")
    
    print(f"\n📊 Betting:")
    print(f"   Average odds: {avg_odds:.2f}")
    print(f"   Average edge: {avg_edge:.1%}")
    print(f"   Average stake: {total_stake/total_bets:.3f} units")
    
    # ===== 9. By Odds Range =====
    print(f"\n📈 Performance by Odds:")
    print(f"\n{'Range':<12} {'Bets':>7} {'Wins':>6} {'Win%':>7} {'Stake':>8} {'P&L':>10} {'ROI':>8}")
    print("-" * 75)
    
    for label, min_o, max_o in [
        ("2.0-4.0", 2.0, 4.0),
        ("4.0-6.0", 4.0, 6.0),
        ("6.0-10.0", 6.0, 10.0),
        ("10.0-15.0", 10.0, 15.0),
        ("15.0+", 15.0, 999.0),
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
            bucket_roi = pnl / stake * 100 if stake > 0 else 0
            
            print(f"{label:<12} {n:>7,} {wins:>6} {wins/n*100:>6.1f}% {stake:>8.2f} {pnl:>+10.2f} {bucket_roi:>+7.1f}%")
    
    # ===== 10. Sample Bets =====
    print(f"\n" + "=" * 80)
    print("📋 SAMPLE BETS (Top 15 by stake)")
    print("=" * 80)
    
    samples = bets_df.sort("stake_units", descending=True).head(15)
    
    print(f"\n{'Date':<12} {'Odds':>6} {'Model%':>7} {'Market%':>8} {'Edge':>6} {'Stake':>7} {'Won':>4} {'P&L':>8}")
    print("-" * 85)
    
    for row in samples.select([
        "race_date", "decimal_odds", "p_model", "q_vigfree",
        "edge", "stake_units", "won", "pnl"
    ]).iter_rows():
        date, odds, model_p, market_p, edge, stake, won, pnl = row
        won_str = "✅" if won else "❌"
        print(f"{str(date):<12} {odds:>6.2f} {model_p:>6.1%} {market_p:>7.1%} "
              f"{edge:>5.1%} {stake:>7.3f} {won_str:>4} {pnl:>+8.2f}")
    
    # ===== 11. Verdict =====
    print(f"\n" + "=" * 80)
    print("🎯 VERDICT")
    print("=" * 80)
    
    print(f"\n   Average betting odds: {avg_odds:.2f}")
    
    if avg_odds < 4.0:
        print(f"   ⚠️  Still betting favorites (< 4.0)")
        print(f"       Increase ODDS_MIN to 4.0 or 6.0")
    elif avg_odds < 8.0:
        print(f"   ✅ Balanced range (4-8)")
    else:
        print(f"   🎲 Longshot focus (8+)")
    
    print(f"\n   ROI: {roi:+.1f}%")
    
    if roi > 5:
        print(f"   🎉 PROFITABLE after commission!")
    elif roi > 0:
        print(f"   ✅ Positive but marginal")
    else:
        print(f"   ❌ LOSING - need to improve model or filters")
    
    print(f"\n   Selectivity: {len(bets_df)/len(test_df)*100:.2f}% of field")
    if len(bets_df)/len(test_df) < 0.05:
        print(f"       ✅ Very selective (< 5%)")
    elif len(bets_df)/len(test_df) < 0.10:
        print(f"       ✅ Selective (5-10%)")
    else:
        print(f"       ⚠️  Too many bets (> 10%) - tighten filters")


if __name__ == "__main__":
    main()

