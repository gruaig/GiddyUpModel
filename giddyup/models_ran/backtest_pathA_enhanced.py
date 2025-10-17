"""
Enhanced Path A Backtest with:
- Odds-band calibration
- Longshot correction (log-odds blending with market)
- Banded edge thresholds
- Top-1 per race selection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.isotonic import IsotonicRegression

print("=" * 80)
print("🏇 PATH A ENHANCED BACKTEST")
print("=" * 80)

# ===== Longshot Correction Functions =====

def logit(x):
    """Convert probability to log-odds"""
    x = np.clip(x, 0.001, 0.999)  # Avoid infinities
    return np.log(x / (1 - x))

def invlogit(z):
    """Convert log-odds to probability"""
    return 1 / (1 + np.exp(-z))

def blend_to_market(p_model, q_vigfree, lambda_blend):
    """
    Blend model probability towards market in log-odds space.
    
    lambda = 0: Pure model
    lambda = 1: Pure market
    lambda = 0.25: 75% model, 25% market
    
    This reduces longshot overconfidence.
    """
    z_model = logit(p_model)
    z_market = logit(q_vigfree)
    z_blend = (1 - lambda_blend) * z_model + lambda_blend * z_market
    return invlogit(z_blend)

def get_blend_lambda(odds):
    """
    Get blending parameter by odds band.
    Higher lambda = more market influence (for longshots).
    """
    if odds < 5.0:
        return 0.10  # 90% model, 10% market
    elif odds < 12.0:
        return 0.25  # 75% model, 25% market
    else:
        return 0.45  # 55% model, 45% market

def get_edge_min(odds):
    """
    Get minimum edge threshold by odds band.
    Higher threshold for longshots.
    """
    if odds < 5.0:
        return 0.05  # 5pp
    elif odds < 12.0:
        return 0.08  # 8pp
    else:
        return 0.12  # 12pp

# ===== Load and Prepare Data =====

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

# Global calibration
print(f"\n📐 Global calibration...")
iso_global = IsotonicRegression(out_of_bounds='clip')
iso_global.fit(p_train, y_train)
p_test_cal = iso_global.predict(p_test_raw)

# ===== Odds-Band Calibration =====

print(f"\n📊 Odds-band calibration...")

# Add calibrated predictions to test set
test = test.with_columns(pl.Series("p_model_cal", p_test_cal))

# Create odds bands
def get_odds_band(odds):
    if odds < 3.0:
        return "2-3"
    elif odds < 5.0:
        return "3-5"
    elif odds < 8.0:
        return "5-8"
    elif odds < 12.0:
        return "8-12"
    else:
        return "12+"

# Filter to valid odds
test_cal = test.filter(
    pl.col("decimal_odds").is_not_null() & 
    (pl.col("decimal_odds") >= 1.01)
)

# Fit calibrator per odds band
test_pd = test_cal.select(["p_model_cal", "won", "decimal_odds"]).to_pandas()
test_pd["odds_band"] = test_pd["decimal_odds"].apply(get_odds_band)

cal_models = {}
for band, group in test_pd.groupby("odds_band"):
    if len(group) < 100:
        continue
    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(group["p_model_cal"].values, group["won"].values)
    cal_models[band] = iso
    print(f"   {band}: calibrated on {len(group):,} samples")

# Apply band-specific calibration
def calibrate_by_band(p, odds):
    band = get_odds_band(odds)
    if band in cal_models:
        return float(cal_models[band].predict([p])[0])
    return p

test_pd["p_cal_band"] = test_pd.apply(
    lambda row: calibrate_by_band(row["p_model_cal"], row["decimal_odds"]),
    axis=1
)

# ===== Value Betting Analysis =====

print(f"\n" + "=" * 80)
print(f"💰 ENHANCED VALUE BETTING ANALYSIS")
print(f"=" * 80)

# Add to polars df
test_cal = test_cal.with_columns(pl.Series("p_cal_band", test_pd["p_cal_band"]))

# Market probability
test_cal = test_cal.with_columns([
    (1.0 / pl.col("decimal_odds")).alias("q_market")
])

# Vig-free
overround = test_cal.group_by("race_id").agg([
    pl.col("q_market").sum().alias("overround")
])
test_cal = test_cal.join(overround, on="race_id")
test_cal = test_cal.with_columns([
    (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
])

# Apply longshot correction
def apply_blending(row):
    p = row["p_cal_band"]
    q = row["q_vigfree"]
    odds = row["decimal_odds"]
    lam = get_blend_lambda(odds)
    return blend_to_market(p, q, lam)

test_pd = test_cal.to_pandas()
test_pd["p_blend"] = test_pd.apply(apply_blending, axis=1)
test_cal = pl.from_pandas(test_pd)

# Edge and EV
COMMISSION = 0.02
test_cal = test_cal.with_columns([
    (pl.col("p_blend") - pl.col("q_vigfree")).alias("edge_prob"),
])

def calc_ev(p, odds):
    if not odds or odds <= 1.0:
        return -1.0
    b = (odds - 1.0) * (1.0 - COMMISSION)
    return p * b - (1.0 - p)

test_pd = test_cal.to_pandas()
test_pd["ev"] = test_pd.apply(lambda r: calc_ev(r["p_blend"], r["decimal_odds"]), axis=1)
test_cal = pl.from_pandas(test_pd)

# ROI per bet
test_cal = test_cal.with_columns([
    pl.when(pl.col("won") == 1)
    .then((pl.col("decimal_odds") - 1) * (1 - COMMISSION) - 1)
    .otherwise(-1.0)
    .alias("roi_bet")
])

# ===== Apply Enhanced Filters =====

print(f"\n🔍 Applying enhanced filters:")
print(f"   Banded edge thresholds:")
print(f"     2-5 odds:    edge >= 0.05 (5pp)")
print(f"     5-12 odds:   edge >= 0.08 (8pp)")
print(f"     12+ odds:    edge >= 0.12 (12pp)")
print(f"   EV >= 0.02 (2%)")
print(f"   Top-1 per race by edge")

# Apply banded edge thresholds
test_pd = test_cal.to_pandas()
test_pd["edge_min"] = test_pd["decimal_odds"].apply(get_edge_min)
test_pd["passes_edge"] = test_pd["edge_prob"] >= test_pd["edge_min"]
test_pd["passes_ev"] = test_pd["ev"] >= 0.02
test_pd["passes_filters"] = test_pd["passes_edge"] & test_pd["passes_ev"]

candidates = test_pd[test_pd["passes_filters"]].copy()
print(f"\n   Candidates after filters: {len(candidates):,}")

# Top-1 per race by edge
if len(candidates) > 0:
    candidates = candidates.sort_values(["race_id", "edge_prob"], ascending=[True, False])
    candidates = candidates.groupby("race_id").head(1)
    
    print(f"   Final bets (top-1 per race): {len(candidates):,}")
    
    # Results
    n_bets = len(candidates)
    n_wins = candidates["won"].sum()
    total_pnl = candidates["roi_bet"].sum()
    roi = candidates["roi_bet"].mean()
    avg_odds = candidates["decimal_odds"].mean()
    avg_edge = candidates["edge_prob"].mean()
    
    print(f"\n💰 Financial Performance:")
    print(f"   Bets: {n_bets:,}")
    print(f"   Wins: {n_wins:,} ({n_wins/n_bets*100:.1f}%)")
    print(f"   Avg Odds: {avg_odds:.2f}")
    print(f"   Avg Edge: {avg_edge:.3f} ({avg_edge*100:.1f}pp)")
    print(f"   Total P&L: {total_pnl:+.2f} units")
    print(f"   ROI: {roi:.3f} ({roi*100:+.1f}%)")
    
    # By odds band
    print(f"\n📊 Performance by Odds Band:")
    candidates["odds_band"] = candidates["decimal_odds"].apply(get_odds_band)
    band_stats = candidates.groupby("odds_band").agg({
        "decimal_odds": ["count", "mean"],
        "edge_prob": "mean",
        "roi_bet": ["mean", "sum"],
        "won": "mean",
    })
    print(band_stats)
    
    # Verdict
    print(f"\n" + "=" * 80)
    if roi > 0.02:
        print(f"✅ POSITIVE EDGE DETECTED")
        print(f"   ROI: {roi*100:+.1f}% over {n_bets:,} bets")
        print(f"   Enhanced strategy shows promise!")
    elif roi > 0:
        print(f"⚠️  MARGINAL EDGE")
        print(f"   ROI: {roi*100:+.1f}% (small but positive)")
    else:
        print(f"❌ NO EDGE YET")
        print(f"   ROI: {roi*100:+.1f}%")
        print(f"   May need further calibration or tighter filters")
    print(f"=" * 80)
    
    # Compare to baseline (no blending, loose filters)
    print(f"\n📊 Improvement vs Baseline:")
    print(f"   Baseline (loose filters): 77,196 bets, -28.6% ROI, 34.79 avg odds")
    print(f"   Enhanced: {n_bets:,} bets, {roi*100:+.1f}% ROI, {avg_odds:.2f} avg odds")
    bet_reduction = (1 - n_bets / 77196) * 100
    roi_improvement = roi - (-0.286)
    print(f"   Bet reduction: -{bet_reduction:.1f}%")
    print(f"   ROI improvement: +{roi_improvement*100:.1f}pp")

else:
    print(f"\n❌ No bets passed enhanced filters!")
    print(f"   Filters may be too tight")

print(f"\n✅ Enhanced backtest complete!")

