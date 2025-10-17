"""
Hybrid Model Backtest

Uses:
- Path A model for predictions (ability-only training)
- Market features for intelligent filtering
- 6-gate system for selection
- Adaptive blending based on market context
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.isotonic import IsotonicRegression

from giddyup.data.feature_lists import ABILITY_FEATURES
from giddyup.data.market import add_market_features_from_data
from giddyup.models.hybrid import (
    score_hybrid,
    select_top_per_race,
    calculate_stake,
    MIN_DISAGREEMENT_RATIO,
    MIN_EDGE_ABSOLUTE,
    MIN_RANK,
    MAX_RANK,
    ODDS_MIN,
    ODDS_MAX,
    MAX_OVERROUND,
    MIN_EV_ADJUSTED,
    COMMISSION,
)

print("=" * 80)
print("🏇 HYBRID MODEL BACKTEST")
print("Path A Training + Market-Aware Scoring")
print("=" * 80)

print(f"\n⚙️  Hybrid Configuration:")
print(f"   Disagreement: ≥ {MIN_DISAGREEMENT_RATIO:.2f}x (model {(MIN_DISAGREEMENT_RATIO-1)*100:.0f}%+ higher)")
print(f"   Market Rank: {MIN_RANK}-{MAX_RANK} (avoid favorites)")
print(f"   Edge: ≥ {MIN_EDGE_ABSOLUTE*100:.0f}pp")
print(f"   Odds: {ODDS_MIN:.1f}-{ODDS_MAX:.1f}")
print(f"   Overround: ≤ {MAX_OVERROUND:.2f}")
print(f"   EV (adj): ≥ {MIN_EV_ADJUSTED*100:.0f}%")
print(f"   Top-1 per race by edge")

# ===== Load Data =====

print("\n📊 Loading dataset...")
df = pl.read_parquet("data/training_dataset.parquet")
print(f"   Loaded {len(df):,} rows")

# Features
features = [f for f in ABILITY_FEATURES if f in df.columns]
print(f"\n📋 Using {len(features)} ability features for predictions")

# Split
train = df.filter((pl.col("race_date") >= pl.lit("2006-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
                   (pl.col("race_date") <= pl.lit("2023-12-31").str.strptime(pl.Date, "%Y-%m-%d")))
test = df.filter((pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d")))

print(f"\n📅 Data Split:")
print(f"   Train: {len(train):,} rows (2006-2023)")
print(f"   Test:  {len(test):,} rows (2024-2025)")

# ===== Train Path A Model =====

print(f"\n🚂 Training Path A model (ability-only)...")

X_train = train.select(features).fill_null(0).to_pandas()
y_train = train["won"].to_pandas()

X_test = test.select(features).fill_null(0).to_pandas()
y_test = test["won"].to_pandas()

model = LGBMClassifier(
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31,
    random_state=42,
    verbosity=-1
)
model.fit(X_train, y_train)

print(f"   ✅ Model trained")

# ===== Predict =====

print(f"\n🔮 Generating predictions...")
p_train = model.predict_proba(X_train)[:, 1]
p_test_raw = model.predict_proba(X_test)[:, 1]

# Calibrate
iso = IsotonicRegression(out_of_bounds='clip')
iso.fit(p_train, y_train)
p_test_cal = iso.predict(p_test_raw)

print(f"   ✅ Predictions calibrated")

# ===== Add Predictions First =====

print(f"\n💰 Adding predictions and market features...")

# Add predictions to test set BEFORE market filtering
test = test.with_columns(pl.Series("p_model", p_test_cal))

# Add market features from decimal_odds (this may filter rows)
test = add_market_features_from_data(test)

print(f"   ✅ Market features added")
print(f"      Final test size: {len(test):,} horses")
print(f"      - market_rank")
print(f"      - q_vigfree")
print(f"      - overround")
print(f"      - is_favorite")

# ===== Apply Hybrid Scoring =====

print(f"\n🎯 Applying hybrid 6-gate system...")

# Score with hybrid logic (p_model already in df)
# Calculate disagreement metrics
test = test.with_columns([
    (pl.col("p_model") / pl.col("q_vigfree")).alias("disagreement_ratio"),
    (pl.col("p_model") - pl.col("q_vigfree")).alias("edge_absolute"),
])

# Apply adaptive blending and gates
test_pd = test.to_pandas()

from giddyup.models.hybrid import get_adaptive_lambda, blend_to_market, calculate_ev_adjusted, passes_hybrid_gates

test_pd["lambda"] = test_pd.apply(
    lambda r: get_adaptive_lambda(r["decimal_odds"], r["market_rank"], r["overround"]),
    axis=1
)

test_pd["p_blend"] = test_pd.apply(
    lambda r: blend_to_market(r["p_model"], r["q_vigfree"], r["lambda"]),
    axis=1
)

test_pd["ev_adjusted"] = test_pd.apply(
    lambda r: calculate_ev_adjusted(r["p_blend"], r["decimal_odds"], r["market_rank"]),
    axis=1
)

test_pd["passes_gates"], test_pd["gate_reason"] = zip(*test_pd.apply(
    lambda r: passes_hybrid_gates(r.to_dict()),
    axis=1
))

test_scored = pl.from_pandas(test_pd)

# Select bets (top-1 per race)
bets = select_top_per_race(test_scored)

print(f"\n   Candidates passing all gates: {test_scored.filter(pl.col('passes_gates') == True).height:,}")
print(f"   Final bets (top-1 per race): {len(bets):,}")

# ===== Calculate Stakes =====

if len(bets) > 0:
    bets_pd = bets.to_pandas()
    
    bets_pd["stake_units"] = bets_pd.apply(
        lambda r: calculate_stake(r["p_blend"], r["decimal_odds"]),
        axis=1
    )
    
    # Calculate ROI
    bets_pd["roi_bet"] = bets_pd.apply(
        lambda r: (r["decimal_odds"] - 1) * (1 - COMMISSION) - 1 if r["won"] == 1 else -1.0,
        axis=1
    )
    
    bets_pd["pnl"] = bets_pd["roi_bet"] * bets_pd["stake_units"]
    
    bets = pl.from_pandas(bets_pd)
    
    # ===== Results =====
    
    print(f"\n" + "=" * 80)
    print(f"💰 HYBRID BACKTEST RESULTS")
    print(f"=" * 80)
    
    n_bets = len(bets)
    n_wins = bets["won"].sum()
    total_stake = bets["stake_units"].sum()
    total_pnl = bets["pnl"].sum()
    roi = total_pnl / max(1, total_stake)
    avg_odds = bets["decimal_odds"].mean()
    avg_edge = bets["edge_absolute"].mean()
    avg_disagreement = bets["disagreement_ratio"].mean()
    avg_rank = bets["market_rank"].mean()
    
    print(f"\n📊 Overall Performance:")
    print(f"   Bets: {n_bets:,} ({n_bets/22*12:.0f}/year)")
    print(f"   Wins: {n_wins:,} ({n_wins/n_bets*100:.1f}%)")
    print(f"   Avg Odds: {avg_odds:.2f}")
    print(f"   Avg Market Rank: {avg_rank:.1f}")
    print(f"   Avg Disagreement: {avg_disagreement:.2f}x")
    print(f"   Avg Edge: {avg_edge:.3f} ({avg_edge*100:.1f}pp)")
    
    print(f"\n💰 Financial Results:")
    print(f"   Total Staked: {total_stake:.2f}u")
    print(f"   Total P&L: {total_pnl:+.2f}u")
    print(f"   ROI: {roi:.3f} ({roi*100:+.1f}%)")
    
    # Risk metrics
    cumulative_pnl = np.cumsum(bets_pd["pnl"].values)
    running_max = np.maximum.accumulate(np.concatenate([[0], cumulative_pnl]))
    drawdown = running_max[1:] - cumulative_pnl
    max_dd = drawdown.max() if len(drawdown) > 0 else 0
    
    print(f"\n⚠️  Risk Metrics:")
    print(f"   Max Drawdown: {max_dd:.2f}u")
    if len(bets) > 1:
        sharpe = roi / max(bets_pd["roi_bet"].std(), 0.001)
        print(f"   Sharpe (approx): {sharpe:.2f}")
    
    # ===== By Odds Band =====
    
    print(f"\n📊 Performance by Odds Band:")
    
    def get_odds_band(odds):
        if odds < 5.0:
            return "4-5"
        elif odds < 8.0:
            return "5-8"
        elif odds < 12.0:
            return "8-12"
        else:
            return "12-15"
    
    bets_pd["odds_band"] = bets_pd["decimal_odds"].apply(get_odds_band)
    
    band_stats = bets_pd.groupby("odds_band").agg({
        "decimal_odds": ["count", "mean"],
        "market_rank": "mean",
        "edge_absolute": "mean",
        "stake_units": "sum",
        "pnl": "sum",
        "won": "mean",
    })
    band_stats.columns = ["n_bets", "avg_odds", "avg_rank", "avg_edge", "total_stake", "total_pnl", "win_rate"]
    band_stats["roi"] = band_stats["total_pnl"] / band_stats["total_stake"]
    
    print(band_stats)
    
    # ===== By Market Rank =====
    
    print(f"\n📊 Performance by Market Rank:")
    
    rank_stats = bets_pd.groupby("market_rank").agg({
        "decimal_odds": ["count", "mean"],
        "edge_absolute": "mean",
        "pnl": "sum",
        "won": "mean",
    })
    rank_stats.columns = ["n_bets", "avg_odds", "avg_edge", "total_pnl", "win_rate"]
    
    print(rank_stats)
    
    # ===== Monthly Performance =====
    
    print(f"\n📅 Monthly Performance:")
    
    bets_pd["year_month"] = bets_pd["race_date"].apply(lambda d: d.strftime("%Y-%m"))
    
    monthly = bets_pd.groupby("year_month").agg({
        "pnl": "sum",
        "stake_units": "sum",
        "decimal_odds": "count",
    })
    monthly.columns = ["pnl", "stake", "n_bets"]
    monthly["roi"] = monthly["pnl"] / monthly["stake"]
    monthly = monthly.sort_index()
    
    print(monthly.head(15))
    print("...")
    print(monthly.tail(7))
    
    positive_months = (monthly["roi"] > 0).sum()
    print(f"\n   Positive months: {positive_months}/{len(monthly)} ({positive_months/len(monthly)*100:.0f}%)")
    
    # ===== Comparison =====
    
    print(f"\n" + "=" * 80)
    print(f"📈 COMPARISON: Path A vs Hybrid")
    print(f"=" * 80)
    
    print(f"\nPath A V3 (Pure Ability, Tight Filters):")
    print(f"   10 bets | +118.3% ROI | 8.00 avg odds | 5 bets/year")
    
    print(f"\nHybrid (Ability Training + Market Filtering):")
    print(f"   {n_bets:,} bets | {roi*100:+.1f}% ROI | {avg_odds:.2f} avg odds | {n_bets/22*12:.0f} bets/year")
    
    # ===== Verdict =====
    
    print(f"\n" + "=" * 80)
    if roi > 0.05 and n_bets >= 100:
        print(f"✅ HYBRID MODEL SUCCESS")
        print(f"   ROI: {roi*100:+.1f}% over {n_bets:,} bets")
        print(f"   Volume: {n_bets/22*12:.0f} bets/year (sufficient for validation)")
        print(f"   Total P&L: {total_pnl:+.2f}u")
        print(f"\n   This is a VIABLE strategy! ✨")
        print(f"\n   Next Steps:")
        print(f"   1. Register model in MLflow")
        print(f"   2. Create production scoring script")
        print(f"   3. Paper trade for 1-2 months")
        print(f"   4. Deploy with small stakes if validated")
    elif roi > 0.02 and n_bets >= 50:
        print(f"⚠️  HYBRID MODEL: MARGINAL")
        print(f"   ROI: {roi*100:+.1f}% over {n_bets:,} bets")
        print(f"   Edge exists but small")
        print(f"\n   Consider:")
        print(f"   - Tighter disagreement threshold (1.4x)")
        print(f"   - Stricter rank filter (4-7 only)")
        print(f"   - Paper trade to validate")
    elif n_bets < 50:
        print(f"⚠️  INSUFFICIENT SAMPLE SIZE")
        print(f"   Only {n_bets} bets found")
        print(f"   ROI: {roi*100:+.1f}%")
        print(f"\n   Action: Relax filters to get more bets")
    else:
        print(f"❌ HYBRID MODEL: NO EDGE")
        print(f"   ROI: {roi*100:+.1f}% over {n_bets:,} bets")
        print(f"\n   Try:")
        print(f"   1. Increase disagreement to 1.5x")
        print(f"   2. Tighten edge to 0.05")
        print(f"   3. Focus on 6-12 odds only")
    print(f"=" * 80)
    
    # ===== Top 10 Best Bets =====
    
    if len(bets) > 0:
        print(f"\n🎯 Top 10 Profitable Bets:")
        top_wins = bets_pd[bets_pd["won"] == 1].nlargest(10, "pnl")
        
        if len(top_wins) > 0:
            for idx, row in top_wins.iterrows():
                print(f"\n   {row['race_date']} | Rank {row['market_rank']:.0f} | {row['decimal_odds']:.2f} odds")
                print(f"      Model: {row['p_model']:.1%} | Market: {row['q_vigfree']:.1%} | Disagreement: {row['disagreement_ratio']:.2f}x")
                print(f"      Edge: {row['edge_absolute']:.3f} | Stake: {row['stake_units']:.3f}u | P&L: +{row['pnl']:.2f}u")
        
        print(f"\n🔴 Top 5 Worst Losses:")
        top_losses = bets_pd[bets_pd["won"] == 0].nsmallest(5, "pnl")
        
        if len(top_losses) > 0:
            for idx, row in top_losses.iterrows():
                print(f"\n   {row['race_date']} | Rank {row['market_rank']:.0f} | {row['decimal_odds']:.2f} odds")
                print(f"      Model: {row['p_model']:.1%} | Market: {row['q_vigfree']:.1%} | Disagreement: {row['disagreement_ratio']:.2f}x")
                print(f"      Edge: {row['edge_absolute']:.3f} | Stake: {row['stake_units']:.3f}u | P&L: {row['pnl']:.2f}u")

else:
    print(f"\n❌ No bets found!")
    print(f"   All horses filtered out by 6-gate system")
    print(f"   Try relaxing thresholds")

print(f"\n✅ Hybrid backtest complete!")

