"""
Enhanced Backtest Script with GPR Analysis

Backtests the value betting strategy on 2024-2025 holdout data.
Analyzes performance by:
- gpr_minus_or buckets (our rating vs official rating)
- Odds bands
- Time period (monthly stability)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import os
import polars as pl
import numpy as np
import mlflow
from dotenv import load_dotenv

from giddyup.data.build import build_training_data
from giddyup.data.feature_lists import ABILITY_FEATURES
from giddyup.price.value import ev_win

load_dotenv()

# ===== Configuration =====
EDGE_MIN = float(os.getenv("EDGE_MIN", "0.03"))
ODDS_MIN = float(os.getenv("ODDS_MIN", "2.0"))
EV_MIN = float(os.getenv("EV_MIN", "0.02"))
COMMISSION = float(os.getenv("COMMISSION", "0.02"))
KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", "0.25"))
MAX_STAKE = float(os.getenv("MAX_STAKE", "0.5"))


def load_test_data_with_predictions(
    date_from: str = "2024-01-01",
    date_to: str = "2025-10-16",
    run_id: str = "c582230dc31f47fe8846ad31a2553f99"
) -> pl.DataFrame:
    """
    Load test data and add model predictions.
    
    Args:
        date_from: Start date
        date_to: End date
        run_id: MLflow run ID (from training)
        
    Returns:
        DataFrame with predictions and outcomes
    """
    print(f"\n📊 Loading test data: {date_from} to {date_to}")
    
    # Load data
    df = build_training_data(
        date_from=date_from,
        date_to=date_to,
        output_path=None
    )
    
    print(f"   Loaded {len(df):,} runners from {df['race_id'].n_unique():,} races")
    
    # Load model
    print(f"\n🤖 Loading model from run: {run_id}")
    mlflow.set_tracking_uri('file:///home/smonaghan/GiddyUpModel/giddyup/mlruns')
    model_uri = f"runs:/{run_id}/ensemble"
    model = mlflow.pyfunc.load_model(model_uri)
    
    # Prepare features
    X = df.select([f for f in ABILITY_FEATURES if f in df.columns])
    X = X.with_columns([pl.col(col).fill_null(0) for col in X.columns])
    
    # Predict
    print(f"   Predicting...")
    p_model = model.predict(X.to_pandas()).astype(float)
    
    df = df.with_columns([
        pl.Series(name="p_model", values=p_model)
    ])
    
    print(f"   ✅ Predictions complete")
    
    return df


def compute_value_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """
    Compute value betting metrics: edge, EV, stakes.
    
    Args:
        df: DataFrame with p_model, decimal_odds, won
        
    Returns:
        DataFrame with value metrics added
    """
    print(f"\n🧮 Computing value metrics...")
    
    # Filter to rows with valid odds
    df = df.filter(
        pl.col("decimal_odds").is_not_null() &
        (pl.col("decimal_odds") >= 1.01)
    )
    
    # Market probability
    df = df.with_columns([
        (1.0 / pl.col("decimal_odds")).alias("q_market")
    ])
    
    # Vig-free per race
    overround = df.group_by("race_id").agg([
        pl.col("q_market").sum().alias("overround")
    ])
    
    df = df.join(overround, on="race_id")
    
    df = df.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
    ])
    
    # Edge
    df = df.with_columns([
        (pl.col("p_model") - pl.col("q_vigfree")).alias("edge_prob")
    ])
    
    # EV after commission
    def calc_ev(p, odds):
        return ev_win(p, odds, COMMISSION)
    
    df = df.with_columns([
        pl.struct(["p_model", "decimal_odds"]).map_elements(
            lambda x: calc_ev(x["p_model"], x["decimal_odds"]),
            return_dtype=pl.Float64
        ).alias("ev_after_commission")
    ])
    
    # ROI per bet (actual result)
    df = df.with_columns([
        pl.when(pl.col("won") == 1)
        .then((pl.col("decimal_odds") - 1.0) * (1.0 - COMMISSION) - 1.0)
        .otherwise(-1.0)
        .alias("roi_bet")
    ])
    
    print(f"   ✅ Metrics computed")
    
    return df


def apply_filters(df: pl.DataFrame) -> pl.DataFrame:
    """
    Apply betting filters.
    
    Args:
        df: DataFrame with value metrics
        
    Returns:
        Filtered DataFrame (bets only)
    """
    print(f"\n🔍 Applying filters:")
    print(f"   Edge >= {EDGE_MIN:.3f}")
    print(f"   Odds >= {ODDS_MIN:.2f}")
    print(f"   EV >= {EV_MIN:.3f}")
    
    n_before = len(df)
    
    bets = df.filter(
        (pl.col("edge_prob") >= EDGE_MIN) &
        (pl.col("decimal_odds") >= ODDS_MIN) &
        (pl.col("ev_after_commission") >= EV_MIN)
    )
    
    n_after = len(bets)
    
    print(f"   {n_before:,} horses → {n_after:,} bets ({n_after/max(1,n_before)*100:.1f}%)")
    
    return bets


def analyze_by_gpr_delta(bets: pl.DataFrame) -> None:
    """
    Analyze performance by gpr_minus_or buckets.
    
    Args:
        bets: DataFrame with bets and outcomes
    """
    print(f"\n" + "=" * 80)
    print(f"📊 PERFORMANCE BY GPR MINUS OR")
    print(f"=" * 80)
    
    # Create buckets
    bets = bets.with_columns([
        pl.when(pl.col("gpr_minus_or") < -10).then("< -10 (much worse)")
        .when(pl.col("gpr_minus_or") < -5).then("-10 to -5 (worse)")
        .when(pl.col("gpr_minus_or") < 0).then("-5 to 0 (slightly worse)")
        .when(pl.col("gpr_minus_or") < 5).then("0 to +5 (slightly better)")
        .when(pl.col("gpr_minus_or") < 10).then("+5 to +10 (better)")
        .otherwise("+10+ (much better)")
        .alias("gpr_bucket")
    ])
    
    # Analyze per bucket
    analysis = bets.group_by("gpr_bucket").agg([
        pl.len().alias("n_bets"),
        pl.col("decimal_odds").mean().alias("avg_odds"),
        pl.col("edge_prob").mean().alias("avg_edge"),
        pl.col("roi_bet").mean().alias("roi"),
        pl.col("roi_bet").sum().alias("total_pnl"),
        pl.col("won").mean().alias("win_rate"),
    ]).sort("gpr_bucket")
    
    print(analysis)
    
    # Overall expectation
    print(f"\n💡 Insight:")
    print(f"   Horses with GPR >> OR should outperform (positive ROI)")
    print(f"   Horses with GPR << OR should underperform (avoid these)")


def analyze_by_odds_band(bets: pl.DataFrame) -> None:
    """
    Analyze performance by odds bands.
    
    Args:
        bets: DataFrame with bets and outcomes
    """
    print(f"\n" + "=" * 80)
    print(f"📊 PERFORMANCE BY ODDS BAND")
    print(f"=" * 80)
    
    # Create odds bands
    bets = bets.with_columns([
        pl.when(pl.col("decimal_odds") < 3.0).then("2.0-3.0")
        .when(pl.col("decimal_odds") < 5.0).then("3.0-5.0")
        .when(pl.col("decimal_odds") < 8.0).then("5.0-8.0")
        .when(pl.col("decimal_odds") < 15.0).then("8.0-15.0")
        .otherwise("15.0+")
        .alias("odds_band")
    ])
    
    analysis = bets.group_by("odds_band").agg([
        pl.len().alias("n_bets"),
        pl.col("decimal_odds").mean().alias("avg_odds"),
        pl.col("edge_prob").mean().alias("avg_edge"),
        pl.col("roi_bet").mean().alias("roi"),
        pl.col("roi_bet").sum().alias("total_pnl"),
        pl.col("won").mean().alias("win_rate"),
    ]).sort("odds_band")
    
    print(analysis)


def analyze_by_month(bets: pl.DataFrame) -> None:
    """
    Analyze performance by month for stability check.
    
    Args:
        bets: DataFrame with bets and outcomes
    """
    print(f"\n" + "=" * 80)
    print(f"📊 PERFORMANCE BY MONTH (Stability Check)")
    print(f"=" * 80)
    
    # Extract year-month
    bets = bets.with_columns([
        pl.col("race_date").dt.strftime("%Y-%m").alias("year_month")
    ])
    
    analysis = bets.group_by("year_month").agg([
        pl.len().alias("n_bets"),
        pl.col("decimal_odds").mean().alias("avg_odds"),
        pl.col("roi_bet").mean().alias("roi"),
        pl.col("roi_bet").sum().alias("total_pnl"),
    ]).sort("year_month")
    
    print(analysis)
    
    # Stability metrics
    monthly_rois = analysis["roi"].to_numpy()
    
    print(f"\n📈 Stability Metrics:")
    print(f"   Mean Monthly ROI: {monthly_rois.mean():.3f} ({monthly_rois.mean()*100:.1f}%)")
    print(f"   Std Dev: {monthly_rois.std():.3f}")
    print(f"   Sharpe-ish: {monthly_rois.mean()/max(monthly_rois.std(), 0.001):.2f}")
    print(f"   Positive Months: {(monthly_rois > 0).sum()}/{len(monthly_rois)}")


def overall_summary(bets: pl.DataFrame) -> None:
    """
    Print overall backtest summary.
    
    Args:
        bets: DataFrame with bets and outcomes
    """
    print(f"\n" + "=" * 80)
    print(f"🎯 OVERALL BACKTEST SUMMARY")
    print(f"=" * 80)
    
    n_bets = len(bets)
    n_wins = bets["won"].sum()
    total_pnl = bets["roi_bet"].sum()
    roi = bets["roi_bet"].mean()
    avg_odds = bets["decimal_odds"].mean()
    avg_edge = bets["edge_prob"].mean()
    
    print(f"\n📊 Results:")
    print(f"   Bets: {n_bets:,}")
    print(f"   Wins: {n_wins:,} ({n_wins/n_bets*100:.1f}%)")
    print(f"   Avg Odds: {avg_odds:.2f}")
    print(f"   Avg Edge: {avg_edge:.3f} ({avg_edge*100:.1f}pp)")
    print(f"\n💰 Financials (1 unit per bet):")
    print(f"   Total P&L: {total_pnl:+.2f} units")
    print(f"   ROI: {roi:.3f} ({roi*100:+.1f}%)")
    print(f"   Commission Paid: ~{n_wins * COMMISSION:.2f} units")
    
    # Risk metrics
    roi_values = bets["roi_bet"].to_numpy()
    cumulative_pnl = np.cumsum(roi_values)
    running_max = np.maximum.accumulate(cumulative_pnl)
    drawdown = running_max - cumulative_pnl
    max_dd = drawdown.max()
    
    print(f"\n⚠️  Risk:")
    print(f"   Max Drawdown: {max_dd:.2f} units")
    print(f"   Sharpe (approx): {roi / max(roi_values.std(), 0.001):.2f}")
    
    # Verdict
    print(f"\n" + "=" * 80)
    if roi > 0.02 and n_bets >= 100:
        print(f"✅ VERDICT: Model shows POSITIVE EDGE")
        print(f"   ROI: {roi*100:+.1f}% after {COMMISSION*100:.0f}% commission")
        print(f"   Sample: {n_bets:,} bets (sufficient)")
    elif roi > 0 and n_bets >= 100:
        print(f"⚠️  VERDICT: Model shows MARGINAL EDGE")
        print(f"   ROI: {roi*100:+.1f}% (low but positive)")
        print(f"   Consider: tighter filters or more data")
    else:
        print(f"❌ VERDICT: Model does NOT show edge")
        print(f"   ROI: {roi*100:+.1f}%")
        print(f"   Action: Review calibration, features, or thresholds")
    print(f"=" * 80)


def main():
    print("=" * 80)
    print("🏇 GIDDYUP VALUE BACKTEST (2024-2025)")
    print("=" * 80)
    print(f"\n⚙️  Configuration:")
    print(f"   Edge: >= {EDGE_MIN:.3f} ({EDGE_MIN*100:.1f}pp)")
    print(f"   Odds: >= {ODDS_MIN:.2f}")
    print(f"   EV: >= {EV_MIN:.3f} ({EV_MIN*100:.1f}%)")
    print(f"   Commission: {COMMISSION:.3f} ({COMMISSION*100:.1f}%)")
    
    # Load test data with predictions
    df = load_test_data_with_predictions(
        date_from="2024-01-01",
        date_to="2025-10-16",
        run_id="c582230dc31f47fe8846ad31a2553f99"  # Latest training run
    )
    
    # Compute value metrics
    df = compute_value_metrics(df)
    
    # Filter to bets
    bets = apply_filters(df)
    
    if len(bets) == 0:
        print(f"\n❌ No bets found with current filters")
        print(f"   Try relaxing thresholds")
        return
    
    # Overall summary
    overall_summary(bets)
    
    # Detailed analyses
    analyze_by_gpr_delta(bets)
    analyze_by_odds_band(bets)
    analyze_by_month(bets)
    
    print(f"\n✅ Backtest complete!")


if __name__ == "__main__":
    main()

