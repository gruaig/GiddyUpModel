"""
Hybrid Model: Daily Production Scoring Script

Run this daily to get tomorrow's bet recommendations.

Usage:
    python score_tomorrow_hybrid.py --date 2025-10-18
    python score_tomorrow_hybrid.py  # Defaults to tomorrow
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import os
import argparse
from datetime import datetime, timedelta
import polars as pl
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.isotonic import IsotonicRegression
from dotenv import load_dotenv

from giddyup.data.build import build_training_data
from giddyup.data.market import add_market_features_from_data
from giddyup.data.feature_lists import ABILITY_FEATURES
from giddyup.models.hybrid import (
    get_adaptive_lambda,
    blend_to_market,
    calculate_ev_adjusted,
    passes_hybrid_gates,
    calculate_stake,
    MIN_DISAGREEMENT_RATIO,
    MIN_EDGE_ABSOLUTE,
    MIN_RANK,
    MAX_RANK,
    ODDS_MIN,
    ODDS_MAX,
)

load_dotenv()


def load_production_model():
    """
    Load the production Path A model.
    
    For now, trains a quick model from saved dataset.
    In production, would load from MLflow.
    """
    
    print("\n🤖 Loading Path A model...")
    
    # Load training data
    df = pl.read_parquet("data/training_dataset.parquet")
    
    # Train set
    train = df.filter((pl.col("race_date") >= pl.lit("2006-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
                       (pl.col("race_date") <= pl.lit("2023-12-31").str.strptime(pl.Date, "%Y-%m-%d")))
    
    features = [f for f in ABILITY_FEATURES if f in train.columns]
    
    X_train = train.select(features).fill_null(0).to_pandas()
    y_train = train["won"].to_pandas()
    
    # Train
    model = LGBMClassifier(
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
        verbosity=-1
    )
    model.fit(X_train, y_train)
    
    # Calibrate
    p_train = model.predict_proba(X_train)[:, 1]
    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(p_train, y_train)
    
    print(f"   ✅ Model loaded and calibrated")
    
    return model, iso, features


def score_date(target_date: str, model, calibrator, features):
    """
    Score all races for a target date.
    
    Args:
        target_date: Date to score (YYYY-MM-DD)
        model: Trained LightGBM model
        calibrator: Isotonic calibrator
        features: Feature list
        
    Returns:
        DataFrame with bet recommendations
    """
    
    print(f"\n📊 Scoring races for {target_date}...")
    
    # Build features for target date
    df = build_training_data(
        date_from=target_date,
        date_to=target_date,
        output_path=None
    )
    
    if len(df) == 0:
        print(f"   ⚠️  No races found for {target_date}")
        return pl.DataFrame()
    
    print(f"   Loaded {len(df)} horses from {df['race_id'].n_unique()} races")
    
    # Predict
    X = df.select(features).fill_null(0).to_pandas()
    p_raw = model.predict_proba(X)[:, 1]
    p_cal = calibrator.predict(p_raw)
    
    df = df.with_columns(pl.Series("p_model", p_cal))
    
    # Add market features
    df = add_market_features_from_data(df)
    
    print(f"   After market filter: {len(df)} horses")
    
    # Calculate disagreement
    df = df.with_columns([
        (pl.col("p_model") / pl.col("q_vigfree")).alias("disagreement_ratio"),
        (pl.col("p_model") - pl.col("q_vigfree")).alias("edge_absolute"),
    ])
    
    # Apply hybrid logic
    df_pd = df.to_pandas()
    
    df_pd["lambda"] = df_pd.apply(
        lambda r: get_adaptive_lambda(r["decimal_odds"], r["market_rank"], r["overround"]),
        axis=1
    )
    
    df_pd["p_blend"] = df_pd.apply(
        lambda r: blend_to_market(r["p_model"], r["q_vigfree"], r["lambda"]),
        axis=1
    )
    
    df_pd["ev_adjusted"] = df_pd.apply(
        lambda r: calculate_ev_adjusted(r["p_blend"], r["decimal_odds"], r["market_rank"]),
        axis=1
    )
    
    df_pd["passes_gates"], df_pd["gate_reason"] = zip(*df_pd.apply(
        lambda r: passes_hybrid_gates(r.to_dict()),
        axis=1
    ))
    
    df_pd["stake_units"] = df_pd.apply(
        lambda r: calculate_stake(r["p_blend"], r["decimal_odds"]) if r["passes_gates"] else 0.0,
        axis=1
    )
    
    df = pl.from_pandas(df_pd)
    
    # Filter to passing horses
    candidates = df.filter(pl.col("passes_gates") == True)
    
    print(f"   Candidates passing all gates: {len(candidates)}")
    
    # Top-1 per race
    if len(candidates) > 0:
        candidates_pd = candidates.to_pandas()
        candidates_pd = candidates_pd.sort_values(["race_id", "edge_absolute"], ascending=[True, False])
        bets = candidates_pd.groupby("race_id", as_index=False).head(1)
        
        print(f"   Final bets (top-1 per race): {len(bets)}")
        
        return pl.from_pandas(bets)
    
    return pl.DataFrame()


def display_bets(bets: pl.DataFrame):
    """Display bet recommendations."""
    
    if len(bets) == 0:
        print(f"\n⚠️  No bets found for this date")
        print(f"   All horses filtered out by 6-gate system")
        return
    
    print(f"\n" + "=" * 100)
    print(f"🎯 BET RECOMMENDATIONS")
    print(f"=" * 100)
    
    total_stake = bets["stake_units"].sum()
    
    print(f"\nTotal Bets: {len(bets)}")
    print(f"Total Stake: {total_stake:.3f} units")
    print(f"\n{'='*100}")
    
    bets_pd = bets.to_pandas()
    
    for idx, row in bets_pd.iterrows():
        print(f"\n🏇 Race {idx+1}")
        print(f"   Time: {row['off_time']}")
        print(f"   Course: {row.get('course_name', 'Unknown')}")
        print(f"   Horse: {row.get('horse_name', f'Horse ID {row['horse_id']}')} (#{row.get('num', '?')})")
        print(f"   Odds: {row['decimal_odds']:.2f} (Market Rank: {row['market_rank']:.0f})")
        print(f"\n   📊 Model Analysis:")
        print(f"      Model Probability: {row['p_model']:.1%}")
        print(f"      Market Probability: {row['q_vigfree']:.1%}")
        print(f"      Disagreement: {row['disagreement_ratio']:.2f}x")
        print(f"      Edge: {row['edge_absolute']:.3f} ({row['edge_absolute']*100:.1f}pp)")
        print(f"      EV (adjusted): {row['ev_adjusted']:.3f} ({row['ev_adjusted']*100:.1f}%)")
        print(f"\n   💰 Bet Recommendation:")
        print(f"      Stake: {row['stake_units']:.3f} units @ {row['decimal_odds']:.2f} odds")
        print(f"      Blending: λ={row['lambda']:.2f} ({(1-row['lambda'])*100:.0f}% model, {row['lambda']*100:.0f}% market)")
        print(f"\n   {'='*100}")


def main():
    parser = argparse.ArgumentParser(description="Score tomorrow's races (Hybrid V3)")
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD), default: tomorrow")
    
    args = parser.parse_args()
    
    # Default to tomorrow
    if args.date:
        target_date = args.date
    else:
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print("=" * 100)
    print("🏇 HYBRID MODEL V3 - Daily Scoring")
    print("=" * 100)
    print(f"\n📅 Target Date: {target_date}")
    print(f"\n⚙️  Configuration:")
    print(f"   Disagreement: ≥ {MIN_DISAGREEMENT_RATIO:.2f}x")
    print(f"   Market Rank: {MIN_RANK}-{MAX_RANK}")
    print(f"   Edge: ≥ {MIN_EDGE_ABSOLUTE*100:.0f}pp")
    print(f"   Odds: {ODDS_MIN:.1f}-{ODDS_MAX:.1f}")
    
    # Load model
    model, calibrator, features = load_production_model()
    
    # Score target date
    bets = score_date(target_date, model, calibrator, features)
    
    # Display
    display_bets(bets)
    
    # Summary
    if len(bets) > 0:
        print(f"\n✅ {len(bets)} bet(s) recommended for {target_date}")
        print(f"\n📊 Expected (based on backtest):")
        print(f"   Win Rate: ~11-12%")
        print(f"   ROI: +3.1%")
        print(f"   Average: ~3-4 bets/day")
    else:
        print(f"\n⚠️  No bets for {target_date}")
        print(f"   This is normal - not every day has qualifying opportunities")
    
    print(f"\n" + "=" * 100)


if __name__ == "__main__":
    main()

