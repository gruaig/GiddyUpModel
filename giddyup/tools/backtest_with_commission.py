"""
Realistic backtest with 5% commission on winning bets.

Loads trained model, scores 2024 races, applies betting strategy,
and calculates P&L with Betfair-style commission.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import numpy as np
import pickle


COMMISSION_RATE = 0.05  # 5% on winning bets (Betfair standard)


def calculate_pnl_with_commission(stake: float, odds: float, won: bool) -> float:
    """
    Calculate P&L including 5% commission on winning bets.
    
    Args:
        stake: Bet stake (units)
        odds: Decimal odds
        won: Whether bet won
        
    Returns:
        Net P&L after commission
        
    Example:
        >>> calculate_pnl_with_commission(1.0, 5.0, True)  # Win at 5.0
        3.80  # (1.0 * (5.0-1) * 0.95) = profit after 5% commission
        >>> calculate_pnl_with_commission(1.0, 5.0, False)  # Lose
        -1.00
    """
    if won:
        # Gross profit
        gross_profit = stake * (odds - 1)
        # Apply 5% commission
        net_profit = gross_profit * (1 - COMMISSION_RATE)
        return net_profit
    else:
        # Losing bet - lose full stake
        return -stake


def main():
    """Run backtest with commission."""
    
    print("🏇 2024 Backtest with 5% Commission (Betfair)")
    print("=" * 80)
    
    # ===== 1. Load Data =====
    print("\n📊 Loading 2024 data...")
    df = pl.read_parquet("data/training_dataset.parquet")
    
    test_df = df.filter(
        (pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
        (pl.col("race_date") <= pl.lit("2024-12-31").str.strptime(pl.Date, "%Y-%m-%d"))
    )
    
    print(f"   Runners: {len(test_df):,}")
    print(f"   Races: {test_df['race_id'].n_unique():,}")
    print(f"   Actual winners: {test_df['won'].sum():,} ({test_df['won'].mean():.1%})")
    
    # ===== 2. Load Model =====
    print("\n📥 Attempting to load trained model...")
    
    mlruns_path = Path("mlruns/0")
    model_loaded = False
    
    if mlruns_path.exists():
        run_dirs = [d for d in mlruns_path.iterdir() if d.is_dir() and d.name != "meta.yaml"]
        if run_dirs:
            latest_run = max(run_dirs, key=lambda p: p.stat().st_mtime)
            model_path = latest_run / "artifacts" / "calibrated_model" / "model.pkl"
            
            if model_path.exists():
                print(f"   ✅ Found model: {latest_run.name}")
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                model_loaded = True
            else:
                print(f"   ⚠️  Model file not found")
        else:
            print(f"   ⚠️  No run directories found")
    else:
        print(f"   ⚠️  MLflow directory not found")
    
    # ===== 3. Make Predictions =====
    if model_loaded:
        print("\n🔮 Generating predictions with trained model...")
        from giddyup.data.build import get_feature_list
        feature_cols = get_feature_list()
        
        X_test = test_df.select(feature_cols).to_numpy()
        predictions = model.predict(X_test)
        
        test_df = test_df.with_columns(pl.Series("model_prob", predictions))
    else:
        print("\n🔮 Using FALLBACK predictions (for demo)...")
        print("   (In production, use actual trained model)")
        
        # Simulate what model does: market prob + small form adjustments
        test_df = test_df.with_columns([
            (1 / pl.col("decimal_odds").clip(lower_bound=1.01))
                .alias("market_prob"),
        ])
        
        # Add realistic adjustments based on form
        test_df = test_df.with_columns([
            pl.when(
                (pl.col("racing_post_rating") > 100) &
                (pl.col("trainer_sr_total") > 0.15)
            )
                .then(pl.col("market_prob") * 1.12)  # 12% boost
            .when(
                (pl.col("wins_at_course") > 1) &
                (pl.col("runs_at_course") > 3)
            )
                .then(pl.col("market_prob") * 1.08)  # 8% boost
            .when(
                (pl.col("best_rpr_last_3") > pl.col("racing_post_rating") + 5)
            )
                .then(pl.col("market_prob") * 1.10)  # 10% boost for improving
            .when(
                (pl.col("days_since_run") < 10) &
                (pl.col("last_pos") == 1)
            )
                .then(pl.col("market_prob") * 1.06)  # 6% boost for recent winner
            .otherwise(pl.col("market_prob"))
                .clip(upper_bound=0.95)
                .alias("model_prob"),
        ])
    
    # ===== 4. Calculate Edge & Stakes =====
    print("\n💰 Calculating edge and Kelly stakes...")
    
    test_df = test_df.with_columns([
        # Market probability
        (1 / pl.col("decimal_odds").clip(lower_bound=1.01))
            .alias("market_prob"),
        
        # Edge
        (pl.col("model_prob") - (1 / pl.col("decimal_odds").clip(lower_bound=1.01)))
            .alias("edge"),
        
        # Fair odds (what odds should be based on model)
        (1 / pl.col("model_prob").clip(lower_bound=0.01))
            .alias("fair_odds"),
    ])
    
    # Kelly fraction (25% fractional Kelly for safety)
    test_df = test_df.with_columns([
        (((pl.col("model_prob") * pl.col("decimal_odds") - 1) / 
         (pl.col("decimal_odds") - 1).clip(lower_bound=0.01))
            .clip(lower_bound=0, upper_bound=1.0) * 0.25)
            .alias("kelly_fraction")
    ])
    
    test_df = test_df.with_columns([
        pl.col("kelly_fraction").clip(lower_bound=0, upper_bound=1.0).alias("stake_units")
    ])
    
    # ===== 5. Apply Betting Filters =====
    print("\n🎯 Betting criteria:")
    print(f"   - Edge > 2% (model finds value)")
    print(f"   - Kelly fraction > 0.5%")
    print(f"   - Commission: 5% on winning bets")
    
    bets_df = test_df.filter(
        (pl.col("edge") > 0.02) &  # 2% edge (realistic threshold)
        (pl.col("kelly_fraction") > 0.005)
    )
    
    print(f"\n   Bets found: {len(bets_df):,} ({len(bets_df)/len(test_df)*100:.2f}% of runners)")
    
    if len(bets_df) == 0:
        print("\n   ⚠️  NO BETS with 2% edge threshold")
        print("   Trying 1% edge...")
        
        bets_df = test_df.filter(
            (pl.col("edge") > 0.01) &
            (pl.col("kelly_fraction") > 0.002)
        )
        
        print(f"   With 1% edge: {len(bets_df):,} bets")
    
    if len(bets_df) == 0:
        print("\n   Still no bets! Showing top 50 by edge for demonstration...")
        bets_df = test_df.sort("edge", descending=True).head(50)
    
    # ===== 6. Calculate P&L with Commission =====
    print(f"\n💵 Calculating P&L with 5% commission...")
    
    # Calculate P&L row by row
    pnl_list = []
    for row in bets_df.select(["stake_units", "decimal_odds", "won"]).iter_rows():
        stake, odds, won = row
        pnl = calculate_pnl_with_commission(stake, odds, won)
        pnl_list.append(pnl)
    
    bets_df = bets_df.with_columns(pl.Series("pnl_after_comm", pnl_list))
    
    # Also calculate P&L without commission for comparison
    bets_df = bets_df.with_columns([
        pl.when(pl.col("won"))
            .then(pl.col("stake_units") * (pl.col("decimal_odds") - 1))
        .otherwise(-pl.col("stake_units"))
            .alias("pnl_before_comm")
    ])
    
    # ===== 7. Overall Results =====
    print(f"\n" + "=" * 80)
    print("📊 2024 BACKTEST RESULTS")
    print("=" * 80)
    
    total_bets = len(bets_df)
    total_wins = bets_df["won"].sum()
    total_stake = bets_df["stake_units"].sum()
    total_pnl_before = bets_df["pnl_before_comm"].sum()
    total_pnl_after = bets_df["pnl_after_comm"].sum()
    avg_odds = bets_df["decimal_odds"].mean()
    avg_stake = total_stake / total_bets if total_bets > 0 else 0
    
    roi_before = (total_pnl_before / total_stake * 100) if total_stake > 0 else 0
    roi_after = (total_pnl_after / total_stake * 100) if total_stake > 0 else 0
    commission_cost = total_pnl_before - total_pnl_after
    
    print(f"\n💰 Financial Summary (Unit Size = 1.0):")
    print(f"   Bets Placed: {total_bets:,}")
    print(f"   Winners: {total_wins} ({total_wins/total_bets*100:.1f}%)")
    print(f"   Total Staked: {total_stake:.2f} units")
    print(f"\n   Before Commission:")
    print(f"      P&L: {total_pnl_before:+.2f} units")
    print(f"      ROI: {roi_before:+.1f}%")
    print(f"\n   After 5% Commission:")
    print(f"      Commission Paid: {commission_cost:.2f} units")
    print(f"      Net P&L: {total_pnl_after:+.2f} units")
    print(f"      Net ROI: {roi_after:+.1f}%")
    print(f"\n   Betting Stats:")
    print(f"      Average Odds: {avg_odds:.2f}")
    print(f"      Average Stake: {avg_stake:.3f} units")
    print(f"      Average Edge: {bets_df['edge'].mean():.2%}")
    
    # ===== 8. Odds Distribution =====
    print(f"\n📈 Performance by Odds Range:")
    print(f"\n{'Range':<15} {'Bets':>8} {'Wins':>6} {'Win%':>7} {'Stake':>8} {'P&L (net)':>12} {'ROI':>8}")
    print("-" * 85)
    
    for label, min_o, max_o in [
        ("Favs (1-3)", 1.0, 3.0),
        ("Short (3-5)", 3.0, 5.0),
        ("Mid (5-8)", 5.0, 8.0),
        ("Long (8-12)", 8.0, 12.0),
        ("Outsider (12-20)", 12.0, 20.0),
        ("Longshot (20+)", 20.0, 999.0),
    ]:
        bucket = bets_df.filter(
            (pl.col("decimal_odds") >= min_o) &
            (pl.col("decimal_odds") < max_o)
        )
        
        if len(bucket) > 0:
            n = len(bucket)
            wins = bucket["won"].sum()
            stake = bucket["stake_units"].sum()
            pnl_net = bucket["pnl_after_comm"].sum()
            win_pct = wins / n * 100
            roi = pnl_net / stake * 100 if stake > 0 else 0
            
            print(f"{label:<15} {n:>8,} {wins:>6} {win_pct:>6.1f}% {stake:>8.2f} {pnl_net:>+12.2f} {roi:>+7.1f}%")
    
    # ===== 9. Sample Bets =====
    print(f"\n" + "=" * 80)
    print("📋 SAMPLE BETS - Top 20 by Stake (Unit Size = 1.0)")
    print("=" * 80)
    
    samples = bets_df.sort("stake_units", descending=True).head(20)
    
    print(f"\n{'Date':<12} {'Odds':>6} {'Model%':>7} {'Market%':>8} {'Edge':>6} {'Stake':>7} {'Won':>4} {'P&L(net)':>10}")
    print("-" * 90)
    
    for row in samples.select([
        "race_date", "decimal_odds", "model_prob", "market_prob",
        "edge", "stake_units", "won", "pnl_after_comm"
    ]).iter_rows():
        date, odds, model_p, market_p, edge, stake, won, pnl = row
        won_str = "✅" if won else "❌"
        print(f"{str(date):<12} {odds:>6.2f} {model_p:>6.1%} {market_p:>7.1%} "
              f"{edge:>5.1%} {stake:>7.3f} {won_str:>4} {pnl:>+10.2f}")
    
    # ===== 10. Value Analysis =====
    print(f"\n" + "=" * 80)
    print("🎯 VALUE ANALYSIS")
    print("=" * 80)
    
    print(f"\n📊 Is model finding value or betting favorites?")
    
    # Categorize bets
    favorites = bets_df.filter(pl.col("decimal_odds") < 4.0)
    mid_range = bets_df.filter(
        (pl.col("decimal_odds") >= 4.0) &
        (pl.col("decimal_odds") < 10.0)
    )
    longshots = bets_df.filter(pl.col("decimal_odds") >= 10.0)
    
    print(f"\n   Favorites (odds < 4.0):")
    if len(favorites) > 0:
        fav_stake = favorites["stake_units"].sum()
        fav_pnl = favorites["pnl_after_comm"].sum()
        fav_roi = fav_pnl / fav_stake * 100
        fav_wins = favorites["won"].sum()
        print(f"      Bets: {len(favorites):,} ({len(favorites)/total_bets*100:.1f}%)")
        print(f"      Wins: {fav_wins} ({fav_wins/len(favorites)*100:.1f}%)")
        print(f"      ROI: {fav_roi:+.1f}%")
        print(f"      Average odds: {favorites['decimal_odds'].mean():.2f}")
    else:
        print(f"      No bets in this range")
    
    print(f"\n   Mid-range (odds 4-10):")
    if len(mid_range) > 0:
        mid_stake = mid_range["stake_units"].sum()
        mid_pnl = mid_range["pnl_after_comm"].sum()
        mid_roi = mid_pnl / mid_stake * 100
        mid_wins = mid_range["won"].sum()
        print(f"      Bets: {len(mid_range):,} ({len(mid_range)/total_bets*100:.1f}%)")
        print(f"      Wins: {mid_wins} ({mid_wins/len(mid_range)*100:.1f}%)")
        print(f"      ROI: {mid_roi:+.1f}%")
        print(f"      Average odds: {mid_range['decimal_odds'].mean():.2f}")
    else:
        print(f"      No bets in this range")
    
    print(f"\n   Longshots (odds 10+):")
    if len(longshots) > 0:
        long_stake = longshots["stake_units"].sum()
        long_pnl = longshots["pnl_after_comm"].sum()
        long_roi = long_pnl / long_stake * 100
        long_wins = longshots["won"].sum()
        print(f"      Bets: {len(longshots):,} ({len(longshots)/total_bets*100:.1f}%)")
        print(f"      Wins: {long_wins} ({long_wins/len(longshots)*100:.1f}%)")
        print(f"      ROI: {long_roi:+.1f}%")
        print(f"      Average odds: {longshots['decimal_odds'].mean():.2f}")
    else:
        print(f"      No bets in this range")
    
    # ===== 11. Verdict =====
    print(f"\n" + "=" * 80)
    print("🎯 VERDICT")
    print("=" * 80)
    
    print(f"\n   Average betting odds: {avg_odds:.2f}")
    
    if avg_odds < 4.0:
        print(f"\n   ⚠️  MODEL IS BETTING SHORT-PRICED FAVORITES")
        print(f"\n   What this means:")
        print(f"      - Model closely follows market consensus")
        print(f"      - Mainly betting on well-fancied horses")
        print(f"      - Low variance but hard to beat commission")
        print(f"      - Market features (decimal_odds, market_rank) dominate")
        
        print(f"\n   ROI after commission: {roi_after:+.1f}%")
        
        if roi_after > 3:
            print(f"      ✅ Still profitable! Model finding some mispricing")
        elif roi_after > 0:
            print(f"      ⚠️  Barely profitable - commission eats most edge")
        else:
            print(f"      ❌ LOSING - Commission too high for small edges")
        
        print(f"\n   💡 To improve:")
        print(f"      1. Remove decimal_odds from features")
        print(f"         → Model becomes more independent")
        print(f"         → May find bigger mispricing")
        print(f"         → But lower AUC (0.65 vs 0.96)")
        print(f"\n      2. Increase edge threshold to 5-10%")
        print(f"         → Only bet when strong disagreement with market")
        print(f"         → Fewer bets but higher edge per bet")
        print(f"\n      3. Focus on specific angles:")
        print(f"         → Course specialists (high wins_at_course)")
        print(f"         → Draw bias corrections")
        print(f"         → Recent form improvers")
    
    elif avg_odds < 10.0:
        print(f"\n   ✅ BALANCED BETTING")
        print(f"      Mix of favorites and mid-range")
        print(f"      ROI: {roi_after:+.1f}%")
    
    else:
        print(f"\n   🎲 LONGSHOT FOCUS")
        print(f"      High variance strategy")
        print(f"      Need large sample (1000+ bets)")
        print(f"      ROI: {roi_after:+.1f}%")
    
    # ===== 12. Commission Impact =====
    print(f"\n📉 Commission Impact:")
    print(f"   ROI before commission: {roi_before:+.1f}%")
    print(f"   ROI after 5% commission: {roi_after:+.1f}%")
    print(f"   Commission cost: {roi_before - roi_after:.1f} percentage points")
    print(f"   Total commission paid: {commission_cost:.2f} units ({commission_cost/total_stake*100:.1f}% of stakes)")
    
    # ===== 13. Recommendations =====
    print(f"\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    if avg_odds < 4.0:
        print(f"""
   Your model with market features (AUC = 0.96) is betting favorites.
   
   This is EXPECTED because:
      - Market odds are highly predictive (AUC ~0.96)
      - Model includes decimal_odds as a feature
      - Model learns: "low odds = high win probability"
      - Form features add small refinements
      
   Result: Model AGREES with market most of the time
   
   To find MORE value, you have 3 options:
   
   Option A: REMOVE market features
      Remove: decimal_odds, market_rank, is_fav
      Keep: Speed ratings, form, connections
      Result: Lower AUC (0.65) but more independent
      
   Option B: USE market features differently
      Don't train on decimal_odds
      Instead: Compare model prob vs market prob at BETTING time
      Only bet when model >> market (5-10% edge)
      
   Option C: FOCUS on market inefficiencies
      Look for specific patterns market misprices:
         - Course specialists (high wins_at_course)
         - Improving form (best_rpr_last_3 rising)
         - Draw bias at specific courses
         - Trainer hot streaks (high recent SR)
      
   Current best approach: Option B
      Train WITHOUT decimal_odds
      Compare predictions vs market odds later
      Find genuine mispricing
        """)


if __name__ == "__main__":
    main()

