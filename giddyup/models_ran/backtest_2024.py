"""
Real backtest using the trained model on 2024 hold-out data.

Loads the actual model, scores 2024 races, and shows what bets would be placed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import numpy as np
import pickle
import os


def main():
    """Run backtest on 2024 data."""
    
    print("🏇 GiddyUp Model Backtest - 2024 Hold-Out Period")
    print("=" * 80)
    
    # ===== 1. Load Data =====
    print("\n📊 Loading 2024 hold-out data...")
    df = pl.read_parquet("data/training_dataset.parquet")
    
    # Filter to 2024
    test_df = df.filter(
        (pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
        (pl.col("race_date") <= pl.lit("2024-12-31").str.strptime(pl.Date, "%Y-%m-%d"))
    )
    
    print(f"   Runners: {len(test_df):,}")
    print(f"   Races: {test_df['race_id'].n_unique():,}")
    print(f"   Winners: {test_df['won'].sum():,} ({test_df['won'].mean():.1%})")
    
    # ===== 2. Load Model =====
    print("\n📥 Loading trained model from MLflow...")
    
    # Load the actual model artifacts
    mlruns_path = Path("mlruns/0")
    if not mlruns_path.exists():
        print("   ⚠️  MLflow artifacts not found!")
        print("   Using fallback: Market-based predictions")
        use_actual_model = False
    else:
        # Find the latest run
        run_dirs = list(mlruns_path.iterdir())
        if run_dirs:
            latest_run = max(run_dirs, key=lambda p: p.stat().st_mtime)
            print(f"   Run ID: {latest_run.name}")
            
            # Try to load the ensemble
            model_path = latest_run / "artifacts" / "calibrated_model" / "model.pkl"
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                print(f"   ✅ Loaded CalibratedEnsemble")
                use_actual_model = True
            else:
                print(f"   ⚠️  Model file not found, using fallback")
                use_actual_model = False
        else:
            use_actual_model = False
    
    # ===== 3. Generate Predictions =====
    print("\n🔮 Generating predictions...")
    
    from giddyup.data.build import get_feature_list
    feature_cols = get_feature_list()
    
    if use_actual_model:
        # Use actual trained model
        X_test = test_df.select(feature_cols).to_numpy()
        predictions = model.predict(X_test)
        test_df = test_df.with_columns(pl.Series("model_prob", predictions))
    else:
        # Fallback: Use implied probability from odds (for demo)
        test_df = test_df.with_columns([
            (1 / pl.col("decimal_odds").clip(lower_bound=1.01))
                .alias("model_prob")
        ])
    
    # ===== 4. Calculate Betting Metrics =====
    print("\n💰 Calculating edge and stakes...")
    
    test_df = test_df.with_columns([
        # Market implied probability
        (1 / pl.col("decimal_odds").clip(lower_bound=1.01))
            .alias("market_prob"),
        
        # Edge
        (pl.col("model_prob") - (1 / pl.col("decimal_odds").clip(lower_bound=1.01)))
            .alias("edge"),
    ])
    
    # Kelly stake (fractional at 25%)
    test_df = test_df.with_columns([
        (((pl.col("model_prob") * pl.col("decimal_odds") - 1) / 
         (pl.col("decimal_odds") - 1).clip(lower_bound=0.01))
            .clip(lower_bound=0, upper_bound=1.0) * 0.25)
            .alias("kelly_fraction")
    ])
    
    test_df = test_df.with_columns([
        pl.col("kelly_fraction").clip(upper_bound=1.0).alias("stake_units")
    ])
    
    # ===== 5. Filter to Bets =====
    print("\n🎯 Applying betting filters...")
    print("   Criteria:")
    print("      - Edge > 5% (model_prob > market_prob + 0.05)")
    print("      - Kelly fraction > 1%")
    print("      - Stake capped at 1.0 units")
    
    bets_df = test_df.filter(
        (pl.col("edge") > 0.05) &
        (pl.col("kelly_fraction") > 0.01)
    )
    
    print(f"\n   ✅ Found {len(bets_df):,} bets ({len(bets_df)/len(test_df)*100:.2f}% of runners)")
    
    # ===== 6. Calculate P&L =====
    bets_df = bets_df.with_columns([
        pl.when(pl.col("won"))
            .then(pl.col("stake_units") * (pl.col("decimal_odds") - 1))
        .otherwise(-pl.col("stake_units"))
            .alias("pnl")
    ])
    
    # ===== 7. Results =====
    print(f"\n" + "=" * 80)
    print("📊 2024 BACKTEST RESULTS (Unit Size = 1.0)")
    print("=" * 80)
    
    total_stake = bets_df["stake_units"].sum()
    total_pnl = bets_df["pnl"].sum()
    total_wins = bets_df["won"].sum()
    roi = (total_pnl / total_stake * 100) if total_stake > 0 else 0
    
    print(f"\n💰 Financial Summary:")
    print(f"   Bets Placed: {len(bets_df):,}")
    print(f"   Winners: {total_wins} ({total_wins/len(bets_df)*100:.1%})")
    print(f"   Total Staked: {total_stake:.2f} units")
    print(f"   Total Return: {total_pnl:+.2f} units")
    print(f"   ROI: {roi:+.1f}%")
    print(f"   Profit per bet: {total_pnl/len(bets_df):+.3f} units")
    
    # ===== 8. Odds Distribution =====
    print(f"\n📈 Bets by Odds Range:")
    print(f"\n{'Range':<12} {'Bets':>8} {'Wins':>6} {'Win%':>7} {'Stake':>8} {'P&L':>10} {'ROI':>8}")
    print("-" * 80)
    
    odds_buckets = [
        ("1.0-3.0", 1.0, 3.0),
        ("3.0-5.0", 3.0, 5.0),
        ("5.0-8.0", 5.0, 8.0),
        ("8.0-12.0", 8.0, 12.0),
        ("12.0-20.0", 12.0, 20.0),
        ("20.0+", 20.0, 999.0),
    ]
    
    for label, min_o, max_o in odds_buckets:
        bucket = bets_df.filter(
            (pl.col("decimal_odds") >= min_o) &
            (pl.col("decimal_odds") < max_o)
        )
        
        if len(bucket) > 0:
            n = len(bucket)
            wins = bucket["won"].sum()
            stake = bucket["stake_units"].sum()
            pnl = bucket["pnl"].sum()
            win_pct = wins / n * 100
            roi_pct = pnl / stake * 100 if stake > 0 else 0
            
            print(f"{label:<12} {n:>8,} {wins:>6} {win_pct:>6.1f}% {stake:>8.2f} {pnl:>+10.2f} {roi_pct:>+7.1f}%")
    
    # ===== 9. Sample Winning & Losing Bets =====
    print(f"\n" + "=" * 80)
    print("✅ SAMPLE WINNING BETS (Top 10 by profit)")
    print("=" * 80)
    
    winners = bets_df.filter(pl.col("won") == True).sort("pnl", descending=True).head(10)
    
    print(f"\n{'Date':<12} {'Odds':>6} {'Model%':>7} {'Market%':>8} {'Edge':>6} {'Stake':>7} {'Profit':>8}")
    print("-" * 80)
    
    for row in winners.select([
        "race_date", "decimal_odds", "model_prob", "market_prob", "edge", "stake_units", "pnl"
    ]).iter_rows():
        date, odds, model_p, market_p, edge, stake, pnl = row
        print(f"{str(date):<12} {odds:>6.2f} {model_p:>6.1%} {market_p:>7.1%} {edge:>5.1%} {stake:>7.3f} {pnl:>+8.2f}")
    
    print(f"\n" + "=" * 80)
    print("❌ SAMPLE LOSING BETS (Top 10 by loss)")
    print("=" * 80)
    
    losers = bets_df.filter(pl.col("won") == False).sort("pnl").head(10)
    
    print(f"\n{'Date':<12} {'Odds':>6} {'Model%':>7} {'Market%':>8} {'Edge':>6} {'Stake':>7} {'Loss':>8}")
    print("-" * 80)
    
    for row in losers.select([
        "race_date", "decimal_odds", "model_prob", "market_prob", "edge", "stake_units", "pnl"
    ]).iter_rows():
        date, odds, model_p, market_p, edge, stake, pnl = row
        print(f"{str(date):<12} {odds:>6.2f} {model_p:>6.1%} {market_p:>7.1%} {edge:>5.1%} {stake:>7.3f} {pnl:>+8.2f}")
    
    # ===== 10. Verdict =====
    print(f"\n" + "=" * 80)
    print("🎯 VERDICT")
    print("=" * 80)
    
    avg_odds = bets_df['decimal_odds'].mean()
    
    print(f"\n   Average betting odds: {avg_odds:.2f}")
    
    if avg_odds < 4.0:
        print(f"\n   ⚠️  Model is betting SHORT-PRICED FAVORITES")
        print(f"       This means:")
        print(f"       - Following market closely (not independent)")
        print(f"       - Hard to find mispricing in efficient part of market")
        print(f"       - ROI likely low after commissions")
        print(f"\n   💡 Suggestions:")
        print(f"       - Increase edge threshold (try 10% instead of 5%)")
        print(f"       - Remove decimal_odds from features (more independent)")
        print(f"       - Focus on longshots where market is less efficient")
    
    elif avg_odds < 8.0:
        print(f"\n   ✅ Model is betting BALANCED RANGE")
        print(f"       Mix of favorites and value plays")
        print(f"       Good for consistent returns")
    
    else:
        print(f"\n   🎲 Model is betting LONGSHOTS")
        print(f"       High variance but potentially valuable")
        print(f"       Need large sample size (1000+ bets)")
    
    print(f"\n   ROI: {roi:+.1f}%")
    
    if roi > 10:
        print(f"   🎉 EXCELLENT - Strong edge found!")
    elif roi > 5:
        print(f"   ✅ GOOD - Profitable after commissions")
    elif roi > 0:
        print(f"   ⚠️  MARGINAL - May lose after 2-5% commission")
    else:
        print(f"   ❌ LOSING - No edge detected")


if __name__ == "__main__":
    main()

