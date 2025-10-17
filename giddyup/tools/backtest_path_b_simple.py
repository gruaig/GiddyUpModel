"""
Path B Backtest - Simplified Version

Uses market-rank based probability estimates (like Hybrid V3 SQL logic)
plus Path B's banded thresholds and blending.
"""

import polars as pl
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from giddyup.data.build import build_training_data
from giddyup.scoring.path_b_hybrid import load_config, score_hybrid


def main():
    print("\n" + "="*80)
    print("PATH B — SIMPLIFIED BACKTEST")
    print("="*80 + "\n")
    
    # Load config
    config = load_config()
    print("✅ Configuration loaded")
    print(f"   Target: {config['targets']['min_bets_per_year']}-{config['targets']['max_bets_per_year']} bets/year, {config['targets']['min_roi']*100}%+ ROI\n")
    
    # Build test data
    print("📊 Building test dataset (2024-2025)...")
    df_test = build_training_data(
        date_from=config['backtest']['test_from'],
        date_to=config['backtest']['test_to']
    )
    
    print(f"   ✅ {len(df_test):,} runners loaded\n")
    
    # Create simple model predictions based on market rank
    # (similar to Hybrid V3 SQL logic)
    print("🎯 Generating simple rank-based predictions...")
    
    # Add market rank
    df_test = df_test.with_columns([
        pl.col("decimal_odds").rank("ordinal").over("race_id").alias("market_rank")
    ])
    
    # Simple model: adjust vig-free prob by rank
    df_test = df_test.with_columns([
        (1.0 / pl.col("decimal_odds")).alias("q_market")
    ])
    
    df_test = df_test.with_columns([
        pl.col("q_market").sum().over("race_id").alias("overround")
    ])
    
    df_test = df_test.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
    ])
    
    # Simple model probability based on rank (like Hybrid V3)
    df_test = df_test.with_columns([
        pl.when(pl.col("market_rank") == 1).then(pl.col("q_vigfree") * 1.2)
        .when(pl.col("market_rank") == 2).then(pl.col("q_vigfree") * 1.15)
        .when(pl.col("market_rank") == 3).then(pl.col("q_vigfree") * 2.4)
        .when(pl.col("market_rank") == 4).then(pl.col("q_vigfree") * 2.3)
        .when(pl.col("market_rank") == 5).then(pl.col("q_vigfree") * 2.0)
        .when(pl.col("market_rank") == 6).then(pl.col("q_vigfree") * 1.8)
        .otherwise(pl.col("q_vigfree") * 1.1)
        .alias("p_model_simple")
    ])
    
    # Clip to valid probability range
    df_test = df_test.with_columns([
        pl.col("p_model_simple").clip(0.001, 0.999).alias("p_model_simple")
    ])
    
    p_model = df_test["p_model_simple"].to_numpy()
    
    print(f"   ✅ Simple predictions generated")
    print(f"   Mean probability: {p_model.mean():.3f}\n")
    
    # Apply Path B scoring
    print("🔧 Applying Path B hybrid scoring...")
    df_scored = score_hybrid(df_test, p_model, config)
    
    print(f"   ✅ After gates: {len(df_scored):,} bets\n")
    
    if len(df_scored) == 0:
        print("❌ No bets passed gates! Config too strict.\n")
        return
    
    # Calculate metrics
    print("="*80)
    print("RESULTS")
    print("="*80 + "\n")
    
    # Basic stats
    n_bets = len(df_scored)
    n_won = df_scored["won"].sum()
    win_rate = n_won / n_bets if n_bets > 0 else 0
    
    # Financial
    commission = config['market']['commission']
    df_scored = df_scored.with_columns([
        pl.when(pl.col("won") == 1)
        .then(pl.col("stake_units") * (pl.col("decimal_odds") - 1) * (1 - commission))
        .otherwise(-pl.col("stake_units"))
        .alias("pnl_units")
    ])
    
    total_stake = df_scored["stake_units"].sum()
    total_pnl = df_scored["pnl_units"].sum()
    roi = (total_pnl / total_stake * 100) if total_stake > 0 else 0
    
    # Annualize
    if "race_date" in df_scored.columns:
        date_min = df_scored["race_date"].min()
        date_max = df_scored["race_date"].max()
        days_span = (date_max - date_min).days if date_min and date_max else 365
    else:
        days_span = 655  # ~2024-2025 span
    
    years_span = max(days_span / 365.25, 0.5)  # At least 0.5 years
    annual_bets = n_bets / years_span
    
    print(f"Overall:")
    print(f"  Total bets: {n_bets:,}")
    print(f"  Wins: {n_won} ({win_rate*100:.1f}%)")
    print(f"  Annual rate: {annual_bets:.0f} bets/year")
    print(f"  Avg odds: {df_scored['decimal_odds'].mean():.2f}")
    print()
    print(f"Financial:")
    print(f"  Total stake: {total_stake:.2f} units")
    print(f"  Total P&L: {total_pnl:+.2f} units")
    status = "✅" if roi > 0 else "❌"
    print(f"  ROI: {roi:+.2f}% {status}")
    print()
    
    # Check targets
    print(f"Targets:")
    targets_met = []
    
    vol_ok = config['targets']['min_bets_per_year'] <= annual_bets <= config['targets']['max_bets_per_year']
    roi_ok = roi / 100 >= config['targets']['min_roi']
    
    print(f"  {'✅' if vol_ok else '❌'} Volume: {annual_bets:.0f} bets/year (target: {config['targets']['min_bets_per_year']}-{config['targets']['max_bets_per_year']})")
    print(f"  {'✅' if roi_ok else '❌'} ROI: {roi:+.2f}% (target: {config['targets']['min_roi']*100}%+)")
    print()
    
    # By band
    print("─"*80)
    print("By Odds Band:")
    print("─"*80 + "\n")
    
    for band in ["1.5-3.0", "3.0-5.0", "5.0-8.0", "8.0-12.0", "12.0-999"]:
        df_band = df_scored.filter(pl.col("odds_band") == band)
        if len(df_band) == 0:
            continue
        
        n = len(df_band)
        won = df_band["won"].sum()
        stake = df_band["stake_units"].sum()
        pnl = df_band["pnl_units"].sum()
        band_roi = (pnl / stake * 100) if stake > 0 else 0
        avg_odds = df_band["decimal_odds"].mean()
        avg_edge = df_band["edge_pp"].mean() * 100
        
        status = "✅" if band_roi > 0 else "❌"
        print(f"{band:>10} ({n:4} bets): Odds {avg_odds:5.2f} | Edge +{avg_edge:5.1f}pp | ROI {band_roi:+6.2f}% {status}")
    
    print()
    print("="*80)
    
    if vol_ok and roi_ok:
        print("✅ ALL TARGETS MET!")
    else:
        print("⚠️  Targets not met - tune config and re-run")
        print()
        if not vol_ok:
            if annual_bets < config['targets']['min_bets_per_year']:
                print("→ Volume too low: Loosen gates (decrease edge_min)")
            else:
                print("→ Volume too high: Tighten gates (increase edge_min)")
        
        if not roi_ok:
            print("→ ROI too low: Tighten gates or adjust lambda")
    
    print("="*80 + "\n")
    
    # Save summary
    with open("backtest_path_b_results.log", "w") as f:
        f.write(f"PATH B BACKTEST (Simplified)\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"Overall:\n")
        f.write(f"  Bets: {n_bets:,}\n")
        f.write(f"  Annual: {annual_bets:.0f}/year\n")
        f.write(f"  Win rate: {win_rate*100:.1f}%\n")
        f.write(f"  ROI: {roi:+.2f}%\n\n")
        
        f.write(f"By Band:\n")
        for band in ["1.5-3.0", "3.0-5.0", "5.0-8.0", "8.0-12.0", "12.0-999"]:
            df_band = df_scored.filter(pl.col("odds_band") == band)
            if len(df_band) == 0:
                continue
            
            n = len(df_band)
            stake = df_band["stake_units"].sum()
            pnl = df_band["pnl_units"].sum()
            band_roi = (pnl / stake * 100) if stake > 0 else 0
            
            f.write(f"  {band}: {n} bets, ROI {band_roi:+.2f}%\n")
    
    print("📄 Results saved to: backtest_path_b_results.log\n")


if __name__ == "__main__":
    main()

