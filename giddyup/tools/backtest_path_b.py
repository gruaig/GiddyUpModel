"""
Path B — Hybrid Market-Aware Backtest

Test ability-only model + market-aware scoring on 2024-2025 holdout.
Target: 200-500 bets/year with 5-15% ROI.
"""

import polars as pl
import numpy as np
from pathlib import Path
import mlflow
from sklearn.metrics import log_loss, roc_auc_score
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from giddyup.data.build import build_training_data
from giddyup.scoring.path_b_hybrid import (
    load_config, score_hybrid, format_selection_summary
)


def main():
    print("\n" + "="*80)
    print("PATH B — HYBRID MARKET-AWARE BACKTEST")
    print("="*80 + "\n")
    
    # Load config
    config = load_config()
    print("✅ Configuration loaded")
    print(f"   Snapshot: T-{config['snapshot']['minutes_before']}")
    print(f"   Commission: {config['market']['commission']*100}%")
    print(f"   Target volume: {config['targets']['min_bets_per_year']}-{config['targets']['max_bets_per_year']} bets/year")
    print(f"   Target ROI: {config['targets']['min_roi']*100}%+")
    
    # Load model from MLflow
    print(f"\n📦 Loading model: {config['model']['name']}")
    try:
        model_uri = f"models:/{config['model']['name']}/{config['model']['stage']}"
        model = mlflow.sklearn.load_model(model_uri)
        print("   ✅ Model loaded from MLflow")
    except Exception as e:
        print(f"   ⚠️  Could not load from MLflow: {e}")
        print("   Using fallback: Retraining model inline...")
        
        # Fallback: train model inline
        from giddyup.models.trainer import train_model, TrainConfig
        from giddyup.data.feature_lists import ABILITY_FEATURES
        
        train_cfg = TrainConfig(
            train_date_from="2006-01-01",
            train_date_to="2023-12-31",
            features=ABILITY_FEATURES,
            n_folds=5
        )
        
        df_train = build_training_data(
            date_from=train_cfg.train_date_from,
            date_to=train_cfg.train_date_to,
            include_market=False
        )
        
        model, _ = train_model(df_train, train_cfg, log_mlflow=False)
        print("   ✅ Model trained inline")
    
    # Build test dataset (2024-2025 with market features)
    print("\n📊 Building test dataset (2024-2025)...")
    print("   Including market features for scoring...")
    
    df_test = build_training_data(
        date_from=config['backtest']['test_from'],
        date_to=config['backtest']['test_to'],
        include_market=True  # Need market for Path B scoring
    )
    
    print(f"   ✅ {len(df_test):,} runners loaded")
    print(f"   Date range: {df_test['off_time'].min()} to {df_test['off_time'].max()}")
    
    # Get predictions
    print("\n🎯 Generating predictions...")
    from giddyup.data.feature_lists import ABILITY_FEATURES
    
    X_test = df_test.select(ABILITY_FEATURES).to_numpy()
    
    # Handle model type (ensemble or single)
    if hasattr(model, 'predict_proba'):
        p_model = model.predict_proba(X_test)[:, 1]
    else:
        # Ensemble of models + calibrator
        p_model = model.predict(X_test)
    
    print(f"   ✅ Predictions generated")
    print(f"   Mean probability: {p_model.mean():.3f}")
    print(f"   AUC-ROC: {roc_auc_score(df_test['won'].to_numpy(), p_model):.3f}")
    
    # Apply Path B hybrid scoring
    print("\n🔧 Applying Path B hybrid scoring...")
    print("   - Odds-band specific lambda blending")
    print("   - Banded edge thresholds")
    print("   - Top-1 per race selection")
    
    df_scored = score_hybrid(df_test, p_model, config)
    
    print(f"\n   ✅ Selections after gates: {len(df_scored):,} bets")
    
    if len(df_scored) == 0:
        print("\n❌ No bets passed gates! Thresholds too strict.")
        return
    
    # Calculate performance metrics
    print("\n📈 BACKTEST RESULTS")
    print("="*80)
    
    # Overall metrics
    n_bets = len(df_scored)
    n_won = df_scored['won'].sum()
    win_rate = n_won / n_bets if n_bets > 0 else 0
    
    # Financial metrics
    commission = config['market']['commission']
    
    # Calculate P&L per bet
    df_scored = df_scored.with_columns([
        pl.when(pl.col("won") == 1)
        .then(
            pl.col("stake_units") * (pl.col("decimal_odds") - 1) * (1 - commission)
        )
        .otherwise(-pl.col("stake_units"))
        .alias("pnl_units")
    ])
    
    total_stake = df_scored['stake_units'].sum()
    total_pnl = df_scored['pnl_units'].sum()
    roi = (total_pnl / total_stake * 100) if total_stake > 0 else 0
    
    # Annualize for full year
    date_min = df_scored['off_time'].min()
    date_max = df_scored['off_time'].max()
    days_span = (date_max - date_min).days if date_min and date_max else 365
    years_span = days_span / 365.25
    annual_bets = n_bets / years_span if years_span > 0 else n_bets
    
    print(f"\nOverall Performance:")
    print(f"  Total bets: {n_bets:,}")
    print(f"  Wins: {n_won} ({win_rate*100:.1f}%)")
    print(f"  Annual bet rate: {annual_bets:.0f} bets/year")
    print(f"\nFinancial:")
    print(f"  Total stake: {total_stake:.2f} units")
    print(f"  Total P&L: {total_pnl:+.2f} units")
    print(f"  ROI: {roi:+.2f}% ✅" if roi > 0 else f"  ROI: {roi:+.2f}% ❌")
    print(f"  Avg odds: {df_scored['decimal_odds'].mean():.2f}")
    
    # Check targets
    print(f"\nTargets:")
    target_met = []
    
    if config['targets']['min_bets_per_year'] <= annual_bets <= config['targets']['max_bets_per_year']:
        print(f"  ✅ Volume: {annual_bets:.0f} bets/year (target: {config['targets']['min_bets_per_year']}-{config['targets']['max_bets_per_year']})")
        target_met.append(True)
    else:
        print(f"  ❌ Volume: {annual_bets:.0f} bets/year (target: {config['targets']['min_bets_per_year']}-{config['targets']['max_bets_per_year']})")
        target_met.append(False)
    
    if roi / 100 >= config['targets']['min_roi']:
        print(f"  ✅ ROI: {roi:+.2f}% (target: {config['targets']['min_roi']*100}%+)")
        target_met.append(True)
    else:
        print(f"  ❌ ROI: {roi:+.2f}% (target: {config['targets']['min_roi']*100}%+)")
        target_met.append(False)
    
    # Performance by odds band
    print(f"\n{'─'*80}")
    print(f"Performance by Odds Band:")
    print(f"{'─'*80}")
    
    for band in ["1.5-3.0", "3.0-5.0", "5.0-8.0", "8.0-12.0", "12.0-999"]:
        df_band = df_scored.filter(pl.col("odds_band") == band)
        if len(df_band) == 0:
            continue
        
        n_band = len(df_band)
        won_band = df_band['won'].sum()
        stake_band = df_band['stake_units'].sum()
        pnl_band = df_band['pnl_units'].sum()
        roi_band = (pnl_band / stake_band * 100) if stake_band > 0 else 0
        avg_odds_band = df_band['decimal_odds'].mean()
        avg_edge_band = df_band['edge_pp'].mean() * 100
        
        status = "✅" if roi_band > 0 else "❌"
        print(f"\n{band:>10} ({n_band:3} bets):")
        print(f"  Avg odds: {avg_odds_band:5.2f} | Win rate: {won_band/n_band*100:5.1f}%")
        print(f"  Avg edge: +{avg_edge_band:5.1f}pp")
        print(f"  ROI: {roi_band:+6.2f}% {status}")
    
    # Top selections
    print(f"\n{'─'*80}")
    print(f"Top 10 Selections by Edge:")
    print(f"{'─'*80}")
    
    df_top = df_scored.sort("edge_pp", descending=True).head(10)
    for i, row in enumerate(df_top.iter_rows(named=True), 1):
        horse = row.get('horse_name', 'Unknown')
        odds = row['decimal_odds']
        edge = row['edge_pp'] * 100
        ev = row['ev'] * 100
        won_str = "WON ✅" if row['won'] == 1 else "LOST ❌"
        print(f"{i:2}. {horse:20} @ {odds:5.1f} | Edge: +{edge:5.1f}pp | EV: +{ev:5.1f}% | {won_str}")
    
    # Summary
    print(f"\n{'='*80}")
    if all(target_met):
        print("✅ ALL TARGETS MET! Path B is viable.")
    else:
        print("⚠️  Some targets not met. Tune config and re-run.")
    
    print(f"\nNext steps:")
    if roi < config['targets']['min_roi'] * 100:
        print("  - Increase edge thresholds (tighter gates)")
        print("  - Adjust lambda by band (more/less market trust)")
    
    if annual_bets < config['targets']['min_bets_per_year']:
        print("  - Decrease edge thresholds (looser gates)")
        print("  - Lower odds_min (include more favorites)")
    
    if annual_bets > config['targets']['max_bets_per_year']:
        print("  - Increase edge thresholds (tighter gates)")
        print("  - Raise odds_min (exclude more favorites)")
    
    print(f"\n{'='*80}\n")
    
    # Save results
    output_file = "backtest_path_b_results.log"
    with open(output_file, "w") as f:
        f.write(f"PATH B BACKTEST RESULTS\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"Overall:\n")
        f.write(f"  Bets: {n_bets:,}\n")
        f.write(f"  Annual rate: {annual_bets:.0f}/year\n")
        f.write(f"  Win rate: {win_rate*100:.1f}%\n")
        f.write(f"  ROI: {roi:+.2f}%\n")
        f.write(f"  Total stake: {total_stake:.2f}u\n")
        f.write(f"  Total P&L: {total_pnl:+.2f}u\n\n")
        
        f.write(f"By Band:\n")
        for band in ["1.5-3.0", "3.0-5.0", "5.0-8.0", "8.0-12.0", "12.0-999"]:
            df_band = df_scored.filter(pl.col("odds_band") == band)
            if len(df_band) == 0:
                continue
            
            n_band = len(df_band)
            stake_band = df_band['stake_units'].sum()
            pnl_band = df_band['pnl_units'].sum()
            roi_band = (pnl_band / stake_band * 100) if stake_band > 0 else 0
            
            f.write(f"  {band}: {n_band} bets, ROI {roi_band:+.2f}%\n")
    
    print(f"📄 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    main()

