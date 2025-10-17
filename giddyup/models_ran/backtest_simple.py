"""
Simple backtest without MLflow - load dataset and retrain quickly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.isotonic import IsotonicRegression

print("=" * 80)
print("🏇 SIMPLE BACKTEST (No MLflow)")
print("=" * 80)

# Load the training dataset
print("\n📊 Loading dataset...")
df = pl.read_parquet("data/training_dataset.parquet")
print(f"   Loaded {len(df):,} rows")

# Features
from giddyup.data.feature_lists import ABILITY_FEATURES

features = [f for f in ABILITY_FEATURES if f in df.columns]
print(f"\n📋 Using {len(features)} features")

# Split
train = df.filter((pl.col("race_date") >= pl.lit("2006-01-01").str.strptime(pl.Date, "%Y-%m-%d")) &
                   (pl.col("race_date") <= pl.lit("2023-12-31").str.strptime(pl.Date, "%Y-%m-%d")))
test = df.filter((pl.col("race_date") >= pl.lit("2024-01-01").str.strptime(pl.Date, "%Y-%m-%d")))

print(f"\n📅 Data Split:")
print(f"   Train: {len(train):,} rows")
print(f"   Test:  {len(test):,} rows")

# Prepare
X_train = train.select(features).fill_null(0).to_pandas()
y_train = train["won"].to_pandas()

X_test = test.select(features).fill_null(0).to_pandas()
y_test = test["won"].to_pandas()

# Train
print(f"\n🚂 Training LightGBM...")
model = LGBMClassifier(
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31,
    random_state=42,
    verbosity=-1
)
model.fit(X_train, y_train)

# Predict
print(f"\n🔮 Predicting...")
p_train = model.predict_proba(X_train)[:, 1]
p_test_raw = model.predict_proba(X_test)[:, 1]

# Calibrate
print(f"\n📐 Calibrating...")
iso = IsotonicRegression(out_of_bounds='clip')
iso.fit(p_train, y_train)
p_test = iso.predict(p_test_raw)

# Add to test dataframe
test = test.with_columns(pl.Series("p_model", p_test))

# Metrics
from sklearn.metrics import roc_auc_score, log_loss

print(f"\n📊 Metrics:")
print(f"   Test AUC: {roc_auc_score(y_test, p_test):.4f}")
print(f"   Test Log Loss: {log_loss(y_test, p_test):.4f}")

# Value betting analysis
print(f"\n" + "=" * 80)
print(f"💰 VALUE BETTING ANALYSIS")
print(f"=" * 80)

# Filter to valid odds
test_bets = test.filter(
    pl.col("decimal_odds").is_not_null() & 
    (pl.col("decimal_odds") >= 1.01)
)

# Market probability
test_bets = test_bets.with_columns([
    (1.0 / pl.col("decimal_odds")).alias("q_market")
])

# Vig-free
overround = test_bets.group_by("race_id").agg([
    pl.col("q_market").sum().alias("overround")
])
test_bets = test_bets.join(overround, on="race_id")
test_bets = test_bets.with_columns([
    (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
])

# Edge
test_bets = test_bets.with_columns([
    (pl.col("p_model") - pl.col("q_vigfree")).alias("edge_prob")
])

# ROI per bet (with 2% commission)
COMMISSION = 0.02
test_bets = test_bets.with_columns([
    pl.when(pl.col("won") == 1)
    .then((pl.col("decimal_odds") - 1) * (1 - COMMISSION) - 1)
    .otherwise(-1.0)
    .alias("roi_bet")
])

# Filter by edge and odds
EDGE_MIN = 0.03
ODDS_MIN = 2.0

filtered = test_bets.filter(
    (pl.col("edge_prob") >= EDGE_MIN) &
    (pl.col("decimal_odds") >= ODDS_MIN)
)

print(f"\n🔍 Filters:")
print(f"   Edge >= {EDGE_MIN:.3f} ({EDGE_MIN*100:.1f}pp)")
print(f"   Odds >= {ODDS_MIN:.2f}")
print(f"\n📊 Results:")
print(f"   Total horses: {len(test_bets):,}")
print(f"   Bets after filter: {len(filtered):,} ({len(filtered)/len(test_bets)*100:.1f}%)")

if len(filtered) > 0:
    n_bets = len(filtered)
    n_wins = filtered["won"].sum()
    total_pnl = filtered["roi_bet"].sum()
    roi = filtered["roi_bet"].mean()
    avg_odds = filtered["decimal_odds"].mean()
    avg_edge = filtered["edge_prob"].mean()
    
    print(f"\n💰 Financial Performance:")
    print(f"   Bets: {n_bets:,}")
    print(f"   Wins: {n_wins:,} ({n_wins/n_bets*100:.1f}%)")
    print(f"   Avg Odds: {avg_odds:.2f}")
    print(f"   Avg Edge: {avg_edge:.3f} ({avg_edge*100:.1f}pp)")
    print(f"   Total P&L: {total_pnl:+.2f} units")
    print(f"   ROI: {roi:.3f} ({roi*100:+.1f}%)")
    
    # By GPR delta (if available)
    if "gpr_minus_or" in filtered.columns:
        print(f"\n📊 Performance by GPR - OR Delta:")
        gpr_buckets = filtered.with_columns([
            pl.when(pl.col("gpr_minus_or") < -5).then(pl.lit("< -5 (worse)"))
            .when(pl.col("gpr_minus_or") < 0).then(pl.lit("-5 to 0"))
            .when(pl.col("gpr_minus_or") < 5).then(pl.lit("0 to +5"))
            .otherwise(pl.lit("+5+ (better)"))
            .alias("gpr_or_bucket")
        ])
        
        gpr_analysis = gpr_buckets.group_by("gpr_or_bucket").agg([
            pl.len().alias("n_bets"),
            pl.col("decimal_odds").mean().alias("avg_odds"),
            pl.col("edge_prob").mean().alias("avg_edge"),
            pl.col("roi_bet").mean().alias("roi"),
            pl.col("won").mean().alias("win_rate"),
        ]).sort("gpr_or_bucket")
        
        print(gpr_analysis)
    else:
        print(f"\n⚠️  gpr_minus_or not available (Path A uses pure ability only)")
    
    # By odds band
    print(f"\n📊 Performance by Odds Band:")
    odds_buckets = filtered.with_columns([
        pl.when(pl.col("decimal_odds") < 3.0).then(pl.lit("2.0-3.0"))
        .when(pl.col("decimal_odds") < 5.0).then(pl.lit("3.0-5.0"))
        .when(pl.col("decimal_odds") < 8.0).then(pl.lit("5.0-8.0"))
        .when(pl.col("decimal_odds") < 15.0).then(pl.lit("8.0-15.0"))
        .otherwise(pl.lit("15.0+"))
        .alias("odds_band")
    ])
    
    odds_analysis = odds_buckets.group_by("odds_band").agg([
        pl.len().alias("n_bets"),
        pl.col("decimal_odds").mean().alias("avg_odds"),
        pl.col("roi_bet").mean().alias("roi"),
        pl.col("won").mean().alias("win_rate"),
    ]).sort("odds_band")
    
    print(odds_analysis)
    
    # Verdict
    print(f"\n" + "=" * 80)
    if roi > 0.02:
        print(f"✅ POSITIVE EDGE DETECTED")
        print(f"   ROI: {roi*100:+.1f}% over {n_bets:,} bets")
        print(f"   This model shows real value!")
    elif roi > 0:
        print(f"⚠️  MARGINAL EDGE")
        print(f"   ROI: {roi*100:+.1f}% (small but positive)")
    else:
        print(f"❌ NO EDGE")
        print(f"   ROI: {roi*100:+.1f}%")
        print(f"   Model needs improvement")
    print(f"=" * 80)
else:
    print(f"\n❌ No bets found with current filters!")

print(f"\n✅ Backtest complete!")

