"""
Stake size simulator - Test 1-5 point strategies on 2024-2025 backtest.

Simulates different base unit sizes and shows impact on:
- Total P&L
- ROI %
- Maximum drawdown
- Volatility (standard deviation)
- Sharpe ratio

Recommends optimal stake size based on risk/reward.
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


def simulate_stake_size(bets_df: pl.DataFrame, base_unit: float) -> dict:
    """
    Simulate betting with a specific base unit size.
    
    Args:
        bets_df: DataFrame with bets
        base_unit: Base unit size (e.g., 1.0, 2.0, etc.)
        
    Returns:
        Dictionary with performance metrics
    """
    # Scale stakes by base unit
    scaled_bets = bets_df.with_columns([
        (pl.col("kelly_fraction") * base_unit).alias("actual_stake")
    ])
    
    # Calculate P&L for each bet
    pnl_list = []
    for row in scaled_bets.select(["actual_stake", "decimal_odds", "won"]).iter_rows():
        stake, odds, won = row
        pnl = calculate_pnl(stake, odds, won, COMMISSION)
        pnl_list.append(pnl)
    
    scaled_bets = scaled_bets.with_columns([
        pl.Series("pnl", pnl_list)
    ])
    
    # Calculate metrics
    total_stake = scaled_bets["actual_stake"].sum()
    total_pnl = scaled_bets["pnl"].sum()
    roi = (total_pnl / total_stake * 100) if total_stake > 0 else 0
    
    # Volatility
    pnl_std = scaled_bets["pnl"].std()
    
    # Maximum drawdown
    cumulative_pnl = scaled_bets["pnl"].cum_sum()
    running_max = cumulative_pnl.cum_max()
    drawdown = running_max - cumulative_pnl
    max_drawdown = drawdown.max()
    
    # Sharpe ratio (annualized, assuming ~250 trading days)
    mean_daily_return = scaled_bets["pnl"].mean()
    std_daily_return = scaled_bets["pnl"].std()
    sharpe = (mean_daily_return / std_daily_return * np.sqrt(250)) if std_daily_return > 0 else 0
    
    return {
        "base_unit": base_unit,
        "total_bets": len(scaled_bets),
        "total_stake": total_stake,
        "total_pnl": total_pnl,
        "roi": roi,
        "volatility": pnl_std,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "avg_stake": total_stake / len(scaled_bets) if len(scaled_bets) > 0 else 0,
    }


def main():
    """Run stake size simulations."""
    
    print("🎲 Stake Size Simulator - 2024-2025 Backtest")
    print("=" * 90)
    
    # ===== 1. Load Data =====
    print("\n📊 Loading 2024-2025 data...")
    df = pl.read_parquet("data/training_dataset.parquet")
    
    test_df = df.filter(
        (pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
        (pl.col("race_date") <= pl.lit("2025-10-16").str.strptime(pl.Date, "%Y-%m-%d"))
    )
    
    print(f"   Runners: {len(test_df):,}")
    print(f"   Races: {test_df['race_id'].n_unique():,}")
    
    # ===== 2. Load Model =====
    print(f"\n📥 Loading trained model...")
    
    # Try MLflow registry first
    try:
        import mlflow
        model = mlflow.sklearn.load_model("models:/hrd_win_prob/latest")
        print(f"   ✅ Loaded from MLflow registry (latest version)")
    except:
        # Fallback to file system
        model_files = list(Path("mlruns").glob("**/model.pkl"))
        if model_files:
            latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
            with open(latest_model, 'rb') as f:
                model = pickle.load(f)
            print(f"   ✅ Loaded from {latest_model}")
        else:
            print(f"   ❌ No model found!")
            return
    
    # ===== 3. Predict =====
    print(f"\n🔮 Generating predictions...")
    
    from giddyup.data.feature_lists import ABILITY_FEATURES
    
    X = test_df.select(ABILITY_FEATURES).to_numpy()
    predictions = model.predict(X)
    
    test_df = test_df.with_columns([
        pl.Series("p_model", predictions)
    ])
    
    print(f"   Predictions: {predictions.min():.1%} to {predictions.max():.1%}")
    
    # ===== 4. Calculate Edge =====
    print(f"\n📈 Calculating edge vs market...")
    
    # Filter to rows with valid odds
    test_df = test_df.filter(
        pl.col("decimal_odds").is_not_null() &
        (pl.col("decimal_odds") >= 1.01)
    )
    
    print(f"   Runners with valid odds: {len(test_df):,}")
    
    test_df = test_df.with_columns([
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
    
    # ===== 5. Calculate Kelly Fractions =====
    print(f"\n💰 Calculating Kelly fractions...")
    
    kelly_list = []
    for row in test_df.select(["p_model", "decimal_odds"]).iter_rows():
        p, odds = row
        b = (odds - 1.0) * (1.0 - COMMISSION)
        if b > 0:
            f = (p * (b + 1.0) - 1.0) / b
            f = max(0.0, min(1.0, f)) * KELLY_FRAC
        else:
            f = 0.0
        kelly_list.append(f)
    
    test_df = test_df.with_columns([
        pl.Series("kelly_fraction", kelly_list)
    ])
    
    # ===== 6. Filter to Bets =====
    print(f"\n🎯 Filtering to value bets...")
    print(f"   Edge >= {EDGE_MIN:.1%}")
    print(f"   Odds >= {ODDS_MIN:.2f}")
    print(f"   Kelly > 0")
    
    bets_df = test_df.filter(
        (pl.col("edge") >= EDGE_MIN) &
        (pl.col("decimal_odds") >= ODDS_MIN) &
        (pl.col("kelly_fraction") > 0)
    )
    
    print(f"\n   ✅ Found {len(bets_df):,} value bets ({len(bets_df)/len(test_df)*100:.2f}% of field)")
    
    if len(bets_df) == 0:
        print("\n   ❌ No bets found! Model agrees too closely with market.")
        print("   Try lower edge threshold or check model independence")
        return
    
    print(f"\n   Average odds: {bets_df['decimal_odds'].mean():.2f}")
    print(f"   Average edge: {bets_df['edge'].mean():.1%}")
    
    # ===== 7. Simulate Different Stake Sizes =====
    print(f"\n" + "=" * 90)
    print("💵 STAKE SIZE SIMULATIONS (1-5 Points)")
    print("=" * 90)
    
    print(f"\n📊 Testing different base unit sizes...")
    print(f"   Commission: {COMMISSION*100:.0f}% on winning bets")
    print(f"   Kelly multiplier: {KELLY_FRAC*100:.0f}% (fractional Kelly)")
    
    results = []
    
    for base_unit in [1.0, 2.0, 3.0, 4.0, 5.0]:
        result = simulate_stake_size(bets_df, base_unit)
        results.append(result)
    
    # ===== 8. Display Results =====
    print(f"\n" + "=" * 90)
    print("📊 RESULTS BY STAKE SIZE")
    print("=" * 90)
    
    print(f"\n{'Unit':>6} {'Total Bets':>12} {'Total Stake':>14} {'P&L':>12} {'ROI':>8} {'Max DD':>10} {'Sharpe':>8} {'Vol/Bet':>10}")
    print("-" * 90)
    
    for r in results:
        print(f"{r['base_unit']:>6.1f} {r['total_bets']:>12,} {r['total_stake']:>14.2f} "
              f"{r['total_pnl']:>+12.2f} {r['roi']:>+7.1f}% {r['max_drawdown']:>10.2f} "
              f"{r['sharpe']:>8.2f} {r['volatility']:>10.2f}")
    
    # ===== 9. Analysis =====
    print(f"\n" + "=" * 90)
    print("📈 ANALYSIS & RECOMMENDATION")
    print("=" * 90)
    
    # Find best by Sharpe (risk-adjusted returns)
    best_sharpe = max(results, key=lambda r: r['sharpe'])
    best_roi = max(results, key=lambda r: r['roi'])
    lowest_dd = min(results, key=lambda r: r['max_drawdown'])
    
    print(f"\n   Best Sharpe Ratio: {best_sharpe['base_unit']:.1f} points (Sharpe: {best_sharpe['sharpe']:.2f})")
    print(f"   Best ROI: {best_roi['base_unit']:.1f} points (ROI: {best_roi['roi']:+.1f}%)")
    print(f"   Lowest Drawdown: {lowest_dd['base_unit']:.1f} points (DD: {lowest_dd['max_drawdown']:.2f})")
    
    # Risk assessment
    print(f"\n💡 Risk/Reward Trade-offs:")
    
    for r in results:
        unit = r['base_unit']
        roi = r['roi']
        dd = r['max_drawdown']
        sharpe = r['sharpe']
        
        # Risk level
        if dd < 50:
            risk = "LOW"
        elif dd < 100:
            risk = "MEDIUM"
        elif dd < 200:
            risk = "HIGH"
        else:
            risk = "VERY HIGH"
        
        # Reward level
        if abs(r['total_pnl']) < 20:
            reward = "LOW"
        elif abs(r['total_pnl']) < 50:
            reward = "MEDIUM"
        elif abs(r['total_pnl']) < 100:
            reward = "HIGH"
        else:
            reward = "VERY HIGH"
        
        print(f"\n   {unit:.1f} points:")
        print(f"      Risk: {risk} (Max DD: {dd:.2f})")
        print(f"      Reward: {reward} (Total P&L: {r['total_pnl']:+.2f})")
        print(f"      Risk-Adjusted: Sharpe {sharpe:.2f}")
        
        if roi > 0:
            print(f"      ✅ PROFITABLE (ROI: {roi:+.1f}%)")
        else:
            print(f"      ❌ LOSING (ROI: {roi:+.1f}%)")
    
    # ===== 10. Recommendation =====
    print(f"\n" + "=" * 90)
    print("🎯 RECOMMENDATION")
    print("=" * 90)
    
    # Recommendation logic
    if all(r['roi'] < 0 for r in results):
        print(f"\n   ❌ ALL STAKE SIZES ARE LOSING")
        print(f"\n   This means model has NO EDGE vs market.")
        print(f"   Possible causes:")
        print(f"      - Model still too similar to market")
        print(f"      - Edge threshold too low (try 0.05 or 0.10)")
        print(f"      - Need more feature engineering")
        recommended_unit = 0
    else:
        # Find profitable stakes
        profitable = [r for r in results if r['roi'] > 0]
        
        if profitable:
            # Recommend based on Sharpe ratio (risk-adjusted)
            best = max(profitable, key=lambda r: r['sharpe'])
            recommended_unit = best['base_unit']
            
            print(f"\n   ✅ RECOMMENDED: {recommended_unit:.1f} POINTS")
            print(f"\n   Why:")
            print(f"      - Best risk-adjusted returns (Sharpe: {best['sharpe']:.2f})")
            print(f"      - ROI: {best['roi']:+.1f}%")
            print(f"      - Max Drawdown: {best['max_drawdown']:.2f} ({best['max_drawdown']/best['base_unit']:.1f}x unit)")
            print(f"      - Total P&L: {best['total_pnl']:+.2f}")
            
            if best['max_drawdown'] / best['base_unit'] > 50:
                print(f"\n   ⚠️  WARNING: High drawdown ({best['max_drawdown']:.2f} / {best['base_unit']:.1f} = {best['max_drawdown']/best['base_unit']:.0f}x)")
                print(f"      Bankroll needed: {best['max_drawdown'] * 3:.0f} points (3x max DD)")
            else:
                print(f"\n   ✅ Reasonable drawdown")
                print(f"      Bankroll needed: {best['max_drawdown'] * 2:.0f} points (2x max DD)")
    
    # ===== 11. Conservative vs Aggressive =====
    print(f"\n📊 Strategy Selection:")
    
    conservative = results[0]  # 1 point
    aggressive = results[-1]   # 5 points
    
    print(f"\n   CONSERVATIVE (1 point):")
    print(f"      P&L: {conservative['total_pnl']:+.2f}")
    print(f"      ROI: {conservative['roi']:+.1f}%")
    print(f"      Max DD: {conservative['max_drawdown']:.2f}")
    print(f"      Sharpe: {conservative['sharpe']:.2f}")
    print(f"      → Good for: Small bankrolls, low risk tolerance")
    
    print(f"\n   AGGRESSIVE (5 points):")
    print(f"      P&L: {aggressive['total_pnl']:+.2f}")
    print(f"      ROI: {aggressive['roi']:+.1f}%")
    print(f"      Max DD: {aggressive['max_drawdown']:.2f}")
    print(f"      Sharpe: {aggressive['sharpe']:.2f}")
    print(f"      → Good for: Large bankrolls, high risk tolerance")
    
    if recommended_unit > 0:
        print(f"\n   RECOMMENDED ({recommended_unit:.1f} points):")
        rec = [r for r in results if r['base_unit'] == recommended_unit][0]
        print(f"      P&L: {rec['total_pnl']:+.2f}")
        print(f"      ROI: {rec['roi']:+.1f}%")
        print(f"      Max DD: {rec['max_drawdown']:.2f}")
        print(f"      Sharpe: {rec['sharpe']:.2f}")
        print(f"      → BEST risk-adjusted returns")
    
    # ===== 12. Bankroll Requirements =====
    print(f"\n💰 Bankroll Requirements:")
    
    for r in results:
        bankroll_needed = r['max_drawdown'] * 3  # 3x max drawdown (conservative)
        print(f"\n   {r['base_unit']:.1f} points → Need {bankroll_needed:.0f} point bankroll")
        print(f"      (3x max drawdown of {r['max_drawdown']:.2f})")
        
        if r['roi'] > 0:
            # Time to double bankroll
            if r['roi'] > 0:
                months_to_double = np.log(2) / np.log(1 + r['roi']/100) * 12
                print(f"      At {r['roi']:+.1f}% ROI: Double bankroll in {months_to_double:.1f} months")
    
    # ===== 13. Final Verdict =====
    print(f"\n" + "=" * 90)
    print("🎯 FINAL VERDICT")
    print("=" * 90)
    
    if recommended_unit > 0:
        rec = [r for r in results if r['base_unit'] == recommended_unit][0]
        
        print(f"\n   ✅ Use {recommended_unit:.1f} POINTS per unit")
        print(f"\n   Expected annual performance:")
        print(f"      - ROI: {rec['roi']:+.1f}%")
        print(f"      - Sharpe: {rec['sharpe']:.2f}")
        print(f"      - Max Drawdown: {rec['max_drawdown']:.2f} points")
        print(f"\n   Required bankroll:")
        print(f"      - Conservative: {rec['max_drawdown'] * 3:.0f} points")
        print(f"      - Aggressive: {rec['max_drawdown'] * 2:.0f} points")
        
        print(f"\n   Example: With 1000 point bankroll:")
        scale = 1000 / (rec['max_drawdown'] * 3)
        print(f"      - Unit size: {recommended_unit * scale:.2f} points")
        print(f"      - Expected annual profit: {rec['total_pnl'] * scale:+.0f} points")
        print(f"      - Expected ROI: {rec['roi']:+.1f}%")
    else:
        print(f"\n   ❌ NO PROFITABLE STAKE SIZE FOUND")
        print(f"\n   Model is not finding value.")
        print(f"   Recommendations:")
        print(f"      1. Check if model is still using market features")
        print(f"      2. Increase edge threshold (0.05 or 0.10)")
        print(f"      3. Add more predictive features")
        print(f"      4. Retrain on different date range")


if __name__ == "__main__":
    main()

